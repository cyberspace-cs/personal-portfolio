"""数据模型（SQLAlchemy 2.0）+ 连接。演示用 SQLite，生产换 PostgreSQL（DATABASE_URL）。"""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Float, Boolean, JSON, Date,
                         ForeignKey, create_engine, select)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from core.config import settings

Base = declarative_base()
_engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), index=True)
    credit_code = Column(String(64))
    legal_person = Column(String(64), index=True)
    reg_capital = Column(String(64))
    established = Column(String(20))
    industry = Column(String(64), index=True)
    status = Column(String(16))
    risk = Column(String(16))
    score = Column(Float)
    tags = Column(JSON)
    address = Column(String(255))


class Boss(Base):
    __tablename__ = "bosses"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), index=True)
    id_card_mask = Column(String(64))
    held_count = Column(Integer)
    total_capital = Column(String(64))
    risk = Column(String(16))


class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), index=True)
    title = Column(String(64))
    company_id = Column(Integer, ForeignKey("companies.id"))
    social_connected = Column(Boolean)
    risk = Column(String(16))


class Flow(Base):
    __tablename__ = "flows"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    date = Column(String(20), index=True)
    counterparty = Column(String(128), index=True)
    bank = Column(String(64))
    amount = Column(Float)
    direction = Column(String(8))
    abnormal = Column(Boolean, index=True)
    note = Column(String(255))


class Social(Base):
    __tablename__ = "socials"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    base = Column(Float)
    months = Column(Integer)
    paid = Column(Boolean)
    gap_months = Column(Integer)
    risk = Column(String(16))


def get_session() -> Session:
    return SessionLocal()
