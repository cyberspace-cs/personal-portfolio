"""前沿 CS / AI 知识聚合平台 —— FastAPI 后端。

提供：
- 分类（categories）增删改查与管理
- 前沿信息（items）列表 / 详情 / 增删改查，含分类、关键词、类型、标签筛选与搜索、排序、分页
- 统计（stats）
- 收藏（favorites，基于匿名会话）
- 生产环境直接托管前端构建产物（web/dist）

运行：uvicorn main:app --reload --port 8000
管理写接口（POST/PUT/DELETE）默认开放；设置环境变量 ADMIN_KEY 后需携带
请求头 X-Admin-Key: <key> 方可调用。
"""
import os
import uuid
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import get_db, init_db, _slug, ensure_tag_conn
import models

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.normpath(os.path.join(ROOT, "..", "web", "dist"))
ADMIN_KEY = os.getenv("ADMIN_KEY")

init_db()

# 首次启动且数据库为空时自动填充种子数据（不影响已有数据）
try:
    from seed_data import seed
    seed()
except Exception as _e:  # pragma: no cover
    print(f"[warn] 自动种子数据失败: {_e}")

app = FastAPI(title="CS 前沿知识聚合平台", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_admin(x_admin_key: Optional[str] = Header(None)) -> None:
    if ADMIN_KEY and x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="需要有效的 X-Admin-Key")


def _item_to_out(row, session_id: Optional[str] = None) -> dict:
    conn = get_db()
    cat = conn.execute(
        "SELECT name, slug FROM categories WHERE id=?", (row["category_id"],)
    ).fetchone() if row["category_id"] else None
    tags = [r["name"] for r in conn.execute(
        "SELECT t.name FROM tags t JOIN item_tags it ON it.tag_id=t.id "
        "WHERE it.item_id=? ORDER BY t.name", (row["id"],)
    ).fetchall()]
    fav = False
    if session_id:
        fav = conn.execute(
            "SELECT 1 FROM favorites WHERE session_id=? AND item_id=?",
            (session_id, row["id"]),
        ).fetchone() is not None
    conn.close()
    return {
        "id": row["id"], "title": row["title"], "slug": row["slug"],
        "summary": row["summary"], "content": row["content"],
        "category_id": row["category_id"],
        "category_name": cat["name"] if cat else "",
        "category_slug": cat["slug"] if cat else "",
        "source_type": row["source_type"], "source_url": row["source_url"],
        "github_stars": row["github_stars"], "author_org": row["author_org"],
        "language": row["language"], "status": row["status"],
        "featured": bool(row["featured"]), "views": row["views"],
        "tags": tags, "created_at": row["created_at"], "updated_at": row["updated_at"],
        "image_url": row["image_url"], "is_favorited": fav,
    }


def _category_to_out(row, count: int = 0) -> dict:
    return {
        "id": row["id"], "name": row["name"], "slug": row["slug"],
        "icon": row["icon"], "description": row["description"],
        "sort_order": row["sort_order"], "count": count,
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "cs-frontier-hub"}


@app.get("/api/stats", response_model=models.Stats)
def stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) c FROM items").fetchone()["c"]
    categories = conn.execute("SELECT COUNT(*) c FROM categories").fetchone()["c"]
    trending = conn.execute("SELECT COUNT(*) c FROM items WHERE status='trending'").fetchone()["c"]
    featured = conn.execute("SELECT COUNT(*) c FROM items WHERE featured=1").fetchone()["c"]
    by_type = {r["source_type"]: r["c"] for r in conn.execute(
        "SELECT source_type, COUNT(*) c FROM items GROUP BY source_type").fetchall()}
    by_category = [{"slug": r["slug"], "name": r["name"], "count": r["c"]} for r in conn.execute(
        "SELECT c.slug, c.name, COUNT(i.id) c FROM categories c "
        "LEFT JOIN items i ON i.category_id=c.id GROUP BY c.id ORDER BY c.sort_order").fetchall()]
    top_viewed = [{"id": r["id"], "title": r["title"], "views": r["views"]} for r in conn.execute(
        "SELECT id, title, views FROM items ORDER BY views DESC LIMIT 5").fetchall()]
    conn.close()
    return {"total": total, "categories": categories, "trending": trending,
            "featured": featured, "by_type": by_type, "by_category": by_category,
            "top_viewed": top_viewed}


@app.get("/api/categories", response_model=List[models.CategoryOut])
def list_categories():
    conn = get_db()
    rows = conn.execute("SELECT * FROM categories ORDER BY sort_order, id").fetchall()
    counts = {r["category_id"]: r["c"] for r in conn.execute(
        "SELECT category_id, COUNT(*) c FROM items GROUP BY category_id").fetchall()}
    conn.close()
    return [_category_to_out(r, counts.get(r["id"], 0)) for r in rows]


@app.post("/api/categories", response_model=models.CategoryOut)
def create_category(payload: models.CategoryInput, _=Depends(require_admin)):
    slug = payload.slug or _slug(payload.name)
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO categories (name, slug, icon, description, sort_order) "
            "VALUES (?,?,?,?,?)", (payload.name, slug, payload.icon, payload.description, payload.sort_order))
        conn.commit()
        row = conn.execute("SELECT * FROM categories WHERE id=?", (cur.lastrowid,)).fetchone()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"分类已存在或参数错误: {e}")
    conn.close()
    return _category_to_out(row, 0)


@app.put("/api/categories/{cat_id}", response_model=models.CategoryOut)
def update_category(cat_id: int, payload: models.CategoryInput, _=Depends(require_admin)):
    conn = get_db()
    row = conn.execute("SELECT * FROM categories WHERE id=?", (cat_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="分类不存在")
    conn.execute(
        "UPDATE categories SET name=?, slug=?, icon=?, description=?, sort_order=? WHERE id=?",
        (payload.name, payload.slug or row["slug"], payload.icon, payload.description, payload.sort_order, cat_id))
    conn.commit()
    row = conn.execute("SELECT * FROM categories WHERE id=?", (cat_id,)).fetchone()
    conn.close()
    return _category_to_out(row, 0)


@app.delete("/api/categories/{cat_id}")
def delete_category(cat_id: int, _=Depends(require_admin)):
    conn = get_db()
    conn.execute("UPDATE items SET category_id=NULL WHERE category_id=?", (cat_id,))
    conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "deleted": cat_id}


def _build_items_query(q, category, source_type, tag, status, featured, session_id, sort, page, page_size):
    where = []
    params = []
    if category:
        where.append("i.category_id=(SELECT id FROM categories WHERE slug=?)")
        params.append(category)
    if source_type:
        where.append("i.source_type=?")
        params.append(source_type)
    if status:
        where.append("i.status=?")
        params.append(status)
    if featured:
        where.append("i.featured=1")
    if tag:
        where.append("i.id IN (SELECT item_id FROM item_tags it JOIN tags t ON t.id=it.tag_id WHERE t.slug=?)")
        params.append(_slug(tag))
    if q:
        like = f"%{q}%"
        where.append(
            "(i.title LIKE ? OR i.summary LIKE ? OR i.content LIKE ? OR i.author_org LIKE ? "
            "OR i.id IN (SELECT item_id FROM item_tags it JOIN tags t ON t.id=it.tag_id WHERE t.name LIKE ?))")
        params += [like, like, like, like, like]

    order = {
        "latest": "i.created_at DESC, i.id DESC",
        "stars": "i.github_stars IS NULL, i.github_stars DESC",
        "views": "i.views DESC, i.id DESC",
        "title": "i.title ASC",
    }.get(sort, "i.featured DESC, i.created_at DESC, i.id DESC")

    clause = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"SELECT i.* FROM items i {clause}"
    count_sql = f"SELECT COUNT(*) c FROM items i {clause}"
    conn = get_db()
    total = conn.execute(count_sql, params).fetchone()["c"]
    offset = (page - 1) * page_size
    rows = conn.execute(sql + f" ORDER BY {order} LIMIT ? OFFSET ?", params + [page_size, offset]).fetchall()
    items = [_item_to_out(r, session_id) for r in rows]
    conn.close()
    return items, total


@app.get("/api/items", response_model=models.ItemListResp)
def list_items(
    q: Optional[str] = None,
    category: Optional[str] = None,
    source_type: Optional[str] = None,
    tag: Optional[str] = None,
    status: Optional[str] = None,
    featured: bool = False,
    sort: str = "latest",
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=60),
    session_id: Optional[str] = None,
):
    items, total = _build_items_query(q, category, source_type, tag, status, featured, session_id, sort, page, page_size)
    total_pages = (total + page_size - 1) // page_size if total else 0
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}


@app.get("/api/items/{ident}", response_model=models.ItemOut)
def get_item(ident: str, session_id: Optional[str] = None):
    conn = get_db()
    row = conn.execute("SELECT * FROM items WHERE id=? OR slug=?", (ident, ident)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="条目不存在")
    conn.execute("UPDATE items SET views=views+1 WHERE id=?", (row["id"],))
    conn.commit()
    conn.close()
    return _item_to_out(row, session_id)


@app.post("/api/items", response_model=models.ItemOut)
def create_item(payload: models.ItemInput, _=Depends(require_admin)):
    slug = payload.slug or _slug(payload.title)
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO items (title, slug, summary, content, category_id, source_type, source_url, "
            "github_stars, author_org, language, status, featured, image_url) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (payload.title, slug, payload.summary, payload.content, payload.category_id,
             payload.source_type, payload.source_url, payload.github_stars, payload.author_org,
             payload.language, payload.status, int(bool(payload.featured)), payload.image_url or ""))
        iid = cur.lastrowid
        for t in payload.tags:
            tid = ensure_tag_conn(conn, t)
            conn.execute("INSERT OR IGNORE INTO item_tags (item_id, tag_id) VALUES (?,?)", (iid, tid))
        conn.commit()
        row = conn.execute("SELECT * FROM items WHERE id=?", (iid,)).fetchone()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"创建失败（slug 可能重复）: {e}")
    conn.close()
    return _item_to_out(row, None)


@app.put("/api/items/{item_id}", response_model=models.ItemOut)
def update_item(item_id: int, payload: models.ItemInput, _=Depends(require_admin)):
    conn = get_db()
    row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="条目不存在")
    slug = payload.slug or row["slug"]
    conn.execute(
        "UPDATE items SET title=?, slug=?, summary=?, content=?, category_id=?, source_type=?, "
        "source_url=?, github_stars=?, author_org=?, language=?, status=?, featured=?, image_url=?, updated_at=CURRENT_TIMESTAMP "
        "WHERE id=?",
        (payload.title, slug, payload.summary, payload.content, payload.category_id, payload.source_type,
         payload.source_url, payload.github_stars, payload.author_org, payload.language, payload.status,
         int(bool(payload.featured)), payload.image_url or "", item_id))
    conn.execute("DELETE FROM item_tags WHERE item_id=?", (item_id,))
    for t in payload.tags:
        tid = ensure_tag_conn(conn, t)
        conn.execute("INSERT OR IGNORE INTO item_tags (item_id, tag_id) VALUES (?,?)", (item_id, tid))
    conn.commit()
    row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    conn.close()
    return _item_to_out(row, None)


@app.delete("/api/items/{item_id}")
def delete_item(item_id: int, _=Depends(require_admin)):
    conn = get_db()
    conn.execute("DELETE FROM item_tags WHERE item_id=?", (item_id,))
    conn.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "deleted": item_id}


# --------------------------------------------------------------------------- #
# 收藏（基于匿名会话）
# --------------------------------------------------------------------------- #
@app.post("/api/session", response_model=models.SessionOut)
def create_session():
    sid = str(uuid.uuid4())
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO sessions (id) VALUES (?)", (sid,))
    conn.commit()
    conn.close()
    return {"session_id": sid}


@app.get("/api/favorites", response_model=List[models.ItemOut])
def list_favorites(session_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT i.* FROM items i JOIN favorites f ON f.item_id=i.id "
        "WHERE f.session_id=? ORDER BY f.created_at DESC", (session_id,)
    ).fetchall()
    items = [_item_to_out(r, session_id) for r in rows]
    conn.close()
    return items


@app.post("/api/favorites", response_model=models.FavoriteToggleResp)
def toggle_favorite(body: dict):
    session_id = body.get("session_id")
    item_id = body.get("item_id")
    if not session_id or not item_id:
        raise HTTPException(status_code=400, detail="需要 session_id 与 item_id")
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO sessions (id) VALUES (?)", (session_id,))
    existing = conn.execute("SELECT 1 FROM favorites WHERE session_id=? AND item_id=?", (session_id, item_id)).fetchone()
    if existing:
        conn.execute("DELETE FROM favorites WHERE session_id=? AND item_id=?", (session_id, item_id))
        favorited = False
    else:
        conn.execute("INSERT INTO favorites (session_id, item_id) VALUES (?,?)", (session_id, item_id))
        favorited = True
    conn.commit()
    conn.close()
    return {"ok": True, "favorited": favorited}


@app.delete("/api/favorites/{item_id}")
def remove_favorite(item_id: int, session_id: str):
    conn = get_db()
    conn.execute("DELETE FROM favorites WHERE session_id=? AND item_id=?", (session_id, item_id))
    conn.commit()
    conn.close()
    return {"ok": True, "favorited": False}


@app.post("/api/crawler/run")
def run_crawler_endpoint(body: dict = {}, _=Depends(require_admin)):
    """触发爬虫抓取前沿信息（需要 X-Admin-Key）。
    支持 sources: github / gitee / hf / arxiv / csdn / news / semantic
    """
    sources = body.get("sources") or ["github", "gitee", "hf", "arxiv", "csdn", "news"]
    try:
        limit = int(body.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20
    try:
        from crawler import run_crawler as _run
        return _run(sources, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"爬虫执行失败: {e}")


# --------------------------------------------------------------------------- #
# 托管前端构建产物（web/dist）
# --------------------------------------------------------------------------- #
if os.path.isdir(DIST):
    app.mount("/", StaticFiles(directory=DIST, html=True), name="spa")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
