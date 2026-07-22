"""自动赛事聚合（collector）测试

覆盖：
  - HeikeSongAdapter 解析真实抓取的 HTML fixture（轮播精选）
  - BundleAdapter 载入多源数据集
  - 分类自动归类 / slug 生成
  - import_competitions 幂等（重复写入 created=0）
  - run_collection 端到端（用桩适配器，不依赖外网）
  - /api/collect 需登录鉴权
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collector import (
    HeikeSongAdapter,
    BundleAdapter,
    SourceAdapter,
    run_collection,
    classify_category,
    slugify,
    RawCompetition,
)
from database import get_db, import_competitions, init_db

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "heikesong.html")


def _html() -> str:
    with open(FIX, encoding="utf-8", errors="ignore") as f:
        return f.read()


def test_heikesong_parse_real_fixture():
    items = HeikeSongAdapter().parse(_html())
    assert len(items) >= 1
    titles = " ".join(i.title for i in items)
    assert "DeFi Forge" in titles
    for it in items:
        assert it.status == "ongoing"
        assert it.featured is True
        assert it.source_url.startswith("http")


def test_bundle_loads():
    items = BundleAdapter().parse()
    assert len(items) >= 10
    allowed = {"hackathon", "data", "algorithm", "ctf", "ai", "innovation", "dev", "design"}
    for it in items:
        assert it.category_slug in allowed
        assert it.title


def test_classify_and_slug():
    assert classify_category("2026 腾讯广告算法大赛") == "algorithm"
    assert classify_category("强网杯 CTF 网络安全") == "ctf"
    assert classify_category("AI 大模型黑客松") == "ai"
    s = slugify("Hello World 黑客松!")
    assert " " not in s and len(s) > 0


def test_import_idempotent():
    init_db()
    rows = [
        RawCompetition(title="幂等测试赛 A", source="ut").to_row(),
        RawCompetition(title="幂等测试赛 B", source="ut").to_row(),
    ]
    s1 = import_competitions(rows)
    assert s1["created"] == 2
    s2 = import_competitions(rows)
    assert s2["created"] == 0
    assert s2["updated"] == 2
    conn = get_db()
    conn.execute("DELETE FROM competitions WHERE source='ut'")
    conn.commit()
    conn.close()


def test_run_collection_with_stub():
    init_db()

    class Stub(SourceAdapter):
        name = "stub"
        homepage = ""

        def fetch(self):
            return ""

        def parse(self, html=""):
            return [RawCompetition(
                title="Stub 聚合赛", source="stub", summary="x",
                category_slug="ai", organizer="Org", location="线上",
                mode="online", prize="¥1", prize_amount=1, status="ongoing",
                start_date="2026-01-01", end_date="2026-02-01",
                reg_deadline="2026-01-15", tags=["t"],
            )]

    res = run_collection([Stub()])
    assert res["total"] == 1
    assert res["created"] >= 1
    # 重复运行仍幂等
    res2 = run_collection([Stub()])
    assert res2["created"] == 0
    conn = get_db()
    conn.execute("DELETE FROM competitions WHERE source='stub'")
    conn.commit()
    conn.close()


def test_collect_endpoint_requires_auth(client):
    # 未登录应被拒绝
    r = client.post("/api/collect")
    assert r.status_code == 401
    # 来源列表接口可匿名访问
    r2 = client.get("/api/collect/sources")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list) and len(r2.json()) >= 1
