"""前沿 CS / AI 信息爬虫。

从公开、无需鉴权的来源抓取最新前沿信息并写入本地数据库：
- GitHub 仓库（topic 检索，国内外均可访问，作为主源）
- Gitee 仓库（码云，国内访问更稳，作为 GitHub 的备源）
- HuggingFace Papers（含真实封面缩略图 thumbnailUrl，解决「看不到画像」）
- arXiv API（cs.CL / cs.LG / cs.AI / cs.CV 最新论文）
- CSDN 博客（用户 RSS 聚合，覆盖国内技术分享）
- AI 资讯（VentureBeat / The Batch / Google AI / HuggingFace Blog 等 RSS）
- Semantic Scholar 论文（带 429 退避，补充论文源）

设计要点：
- 仅使用标准库（urllib / xml.etree / json），无第三方依赖。
- 按 source_url 去重，已存在的条目自动跳过。
- 网络不可用时安全返回统计，不会抛崩。
- 与数据库 schema 对齐（含 image_url）。

用法：
    python crawler.py                      # 抓取全部可用源，各 20 条
    python crawler.py --source github      # 仅 GitHub
    python crawler.py --source gitee       # 仅 Gitee
    python crawler.py --source csdn        # 仅 CSDN 博客
    python crawler.py --source news        # 仅 AI 资讯
    python crawler.py --limit 40           # 控制每个源的数量
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
import urllib.request
import urllib.error
import urllib.parse
from database import get_db, init_db, get_category_by_slug, insert_item, count_items

UA = "cs-frontier-hub-crawler/1.1 (+https://github.com/cyberspace-cs/personal-portfolio)"

# 文本 -> 分类 slug 的关键词映射（顺序即优先级，越具体越靠前）
CATEGORY_KEYWORDS = [
    ("agent-framework", ["langchain", "langgraph", "llamaindex", "llama_index", "agent framework", "agentic framework"]),
    ("multi-agent", ["multi-agent", "multi agent", "autogen", "crewai", "agent orchestrat", "orchestrat"]),
    ("mcp", ["model context protocol", " mcp", "mcp server"]),
    ("rag", ["rag", "retrieval-augmented", "retrieval augmented", "graphrag", "retrieval-aug"]),
    ("agent-eval", ["swe-bench", "agentbench", "terminal-bench", "agent evaluation", "agent harness", "benchmark for agent"]),
    ("agent-arch", ["agent memory", "agent architecture", "agent planning", "tool-use agent", "tool use agent"]),
    ("rl-agentic", ["agentic rl", "verl", "grpo", "rlhf", "reinforcement learning", "reward model", "ppo"]),
    ("finetune", ["sft", "fine-tun", "instruction tun", " lora", "qlora", "dpo", "alignment", "post-train", "post train"]),
    ("pretrain", ["pre-train", "pretraining", "pretrain", "megatron", "scaling law", "scaling laws"]),
    ("context-parallel", ["ring attention", "context parallel", "sequence parallel", "long context", "long-context"]),
    ("gpu-triton", ["triton", "cuda kernel", "gpu kernel", "flashattention", "cutlass", "gpu operator"]),
    ("inference-engine", ["vllm", "sglang", "tensorrt", "inference engine", "inference serving", "llm serving"]),
    ("inference-opt", ["kv-cache", "kv cache", "quantiz", "speculative decoding", "pagedattention", "inference optim"]),
    ("llm-arch", ["transformer", "mixture of experts", "moe", "llm architecture", "attention mechanism", "kv compression"]),
    ("multimodal", ["vlm", "vision-language", "vision language", "multi-modal", "multimodal", "image generation", "diffusion", "video generation"]),
    ("ai-infra", ["ai infra", "training cluster", "hunyuan", "distributed training", "collective communication", "training infrastructure"]),
    ("data", ["dataset", "synthetic data", "data flywheel", "data engine", "data pipeline"]),
    ("systems", ["operating system", "kernel", "rust ", "database", "sandbox", "linux kernel", "file system"]),
    ("conference", ["icml", "iclr", "neurips", "nips", "acl ", "cvpr", "conference"]),
    ("frontier-model", ["deepseek", "kimi", "claude", "gpt-4", "gpt4", "gemini", "qwen", "llama 3", "llama3", "model release", "frontier model"]),
]

# 各源默认分类关键词：博客 / 资讯更泛，补一些高频词
BLOG_KEYWORDS = [
    ("agent-framework", ["agent", "langchain", "langgraph", "crewai", "autogen"]),
    ("rag", ["rag", "检索增强", "知识库"]),
    ("finetune", ["微调", "fine-tun", "lora", "对齐", "sft"]),
    ("llm-arch", ["大模型", "llm", "transformer", "大模型架构"]),
    ("multimodal", ["多模态", "multimodal", "vlm", "视觉"]),
    ("inference-opt", ["推理", "inference", "量化", "quantiz"]),
    ("rl-agentic", ["强化学习", "reinforcement", "rlhf", "grpo"]),
    ("ai-infra", ["ai infra", "训练", "推理服务", "算力"]),
    ("frontier-model", ["gpt", "claude", "gemini", "deepseek", "kimi", "qwen", "大模型发布", "发布"]),
]

# CSDN 技术博主 RSS（可按需扩展；格式 https://blog.csdn.net/<username>/rss/list）
CSDN_BLOGGERS = [
    "weixin_43902449",  # 已验证可访问的示例博主
]

# AI 资讯 / 博客 RSS 源（覆盖国内外）
NEWS_FEEDS = [
    ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    ("Google AI Blog", "https://blog.google/technology/ai/rss/"),
    ("Google Research Blog", "https://research.google/blog/rss/"),
    ("MIT Tech Review · AI", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ("The Verge · AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("BAIR Blog", "https://bair.berkeley.edu/blog/feed.xml"),
    ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml"),
    ("Towards Data Science", "https://towardsdatascience.com/feed"),
    ("Machine Learning Mastery", "https://machinelearningmastery.com/feed/"),
]

# GitHub 检索式（topic 维度，多角度覆盖前沿）
GITHUB_QUERIES = [
    "topic:llm stars:>2000",
    "topic:agent stars:>800",
    "topic:rag stars:>500",
    "topic:llm-inference stars:>500",
    "topic:mcp-server stars:>200",
]


def _slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    s = re.sub(r"[\s_-]+", "-", s)
    return s or "item"


def classify(text: str) -> str:
    t = (text or "").lower()
    # 博客 / 中文资讯优先用更贴合的关键词
    for slug, kws in BLOG_KEYWORDS:
        if any(kw in t for kw in kws):
            return slug
    for slug, kws in CATEGORY_KEYWORDS:
        if any(kw in t for kw in kws):
            return slug
    return "frontier-model"


def http_get_json(url: str, timeout: int = 25) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get_text(url: str, timeout: int = 25) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _exists_by_url(conn: sqlite3.Connection, url: str) -> bool:
    return conn.execute("SELECT 1 FROM items WHERE source_url=?", (url,)).fetchone() is not None


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _strip_html(html: str) -> str:
    return _clean(re.sub(r"<[^>]+>", " ", html or ""))


# --------------------------------------------------------------------------- #
# RSS / Atom 解析（博客、资讯通用）
# --------------------------------------------------------------------------- #
def parse_feed(raw: str) -> list[dict]:
    """返回 [{title, link, summary, published}]，兼容 RSS 2.0 与 Atom。"""
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(raw)
    except Exception:
        return []
    ns = {
        "a": "http://www.w3.org/2005/Atom",
        "dc": "http://purl.org/dc/elements/1.1/",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }
    items = []
    # RSS 2.0: rss/channel/item
    for it in root.findall(".//item"):
        title = _clean(it.findtext("title", default=""))
        link = _clean(it.findtext("link", default=""))
        desc = it.findtext("description", default="") or ""
        # 优先取 content:encoded
        ce = it.find("content:encoded", ns)
        if ce is not None and ce.text:
            desc = ce.text
        summary = _strip_html(desc)[:400]
        pub = _clean(it.findtext("pubDate", default="") or it.findtext("dc:date", default="", namespaces=ns))
        if title and link:
            items.append({"title": title, "link": link, "summary": summary, "published": pub})
    # Atom: feed/entry
    for en in root.findall("a:entry", ns) or root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title = _clean(en.findtext("a:title", default="", namespaces=ns))
        summary_el = en.find("a:summary", ns) or en.find("a:content", ns)
        summary = _strip_html(summary_el.text if summary_el is not None else "")[:400]
        link = ""
        for l in en.findall("a:link", ns):
            rel = l.get("rel")
            if rel in (None, "alternate"):
                link = l.get("href") or ""
                break
        if not link:
            link = _clean(en.findtext("a:id", default="", namespaces=ns))
        pub = _clean(en.findtext("a:updated", default="", namespaces=ns) or en.findtext("a:published", default="", namespaces=ns))
        if title and link:
            items.append({"title": title, "link": link, "summary": summary, "published": pub})
    return items


def _feed_entries(feed_url: str, source_type: str, tags: list[str], limit: int) -> tuple[list[dict], str | None]:
    try:
        raw = http_get_text(feed_url)
    except urllib.error.HTTPError as e:
        return [], f"HTTP {e.code}"
    except Exception as e:
        return [], str(e)
    if not raw:
        return [], "empty"
    out = []
    for it in parse_feed(raw)[:limit]:
        body = f"{it['title']} {it['summary']}"
        slug_src = it["link"].rstrip("/").split("/")[-1] or it["title"]
        out.append({
            "title": it["title"],
            "slug": _slugify(f"{source_type}-{slug_src}")[:80],
            "summary": it["summary"] or it["title"],
            "content": f"## 简介\n{it['summary']}\n\n## 来源\n- {tags[0] if tags else '来源'}: {it['link']}",
            "category_slug": classify(body),
            "source_type": source_type,
            "source_url": it["link"],
            "github_stars": None,
            "author_org": "",
            "language": "",
            "status": "active",
            "featured": False,
            "image_url": "",
            "tags": list(tags),
        })
    return out, None


# --------------------------------------------------------------------------- #
# GitHub 仓库
# --------------------------------------------------------------------------- #
def fetch_github(limit: int = 20) -> list[dict]:
    out: list[dict] = []
    seen = set()
    per = max(8, min(30, limit))
    for q in GITHUB_QUERIES:
        if len(out) >= limit:
            break
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({
            "q": q, "sort": "stars", "order": "desc", "per_page": str(per),
        })
        try:
            data = http_get_json(url)
        except Exception:
            continue
        if not data or "items" not in data:
            continue
        for r in data["items"]:
            full = r.get("full_name")
            if not full or full in seen:
                continue
            seen.add(full)
            desc = _clean(r.get("description") or "")
            body = f"{r.get('name','')} {desc}"
            out.append({
                "title": full,
                "slug": _slugify(f"github-{full}"),
                "summary": desc[:400] or full,
                "content": f"## 简介\n{desc}\n\n## 仓库\n- {r.get('html_url')}\n- ⭐ {r.get('stargazers_count')} · 🍴 {r.get('forks_count')}\n- 语言：{r.get('language') or '—'}\n- 主页：{r.get('homepage') or '—'}",
                "category_slug": classify(body),
                "source_type": "repo",
                "source_url": r.get("html_url"),
                "github_stars": r.get("stargazers_count"),
                "author_org": (r.get("owner") or {}).get("login", ""),
                "language": r.get("language") or "",
                "status": "active",
                "featured": False,
                "image_url": (r.get("owner") or {}).get("avatar_url") or "",
                "tags": ["GitHub", "开源"],
            })
    return out[:limit]


# --------------------------------------------------------------------------- #
# Gitee 仓库（国内备源）
# --------------------------------------------------------------------------- #
def fetch_gitee(limit: int = 20) -> list[dict]:
    queries = ["LLM", "大模型", "agent", "RAG", "深度学习"]
    out: list[dict] = []
    seen = set()
    for q in queries:
        if len(out) >= limit:
            break
        # 注意：Gitee 的 sort 参数较挑剔，这里仅用 order 避免 400，本地再按 star 排序
        url = "https://gitee.com/api/v5/search/repositories?" + urllib.parse.urlencode({
            "q": q, "order": "desc", "page": 1, "per_page": str(min(20, limit)),
        })
        try:
            data = http_get_json(url)
        except urllib.error.HTTPError as e:
            # 403/400 等（如数据中心 IP 被限），跳过该源
            continue
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        for r in data:
            full = r.get("full_name") or r.get("path")
            if not full or full in seen:
                continue
            seen.add(full)
            desc = _clean(r.get("description") or "")
            body = f"{r.get('name','')} {desc}"
            out.append({
                "title": full,
                "slug": _slugify(f"gitee-{full}"),
                "summary": desc[:400] or full,
                "content": f"## 简介\n{desc}\n\n## 仓库\n- {r.get('html_url')}\n- ⭐ {r.get('stargazers_count')}",
                "category_slug": classify(body),
                "source_type": "repo",
                "source_url": r.get("html_url"),
                "github_stars": r.get("stargazers_count"),
                "author_org": (r.get("owner") or {}).get("login", "") if isinstance(r.get("owner"), dict) else r.get("owner", ""),
                "language": r.get("language") or "",
                "status": "active",
                "featured": False,
                "image_url": "",
                "tags": ["Gitee", "开源", "国内镜像"],
            })
    out.sort(key=lambda x: (x.get("github_stars") or 0), reverse=True)
    return out[:limit]


# --------------------------------------------------------------------------- #
# HuggingFace Papers（含真实封面）
# --------------------------------------------------------------------------- #
def fetch_huggingface(limit: int = 20) -> list[dict]:
    url = f"https://huggingface.co/api/papers?sort=upvotes&limit={limit}"
    data = http_get_json(url)
    if not data:
        return []
    out = []
    for p in data:
        pid = p.get("id")  # arxiv id, 如 2405.04434
        if not pid:
            continue
        abs_url = f"https://arxiv.org/abs/{pid}"
        summary = ""
        try:
            detail = http_get_json(f"https://huggingface.co/api/papers/{pid}")
            summary = detail.get("summary") or detail.get("abstract") or ""
        except Exception:
            pass
        authors = p.get("authors") or []
        org = authors[0].get("name", "") if authors else ""
        title = _clean(p.get("title", ""))
        if not title:
            continue
        body = (summary or title)
        out.append({
            "title": title,
            "slug": _slugify(f"hf-{pid}"),
            "summary": _clean(summary)[:400] if summary else title,
            "content": f"## 简介\n{_clean(summary)}\n\n## 来源\n- HuggingFace Papers: https://huggingface.co/papers/{pid}\n- arXiv: {abs_url}",
            "category_slug": classify(body),
            "source_type": "paper",
            "source_url": abs_url,
            "github_stars": None,
            "author_org": org,
            "language": "",
            "status": "active",
            "featured": False,
            "image_url": p.get("thumbnailUrl") or "",
            "tags": ["HuggingFace", "论文"],
        })
    return out


# --------------------------------------------------------------------------- #
# arXiv
# --------------------------------------------------------------------------- #
def fetch_arxiv(categories: list[str] | None = None, max_per: int = 8) -> list[dict]:
    if categories is None:
        categories = ["cs.CL", "cs.LG", "cs.AI", "cs.CV"]
    cat_query = " OR ".join(f"cat:{c}" for c in categories)
    query = urllib.parse.urlencode({
        "search_query": cat_query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(max_per * len(categories)),
    })
    try:
        raw = http_get_text(f"http://export.arxiv.org/api/query?{query}")
    except Exception:
        return []
    if not raw:
        return []
    import xml.etree.ElementTree as ET
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw)
    out = []
    seen = set()
    for entry in root.findall("a:entry", ns):
        title = _clean(entry.findtext("a:title", default="", namespaces=ns))
        summary = _clean(entry.findtext("a:summary", default="", namespaces=ns))
        if not title or title in seen:
            continue
        seen.add(title)
        id_url = entry.findtext("a:id", default="", namespaces=ns)
        m = re.search(r"abs/([\w.\-/]+)", id_url)
        pid = m.group(1) if m else _slugify(title)
        authors = [a.findtext("a:name", default="", namespaces=ns) for a in entry.findall("a:author", ns)]
        org = authors[0] if authors else ""
        out.append({
            "title": title,
            "slug": _slugify(f"arxiv-{pid}"),
            "summary": summary[:400],
            "content": f"## 简介\n{summary}\n\n## 来源\n- arXiv: {id_url}",
            "category_slug": classify(f"{title} {summary}"),
            "source_type": "paper",
            "source_url": id_url,
            "github_stars": None,
            "author_org": org,
            "language": "",
            "status": "active",
            "featured": False,
            "image_url": "",
            "tags": ["arXiv", "论文"],
        })
        if len(out) >= max_per * len(categories):
            break
    return out


# --------------------------------------------------------------------------- #
# CSDN 博客（用户 RSS 聚合）
# --------------------------------------------------------------------------- #
def fetch_csdn(limit: int = 20) -> list[dict]:
    out: list[dict] = []
    per_blog = max(3, limit // max(1, len(CSDN_BLOGGERS)))
    for user in CSDN_BLOGGERS:
        if len(out) >= limit:
            break
        feed = f"https://blog.csdn.net/{user}/rss/list"
        entries, err = _feed_entries(feed, "blog", ["CSDN", "博客"], per_blog)
        if err:
            print(f"[crawler] CSDN({user}) 跳过: {err}")
            continue
        out += entries
    return out[:limit]


# --------------------------------------------------------------------------- #
# AI 资讯（多 RSS 源）
# --------------------------------------------------------------------------- #
def fetch_ai_news(limit: int = 20) -> list[dict]:
    out: list[dict] = []
    per_feed = max(2, limit // max(1, len(NEWS_FEEDS)))
    for name, feed in NEWS_FEEDS:
        if len(out) >= limit:
            break
        entries, err = _feed_entries(feed, "news", [name, "AI资讯"], per_feed)
        if err:
            print(f"[crawler] 资讯源({name}) 跳过: {err}")
            continue
        out += entries
    return out[:limit]


# --------------------------------------------------------------------------- #
# Semantic Scholar 论文（带 429 退避）
# --------------------------------------------------------------------------- #
def fetch_semantic_scholar(limit: int = 10) -> list[dict]:
    queries = ["large language model agent", "multimodal foundation model", "llm inference optimization"]
    out: list[dict] = []
    seen = set()
    per = max(3, limit // len(queries))
    for q in queries:
        if len(out) >= limit:
            break
        url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode({
            "query": q, "limit": str(per),
            "fields": "title,url,abstract,year",
        })
        for attempt in range(2):  # 1 次重试，应对 429
            try:
                data = http_get_json(url)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt == 0:
                    time.sleep(3)  # 退避后重试
                    continue
                data = None
                break
            except Exception:
                data = None
                break
        if not data or "data" not in data:
            continue
        for p in data["data"]:
            title = _clean(p.get("title") or "")
            link = p.get("url") or (f"https://www.semanticscholar.org/paper/{p.get('paperId')}" if p.get("paperId") else "")
            if not title or not link or link in seen:
                continue
            seen.add(link)
            abs = _strip_html(p.get("abstract") or "")[:400]
            body = f"{title} {abs}"
            out.append({
                "title": title,
                "slug": _slugify(f"s2-{p.get('paperId', title)}"),
                "summary": abs or title,
                "content": f"## 简介\n{abs}\n\n## 来源\n- Semantic Scholar: {link}",
                "category_slug": classify(body),
                "source_type": "paper",
                "source_url": link,
                "github_stars": None,
                "author_org": "",
                "language": "",
                "status": "active",
                "featured": False,
                "image_url": "",
                "tags": ["SemanticScholar", "论文"],
            })
    return out[:limit]


# --------------------------------------------------------------------------- #
# 入库
# --------------------------------------------------------------------------- #
def store(entries: list[dict]) -> dict:
    init_db()
    conn = get_db()
    added = skipped = errors = 0
    with_imgs = 0
    for e in entries:
        try:
            if _exists_by_url(conn, e["source_url"]):
                skipped += 1
                continue
            cat = get_category_by_slug(e["category_slug"])
            data = {
                "title": e["title"], "slug": e["slug"], "summary": e["summary"],
                "content": e["content"], "category_id": cat["id"] if cat else None,
                "source_type": e["source_type"], "source_url": e["source_url"],
                "github_stars": e["github_stars"], "author_org": e["author_org"],
                "language": e["language"], "status": e["status"],
                "featured": e["featured"], "image_url": e.get("image_url", ""),
            }
            insert_item(data, e.get("tags", []))
            added += 1
            if e.get("image_url"):
                with_imgs += 1
        except Exception as ex:
            errors += 1
            print(f"[crawler] 写入失败「{e.get('title','')}」: {ex}")
    conn.close()
    return {"added": added, "skipped": skipped, "errors": errors, "with_images": with_imgs}


# 各源适配器注册表
ADAPTERS = {
    "github": ("GitHub 仓库", fetch_github),
    "gitee": ("Gitee 仓库", fetch_gitee),
    "hf": ("HuggingFace 论文", fetch_huggingface),
    "arxiv": ("arXiv 论文", fetch_arxiv),
    "csdn": ("CSDN 博客", fetch_csdn),
    "news": ("AI 资讯", fetch_ai_news),
    "semantic": ("Semantic Scholar 论文", fetch_semantic_scholar),
}


def run_crawler(sources: list[str] | None = None, limit: int = 20) -> dict:
    if sources is None:
        sources = ["github", "gitee", "hf", "arxiv", "csdn", "news"]
    by_source: dict[str, dict] = {}
    proc_errors: list[str] = []
    for src in sources:
        if src not in ADAPTERS:
            proc_errors.append(f"未知源: {src}")
            continue
        label, fn = ADAPTERS[src]
        try:
            if src == "arxiv":
                entries = fn(max_per=max(4, limit // 2))
            elif src in ("github", "gitee"):
                entries = fn(limit=limit)
            else:
                entries = fn(limit=limit)
            res = store(entries)
            by_source[label] = {"fetched": len(entries), **res}
        except Exception as ex:
            proc_errors.append(f"{label}:{ex}")
            by_source[label] = {"fetched": 0, "added": 0, "skipped": 0, "errors": 1, "with_images": 0}
    total_added = sum(v.get("added", 0) for v in by_source.values())
    return {
        "added": total_added,
        "skipped": sum(v.get("skipped", 0) for v in by_source.values()),
        "errors": sum(v.get("errors", 0) for v in by_source.values()),
        "with_images": sum(v.get("with_images", 0) for v in by_source.values()),
        "by_source": by_source,
        "sources": sources,
        "proc_errors": proc_errors,
        "db_total": count_items(),
    }


def main():
    ap = argparse.ArgumentParser(description="CS 前沿信息爬虫")
    ap.add_argument("--source", choices=list(ADAPTERS.keys()) + ["all"], default="all")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()
    srcs = list(ADAPTERS.keys()) if args.source == "all" else [args.source]
    print(f"[crawler] 开始抓取 sources={srcs} limit={args.limit}")
    res = run_crawler(srcs, args.limit)
    print("[crawler] 结果:", json.dumps(res, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
