"""验证 MemoryStore 的上下文感知滚动摘要压缩（无 Key 降级路径可跑）。

跑法：python -m agent._verify_compress   （在 shuati-coach/server 目录下）
预期：写入超过 SHORT_LIMIT 轮后，旧对话被压缩进 agent_conv_summary，
      build_context 的[对话历史(含压缩)]段同时包含“更早对话压缩摘要”与“最近对话”原文。
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.memory import MemoryStore, SHORT_LIMIT, BUDGET, ensure_tables
from agent.llm import HAS_KEY


async def main():
    ensure_tables()  # 确保 agent_conv_summary 等表存在
    uid, sid = 99001, "verify-compress"
    mem = MemoryStore(uid, sid)
    mem.clear_session()

    # 写入 SHORT_LIMIT + 6 轮，触发 6 轮溢出压缩
    for i in range(SHORT_LIMIT + 6):
        await mem.add_turn("user", f"第{i}轮：我不会概率统计里的期望与方差，请结合我的错题本讲一下")
        await mem.add_turn("assistant", f"第{i}轮：期望是加权平均、方差衡量离散程度，建议先刷变式题巩固")

    summary = mem.get_summary()
    short = mem.short_context()
    ctx = mem.build_context("我现在想制定冲刺计划", "最近薄弱：概率统计")

    print("[step] got summary and context")
    slen = len(short)
    print("[step] short len =", slen)
    print("[step] summary len =", len(summary))
    print("[step] summary head =", summary[:200])
    has_old = "更早对话压缩摘要" in ctx
    has_recent = "最近对话" in ctx
    print("[step] has_old_summary=", has_old, "has_recent=", has_recent)

    assert slen <= SHORT_LIMIT, "滑窗溢出未正确截断"
    assert summary, "溢出的旧对话未被压缩进摘要"
    assert has_old and has_recent, "build_context 未注入压缩段"
    print("[ALL PASS] 上下文感知滚动摘要压缩验证通过")


if __name__ == "__main__":
    asyncio.run(main())
    print("\n[OK] 上下文感知滚动摘要压缩验证通过")
