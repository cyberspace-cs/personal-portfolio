"""TDD：流水异常检测 seam 测试。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.seed import seed, _engine, Base
from data.models import Company, Flow, SessionLocal
from sqlalchemy import select
from services.search import detect_anomalies, search_flows


def setup_module(_):
    Base.metadata.create_all(_engine)
    seed()


def test_detect_anomalies_returns_flagged():
    anomalies = detect_anomalies()
    assert len(anomalies) >= 1
    assert all(f["abnormal"] is True for f in anomalies)


def test_anomaly_amount_threshold():
    # 已知种子：公转私 480 万为异常
    big = [f for f in detect_anomalies() if f["amount"] >= 4_000_000]
    assert any("陈嘉禾" in f["counterparty"] for f in big)


def test_search_flows_by_keyword():
    res = search_flows("云栖")
    assert len(res) >= 1
    assert any("云栖" in f["counterparty"] for f in res)
