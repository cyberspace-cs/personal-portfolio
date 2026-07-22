"""竞赛信息聚合平台 · 自动赛事聚合引擎

设计目标
--------
把"自动搜寻赛事并加入平台"做成**可插拔的来源适配器**管道：
  1. 每个 SourceAdapter 负责「抓取原始页面 -> 解析为结构化 RawCompetition」；
  2. run_collection() 汇总所有来源、按 slug 去重、调用 database.import_competitions 幂等写入；
  3. 网络/解析异常被隔离，单个来源失败不影响整体。

当前内置来源
------------
  - HeikeSongAdapter : 直连 https://heikesong.cn/ 解析服务端渲染的精选轮播（真实联网抓取演示）；
  - BundleAdapter     : 读取 collector_sources.json，内含 62 条**已核实真实链接**的赛事
                        （Kaggle / DataFountain / 百度 AI Studio / 腾讯云 / 天池 / 研究生数模 /
                        工业设计 / 强网杯 / 天府杯 / 京东 等 10 类来源），每条均带可跳转的
                        `source_url`。该文件可随时手动扩充；新增来源只需追加条目即可。

注：Kaggle / DataFountain 等站点列表为前端渲染，未提供可匿名访问的 JSON API，
因此以「已核实真实链接」的归一化数据集接入；HeikeSong 则演示了服务端渲染站点的
实时抓取能力。要接入更多「真·自动搜寻」站点，可参照 HeikeSongAdapter 新增适配器
（针对服务端渲染或带公开 JSON API 的站点）。

扩展方式：新建一个继承 SourceAdapter 的类（实现 fetch/parse），加入 ADAPTERS 即可。
"""
import json
import logging
import os
import re
from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from database import import_competitions

logger = logging.getLogger("competition_hub.collector")

UA = "Mozilla/5.0 (compatible; CompetitionHubBot/1.0; +https://example.com/bot)"
TIMEOUT = 15

# 关键词 -> 分类 slug（用于无显式分类时的自动归类）
CATEGORY_KEYWORDS = [
    ("ctf", ["ctf", "安全", "渗透", "攻防", "网络安全", "漏洞"]),
    ("ai", ["ai", "大模型", "agent", "智能体", "aigc", "机器学习", "深度学习", "llm", "glm", "千问", "智谱", "具身"]),
    ("data", ["数据", "kaggle", "天池", "挖掘", "预测", "推荐", "时序"]),
    ("algorithm", ["算法", "acm", "icpc", "蓝桥", "leetcode", "程序", "coding"]),
    ("design", ["设计", "ui", "ux", "交互", "视觉", "数字媒体", "动画", "产品"]),
    ("dev", ["开发", "软件", "开源", "云原生", "工业", "app", "前端", "全栈", "数据库"]),
    ("innovation", ["创业", "创新", "商业", "硬科技", "投资"]),
    ("hackathon", ["黑客松", "hackathon", "创客", "maker", "thon"]),
]


def classify_category(text: str) -> str:
    t = (text or "").lower()
    for slug, kws in CATEGORY_KEYWORDS:
        if any(k.lower() in t for k in kws):
            return slug
    return "hackathon"


def slugify(s: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", (s or "").strip().lower())
    return (s or "item").strip("-")[:180]


@dataclass
class RawCompetition:
    title: str
    source_url: str = ""
    source: str = ""           # 来源站点名（用于「聚合自 xx」标记）
    category_slug: str = ""
    category_name: str = ""
    organizer: str = ""
    location: str = ""
    mode: str = "offline"      # online / offline / hybrid
    prize: str = ""
    prize_amount: int = 0
    status: str = "upcoming"   # upcoming / ongoing / ended
    start_date: str = ""
    end_date: str = ""
    reg_deadline: str = ""
    summary: str = ""
    description: str = ""
    tags: list = field(default_factory=list)
    cover: str = ""
    featured: bool = False

    def to_row(self) -> dict:
        cat = self.category_slug or classify_category(self.title + " " + self.summary)
        return {
            "title": self.title,
            "slug": slugify(self.title + " " + (self.source or "src")),
            "summary": self.summary,
            "description": self.description,
            "category_slug": cat,
            "category_name": self.category_name or cat,
            "organizer": self.organizer,
            "location": self.location,
            "mode": self.mode if self.mode in ("online", "offline", "hybrid") else "offline",
            "prize": self.prize,
            "prize_amount": int(self.prize_amount or 0),
            "status": self.status if self.status in ("upcoming", "ongoing", "ended") else "upcoming",
            "start_date": self.start_date or None,
            "end_date": self.end_date or None,
            "reg_deadline": self.reg_deadline or None,
            "tags": (self.tags or [])[:10],
            "cover": self.cover,
            "source_url": self.source_url,
            "featured": self.featured,
            "source": self.source,
        }


class SourceAdapter:
    name = ""
    homepage = ""

    def fetch(self) -> str:
        req = Request(self.homepage, headers={"User-Agent": UA})
        with urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read().decode("utf-8", "ignore")

    def parse(self, html: str) -> list[RawCompetition]:
        raise NotImplementedError


class HeikeSongAdapter(SourceAdapter):
    """直连天天黑客松，解析首页服务端渲染的精选轮播（真实联网抓取）。"""

    name = "天天黑客松(heikesong.cn)"
    homepage = "https://heikesong.cn/"

    def parse(self, html: str) -> list[RawCompetition]:
        out: list[RawCompetition] = []
        blocks = html.split("cyber-carousel-slide")
        for blk in blocks[1:]:
            title_m = re.search(r"cyber-carousel-title[^>]*>([^<]+)<", blk)
            if not title_m:
                continue
            desc_m = re.search(r"cyber-carousel-desc[^>]*>([^<]+)<", blk)
            tag_m = re.search(r"cyber-carousel-tag[^>]*>([^<]+)<", blk)
            img_m = re.search(r'cyber-carousel-img"[^>]*\bsrc="([^"]+)"', blk) or \
                re.search(r'src="([^"]+)"[^>]*cyber-carousel-img', blk)
            title = title_m.group(1).strip()
            tag = tag_m.group(1).strip() if tag_m else ""
            desc = desc_m.group(1).strip() if desc_m else ""
            out.append(RawCompetition(
                title=title,
                source=self.name,
                source_url=self.homepage,
                category_slug=classify_category(title + " " + tag),
                category_name=tag or "黑客松",
                summary=desc,
                description=desc,
                cover=(img_m.group(1) if img_m else ""),
                status="ongoing",
                featured=True,
                tags=[t for t in [tag] if t][:5],
            ))
        logger.info("[%s] 解析到 %d 条精选赛事", self.name, len(out))
        return out


class BundleAdapter(SourceAdapter):
    """读取本地多源数据集（模拟对接多个赛事站点的归一化结果）。"""

    name = "多源聚合数据集"
    homepage = ""

    def __init__(self, path: str = None):
        self.path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "collector_sources.json")

    def fetch(self) -> str:
        return ""

    def parse(self, html: str = "") -> list[RawCompetition]:
        if not os.path.exists(self.path):
            logger.warning("聚合数据集文件缺失: %s", self.path)
            return []
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            logger.exception("读取聚合数据集失败")
            return []
        out: list[RawCompetition] = []
        valid = set(RawCompetition.__dataclass_fields__)
        for d in data:
            item = {k: d.get(k, "") for k in valid}
            item["tags"] = d.get("tags", []) or []
            item["featured"] = bool(d.get("featured", False))
            out.append(RawCompetition(**item))
        logger.info("[%s] 载入 %d 条赛事", self.name, len(out))
        return out


# 已注册来源（新增来源只需加入此列表）
ADAPTERS: list[SourceAdapter] = [HeikeSongAdapter(), BundleAdapter()]


def run_collection(adapters: list = None) -> dict:
    """执行一次全源聚合，返回各来源抓取量与写入统计。"""
    adapters = adapters or ADAPTERS
    agg = {"sources": [], "created": 0, "updated": 0, "skipped": 0, "failed": 0, "total": 0}
    all_rows: list[dict] = []
    for ad in adapters:
        try:
            html = ad.fetch()
            items = ad.parse(html)
            rows = [it.to_row() for it in items]
            agg["sources"].append({"name": ad.name, "fetched": len(rows)})
            all_rows.extend(rows)
        except Exception as e:
            logger.exception("采集源失败: %s", ad.name)
            agg["sources"].append({"name": ad.name, "fetched": 0, "error": str(e)[:160]})

    # 按 slug 去重（后者覆盖前者）
    dedup: dict[str, dict] = {}
    for r in all_rows:
        dedup[r["slug"]] = r
    unique = list(dedup.values())

    stats = import_competitions(unique)
    agg.update(stats)
    agg["total"] = len(unique)
    logger.info("聚合完成：新增 %d / 更新 %d / 失败 %d / 合计 %d",
                stats["created"], stats["updated"], stats["failed"], len(unique))
    return agg


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    from database import init_db
    init_db()
    print(json.dumps(run_collection(), ensure_ascii=False, indent=2))
