"""竞赛信息聚合平台 · 后端 API 服务
FastAPI + SQLite · 竞赛聚合 / 分类筛选 / 关键词搜索 / 用户认证 / 收藏
"""
import hashlib
import json
import logging
import os
import secrets
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger("competition_hub")

from database import get_db, init_db
from models import (
    CategoryIn, CategoryOut, CompetitionIn, CompetitionOut, CompetitionList,
    UserRegister, UserLogin, UserOut, AuthOut, FavoriteAction,
)
from seed import seed_if_empty


# ---------------- 安全工具（零额外依赖） ----------------
def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + "$" + dk.hex()


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        return secrets.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


def _gen_token() -> str:
    return secrets.token_urlsafe(32)


TOKEN_TTL_DAYS = 30


def _create_token(conn, user_id: int) -> str:
    token = _gen_token()
    expires = datetime.now() + timedelta(days=TOKEN_TTL_DAYS)
    conn.execute(
        "INSERT INTO auth_tokens (token, user_id, expires_at) VALUES (?,?,?)",
        (token, user_id, expires),
    )
    conn.commit()
    return token


# ---------------- 行 -> Pydantic ----------------
def _row_to_competition(row, conn, user_id=None) -> CompetitionOut:
    data = dict(row)
    cat = conn.execute(
        "SELECT name FROM categories WHERE id=?", (data.get("category_id"),)
    ).fetchone()
    data["category_name"] = cat["name"] if cat else ""
    try:
        data["tags"] = json.loads(data.get("tags") or "[]")
    except Exception:
        data["tags"] = []
    data["is_favorited"] = False
    if user_id:
        fav = conn.execute(
            "SELECT 1 FROM favorites WHERE user_id=? AND competition_id=?",
            (user_id, data["id"]),
        ).fetchone()
        data["is_favorited"] = bool(fav)
    data["featured"] = bool(data.get("featured"))
    return CompetitionOut(**data)


# ---------------- 认证依赖 ----------------
def get_current_user(authorization: str = Header(None)) -> dict | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    conn = get_db()
    row = conn.execute(
        """SELECT u.*, t.expires_at FROM auth_tokens t
           JOIN users u ON u.id = t.user_id WHERE t.token=?""",
        (token,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    expires = datetime.fromisoformat(row["expires_at"]) if isinstance(row["expires_at"], str) else row["expires_at"]
    if expires < datetime.now():
        return None
    return dict(row)


def require_user(authorization: str = Header(None)) -> dict:
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return user


# ---------------- 应用 ----------------
app = FastAPI(title="竞赛信息聚合平台 API", version="1.0.0")

# R1: CORS 收敛为可信源（默认本地开发源，生产通过 ALLOWED_ORIGINS 注入）
_ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-Id"],
)


# R2: 安全响应头中间件（CSP / 防嗅探 / 防点击劫持 / 隐私Referrer）
@app.middleware("http")
async def _security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "media-src 'self' data:; "
        "font-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'",
    )
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    return response


# R3: 认证接口按 IP 限流（固定窗口：10 次/60 秒），防止爆破
_AUTH_RATE_LIMIT = 10
_AUTH_RATE_WINDOW = 60
_auth_hits: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("X-Forwarded-For")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_auth_rate_limit(request: Request):
    ip = _client_ip(request)
    now = time.time()
    window = _auth_hits[ip]
    window[:] = [t for t in window if now - t < _AUTH_RATE_WINDOW]
    if len(window) >= _AUTH_RATE_LIMIT:
        retry = int(_AUTH_RATE_WINDOW - (now - window[0])) + 1
        raise HTTPException(
            status_code=429,
            detail="认证请求过于频繁，请稍后再试",
            headers={"Retry-After": str(max(retry, 1))},
        )
    window.append(now)


# R5: 全局未捕获异常处理 —— 客户端只收到安全文案，内部堆栈落服务端日志
async def _unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("未捕获异常 [%s %s]: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"},
    )


app.add_exception_handler(Exception, _unhandled_exception_handler)


@app.on_event("startup")
def _startup():
    init_db()
    seed_if_empty()


# ---------------- 健康检查 ----------------
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "competition-hub", "time": datetime.now().isoformat()}


# ---------------- 分类 ----------------
@app.get("/api/categories", response_model=list[CategoryOut])
def list_categories():
    conn = get_db()
    rows = conn.execute(
        "SELECT c.*, (SELECT COUNT(*) FROM competitions WHERE category_id=c.id) AS count "
        "FROM categories c ORDER BY c.sort_order, c.id"
    ).fetchall()
    conn.close()
    return [CategoryOut(**dict(r)) for r in rows]


@app.post("/api/categories", response_model=CategoryOut)
def create_category(payload: CategoryIn, _: dict = Depends(require_user)):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO categories (name, slug, icon, description, sort_order) VALUES (?,?,?,?,?)",
            (payload.name, payload.slug, payload.icon, payload.description, payload.sort_order),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM categories WHERE id=?", (cur.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=409, detail="分类 slug 已存在")
    conn.close()
    return CategoryOut(**dict(row))


# ---------------- 竞赛列表（聚合 / 筛选 / 搜索 / 排序 / 分页） ----------------
@app.get("/api/competitions", response_model=CompetitionList)
def list_competitions(
    q: str = Query(None, description="关键词搜索"),
    category: str = Query(None, description="分类 slug"),
    status: str = Query(None, description="upcoming/ongoing/ended"),
    mode: str = Query(None, description="online/offline/hybrid"),
    tag: str = Query(None, description="标签名"),
    sort: str = Query("latest", description="latest/prize/deadline/views"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=60),
    user: dict | None = Depends(get_current_user),
):
    conn = get_db()
    wheres, params = [], []
    if q:
        wheres.append("(c.title LIKE ? OR c.summary LIKE ? OR c.organizer LIKE ? OR c.description LIKE ?)")
        like = f"%{q}%"
        params += [like, like, like, like]
    if category:
        cat = conn.execute("SELECT id FROM categories WHERE slug=?", (category,)).fetchone()
        if not cat:
            conn.close()
            raise HTTPException(status_code=404, detail="分类不存在")
        wheres.append("c.category_id=?")
        params.append(cat["id"])
    if status:
        wheres.append("c.status=?")
        params.append(status)
    if mode:
        wheres.append("c.mode=?")
        params.append(mode)
    if tag:
        wheres.append("c.tags LIKE ?")
        params.append(f'%"{tag}"%')

    where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
    total = conn.execute(
        f"SELECT COUNT(*) AS n FROM competitions c {where_sql}", params
    ).fetchone()["n"]

    order_map = {
        "latest": "c.created_at DESC, c.id DESC",
        "prize": "c.prize_amount DESC, c.id DESC",
        "deadline": "c.reg_deadline ASC, c.id DESC",
        "views": "c.views DESC, c.id DESC",
    }
    order = order_map.get(sort, order_map["latest"])
    offset = (page - 1) * page_size
    rows = conn.execute(
        f"SELECT c.* FROM competitions c {where_sql} ORDER BY {order} LIMIT ? OFFSET ?",
        params + [page_size, offset],
    ).fetchall()
    items = [_row_to_competition(r, conn, user["id"] if user else None) for r in rows]
    conn.close()
    total_pages = (total + page_size - 1) // page_size
    return CompetitionList(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


# ---------------- 竞赛详情 ----------------
@app.get("/api/competitions/{comp_id}", response_model=CompetitionOut)
def get_competition(comp_id: int, user: dict | None = Depends(get_current_user)):
    conn = get_db()
    row = conn.execute("SELECT * FROM competitions WHERE id=?", (comp_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="竞赛不存在")
    conn.execute("UPDATE competitions SET views = views + 1 WHERE id=?", (comp_id,))
    conn.commit()
    out = _row_to_competition(row, conn, user["id"] if user else None)
    conn.close()
    return out


@app.post("/api/competitions", response_model=CompetitionOut)
def create_competition(payload: CompetitionIn, _: dict = Depends(require_user)):
    conn = get_db()
    if payload.category_id:
        cat = conn.execute("SELECT 1 FROM categories WHERE id=?", (payload.category_id,)).fetchone()
        if not cat:
            conn.close()
            raise HTTPException(status_code=400, detail="category_id 不存在")
    try:
        cur = conn.execute(
            """INSERT INTO competitions
               (title, slug, summary, description, category_id, organizer, location, mode,
                prize, prize_amount, status, start_date, end_date, reg_deadline, tags, cover, source_url, featured)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (payload.title, payload.slug, payload.summary, payload.description, payload.category_id,
             payload.organizer, payload.location, payload.mode, payload.prize, payload.prize_amount,
             payload.status, payload.start_date, payload.end_date, payload.reg_deadline,
             json.dumps(payload.tags, ensure_ascii=False), payload.cover, payload.source_url,
             1 if payload.featured else 0),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM competitions WHERE id=?", (cur.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=409, detail="slug 已存在")
    out = _row_to_competition(row, conn)
    conn.close()
    return out


@app.put("/api/competitions/{comp_id}", response_model=CompetitionOut)
def update_competition(comp_id: int, payload: CompetitionIn, _: dict = Depends(require_user)):
    conn = get_db()
    row = conn.execute("SELECT * FROM competitions WHERE id=?", (comp_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="竞赛不存在")
    if payload.category_id:
        cat = conn.execute("SELECT 1 FROM categories WHERE id=?", (payload.category_id,)).fetchone()
        if not cat:
            conn.close()
            raise HTTPException(status_code=400, detail="category_id 不存在")
    conn.execute(
        """UPDATE competitions SET
              title=?, slug=?, summary=?, description=?, category_id=?, organizer=?, location=?, mode=?,
              prize=?, prize_amount=?, status=?, start_date=?, end_date=?, reg_deadline=?, tags=?, cover=?, source_url=?, featured=?,
              updated_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        (payload.title, payload.slug, payload.summary, payload.description, payload.category_id,
         payload.organizer, payload.location, payload.mode, payload.prize, payload.prize_amount,
         payload.status, payload.start_date, payload.end_date, payload.reg_deadline,
         json.dumps(payload.tags, ensure_ascii=False), payload.cover, payload.source_url,
         1 if payload.featured else 0, comp_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM competitions WHERE id=?", (comp_id,)).fetchone()
    out = _row_to_competition(row, conn)
    conn.close()
    return out


@app.delete("/api/competitions/{comp_id}")
def delete_competition(comp_id: int, _: dict = Depends(require_user)):
    conn = get_db()
    row = conn.execute("SELECT 1 FROM competitions WHERE id=?", (comp_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="竞赛不存在")
    conn.execute("DELETE FROM competitions WHERE id=?", (comp_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "deleted": comp_id}


# ---------------- 统计 ----------------
@app.get("/api/stats")
def stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) AS n FROM competitions").fetchone()["n"]
    ongoing = conn.execute("SELECT COUNT(*) AS n FROM competitions WHERE status='ongoing'").fetchone()["n"]
    upcoming = conn.execute("SELECT COUNT(*) AS n FROM competitions WHERE status='upcoming'").fetchone()["n"]
    ended = conn.execute("SELECT COUNT(*) AS n FROM competitions WHERE status='ended'").fetchone()["n"]
    cats = conn.execute("SELECT COUNT(*) AS n FROM categories").fetchone()["n"]
    users = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    top = conn.execute(
        "SELECT c.id, c.title, c.views FROM competitions c ORDER BY c.views DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return {
        "total": total, "ongoing": ongoing, "upcoming": upcoming, "ended": ended,
        "categories": cats, "users": users,
        "top_viewed": [{"id": r["id"], "title": r["title"], "views": r["views"]} for r in top],
    }


# ---------------- 用户认证 ----------------
@app.post("/api/auth/register", response_model=AuthOut)
def register(payload: UserRegister, request: Request):
    _check_auth_rate_limit(request)
    conn = get_db()
    exists = conn.execute("SELECT 1 FROM users WHERE username=?", (payload.username,)).fetchone()
    if exists:
        conn.close()
        raise HTTPException(status_code=409, detail="用户名已存在")
    cur = conn.execute(
        "INSERT INTO users (username, email, password_hash, role) VALUES (?,?,?,?)",
        (payload.username, payload.email, _hash_password(payload.password), "user"),
    )
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
    token = _create_token(conn, user["id"])
    conn.close()
    return AuthOut(token=token, user=_user_out(user))


@app.post("/api/auth/login", response_model=AuthOut)
def login(payload: UserLogin, request: Request):
    _check_auth_rate_limit(request)
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (payload.username,)).fetchone()
    conn.close()
    if not user or not _verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    conn = get_db()
    token = _create_token(conn, user["id"])
    conn.close()
    return AuthOut(token=token, user=_user_out(user))


@app.get("/api/auth/me", response_model=UserOut)
def me(user: dict = Depends(require_user)):
    return _user_out(user)


@app.post("/api/auth/logout")
def logout(authorization: str = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
        conn = get_db()
        conn.execute("DELETE FROM auth_tokens WHERE token=?", (token,))
        conn.commit()
        conn.close()
    return {"ok": True}


def _user_out(row) -> UserOut:
    d = row if isinstance(row, dict) else dict(row)
    return UserOut(
        id=d["id"], username=d["username"], email=d.get("email", ""),
        avatar=d.get("avatar", ""), role=d.get("role", "user"),
        created_at=str(d.get("created_at", "")),
    )


# ---------------- 收藏 ----------------
@app.get("/api/favorites", response_model=list[CompetitionOut])
def list_favorites(user: dict = Depends(require_user)):
    conn = get_db()
    rows = conn.execute(
        """SELECT c.* FROM favorites f JOIN competitions c ON c.id=f.competition_id
           WHERE f.user_id=? ORDER BY f.created_at DESC""",
        (user["id"],),
    ).fetchall()
    items = [_row_to_competition(r, conn, user["id"]) for r in rows]
    conn.close()
    return items


@app.post("/api/favorites")
def add_favorite(payload: FavoriteAction, user: dict = Depends(require_user)):
    conn = get_db()
    comp = conn.execute("SELECT 1 FROM competitions WHERE id=?", (payload.competition_id,)).fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=404, detail="竞赛不存在")
    conn.execute(
        "INSERT OR IGNORE INTO favorites (user_id, competition_id) VALUES (?,?)",
        (user["id"], payload.competition_id),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "favorited": True}


@app.delete("/api/favorites/{comp_id}")
def remove_favorite(comp_id: int, user: dict = Depends(require_user)):
    conn = get_db()
    conn.execute(
        "DELETE FROM favorites WHERE user_id=? AND competition_id=?", (user["id"], comp_id)
    )
    conn.commit()
    conn.close()
    return {"ok": True, "favorited": False}


@app.get("/api/favorites/check/{comp_id}")
def check_favorite(comp_id: int, user: dict | None = Depends(get_current_user)):
    if not user:
        return {"favorited": False}
    conn = get_db()
    fav = conn.execute(
        "SELECT 1 FROM favorites WHERE user_id=? AND competition_id=?", (user["id"], comp_id)
    ).fetchone()
    conn.close()
    return {"favorited": bool(fav)}


# ---------------- 生产环境：托管已构建的前端（静态资源 + SPA 回退） ----------------
_DIST = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "dist"))
if os.path.isdir(_DIST):
    @app.get("/{full_path:path}")
    async def spa_and_assets(full_path: str):
        # 未被显式 API 路由匹配到的 api 路径一律 404
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = os.path.join(_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # 客户端路由（如 /competition/5）回退到 index.html
        return FileResponse(os.path.join(_DIST, "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)
