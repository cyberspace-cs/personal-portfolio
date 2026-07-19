"""本地 CLI 调试入口：无 Web 也能驱动备考 Agent（复用 CoachAgent + CliChannel 渠道抽象）。

用法：
    python run_agent_cli.py [user_id]        # 默认 user_id=1

印证「Agent-native Harness」的 Channel 解耦：核心 Agent 不关心来源，
CLI 只是众多 Channel 之一（另有 ApiChannel 服务 Web/小程序，未来可加飞书/微信/Telegram）。
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from agent.channel import CliChannel, OutboundMessage
from agent.orchestrator import CoachAgent


async def cli_loop(user_id: int):
    agent = CoachAgent()
    ch = CliChannel(user_id=user_id)
    print("=== 刷题教练 CLI（输入 exit / quit 退出）===")
    while True:
        inbound = await ch.receive()
        if inbound.metadata.get("eof"):
            print("\n再见～")
            break
        if inbound.content.strip().lower() in ("exit", "quit"):
            print("再见～")
            break
        if not inbound.content.strip():
            continue
        result = await agent.handle(user_id, inbound.content, inbound.session_id)
        out = OutboundMessage(
            intent=result.get("intent", "chat"),
            content=result.get("reply", ""),
            cards=result.get("cards", {}),
            session_id=inbound.session_id,
            extra={},
        )
        await ch.send(out)


def main():
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    try:
        asyncio.run(cli_loop(user_id))
    except KeyboardInterrupt:
        print("\n再见～")


if __name__ == "__main__":
    main()
