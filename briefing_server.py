#!/usr/bin/env python3
# AI 每日简报 · 只读后端（端口 8089，由 nginx /api/aihot/ 反代）
#
# 线上 taoxie.vip 的 /api/aihot/* 由本服务在 127.0.0.1:8089 提供。
# 早期版本是静态文件服务，读取「每日自动化预生成的 briefings/*.json」，
# 但预生成快照经常缺版块（例如只生成 2/5 个分类），导致简报缺类。
#
# 本版本改为【实时】拉取 aihot v1 公开 API：
#   /api/aihot/daily         -> https://aihot.virxact.com/api/v1/dailies/latest
#   /api/aihot/daily?date=X   -> .../api/v1/dailies/{X}（不存在则回退最近一期）
#   /api/aihot/dailies?take=N -> .../api/v1/dailies?limit=N
#   /api/aihot/hot-topics     -> .../api/v1/hot-topics（当前热点·完整榜单，含热度/信源数）
# 并归一化为前端所需字段（title/summary/sourceName/sourceUrl/permalink），
# 保证「模型 / 产品 / 行业 / 论文 / 观点」五版块齐全。
#
# 仅依赖标准库（http.server + urllib），与运行环境解耦。
import json
import os
import time
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8089
AIHOT = "https://aihot.virxact.com"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# 五个固定版块（顺序即展示顺序）。aihot 日报成品始终包含这五类。
SECTION_ORDER = [
    "模型发布/更新",
    "产品发布/更新",
    "行业动态",
    "论文研究",
    "技巧与观点",
]

# 简单内存缓存，避免每次请求都打 aihot（前端每 5 分钟轮询一次）。
_cache = {}  # key -> (ts, payload)


def fetch_json(url, timeout=20):
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def get_cached(key, ttl, fetcher):
    now = time.time()
    if key in _cache and now - _cache[key][0] < ttl:
        return _cache[key][1]
    val = fetcher()
    _cache[key] = (now, val)
    return val


def norm_item(it):
    """把单条条目归一化为前端字段。兼容 v1（links/source.name）与旧结构。"""
    if not isinstance(it, dict):
        return None
    links = it.get("links") or {}
    url = (
        links.get("aihot")
        or links.get("original")
        or it.get("sourceUrl")
        or it.get("permalink")
        or ""
    )
    src = it.get("source")
    if isinstance(src, dict):
        src_name = src.get("name")
    else:
        src_name = None
    if not src_name:
        src_name = (
            it.get("sourceName")
            or (it.get("attribution") or {}).get("source")
            or "未知来源"
        )
    title = it.get("title") or it.get("title_en")
    if not title:
        return None
    return {
        "title": title,
        "summary": it.get("summary") or "",
        "sourceName": src_name,
        "sourceUrl": url,
        "permalink": links.get("original") or it.get("permalink") or "",
    }


def extract_report(raw):
    """v1 把日报包在 report 对象里；兼容裸结构。"""
    if isinstance(raw, dict) and "report" in raw and isinstance(raw["report"], dict):
        return raw["report"]
    return raw or {}


def norm_sections(sections):
    by = {s.get("label"): s for s in (sections or []) if s.get("label")}
    out = []
    for label in SECTION_ORDER:
        s = by.get(label)
        if not s:
            continue
        items = [norm_item(i) for i in (s.get("items") or []) if isinstance(i, dict)]
        items = [i for i in items if i]
        if items:
            out.append({"label": label, "items": items})
    return out


def norm_hot_item(it):
    """归一化 hot-topics 单条为前端字段。"""
    if not isinstance(it, dict):
        return None
    links = it.get("links") or {}
    url = links.get("aihot") or links.get("original") or it.get("sourceUrl") or ""
    src = it.get("source")
    if isinstance(src, dict):
        src_name = src.get("name")
    else:
        src_name = None
    if not src_name:
        src_name = it.get("sourceName") or "未知来源"
    title = it.get("title")
    if not title:
        return None
    return {
        "rank": it.get("rank"),
        "title": title,
        "sourceName": src_name,
        "sourceUrl": url,
        "signalCount": it.get("signalCount") or 0,
        "sourceCount": it.get("sourceCount") or 0,
        "sourceNames": it.get("sourceNames") or [],
        "latestAt": it.get("latestAt"),
        "storyUrl": links.get("story") or "",
    }


def fetch_hot():
    """当前热点榜单（hot-topics），实时拉取 aihot v1。"""
    raw = fetch_json(f"{AIHOT}/api/v1/hot-topics")
    items = [norm_hot_item(i) for i in (raw.get("items") or [])]
    items = [i for i in items if i]
    items.sort(key=lambda x: (x.get("rank") is None, x.get("rank") or 0))
    return {
        "count": len(items),
        "items": items,
        "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "aihot.virxact.com",
    }


def build_daily(raw):
    rep = extract_report(raw)
    return {
        "date": rep.get("date"),
        "generatedAt": rep.get("generatedAt"),
        "source": "aihot.virxact.com",
        "lead": rep.get("lead"),
        "sections": norm_sections(rep.get("sections")),
        "flashes": [i for i in (norm_item(f) for f in (rep.get("flashes") or [])) if i],
    }


def fetch_daily_report(date=None):
    """取指定日期日报；指定日期不存在则回退最近一期。"""
    if date:
        try:
            return build_daily(fetch_json(f"{AIHOT}/api/v1/dailies/{date}"))
        except Exception:
            pass  # 回退到最新一期
    try:
        return build_daily(fetch_json(f"{AIHOT}/api/v1/dailies/latest"))
    except Exception:
        pass
    # 再回退：从归档取最近一个日期
    try:
        arch = fetch_json(f"{AIHOT}/api/v1/dailies?limit=7")
        items = arch.get("items") or []
        if items and items[0].get("date"):
            return build_daily(fetch_json(f"{AIHOT}/api/v1/dailies/{items[0]['date']}"))
    except Exception:
        pass
    raise RuntimeError("aihot 日报接口暂不可用")


class H(BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)
        try:
            if path.startswith("/api/aihot/daily"):
                date = qs.get("date", [None])[0]
                data = get_cached(
                    "daily:" + str(date), 600, lambda: fetch_daily_report(date)
                )
                self._send(data)
            elif path.startswith("/api/aihot/dailies"):
                try:
                    take = int(qs.get("take", ["180"])[0])
                except ValueError:
                    take = 180
                arch = get_cached(
                    "dailies", 3600, lambda: fetch_json(f"{AIHOT}/api/v1/dailies?limit={take}")
                )
                items = [
                    {"date": i.get("date"), "leadTitle": i.get("leadTitle")}
                    for i in (arch.get("items") or [])
                ][:take]
                self._send({"items": items})
            elif path.startswith("/api/aihot/hot-topics"):
                data = get_cached("hot-topics", 600, fetch_hot)
                self._send(data)
            else:
                self._send({"error": "not found"}, 404)
        except Exception as e:  # noqa: BLE001
            self._send({"error": str(e)}, 502)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", PORT), H).serve_forever()
