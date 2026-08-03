"""五大检索服务（seam：search_* 函数）。内部用 SQLAlchemy，对网关透明。"""
from __future__ import annotations
from sqlalchemy import select, or_
from data.models import Company, Boss, Person, Flow, Social, get_session


def search_companies(q: str) -> list[dict]:
    with get_session() as s:
        stmt = select(Company)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(Company.name.like(like), Company.legal_person.like(like),
                                  Company.industry.like(like)))
        rows = s.execute(stmt).scalars().all()
    return [_company_out(c) for c in rows]


def _company_out(c: Company) -> dict:
    return {"id": c.id, "name": c.name, "creditCode": c.credit_code, "legalPerson": c.legal_person,
            "regCapital": c.reg_capital, "established": c.established, "industry": c.industry,
            "status": c.status, "risk": c.risk, "score": c.score, "tags": c.tags or [],
            "address": c.address}


def search_bosses(q: str) -> list[dict]:
    with get_session() as s:
        stmt = select(Boss)
        if q:
            stmt = stmt.where(Boss.name.like(f"%{q}%"))
        rows = s.execute(stmt).scalars().all()
    return [{"id": b.id, "name": b.name, "idCardMask": b.id_card_mask,
             "heldCount": b.held_count, "totalCapital": b.total_capital, "risk": b.risk}
            for b in rows]


def search_persons(q: str) -> list[dict]:
    with get_session() as s:
        stmt = select(Person)
        if q:
            stmt = stmt.where(Person.name.like(f"%{q}%"))
        rows = s.execute(stmt).scalars().all()
    return [{"id": p.id, "name": p.name, "title": p.title, "companyId": p.company_id,
             "socialConnected": p.social_connected, "risk": p.risk} for p in rows]


def search_flows(q: str) -> list[dict]:
    with get_session() as s:
        stmt = select(Flow)
        if q:
            stmt = stmt.where(or_(Flow.counterparty.like(f"%{q}%"), Flow.note.like(f"%{q}%")))
        rows = s.execute(stmt.order_by(Flow.date.desc())).scalars().all()
    return [_flow_out(f) for f in rows]


def _flow_out(f: Flow) -> dict:
    return {"id": f.id, "date": f.date, "counterparty": f.counterparty, "bank": f.bank,
            "amount": f.amount, "direction": f.direction, "abnormal": f.abnormal, "note": f.note}


def detect_anomalies(company_id: int | None = None) -> list[dict]:
    with get_session() as s:
        stmt = select(Flow).where(Flow.abnormal == True)  # noqa: E712
        if company_id:
            stmt = stmt.where(Flow.company_id == company_id)
        rows = s.execute(stmt).scalars().all()
    return [_flow_out(f) for f in rows]


def search_social(q: str) -> list[dict]:
    with get_session() as s:
        stmt = select(Social)
        rows = s.execute(stmt).scalars().all()
        # 社保按人员/公司名过滤需在应用层 join；演示规模直接返回并按 q 粗筛
    if q:
        # 简化：通过 person/company 名字过滤
        out = []
        with get_session() as s2:
            for soc in rows:
                p = s2.get(Person, soc.person_id)
                comp = s2.get(Company, soc.company_id)
                if (p and q in p.name) or (comp and q in comp.name):
                    out.append(_social_out(soc, p.name if p else "", comp.name if comp else ""))
        return out
    with get_session() as s2:
        return [_social_out(soc,
                            (s2.get(Person, soc.person_id).name if s2.get(Person, soc.person_id) else ""),
                            (s2.get(Company, soc.company_id).name if s2.get(Company, soc.company_id) else ""))
                for soc in rows]


def _social_out(soc: Social, person_name: str, company_name: str) -> dict:
    return {"id": soc.id, "name": person_name, "company": company_name, "base": soc.base,
            "months": soc.months, "paid": soc.paid, "gapMonths": soc.gap_months, "risk": soc.risk}
