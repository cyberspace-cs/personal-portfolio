"""实时适配器（ListingScrapeAdapter）测试

用内联 SSR 风格 HTML fixture 校验「服务端渲染列表页」解析逻辑，不依赖外网。
覆盖：
  - BiendataAdapter / SaikrAdapter 正确提取详情链接与标题
  - 过滤非匹配域名 / 导航文案 / 重复链接
  - 相对 href 经 urljoin 转为绝对 URL
  - ADAPTERS 注册了新实时来源
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collector import BiendataAdapter, SaikrAdapter, ADAPTERS, ListingScrapeAdapter

BIENDATA_HTML = """
<html><body>
  <a href="https://www.biendata.xyz/competition/jciiot/">JCIIOT 2026 开发者大赛</a>
  <a href="https://www.biendata.xyz/competition/SINOPEC-09/">基于具身智能的辅助加油任务</a>
  <a href="https://www.biendata.xyz/competition/hgb-3/">某学术评测榜单</a>
  <a href="/competition/reltest/">相对路径测试赛</a>
  <a href="https://www.biendata.xyz/about">关于我们</a>
  <a href="https://example.com/x">外部站点链接</a>
</body></html>
"""

SAIKR_HTML = """
<html><body>
  <a href="https://m.saikr.com/active/templete/wlaq4/1775556616">第四届全国大学生网络安全知识竞赛</a>
  <a href="https://event.saikr.com/event">发现更多</a>
  <a href="https://news.saikr.com/news/info/1268">环球赛乐入围百度智能云</a>
  <a href="https://www.saikr.com/camp">训练营发现更多</a>
  <a href="https://edu.saikr.com/my/course/5710">全程班课程</a>
</body></html>
"""


def test_biendata_extracts_competitions():
    items = BiendataAdapter().parse(BIENDATA_HTML)
    titles = [i.title for i in items]
    assert "JCIIOT 2026 开发者大赛" in titles
    assert "基于具身智能的辅助加油任务" in titles
    assert "相对路径测试赛" in titles
    # 关于我们 / 外部链接不应被抓取
    assert all("关于我们" not in t for t in titles)
    assert all("外部站点链接" not in t for t in titles)
    # 相对路径应被解析为绝对 URL
    rel = [i for i in items if i.title == "相对路径测试赛"][0]
    assert rel.source_url == "https://www.biendata.xyz/competition/reltest/"
    for it in items:
        assert it.source_url.startswith("https://www.biendata.xyz/competition/")
        assert it.category_slug == "data"  # category_hint


def test_saikr_extracts_competitions_and_filters_nav():
    items = SaikrAdapter().parse(SAIKR_HTML)
    titles = [i.title for i in items]
    assert titles == ["第四届全国大学生网络安全知识竞赛"]
    it = items[0]
    assert it.source_url.startswith("https://m.saikr.com/active/templete/")


def test_dedup_and_skip_texts():
    html = """
    <a href="https://www.biendata.xyz/competition/dup/">去重测试赛</a>
    <a href="https://www.biendata.xyz/competition/dup/">去重测试赛</a>
    <a href="https://www.biendata.xyz/competition/nav/">发现更多</a>
    """
    items = BiendataAdapter().parse(html)
    titles = [i.title for i in items]
    assert titles.count("去重测试赛") == 1
    assert "发现更多" not in titles


def test_listing_adapter_is_registered():
    names = [a.name for a in ADAPTERS]
    assert any("Biendata" in n for n in names)
    assert any("赛氪" in n for n in names)
    assert any("heikesong" in n.lower() or "天天黑客松" in n for n in names)
    # 实时适配器均继承自通用基类
    live = [a for a in ADAPTERS if isinstance(a, ListingScrapeAdapter)]
    assert len(live) >= 2
