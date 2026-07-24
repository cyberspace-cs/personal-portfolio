#!/usr/bin/env python3
"""把当前 coach.db 题库导出为 data/questions.json 种子文件。

用途：
- 让空库在首次启动时通过 seed_questions() 自动灌入完整题库（配合 main.py 的 _load_seed_questions）。
- 为 /api/questions/meta 与「多源题库聚合状态」提供真实的 version / sources / checksum / generated_at。
- 提交后，生产环境（Hermes）拉取代码即可获得一份可复现的种子数据，无需重新跑 LLM 扩容。

用法：
    python export_seed.py            # 导出到 data/questions.json
    python export_seed.py --version 3
"""
import argparse
import hashlib
import json
import os
import sqlite3
from collections import Counter
from datetime import datetime, timezone

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "coach.db")
OUT_PATH = os.path.join(DB_DIR, "data", "questions.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", type=int, default=4, help="题库版本号（默认 4）")
    args = ap.parse_args()

    if not os.path.exists(DB_PATH):
        raise SystemExit(f"[export] 找不到数据库：{DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT cat, src, type, stem, opts, answer, explain, topic, difficulty, src_type, year, license FROM questions ORDER BY id"
    ).fetchall()
    conn.close()

    questions = []
    for r in rows:
        q = dict(r)
        # opts/answer 统一解码为列表，便于阅读；_norm() 入库时会再转回 JSON 串
        try:
            q["opts"] = json.loads(q["opts"]) if isinstance(q["opts"], str) else q["opts"]
        except Exception:
            pass
        try:
            q["answer"] = json.loads(q["answer"]) if isinstance(q["answer"], str) else q["answer"]
        except Exception:
            pass
        questions.append(q)

    src_counter = Counter(q["src"] for q in questions)
    # 校验和：基于题目内容做稳定哈希
    payload = json.dumps(questions, ensure_ascii=False, sort_keys=True).encode("utf-8")
    checksum = hashlib.sha256(payload).hexdigest()[:16]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    doc = {
        "version": args.version,
        "generated_at": generated_at,
        "count": len(questions),
        "sources": dict(src_counter),
        "checksum": checksum,
        "questions": questions,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)

    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"[export] 已导出 {len(questions)} 题 -> {OUT_PATH} ({size_kb:.0f} KB)")
    print(f"[export] version={args.version} generated_at={generated_at} checksum={checksum}")
    print(f"[export] 来源分布: {dict(src_counter)}")


if __name__ == "__main__":
    main()
