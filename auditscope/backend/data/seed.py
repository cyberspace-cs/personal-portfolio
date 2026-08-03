"""种子数据：与前端 mock 对齐，便于联调演示。首次启动自动写入（表空时）。"""
from __future__ import annotations
from sqlalchemy import select
from data.models import (Base, Company, Boss, Person, Flow, Social, _engine,
                         SessionLocal)


def seed() -> None:
    Base.metadata.create_all(_engine)
    with SessionLocal() as s:
        if s.execute(select(Company)).scalars().first():
            return
        c1 = Company(name="星河智能科技有限公司", credit_code="91110108MA01A1B2X3",
                     legal_person="陈嘉禾", reg_capital="5000万人民币", established="2016-03-12",
                     industry="人工智能/软件", status="存续", risk="normal", score=86,
                     tags=["高新企业", "瞪羚企业", "无失信"], address="北京市海淀区中关村南大街5号")
        c2 = Company(name="通汇供应链管理有限公司", credit_code="91310115MA1K35Y7T9",
                     legal_person="王立军", reg_capital="2000万人民币", established="2013-07-21",
                     industry="物流/供应链", status="存续", risk="watch", score=62,
                     tags=["涉诉2起", "股权质押"], address="上海市浦东新区张江路88号")
        c3 = Company(name="云栖数据服务股份有限公司", credit_code="91440300MA5DA2B4K6",
                     legal_person="李文博", reg_capital="12000万人民币", established="2011-09-02",
                     industry="云计算/大数据", status="存续", risk="high", score=38,
                     tags=["失信被执行人", "限制高消费", "税务异常"], address="深圳市南山区科技中一路9号")
        s.add_all([c1, c2, c3])
        s.flush()

        s.add_all([
            Boss(name="陈嘉禾", id_card_mask="110108**********3015", held_count=7,
                 total_capital="3.2亿人民币", risk="normal"),
            Boss(name="李文博", id_card_mask="440301**********1027", held_count=11,
                 total_capital="5.8亿人民币", risk="high"),
        ])
        s.add_all([
            Person(name="赵敏", title="财务总监", company_id=c1.id, social_connected=True, risk="normal"),
            Person(name="孙浩", title="资金经理", company_id=c2.id, social_connected=False, risk="watch"),
            Person(name="周倩", title="前出纳", company_id=c3.id, social_connected=True, risk="high"),
        ])
        s.add_all([
            Flow(company_id=c1.id, date="2025-11-03", counterparty="陈嘉禾(个人账户)",
                 bank="招商银行 6214****8831", amount=4800000, direction="out",
                 abnormal=True, note="大额公转私，无合同支撑"),
            Flow(company_id=c1.id, date="2025-11-08", counterparty="北京某广告有限公司",
                 bank="工商银行 6222****1190", amount=1200000, direction="out",
                 abnormal=False, note="广告服务费"),
            Flow(company_id=c1.id, date="2025-11-15", counterparty="客户回款-深圳市XX科技",
                 bank="招商银行 6214****8831", amount=9300000, direction="in",
                 abnormal=False, note="货款回款"),
            Flow(company_id=c3.id, date="2025-11-22", counterparty="云栖(海南)控股有限公司",
                 bank="建设银行 6217****5520", amount=6600000, direction="out",
                 abnormal=True, note="关联方资金往来，未披露"),
        ])
        s.add_all([
            Social(person_id=1, company_id=c1.id, base=32000, months=36, paid=True, gap_months=0, risk="normal"),
            Social(person_id=2, company_id=c2.id, base=18000, months=28, paid=True, gap_months=2, risk="watch"),
            Social(person_id=3, company_id=c3.id, base=24000, months=12, paid=False, gap_months=9, risk="high"),
        ])
        s.commit()
