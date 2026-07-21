"""数据库连接与会话（SQLite + SQLAlchemy 2.0）。"""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DB_PATH = Path(__file__).parent / "shixi_show.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False：允许 FastAPI 多线程访问同一连接
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def init_db() -> None:
    """建表（首次启动时创建所有表）。"""
    from models import Base
    Base.metadata.create_all(engine)


def get_session():
    """FastAPI 依赖注入用的会话生成器。"""
    with Session(engine) as session:
        yield session
