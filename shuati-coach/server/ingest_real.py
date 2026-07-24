#!/usr/bin/env python3
"""真实题库摄入管线（治本路线：引入官方 / 权威题库，而非 AI 合成）。

为什么需要它：
- 现有题库 99.6% 是 AI 生成的模拟题（src_type='ai_sim'），不具官方权威性。
- 本脚本是「真实题」的统一入口：无论是合法开放数据集，还是用户已授权拥有的
  官方真题 / 教材题（肖秀荣1000题、考研历年真题、考公行测/申论真题卷、LeetCode/牛客真题），
  都经此处校验、去重、打权威标签后入库。
- 绝不抓取受版权保护内容；本脚本只负责「用户/合规渠道提供的文件」的入库。

支持格式：
- JSON : [ {cat, src, type, stem, opts:[...], answer:[idx...], explain, topic, difficulty,
            src_type, year, license}, ... ]
- CSV  : 列含 cat,src,type,stem,opts,answer,explain,topic,difficulty,src_type,year,license
         opts 支持 JSON 数组 或 "A;B;C;D"；answer 支持 [0,1] / "0,1" / "AB"(字母)
- MD   : 每题以空行分隔，含「题干/选项/答案/解析/来源/分类/知识点/难度」标记行

用法：
    python ingest_real.py data/incoming/考研政治真题.json
    python ingest_real.py data/incoming/leetcode.csv --src-type institution
    python ingest_real.py data/incoming/考公真题.md --cat 考公 --src-type official --license "用户授权·自有资料"
    python ingest_real.py file.json --dry-run        # 只校验，不写库
    python ingest_real.py file.json --default-src 考研帮   # 缺 src 字段时回填
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import sys

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("COACH_DB", os.path.join(DB_DIR, "coach.db"))

VALID_TYPES = {"单选题", "多选题", "判断题", "填空题", "简答题"}
VALID_DIFF = {"easy", "medium", "hard"}
VALID_SRC_TYPES = {"official", "institution", "ai_sim"}


def norm_opts(raw):
    """把 opts 解析成字符串列表。支持 JSON 数组 / 分号 / 竖线 分隔。"""
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str):
        s = raw.strip()
        if s.startswith("["):
            try:
                arr = json.loads(s)
                return [str(x).strip() for x in arr if str(x).strip()]
            except Exception:
                pass
        for sep in ("；", ";", "|", "｜", ","):
            if sep in s:
                return [x.strip() for x in s.split(sep) if x.strip()]
        return [s] if s else []
    return []


def norm_answer(raw, n_opts):
    """把 answer 解析成 0 起下标列表，并校验边界。支持 [0,1] / "0,1" / "AB"(字母) / 数字字符串。"""
    if isinstance(raw, list):
        toks = [str(x).strip() for x in raw]
    elif isinstance(raw, str):
        s = raw.strip()
        if s.startswith("["):
            try:
                toks = [str(x).strip() for x in json.loads(s)]
            except Exception:
                toks = re.split(r"[,\s;；]+", s)
        else:
            toks = re.split(r"[,\s;；]+", s)
    else:
        return None
    idx = []
    for t in toks:
        t = t.strip()
        if not t:
            continue
        # 字母 A/B/C -> 0/1/2
        if re.fullmatch(r"[A-Za-z]", t):
            idx.append(ord(t.upper()) - 65)
        else:
            try:
                idx.append(int(t))
            except Exception:
                return None
    idx = sorted(set(i for i in idx if 0 <= i < n_opts))
    return idx if idx else None


def parse_md(text):
    """极简 Markdown 解析：每题以空行分隔，识别 题干/选项/答案/解析/来源/分类/知识点/难度。"""
    blocks = re.split(r"\n\s*\n", text.strip())
    out = []
    for blk in blocks:
        if not blk.strip():
            continue
        q = {"stem": "", "opts": [], "answer": [], "explain": "", "src": "", "cat": "", "topic": "", "difficulty": "", "type": "单选题"}
        cur = None
        for line in blk.splitlines():
            m = re.match(r"\s*(题干|题目|选项|答案|解析|来源|分类|知识点|难度|类型)\s*[:：]\s*(.*)", line)
            if m:
                key, val = m.group(1), m.group(2).strip()
                if key in ("题干", "题目"):
                    q["stem"] = val; cur = None
                elif key == "选项":
                    cur = "opts"
                    # 可能同行多选项 A.xxx B.xxx
                    inline = re.findall(r"[A-Z][.、)]\s*([^A-Z]*)", val)
                    if inline:
                        q["opts"] = [x.strip() for x in inline if x.strip()]
                    elif val:
                        q["opts"] = norm_opts(val)
                elif key == "答案":
                    q["answer"] = norm_answer(val, 999) or []
                    cur = None
                elif key == "解析":
                    q["explain"] = val; cur = None
                elif key == "来源":
                    q["src"] = val; cur = None
                elif key == "分类":
                    q["cat"] = val; cur = None
                elif key == "知识点":
                    q["topic"] = val; cur = None
                elif key == "难度":
                    q["difficulty"] = val; cur = None
                elif key == "类型":
                    q["type"] = val; cur = None
            elif cur == "opts":
                # 续行选项 A.xxx
                m2 = re.match(r"\s*([A-Z])\s*[.、)]\s*(.*)", line)
                if m2:
                    q["opts"].append(m2.group(2).strip())
        if q["stem"] and q["opts"]:
            out.append(q)
    return out


def load_items(path):
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if ext == ".json":
        data = json.loads(text)
        return data if isinstance(data, list) else data.get("questions", [])
    if ext == ".csv":
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    if ext in (".md", ".markdown", ".txt"):
        return parse_md(text)
    raise SystemExit(f"[ingest] 不支持的格式：{ext}")


def build_records(items, args):
    """校验 + 补全字段，返回待入库记录列表。"""
    records = []
    skipped = {"empty_stem": 0, "bad_opts": 0, "bad_answer": 0, "unknown_type": 0, "unknown_diff": 0}
    for i, raw in enumerate(items):
        q = {k: (raw.get(k) if isinstance(raw, dict) else getattr(raw, k, None)) for k in
             ("cat", "src", "type", "stem", "opts", "answer", "explain", "topic", "difficulty", "src_type", "year", "license")}
        stem = (q["stem"] or "").strip()
        if not stem:
            skipped["empty_stem"] += 1
            continue
        opts = norm_opts(q.get("opts"))
        if len(opts) < 2:
            skipped["bad_opts"] += 1
            continue
        ans = norm_answer(q.get("answer"), len(opts))
        if ans is None:
            skipped["bad_answer"] += 1
            continue
        typ = (q.get("type") or "单选题").strip()
        if typ not in VALID_TYPES:
            skipped["unknown_type"] += 1
            typ = "单选题"
        diff = (q.get("difficulty") or "medium").strip()
        if diff not in VALID_DIFF:
            skipped["unknown_diff"] += 1
            diff = "medium"
        src_type = (q.get("src_type") or args.src_type or "institution").strip()
        if src_type not in VALID_SRC_TYPES:
            src_type = "institution"
        rec = (
            q.get("cat") or args.cat or "",
            q.get("src") or args.default_src or "",
            typ,
            stem,
            json.dumps(opts, ensure_ascii=False),
            json.dumps(ans, ensure_ascii=False),
            q.get("explain") or "",
            q.get("topic") or "",
            diff,
            src_type,
            int(q["year"]) if str(q.get("year") or "").strip().isdigit() else None,
            q.get("license") or args.license or "",
        )
        records.append((rec, hashlib.md5(stem.encode("utf-8")).hexdigest()))
    return records, skipped


def main():
    ap = argparse.ArgumentParser(description="真实题库摄入管线")
    ap.add_argument("file", help="JSON / CSV / MD 题库文件")
    ap.add_argument("--cat", default="", help="缺 cat 字段时回填的默认分类")
    ap.add_argument("--default-src", default="", help="缺 src 字段时回填的默认来源名")
    ap.add_argument("--src-type", default="institution", choices=list(VALID_SRC_TYPES),
                    help="权威类型（默认 institution；官方真题用 official）")
    ap.add_argument("--license", default="", help="来源许可说明，如 'CC-BY-SA' / '用户授权·自有资料'")
    ap.add_argument("--dry-run", action="store_true", help="只校验，不写库")
    args = ap.parse_args()

    if not os.path.exists(args.file):
        raise SystemExit(f"[ingest] 找不到文件：{args.file}")

    items = load_items(args.file)
    print(f"[ingest] 解析到 {len(items)} 条待处理")
    records, skipped = build_records(items, args)
    print(f"[ingest] 校验通过 {len(records)} 条；跳过 {skipped}")

    if args.dry_run:
        print("[ingest] --dry-run 模式，未写库。")
        return

    conn = sqlite3.connect(DB_PATH)
    existing = {hashlib.md5(r[0].encode("utf-8")).hexdigest()
               for r in conn.execute("SELECT DISTINCT stem FROM questions").fetchall()}
    seen = set(existing)
    new_rows = []
    dups = 0
    for rec, h in records:
        if h in seen:
            dups += 1
            continue
        seen.add(h)
        new_rows.append(rec)  # rec 已是 12 字段元组
    # rec 是 12 元组，直接插入
    if new_rows:
        conn.executemany(
            "INSERT INTO questions (cat, src, type, stem, opts, answer, explain, topic, difficulty, src_type, year, license) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            new_rows,
        )
        conn.commit()
    conn.close()
    print(f"[ingest] 实际入库 {len(new_rows)} 条；重复跳过 {dups} 条。")


if __name__ == "__main__":
    main()
