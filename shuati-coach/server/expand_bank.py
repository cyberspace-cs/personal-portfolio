"""题库规模化扩容：批量生成 + 导入，把题库从几十题扩到数百/数千/上万。

两条来源（均可选、可叠加、幂等可重复执行）：
  1) AI 生成：调 DeepSeek（call_llm_tool，虚拟工具范式）按「分类 × 学科 × 知识点 × 难度」
     矩阵批量产出结构化 MCQ，schema 校验 + 去重后 bulk-insert 进 questions 表。
  2) 开源数据集导入：import_dataset(path) 读取 MMLU/CMMLU/C-Eval/M3KE 风格的 JSON/CSV
     并映射到本表 schema（cat/src/type/stem/opts/answer/explain/topic/difficulty）。

设计要点：
  - 仅在 server/ 目录运行（from database / agent.llm 依赖 cwd）。
  - 启动前加载本地 .env（gitignored，含 DEEPSEEK_API_KEY + LLM_PROVIDER），绝不硬编码密钥。
  - 无 Key 时 AI 生成自动跳过（仍可纯导入数据集），不影响其它来源。
  - 每批插入后记录一次题库版本（record_bank_version），前端 /api/bank 可见。

运行：
  cd server
  DEEPSEEK_API_KEY=sk-xxx LLM_PROVIDER=deepseek python expand_bank.py          # 全量生成+入库
  python expand_bank.py --per-cell 20 --cat 考研                               # 仅考研，每格20题
  python expand_bank.py --import /path/to/ceval_dev.json                       # 仅导入数据集
"""
import os
import sys
import json
import argparse
import hashlib
import asyncio

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _load_env():
    """加载本地 .env（gitignored），仅设置尚未存在的变量，绝不覆盖环境已传值。"""
    p = os.path.join(HERE, ".env")
    if not os.path.exists(p):
        return
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_env()

from database import get_db, record_bank_version
from agent.llm import call_llm_tool, HAS_KEY


# ================================================================
# 题目矩阵：分类 → 学科 → 知识点（topic）
# ================================================================
TOPIC_MATRIX = {
    "考研": {
        "政治": ["马原", "毛中特", "史纲", "思修法基", "当代世界经济与政治"],
        "英语": ["词汇辨析", "长难句语法", "阅读理解", "英译汉", "写作"],
        "数学": ["高等数学", "线性代数", "概率统计"],
        "计算机408": ["数据结构", "计算机组成原理", "操作系统", "计算机网络"],
    },
    "考公": {
        "行测": ["常识判断", "言语理解与表达", "数量关系", "判断推理", "资料分析"],
        "申论": ["归纳概括", "综合分析", "对策建议", "公文写作"],
    },
    "大厂": {
        "算法与数据结构": ["数组与链表", "树与图", "动态规划", "排序与查找", "字符串"],
        "计算机基础": ["操作系统", "计算机网络", "数据库系统", "设计模式"],
        "编程语言": ["Python", "Java", "C++"],
        "系统设计": ["高并发", "缓存", "消息队列", "微服务架构"],
        "职场软技能": ["自我介绍", "项目复盘", "行为面试"],
    },
}

DIFFICULTIES = ["easy", "medium", "hard"]
DIFF_LABEL = {"easy": "基础", "medium": "进阶", "hard": "拔高"}

SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "stem": {"type": "string"},
                    "opts": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4},
                    "answer": {"type": "array", "items": {"type": "integer"}},
                    "explain": {"type": "string"},
                },
                "required": ["stem", "opts", "answer", "explain"],
            },
        }
    },
    "required": ["questions"],
}

_SYSTEM = (
    "你是资深题库命题专家，擅长为中国考试（考研/考公/大厂面试）命制高质量单选题。"
    "要求：① 题干清晰、无歧义；② 4 个选项互斥且只有一个正确；③ 干扰项有迷惑性；"
    "④ 解析(explain)指出考点与关键推理；⑤ 只输出结构化 JSON，不要额外说明。"
)


CHUNK = 10  # 单次 API 调用最多请求的题数（受 max_tokens 限制，约 12 题为上限）


async def _gen_batch(cat, subject, topic, difficulty, n):
    """向 DeepSeek 分批要 n 道该 (cat/subject/topic/difficulty) 的单选题，返回校验过的题列表。

    说明：call_llm_tool 单次输出受 max_tokens 限制，约 12 题封顶；故把 n 拆成每批 CHUNK 题多次调用，
    累计返回，确保 per-cell 设大时也能真正产出更多题目（否则大 per-cell 会被截断、实际只出 ~12 题）。
    """
    clean_all = []
    for start in range(0, n, CHUNK):
        want = min(CHUNK, n - start)
        user = (
            f"请生成 {want} 道单选题。\n"
            f"分类：{cat}；学科：{subject}；知识点：{topic}；难度：{DIFF_LABEL[difficulty]}（{difficulty}）。\n"
            f"每题：stem=题干；opts=长度4的字符串数组（A/B/C/D，仅1个正确）；"
            f"answer=正确项下标数组（0起，如 [2]）；explain=一句话考点解析。\n"
            f"知识点必须紧扣「{topic}」，不要跑题；难度要与「{DIFF_LABEL[difficulty]}」匹配。"
        )
        last = []
        for attempt in range(3):
            try:
                out = await call_llm_tool(_SYSTEM, user, "gen_mcq_batch", SCHEMA, max_tokens=2600)
                if out and out.get("questions"):
                    last = out["questions"]
                    break
            except Exception as e:
                print(f"  [retry {attempt+1}] {cat}/{topic}/{difficulty}: {repr(e)}")
        if not last:
            continue
        for q in last:
            opts = q.get("opts") or []
            ans = q.get("answer") or []
            stem = (q.get("stem") or "").strip()
            if not stem or len(opts) != 4 or not all(isinstance(o, str) and o.strip() for o in opts):
                continue
            if not ans or not all(isinstance(i, int) and 0 <= i < 4 for i in ans):
                continue
            clean_all.append({
                "stem": stem,
                "opts": [o.strip() for o in opts],
                "answer": ans,
                "explain": (q.get("explain") or "").strip() or "（考点见题干与解析）",
            })
    return clean_all


def _insert(conn, rows):
    conn.executemany(
        "INSERT INTO questions (cat, src, type, stem, opts, answer, explain, topic, difficulty, src_type) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()


async def expand(per_cell=12, only_cat=None, dry_run=False, concurrency=8):
    if not HAS_KEY:
        print("[expand] 未检测到 LLM Key，跳过 AI 生成（可用 --import 导入数据集）。")
        return 0
    conn = get_db()
    existing = {r[0] for r in conn.execute("SELECT DISTINCT stem FROM questions").fetchall()}
    seen = set(existing)
    total_new = 0
    sem = asyncio.Semaphore(concurrency)

    async def worker(cat, subject, topic, diff):
        nonlocal total_new
        async with sem:
            batch = await _gen_batch(cat, subject, topic, diff, per_cell)
        if not batch:
            return
        rows = []
        for q in batch:
            h = hashlib.md5(q["stem"].encode("utf-8")).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            rows.append((
                cat, "AI生成(DeepSeek)", "单选题",
                q["stem"], json.dumps(q["opts"], ensure_ascii=False),
                json.dumps(q["answer"], ensure_ascii=False), q["explain"],
                f"{subject}·{topic}", diff, "ai_sim",
            ))
        if rows:
            if not dry_run:
                _insert(conn, rows)
            total_new += len(rows)
            print(f"[+] {cat}/{subject}·{topic}/{diff}: +{len(rows)} (累计新增 {total_new})")

    tasks = []
    for cat, subjects in TOPIC_MATRIX.items():
        if only_cat and cat != only_cat:
            continue
        for subject, topics in subjects.items():
            for topic in topics:
                for diff in DIFFICULTIES:
                    tasks.append(asyncio.create_task(worker(cat, subject, topic, diff)))
    await asyncio.gather(*tasks)
    conn.close()
    if not dry_run and total_new:
        _record_version()
    print(f"[expand] 完成，本次新增 {total_new} 题（AI 生成）。")
    return total_new


def _record_version(_=None):
    conn = get_db()
    cnt = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    try:
        rid = record_bank_version(
            version=cnt, count=cnt,
            sources={"AI生成(DeepSeek)": cnt},
            summary=f"题库扩容至 {cnt} 题（DeepSeek 批量生成 + 开源数据集）",
            status="published", checksum="",
        )
        print(f"[bank] 已记录版本 version={cnt} id={rid}")
    finally:
        conn.close()


def import_dataset(path, cat_map=None, src="开源数据集"):
    """导入 MMLU/CMMLU/C-Eval/M3KE 风格的数据。支持：
    - JSON: {"questions":[{stem,options/opts,answer/index/answer,subject/topic,...}]}
    - 或 C-Eval 格式: [{"question","A".."E","answer"(字母),"subject",...}]
    - CSV (MMLU): question,options(A/B/...),answer(字母)
    自动把字母答案转为 0 起下标，映射 cat/topic。
    """
    cat_map = cat_map or {}
    conn = get_db()
    seen = {hashlib.md5(r[0].encode()).hexdigest() for r in conn.execute("SELECT stem FROM questions").fetchall()}
    rows = []
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        import csv
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for row in csv.DictReader(f):
                q = _parse_mmlu_row(row)
                if q:
                    rows.append(q)
    else:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("questions", data) if isinstance(data, dict) else data
        for it in items:
            q = _parse_generic_item(it, cat_map)
            if q:
                rows.append(q)
    # 去重 + 入库
    new_rows = []
    for r in rows:
        h = hashlib.md5(r[3].encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        new_rows.append(r)
    if new_rows:
        _insert(conn, new_rows)
    conn.close()
    _record_version()
    print(f"[import] {path}: 解析 {len(rows)} 条，去重后新增 {len(new_rows)} 题。")
    return len(new_rows)


def _letter_to_idx(letter):
    if letter is None:
        return None
    letter = str(letter).strip().upper()
    if letter in "ABCDE":
        return "ABCDE".index(letter)
    try:
        return int(letter)
    except Exception:
        return None


def _parse_mmlu_row(row):
    q = (row.get("question") or "").strip()
    opts = [row.get(k, "") for k in ("A", "B", "C", "D", "E") if row.get(k)]
    ans = _letter_to_idx(row.get("answer"))
    if not q or len(opts) < 2 or ans is None or ans >= len(opts):
        return None
    subj = row.get("subject", "")
    cat = "大厂" if any(k in subj.lower() for k in ("computer", "machine", "math", "statistics")) else "考研"
    return (cat, "开源数据集(MMLU)", "单选题", q,
            json.dumps(opts[:4], ensure_ascii=False), json.dumps([ans], ensure_ascii=False),
            "", subj, "medium")


def _parse_generic_item(it, cat_map):
    stem = it.get("question") or it.get("stem") or it.get("q") or ""
    stem = str(stem).strip()
    opts = it.get("options") or it.get("opts") or it.get("choices") or []
    if isinstance(opts, dict):
        opts = [opts.get(k, "") for k in ("A", "B", "C", "D", "E") if k in opts]
    ans_raw = it.get("answer") or it.get("index") or it.get("label") or it.get("correct")
    ans = _letter_to_idx(ans_raw)
    topic = it.get("subject") or it.get("topic") or it.get("category") or ""
    if not stem or len(opts) < 2 or ans is None or ans >= len(opts):
        return None
    cat = cat_map.get(topic, "考研")
    return (cat, "开源数据集", "单选题", stem,
            json.dumps(opts[:4], ensure_ascii=False), json.dumps([ans], ensure_ascii=False),
            str(it.get("explanation") or it.get("explain") or ""), str(topic), "medium")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cell", type=int, default=12, help="每个(分类×知识点×难度)格生成题数")
    ap.add_argument("--concurrency", type=int, default=8, help="并发生成的(分类×知识点×难度)格数")
    ap.add_argument("--cat", default=None, help="仅生成指定分类（考研/考公/大厂）")
    ap.add_argument("--import", dest="import_path", default=None, help="导入开源数据集 JSON/CSV 路径")
    ap.add_argument("--dry-run", action="store_true", help="只生成不入库")
    args = ap.parse_args()
    if args.import_path:
        import_dataset(args.import_path)
    else:
        import asyncio
        asyncio.run(expand(per_cell=args.per_cell, only_cat=args.cat, dry_run=args.dry_run, concurrency=args.concurrency))


if __name__ == "__main__":
    main()
