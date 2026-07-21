"""数据表建模（吸收 Kimi K3 设计：companies/departments/users/reviews/favorites/reports/audits）。

采用 SQLAlchemy 2.0（Mapped 风格），不依赖 SQLModel，避免与高版本 pydantic 冲突。
审核状态：status 0=审核中 / 1=通过 / 2=拒绝
JSON 字段（tags/scores/stamps）用 SQLAlchemy JSON 类型，SQLite 下自动序列化。
"""
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, index=True)
    industry: Mapped[str] = mapped_column(String, default="")
    logo: Mapped[str] = mapped_column(String, default="")           # 缺图时前端用文字 Logo 兜底
    avg_score: Mapped[float] = mapped_column(Float, default=0.0)     # 由通过的点评聚合
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    stamp: Mapped[str] = mapped_column(String, default="")          # 综合印章：推荐/还想来/一般/避雷
    hot: Mapped[bool] = mapped_column(Boolean, default=False)


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String, default="")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    openid: Mapped[str] = mapped_column(String, default="", index=True)
    nickname: Mapped[str] = mapped_column(String, default="匿名用户")


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    company_name: Mapped[str] = mapped_column(String, default="")     # 冗余，方便列表直出
    dept: Mapped[str] = mapped_column(String, default="")
    role: Mapped[str] = mapped_column(String, default="")
    scores: Mapped[dict] = mapped_column(JSON, default=dict)          # {mentor,growth,转正,薪资,wlb}
    stamps: Mapped[list] = mapped_column(JSON, default=list)          # ['推荐'] 等
    content: Mapped[str] = mapped_column(String, default="")
    status: Mapped[int] = mapped_column(Integer, default=0, index=True)
    audit_reason: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[str] = mapped_column(
        String, default=lambda: datetime.now().strftime("%Y-%m-%d"))


class Favorite(Base):
    __tablename__ = "favorites"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    company_id: Mapped[int] = mapped_column(Integer, index=True)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str] = mapped_column(String, default="")
    status: Mapped[int] = mapped_column(Integer, default=0)          # 0待处理/1已处理


class Audit(Base):
    __tablename__ = "audits"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(Integer, index=True)
    admin_id: Mapped[str] = mapped_column(String, default="admin")
    action: Mapped[str] = mapped_column(String, default="")          # approve / reject
    reason: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[str] = mapped_column(
        String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
