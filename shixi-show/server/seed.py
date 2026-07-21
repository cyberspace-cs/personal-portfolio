"""示例数据：插入公司与点评，并重算各公司聚合分（与前端 mock 对齐）。

运行：python seed.py
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import engine, init_db
from models import Company, Department, Review


def recompute(session: Session, company_id: int) -> None:
    """根据「通过(status=1)」的点评重算公司 avg_score / review_count / stamp。"""
    passed = session.execute(
        select(Review).where(Review.company_id == company_id, Review.status == 1)
    ).scalars().all()
    company = session.get(Company, company_id)
    if not company:
        return
    # review_count 保留 seed 设的历史热度（与 mock 对齐），不在此覆盖
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


def main() -> None:
    init_db()
    with Session(engine) as s:
        # 已存在则跳过，便于重复执行
        if s.execute(select(Company)).scalars().first():
            print("已存在数据，跳过 seed。")
            return

        companies = [
            Company(name="腾讯", industry="互联网", avg_score=4.6, review_count=1280,
                    tags=["转正友好", "导师负责"], stamp="推荐", hot=True),
            Company(name="字节跳动", industry="互联网", avg_score=4.4, review_count=1560,
                    tags=["成长快", "节奏快"], stamp="推荐", hot=True),
            Company(name="阿里", industry="互联网", avg_score=4.2, review_count=980,
                    tags=["体系成熟"], stamp="还想来", hot=False),
            Company(name="某国企研究院", industry="科研", avg_score=3.6, review_count=120,
                    tags=["稳定", "wlb好"], stamp="一般", hot=False),
            Company(name="某创业公司", industry="互联网", avg_score=2.8, review_count=64,
                    tags=["加班多"], stamp="避雷", hot=False),
            Company(name="美团", industry="互联网", avg_score=4.1, review_count=730,
                    tags=["业务多"], stamp="推荐", hot=False),
        ]
        for c in companies:
            s.add(c)
        s.commit()
        for c in companies:
            s.refresh(c)

        departments = [
            Department(company_id=companies[0].id, name="微信"),
            Department(company_id=companies[0].id, name="CSIG"),
            Department(company_id=companies[1].id, name="抖音"),
            Department(company_id=companies[2].id, name="阿里云"),
        ]
        for d in departments:
            s.add(d)

        reviews = [
            Review(company_id=companies[0].id, company_name="腾讯", dept="微信", role="后端开发",
                   scores={"mentor": 5, "growth": 4, "转正": 4, "薪资": 4, "wlb": 3},
                   stamps=["推荐"], content="导师很负责，转正机会大，业务锻炼人。", status=1, created_at="2026-07-20"),
            Review(company_id=companies[1].id, company_name="字节跳动", dept="抖音", role="前端",
                   scores={"mentor": 4, "growth": 5, "转正": 3, "薪资": 5, "wlb": 2},
                   stamps=["推荐"], content="成长快但节奏非常快，薪资给得足。", status=1, created_at="2026-07-18"),
            Review(company_id=companies[4].id, company_name="某创业公司", dept="研发", role="全栈",
                   scores={"mentor": 2, "growth": 3, "转正": 2, "薪资": 3, "wlb": 1},
                   stamps=["避雷"], content="加班严重，转正画饼，谨慎。", status=1, created_at="2026-07-15"),
            Review(company_id=companies[2].id, company_name="阿里", dept="云", role="算法",
                   scores={"mentor": 4, "growth": 4, "转正": 4, "薪资": 4, "wlb": 3},
                   stamps=["还想来"], content="体系成熟，能学到规范。", status=0, created_at="2026-07-21"),
            # 阿里另加一条已通过点评，避免聚合为 0（上面那条保留为待审演示）
            Review(company_id=companies[2].id, company_name="阿里", dept="淘宝", role="后端",
                   scores={"mentor": 5, "growth": 4, "转正": 4, "薪资": 4, "wlb": 4},
                   stamps=["还想来"], content="技术氛围好，成长空间大。", status=1, created_at="2026-07-10"),
            # 美团：通过点评
            Review(company_id=companies[5].id, company_name="美团", dept="外卖", role="产品",
                   scores={"mentor": 4, "growth": 4, "转正": 3, "薪资": 4, "wlb": 3},
                   stamps=["推荐"], content="业务线多，能学到东西。", status=1, created_at="2026-07-12"),
            # 某国企研究院：通过点评
            Review(company_id=companies[3].id, company_name="某国企研究院", dept="科研", role="研究",
                   scores={"mentor": 4, "growth": 3, "转正": 3, "薪资": 3, "wlb": 5},
                   stamps=["一般"], content="稳定，wlb 好，成长一般。", status=1, created_at="2026-07-08"),
        ]
        for r in reviews:
            s.add(r)
        s.commit()

        # 用真实通过数据重算聚合（覆盖初始 mock 数值）
        for c in companies:
            recompute(s, c.id)
        s.commit()
        print("seed 完成：6 家公司 + 4 条点评（3 通过 / 1 审核中）。")


if __name__ == "__main__":
    main()
