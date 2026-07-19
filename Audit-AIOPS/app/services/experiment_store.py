"""
科研实验记录智能体 · 实验数据仓库与检索（AdventureX 黑客松原型）

设计强调（用户最关心两点）：
1. 【真实用户数据接入】用户上传自己的实验记录（.md/.txt/.csv/.json/.jsonl/截图）→
   解析、结构化、实体抽取、入库（落盘到 data/experiments/），成为可被检索的私有知识库；
   平台不替用户编造数据，所有回答都基于「用户自己上传的内容」。
2. 【平台起到的效果】所有"效果"指标均从真实入库数据实时计算：沉淀记录数、抽取实体数、
   跨实验关联数（同一材料/方法出现在 ≥2 个实验）、潜在重复实验预警、估算为研究者节省的时间。
   这些指标随用户上传的数据量真实变化，是平台价值的直接证据。

复用：
- retrieval_hybrid.KeywordRetriever / VectorRetriever（关键词 + 向量 + FAISS，纯 CPU/零依赖）；
- multimodal_encoder.build_visual_encoder（截图经视觉编码转文本，proxy 默认、真实模式可插拔）。
实体抽取用「科研领域词典 + 化学式正则 + 数值参数归一」替代 LLM，纯 CPU、零依赖、可复现，
与既有图 RAG（LightRAG 思路）的"领域词典替代 LLM 抽取"一脉相承。
"""

import csv
import io
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.config import settings
from app.services.multimodal_encoder import build_visual_encoder
from app.services.retrieval_hybrid import KeywordRetriever, VectorRetriever, build_embedding_provider

# ----------------------------- 科研领域实体词典（可扩展） -----------------------------
# 用作「领域词典抽取」替代 LLM。覆盖「光催化分解水制氢」示例领域，用户可自由上传其他领域数据，
# 系统还能通过化学式正则 / 数值参数正则补抽，保证跨领域也能连出关系。
SCIENCE_ENTITIES: Dict[str, List[str]] = {
    "光催化": ["光催化", "photocatalysis", "光催化剂", "光催化反应"],
    "产氢": ["产氢", "析氢", "产氢速率", "氢气析出", "h2 evolution", "放氢"],
    "产氧": ["产氧", "析氧", "o2 evolution", "放氧"],
    "全解水": ["全解水", "整体水分解", "overall water splitting"],
    "TiO2": ["tio2", "二氧化钛", "titanium dioxide", "钛白"],
    "Pt": ["pt", "铂", "铂负载", "pt负载", "铂助催化剂"],
    "CdS": ["cds", "硫化镉", "cadmium sulfide"],
    "g-C3N4": ["g-c3n4", "g c3n4", "石墨相氮化碳", "氮化碳", "gcn"],
    "MoS2": ["mos2", "二硫化钼", "mos₂"],
    "WO3": ["wo3", "三氧化钨", "tungsten oxide"],
    "BiVO4": ["bivo4", "钒酸铋", "biVO₄"],
    "牺牲剂": ["牺牲剂", "牺牲试剂", "sacrificial agent", "甲醇牺牲剂", "乳酸牺牲剂", "三乙醇胺"],
    "紫外光": ["紫外光", "uv光", "uv ", "紫外区"],
    "可见光": ["可见光", "visible light", "模拟太阳光", "全光谱"],
    "氙灯": ["氙灯", "xenon lamp", "氙灯光源"],
    "LED光源": ["led光源", "led ", "蓝光led"],
    "水热法": ["水热", "水热法", "hydrothermal", "溶剂热"],
    "溶胶凝胶": ["溶胶凝胶", "sol-gel", "溶胶-凝胶"],
    "煅烧": ["煅烧", "calcination", "退火", "焙烧"],
    "XRD": ["xrd", "x射线衍射", "x-射线衍射"],
    "SEM": ["sem", "扫描电镜", "扫描电子显微镜"],
    "TEM": ["tem", "透射电镜", "透射电子显微镜"],
    "PL光谱": ["pl光谱", "光致发光", "photoluminescence", "荧光光谱"],
    "紫外可见": ["紫外可见", "uv-vis", "紫外可见吸收", "紫外-可见"],
    "电化学": ["电化学", "电化学阻抗", "eis", "线性扫描", "lsv"],
    "量子效率": ["量子效率", "quantum efficiency", "量子产率", "量子产额", "表观量子效率", "abpe"],
    "比表面积": ["比表面积", "bet", "氮气吸附"],
    "光电流": ["光电流", "photocurrent", "瞬态光电流"],
    "阻抗": ["阻抗", "impedance", "nyquist"],
    "载流子": ["载流子", "charge carrier", "载流子分离", "电子空穴对"],
}

# 常见化学元素（用于化学式实体白名单过滤）
_CHEM_ELEMENTS = {
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P",
    "S", "Cl", "Ar", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu",
    "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc",
    "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe", "Cs", "Ba", "La",
    "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At",
    "Rn", "Fr", "Ra", "Ac", "Th", "Pa", "U",
}

# 数值参数归一（量 + 单位 → 统一实体名）
_PARAM_UNIT_ALIASES = {
    "°C": "温度", "℃": "温度", "K": "温度",
    "pH": "pH",
    "M": "浓度", "mol/L": "浓度", "mol": "浓度", "mmol": "浓度",
    "h": "时间", "min": "时间", "s": "时间",
    "nm": "波长", "mV": "电位",
    "%": "比例",
    "mL": "用量", "L": "用量", "g": "用量", "mg": "用量", "μg": "用量", "ug": "用量",
}
_PARAM_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(°C|℃|K|pH|M|mol/L|mol|mmol|h|min|s|nm|mV|%|mL|L|g|mg|μg|ug)"
)
# 化学分子式：大写开头、含数字或属已知元素、长度受限，避免误匹配普通英文词
_FORMULA_RE = re.compile(r"\b([A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)*)\b")


def extract_science_entities(text: str) -> List[str]:
    """从文本抽取科研实体（材料/方法/参数/指标）。确定性、无模型、CPU 可复现。"""
    if not text:
        return []
    text_l = text.lower()
    found: List[str] = []
    # 1) 领域词典
    for name, aliases in SCIENCE_ENTITIES.items():
        for a in aliases:
            if a.lower() in text_l:
                found.append(name)
                break
    # 2) 化学分子式
    for m in _FORMULA_RE.finditer(text):
        tok = m.group(1)
        if 2 <= len(tok) <= 9 and (any(c.isdigit() for c in tok) or tok in _CHEM_ELEMENTS):
            found.append(tok)
    # 3) 数值参数归一
    for m in _PARAM_RE.finditer(text):
        val, unit = m.group(1), m.group(2)
        label = _PARAM_UNIT_ALIASES.get(unit, unit)
        found.append(f"{label}{val}{unit}")
    # 去重保序
    seen = set()
    out: List[str] = []
    for e in found:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


# ----------------------------- 实验共现图（跨实验关联） -----------------------------

class ExperimentGraph:
    """实体共现图：节点=科研实体，边=同一实验记录内共现（权=共现记录数）。

    跨实验关联定义：两个实体共同出现在 ≥2 条不同实验记录中（即它们把不同实验"连"了起来）。
    这是平台"把零散实验连成知识网络"效果的可视化与量化核心。
    """

    def __init__(self, records: List[dict]):
        self.records = records
        self.entity_records: Dict[str, set] = defaultdict(set)
        self.adj: Dict[str, Dict[str, int]] = defaultdict(dict)
        for i, r in enumerate(records):
            ents = r.get("entities", [])
            for e in ents:
                self.entity_records[e].add(i)
            for a in ents:
                for b in ents:
                    if a != b:
                        self.adj[a][b] = self.adj[a].get(b, 0) + 1

    def payload(self) -> dict:
        nodes = [
            {"id": e, "label": e, "records": len(self.entity_records[e])}
            for e in self.entity_records
        ]
        edges = []
        seen = set()
        for a, nb in self.adj.items():
            for b, w in nb.items():
                key = (a, b) if a < b else (b, a)
                if key in seen:
                    continue
                seen.add(key)
                edges.append({"source": key[0], "target": key[1], "weight": w})
        return {"nodes": nodes, "edges": edges, "record_count": len(self.records)}

    def cross_links(self) -> int:
        """跨实验关联数：共同出现在 ≥2 条不同记录的实体对数。"""
        cnt = 0
        seen = set()
        for a, nb in self.adj.items():
            for b in nb:
                key = (a, b) if a < b else (b, a)
                if key in seen:
                    continue
                seen.add(key)
                ra = self.entity_records.get(a, set())
                rb = self.entity_records.get(b, set())
                if len(ra & rb) >= 2:
                    cnt += 1
        return cnt


# ----------------------------- 实验记录 -----------------------------

def _count_kinds(records: List[dict]) -> Dict[str, int]:
    out: Dict[str, int] = defaultdict(int)
    for r in records:
        out[r.get("kind", "txt")] += 1
    return dict(out)


class ExperimentStore:
    """实验数据仓库：真实文件入库 + 混合检索 + 共现图 + 效果指标。进程内单例。"""

    def __init__(self, data_dir: Optional[str] = None):
        root = Path(__file__).resolve().parents[2]
        self.data_dir = Path(data_dir) if data_dir else (root / "data" / "experiments")
        self.uploads_dir = self.data_dir / "uploads"
        self.records_file = self.data_dir / "records.jsonl"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.records: List[dict] = []
        self._kw = None
        self._vec = None
        self._graph_index = None
        self.load()

    # ---- 持久化 ----
    def load(self):
        if self.records_file.exists():
            for line in self.records_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    try:
                        self.records.append(json.loads(line))
                    except Exception:
                        continue
        self._rebuild_index()

    def _persist_all(self):
        self.records_file.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in self.records),
            encoding="utf-8",
        )

    def _rebuild_index(self):
        if not self.records:
            self._kw = None
            self._vec = None
            self._graph_index = None
            return
        self._kw = KeywordRetriever(self.records, top_k=8)
        self._vec = VectorRetriever(
            self.records, build_embedding_provider(settings.embedding_backend), top_k=8
        )
        self._graph_index = ExperimentGraph(self.records)

    # ---- 入库 ----
    def add_record(self, rec: dict):
        self.records.append(rec)
        with self.records_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._rebuild_index()

    def ingest_file(self, filename: str, raw_bytes: bytes, meta: Optional[dict] = None) -> dict:
        """真实文件入库：按扩展名分发（图片走视觉编码，文本/表格走解析）。"""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
        if ext in ("png", "jpg", "jpeg", "webp", "gif"):
            return self._ingest_image(filename, raw_bytes, meta)
        content = raw_bytes.decode("utf-8", errors="replace")
        kind = {
            "md": "md", "markdown": "md", "txt": "txt", "csv": "csv",
            "json": "json", "jsonl": "json",
        }.get(ext, "txt")
        return self.ingest_text(filename, content, kind, meta)

    def ingest_text(self, filename: str, content: str, kind: str = "md", meta: Optional[dict] = None) -> dict:
        title, body, extra_entities = self._parse(filename, content, kind)
        entities = extract_science_entities(f"{title}\n{body}") + extra_entities
        rec = {
            "id": f"EXP-{len(self.records) + 1:03d}",
            "title": title,
            "content": body[:4000],
            "source_file": filename,
            "kind": kind,
            "entities": entities,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "meta": meta or {},
        }
        self.add_record(rec)
        return rec

    def _ingest_image(self, filename: str, raw_bytes: bytes, meta: Optional[dict]) -> dict:
        path = self.uploads_dir / filename
        path.write_bytes(raw_bytes)
        enc = build_visual_encoder()
        caption = enc.encode_image(str(path), f"实验图像记录：{filename}")
        rec = {
            "id": f"EXP-{len(self.records) + 1:03d}",
            "title": f"图像记录：{filename}",
            "content": caption,
            "source_file": filename,
            "kind": "image",
            "image_path": str(path),
            "entities": extract_science_entities(caption),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "meta": {"encoder_mode": enc.mode, **(meta or {})},
        }
        self.add_record(rec)
        return rec

    def _parse(self, filename: str, content: str, kind: str) -> Tuple[str, str, List[str]]:
        if kind == "csv":
            return self._parse_csv(filename, content)
        if kind == "json":
            return self._parse_json(filename, content)
        return self._parse_md(filename, content)

    def _parse_md(self, filename: str, content: str) -> Tuple[str, str, List[str]]:
        title = filename
        body = content
        extra: List[str] = []
        m = re.match(r"#\s+(.+)", content)
        if m:
            title = m.group(1).strip()
        # 抽取「键：值」式字段作为补充实体（如 催化剂、温度、光源）
        for line in content.splitlines():
            s = line.strip().lstrip("-*").strip()
            if "：" in s or ":" in s:
                sep = "：" if "：" in s else ":"
                k = s.split(sep)[0].strip()
                if 1 < len(k) < 14 and not k.startswith("#"):
                    extra.append(k)
        return title, body, extra

    def _parse_csv(self, filename: str, content: str) -> Tuple[str, str, List[str]]:
        reader = csv.reader(io.StringIO(content))
        rows = [r for r in reader if any(c.strip() for c in r)]
        if not rows:
            return filename, "", []
        header = rows[0]
        n = len(rows) - 1
        sample = rows[1] if n >= 1 else []
        body = f"表格《{filename}》字段：{', '.join(header)}。共 {n} 行数据。"
        if sample:
            body += " 示例：" + "；".join(
                f"{h}={v}" for h, v in list(zip(header, sample))[:6]
            )
        return filename, body, list(header)

    def _parse_json(self, filename: str, content: str) -> Tuple[str, str, List[str]]:
        try:
            obj = json.loads(content)
        except Exception:
            return filename, content[:4000], []
        if isinstance(obj, dict):
            title = obj.get("title") or obj.get("name") or filename
            parts = []
            for k, v in obj.items():
                if isinstance(v, (str, int, float, bool)):
                    parts.append(f"{k}：{v}")
                elif isinstance(v, list):
                    parts.append(f"{k}：{len(v)}项")
                elif isinstance(v, dict):
                    parts.append(f"{k}：{len(v)}个字段")
            body = "\n".join(parts) or content[:2000]
            extra = list(obj.keys())
            return title, body[:4000], extra
        if isinstance(obj, list):
            title = filename
            body = f"JSON 数组，共 {len(obj)} 条记录。"
            if obj and isinstance(obj[0], dict):
                body += " 字段：" + ", ".join(list(obj[0].keys())[:10])
                extra = list(obj[0].keys())
            else:
                extra = []
            return title, body, extra
        return filename, content[:4000], []

    # ---- 检索问答（基于用户真实数据，接地、可追溯） ----
    def query(self, q: str, top_k: int = 3) -> dict:
        if not self.records:
            return {
                "answer": "尚未接入任何实验记录。请先上传您的真实实验数据（.md/.csv/.json/截图），"
                          "或点击「加载示例数据」体验。",
                "sources": [],
                "retrieved": [],
                "grounded": False,
            }
        kw = self._kw.search(q, self._kw.top_k)
        vec = self._vec.search(q, self._vec.top_k)
        scored: Dict[int, float] = defaultdict(float)
        for rank, r in enumerate(kw):
            scored[r["doc_index"]] += 1.0 / (60 + rank)
        for rank, r in enumerate(vec):
            scored[r["doc_index"]] += 1.0 / (60 + rank)
        ordered = sorted(scored.items(), key=lambda x: x[1], reverse=True)[:top_k]
        hits = []
        for i, score in ordered:
            d = self.records[i]
            hits.append(
                {
                    "id": d["id"],
                    "title": d["title"],
                    "snippet": d["content"][:160],
                    "score": round(score, 4),
                    "entities": d.get("entities", [])[:8],
                    "kind": d.get("kind"),
                    "source_file": d.get("source_file"),
                }
            )
        return {
            "answer": self._synthesize(q, hits),
            "sources": [h["title"] for h in hits],
            "retrieved": hits,
            "grounded": True,
        }

    def _synthesize(self, q: str, hits: List[dict]) -> str:
        if not hits:
            return "未在您已上传的实验记录中命中相关内容，可尝试更换关键词，或补充上传相关实验数据。"
        top = hits[0]
        lines = [f"基于您上传的 {len(self.records)} 条真实实验记录，命中 {len(hits)} 条最相关结果："]
        for i, h in enumerate(hits, 1):
            lines.append(
                f"\n{i}. 《{h['title']}》（相关度 {h['score']} · 类型 {h['kind']} · 关键要素："
                f"{', '.join(h['entities'][:6]) or '—'}）"
            )
            lines.append(f"   {h['snippet']}")
        lines.append(
            f"\n💡 综合：问题「{q}」可由上述实验记录直接支撑；点击来源可回溯到您上传的原始文件"
            f"《{top['source_file']}》，确保结论可追溯、可核查（不幻觉）。"
        )
        return "\n".join(lines)

    # ---- 图与指标 ----
    def graph(self) -> dict:
        if not self._graph_index:
            return {"nodes": [], "edges": [], "record_count": 0}
        return self._graph_index.payload()

    def _duplicate_pairs(self, threshold: float = 0.5) -> List[dict]:
        pairs: List[dict] = []
        recs = self.records
        for i in range(len(recs)):
            for j in range(i + 1, len(recs)):
                a = set(recs[i].get("entities", []))
                b = set(recs[j].get("entities", []))
                if not a or not b:
                    continue
                jac = len(a & b) / len(a | b)
                if jac >= threshold:
                    pairs.append(
                        {
                            "a": recs[i]["id"],
                            "a_title": recs[i]["title"],
                            "b": recs[j]["id"],
                            "b_title": recs[j]["title"],
                            "jaccard": round(jac, 3),
                            "shared": sorted(a & b)[:8],
                        }
                    )
        pairs.sort(key=lambda x: -x["jaccard"])
        return pairs

    def metrics(self) -> dict:
        n = len(self.records)
        entities: set = set()
        for r in self.records:
            entities.update(r.get("entities", []))
        cross = self._graph_index.cross_links() if self._graph_index else 0
        dups = self._duplicate_pairs()
        # 估算节省时间：每条记录手工整理+检索约 15 分钟；平台秒级完成（演示假设口径）
        saved_min = n * 15
        saved_h = round(saved_min / 60, 1)
        return {
            "records": n,
            "entities": len(entities),
            "cross_links": cross,
            "potential_duplicates": len(dups),
            "duplicate_pairs": dups[:10],
            "kinds": _count_kinds(self.records),
            "estimated_time_saved_minutes": saved_min,
            "estimated_time_saved_hours": saved_h,
            "estimated_time_saved_note": (
                "估算口径：每条记录手工整理+检索约 15 分钟，平台秒级结构化+检索；为演示假设值，"
                "随真实上传数据量线性增长。"
            ),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }

    def delete(self, rec_id: str) -> int:
        before = len(self.records)
        self.records = [r for r in self.records if r["id"] != rec_id]
        removed = before - len(self.records)
        self._persist_all()
        self._rebuild_index()
        return removed

    def reset(self):
        self.records = []
        if self.records_file.exists():
            self.records_file.unlink()
        self._rebuild_index()


# ----------------------------- 示例数据（真实文件落盘，体现"真实接入"） -----------------------------

_SEED_EXPERIMENTS: List[Tuple[str, str, str]] = [
    (
        "E1-Pt-TiO2-光催化产氢.md",
        "# Pt/TiO2 光催化产氢（基准实验）\n"
        "日期：2026-03-02\n催化剂：Pt/TiO2（Pt 负载量 1%）；合成方法：水热法\n"
        "光源：氙灯（300 W）；牺牲剂：甲醇（10 vol%）；温度：25°C；pH：7\n"
        "表征：XRD 确认锐钛矿相，SEM 显示纳米颗粒形貌。\n"
        "结果：产氢速率 1.20 mmol·g⁻¹·h⁻¹，稳定运行 6 h 无明显衰减。\n"
        "结论：Pt 助催化剂有效促进载流子分离，产氢性能良好。",
        "md",
    ),
    (
        "E2-CdS-可见光产氢.md",
        "# CdS 可见光驱动产氢\n"
        "日期：2026-03-05\n催化剂：CdS 纳米棒；合成方法：水热法\n"
        "光源：可见光（420 nm 滤光）；牺牲剂：乳酸（10 vol%）；温度：25°C\n"
        "表征：TEM 显示一维纳米棒，紫外可见吸收边约 510 nm。\n"
        "结果：产氢速率 0.82 mmol·g⁻¹·h⁻¹。\n"
        "结论：CdS 在可见光区有响应，但光腐蚀需进一步抑制。",
        "md",
    ),
    (
        "E3-gC3N4-煅烧产氢.md",
        "# g-C3N4 煅烧后可见光产氢\n"
        "日期：2026-03-08\n催化剂：g-C3N4；合成方法：煅烧（550°C，2 h）\n"
        "光源：可见光；牺牲剂：三乙醇胺（10 vol%）；温度：25°C\n"
        "表征：XRD 与 PL 光谱显示煅烧后缺陷减少、荧光淬灭增强。\n"
        "结果：产氢速率 0.51 mmol·g⁻¹·h⁻¹。\n"
        "结论：煅烧优化能带结构，提升载流子分离效率。",
        "md",
    ),
    (
        "E4-Pt-TiO2-负载量筛选.csv",
        "样品,Pt负载量(%),产氢速率(mmol/g/h),光源,牺牲剂\n"
        "S1,0.5,0.86,氙灯,甲醇\nS2,1.0,1.20,氙灯,甲醇\n"
        "S3,3.0,1.05,氙灯,甲醇\nS4,5.0,0.74,氙灯,甲醇\n",
        "csv",
    ),
    (
        "E5-MoS2-TiO2-可见光产氢.md",
        "# MoS2/TiO2 复合光催化产氢\n"
        "日期：2026-03-11\n催化剂：MoS2/TiO2（MoS2 2%）；合成方法：水热法\n"
        "光源：可见光；牺牲剂：甲醇（10 vol%）；温度：25°C\n"
        "表征：TEM 与 XRD 确认 MoS2 负载于 TiO2 表面。\n"
        "结果：产氢速率 0.95 mmol·g⁻¹·h⁻¹。\n"
        "结论：MoS2 作为助催化剂替代贵金属 Pt，降低成本。",
        "md",
    ),
    (
        "E6-TiO2-煅烧温度筛选.md",
        "# TiO2 煅烧温度对晶相影响\n"
        "日期：2026-03-14\n材料：TiO2 前驱体；合成方法：煅烧（400/500/600°C）\n"
        "表征：XRD 显示 400°C 主要为无定形，500°C 锐钛矿，600°C 出现金红石相。\n"
        "比表面积（BET）：500°C 样品最高。\n"
        "结论：500°C 煅烧为后续 Pt 负载提供最佳载体。",
        "md",
    ),
    (
        "E7-Pt-TiO2-重复性验证.md",
        "# Pt/TiO2 重复性验证实验\n"
        "日期：2026-03-18\n催化剂：Pt/TiO2（Pt 负载量 1%）；合成方法：水热法\n"
        "光源：氙灯（300 W）；牺牲剂：甲醇（10 vol%）；温度：25°C\n"
        "结果：产氢速率 1.17 mmol·g⁻¹·h⁻¹，与基准 E1 偏差 <3%。\n"
        "结论：合成工艺可重复，数据可靠。",
        "md",
    ),
    (
        "E8-全解水-表观量子效率.md",
        "# Pt/TiO2 全解水与表观量子效率(ABPE)测量\n"
        "日期：2026-03-21\n催化剂：Pt/TiO2（1%）；光源：氙灯（全光谱）\n"
        "条件：无牺牲剂，纯水；同时监测产氢与产氧。\n"
        "表征：紫外可见吸收、光电流测试。\n"
        "结果：产氢速率 0.42，产氧速率 0.20（接近 2:1）；表观量子效率(ABPE) 1.8% @ 365 nm。\n"
        "结论：实现全解水，量子效率有待通过载流子调控进一步提升。",
        "md",
    ),
]


def seed_experiments(store: "ExperimentStore", force: bool = False) -> int:
    """把示例实验以真实文件形式落盘并入库（演示「真实文件接入」），返回新增条数。"""
    seed_dir = store.data_dir / "seed"
    seed_dir.mkdir(parents=True, exist_ok=True)
    if force:
        store.reset()
    before = len(store.records)
    for fname, content, kind in _SEED_EXPERIMENTS:
        fpath = seed_dir / fname
        fpath.write_text(content, encoding="utf-8")
        store.ingest_text(fname, content, kind, meta={"seed": True})
    return len(store.records) - before
