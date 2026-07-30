"""官网图片补全（og:image 解析 + enrich_images）单元测试，无需联网。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collector import _meta_content, enrich_images  # noqa: E402


def test_meta_content_property_first():
    html = '<meta property="og:image" content="https://x.com/a.png">'
    assert _meta_content(html, "og:image") == "https://x.com/a.png"


def test_meta_content_content_first():
    # 属性顺序相反时仍能提取
    html = '<meta content="https://y.com/c.jpg" property="og:image">'
    assert _meta_content(html, "og:image") == "https://y.com/c.jpg"


def test_meta_content_twitter_fallback():
    html = '<meta name="twitter:image" content="https://x.com/b.png">'
    assert _meta_content(html, "twitter:image") == "https://x.com/b.png"


def test_meta_content_missing():
    assert _meta_content("<meta property='og:title' content='x'>", "og:image") == ""


def test_enrich_images_limit_zero_noop():
    # limit=0 不应发起任何网络请求，直接返回 total=0
    r = enrich_images(limit=0)
    assert r["total"] == 0
    assert r["updated"] == 0
    assert r["failed"] == 0
