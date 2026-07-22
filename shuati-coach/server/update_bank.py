"""题库自动化流水线：生成 → 校验 → 记录版本。供定时任务（cron / 平台自动化）调用。

流程：
  1. 调 gen_questions.write_questions() 生成最新 questions.json（含质量校验，失败即抛异常退出）
  2. 确保数据库表存在（init_db）
  3. 在 question_bank_versions 落一条 published 版本记录（含 version/count/sources/checksum）

运行：python update_bank.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gen_questions import write_questions
from database import record_bank_version, init_db


def main():
    # 1) 生成 + 校验（校验失败会抛 AssertionError，非零退出，阻断入库）
    out = write_questions()
    # 2) 确保表存在
    init_db()
    # 3) 记录版本
    rid = record_bank_version(
        version=out["version"],
        count=out["count"],
        sources=out.get("sources", {}),
        summary=f"自动更新：{out['count']} 题，来源 {len(out.get('sources', {}))} 个",
        status="published",
        checksum=out.get("checksum", ""),
    )
    print(f"[bank] 已记录题库版本 version={out['version']} id={rid} status=published")


if __name__ == "__main__":
    main()
