"""实习 Show 后端 API（FastAPI + SQLAlchemy 2.0 + SQLite）。

启动：uvicorn main:app --reload --port 5000
接口：见 README.md / shixi-show/README.md 第 5 节。
"""
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import engine, get_session, init_db
from models import Audit, Company, Favorite, Report, Review


# ---------- 工具：ORM 对象 -> camelCase 响应（对齐小程序字段） ----------

def company_out(c: Company) -> dict:
    return {
        "id": c.id, "name": c.name, "industry": c.industry, "logo": c.logo,
        "avgScore": c.avg_score, "reviewCount": c.review_count,
        "tags": c.tags, "stamp": c.stamp, "hot": c.hot,
    }


def review_out(r: Review) -> dict:
    return {
        "id": r.id, "companyId": r.company_id, "companyName": r.company_name,
        "dept": r.dept, "role": r.role, "scores": r.scores, "stamps": r.stamps,
        "content": r.content, "status": r.status, "auditReason": r.audit_reason,
        "createdAt": r.created_at,
    }


def recompute(session: Session, company_id: int) -> None:
    """重算公司聚合（avg_score / review_count / 综合 stamp）。"""
    passed = session.execute(
        select(Review).where(Review.company_id == company_id, Review.status == 1)
    ).scalars().all()
    company = session.get(Company, company_id)
    if not company:
        return
    # 注：review_count 保留 seed 设的历史热度，仅审核通过时 +1（见 audit_review）
    if passed:
        total = 0.0
        n = 0
        stamp_counter: dict = {}
        for r in passed:
            for v in r.scores.values():
                total += v
                n += 1
            for s in r.stamps:
                stamp_counter[s] = stamp_counter.get(s, 0) + 1
        company.avg_score = round(total / n, 1) if n else 0.0
        company.stamp = max(stamp_counter, key=stamp_counter.get) if stamp_counter else ""
    else:
        company.avg_score = 0.0
        company.stamp = ""
    session.add(company)


# ---------- 启动：建表 + 首次 seed ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with Session(engine) as s:
        if not s.execute(select(Company)).scalars().first():
            import seed
            seed.main()
    yield


app = FastAPI(title="实习 Show API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


# ---------- 用户端接口 ----------

@app.get("/api/companies/rank")
def rank_companies(page: int = 1, size: int = 20, session: Session = Depends(get_session)):
    """热门排行榜（默认按 review_count 降序，热门优先）。"""
    offset = (page - 1) * size
    rows = session.execute(
        select(Company).order_by(Company.review_count.desc()).offset(offset).limit(size)
    ).scalars().all()
    return [company_out(c) for c in rows]


@app.get("/api/companies/search")
def search_companies(q: str = "", session: Session = Depends(get_session)):
    """按公司名 / 行业模糊搜索。"""
    if not q:
        return []
    like = f"%{q}%"
    rows = session.execute(
        select(Company).where(
            (Company.name.like(like)) | (Company.industry.like(like))
        ).order_by(Company.avg_score.desc())
    ).scalars().all()
    return [company_out(c) for c in rows]


@app.get("/api/companies/{company_id}")
def company_detail(company_id: int, session: Session = Depends(get_session)):
    """公司详情 + 通过的点评列表。"""
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    reviews = session.execute(
        select(Review).where(Review.company_id == company_id, Review.status == 1)
        .order_by(Review.id.desc())
    ).scalars().all()
    return {"company": company_out(company), "reviews": [review_out(r) for r in reviews]}


@app.post("/api/reviews")
def create_review(payload: dict, session: Session = Depends(get_session)):
    """提交点评（默认进入审核中 status=0）。"""
    company_id = payload.get("companyId")
    company = session.get(Company, company_id) if company_id else None
    review = Review(
        user_id=payload.get("userId"),
        company_id=company_id,
        company_name=company.name if company else payload.get("companyName", ""),
        dept=payload.get("dept", ""),
        role=payload.get("role", ""),
        scores=payload.get("scores", {}),
        stamps=payload.get("stamps", []),
        content=payload.get("content", ""),
        status=0,
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    return {"ok": True, "review": review_out(review), "message": "已提交，等待审核"}


@app.get("/api/users/my-reviews")
def my_reviews(userId: Optional[int] = None, session: Session = Depends(get_session)):
    """我的点评（带审核状态）。"""
    if userId is None:
        return []
    rows = session.execute(
        select(Review).where(Review.user_id == userId).order_by(Review.id.desc())
    ).scalars().all()
    return [review_out(r) for r in rows]


@app.post("/api/favorites")
def add_favorite(payload: dict, session: Session = Depends(get_session)):
    fav = Favorite(user_id=payload.get("userId", 0), company_id=payload.get("companyId"))
    session.add(fav)
    session.commit()
    return {"ok": True}


@app.post("/api/reports")
def add_report(payload: dict, session: Session = Depends(get_session)):
    rep = Report(review_id=payload.get("reviewId"), user_id=payload.get("userId", 0),
                 reason=payload.get("reason", ""), status=0)
    session.add(rep)
    session.commit()
    return {"ok": True}


# ---------- 管理端接口（审核状态机） ----------

@app.get("/api/admin/reviews")
def admin_list_reviews(status: Optional[int] = None, session: Session = Depends(get_session)):
    """待审 / 全部点评列表。status: 0审核中/1通过/2拒绝/不传=全部。"""
    stmt = select(Review)
    if status is not None:
        stmt = stmt.where(Review.status == status)
    stmt = stmt.order_by(Review.id.desc())
    rows = session.execute(stmt).scalars().all()
    return [review_out(r) for r in rows]


@app.post("/api/admin/reviews/{review_id}/audit")
def audit_review(review_id: int, payload: dict, session: Session = Depends(get_session)):
    """审核：{action: 'approve'|'reject', reason?: string, adminId?: string}。

    审核状态机：0审核中 --approve--> 1通过（计入公司评分）；--reject--> 2拒绝（用户可见理由）。
    """
    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="点评不存在")
    action = payload.get("action")
    reason = payload.get("reason", "")
    if review.status != 0:
        raise HTTPException(status_code=400, detail="该点评已审核，不可重复操作")
    if action == "approve":
        review.status = 1
    elif action == "reject":
        review.status = 2
        review.audit_reason = reason
    else:
        raise HTTPException(status_code=400, detail="action 须为 approve / reject")

    session.add(review)
    session.add(Audit(review_id=review.id, admin_id=payload.get("adminId", "admin"),
                      action=action, reason=reason))
    # 通过则重算公司聚合 + 评论数 +1（保留历史热度）
    if action == "approve":
        recompute(session, review.company_id)
        comp = session.get(Company, review.company_id)
        if comp:
            comp.review_count += 1
            session.add(comp)
    session.commit()
    return {"ok": True, "review": review_out(review)}


@app.get("/api/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
