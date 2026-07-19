"""Channel 接入层（Agent-native Harness）：屏蔽渠道差异，统一 Inbound / Outbound 消息。

对标 nanobot 的 Channel 抽象：WebUI / CLI / API / 飞书 / 微信 / Telegram 等统一为标准
消息，核心 Agent（CoachAgent）不关心来源，只处理 InboundMessage -> OutboundMessage。
这正契合我们「一个核心 Harness + 每垂直域一套 Skills/Memory/Tools」的打法——
未来 Vibe-Trading / Deep Tutor 复用同一 core，只换 Skills 与 Memory，接入层不动。

本模块提供：
  - InboundMessage / OutboundMessage 数据类
  - Channel 抽象基类（receive / send），具体实现 ApiChannel / CliChannel
  - AgentHub：注册多个 Channel，统一把入站消息 dispatch 给 Agent core，屏蔽来源
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from agent.orchestrator import CoachAgent


@dataclass
class InboundMessage:
    user_id: int
    content: str
    session_id: str = "default"
    channel: str = "api"
    metadata: dict = field(default_factory=dict)


@dataclass
class OutboundMessage:
    intent: str = "chat"
    content: str = ""
    cards: dict = field(default_factory=dict)
    source: str = "agent"
    session_id: str = "default"
    extra: dict = field(default_factory=dict)


class Channel:
    """渠道抽象：把外部输入转成 InboundMessage，把 OutboundMessage 发回外部。"""

    name = "base"

    async def receive(self) -> InboundMessage:
        raise NotImplementedError

    async def send(self, msg: OutboundMessage) -> None:
        raise NotImplementedError


class ApiChannel(Channel):
    """HTTP API 渠道：入站来自 FastAPI 请求体，出站经 router 透传为 JSON。"""

    name = "api"

    def __init__(self, agent: CoachAgent):
        self._agent = agent

    async def dispatch(self, inbound: InboundMessage) -> OutboundMessage:
        result = await self._agent.handle(
            inbound.user_id, inbound.content, inbound.session_id
        )
        return OutboundMessage(
            intent=result.get("intent", "chat"),
            content=result.get("reply", ""),
            cards=result.get("cards", {}),
            source=result.get("source", "agent"),
            session_id=inbound.session_id,
            extra={k: result[k] for k in ("rag", "anomaly_alert", "source_detail")
                   if k in result},
        )


class CliChannel(Channel):
    """本地 CLI 渠道：stdin 读取、stdout 输出，无 Web 也能驱动 Agent（调试 / 演示用）。"""

    name = "cli"

    def __init__(self, user_id: int = 1, session_id: str = "default"):
        self.user_id = user_id
        self.session_id = session_id

    async def receive(self) -> InboundMessage:
        try:
            line = await asyncio.to_thread(input, "你> ")
        except EOFError:
            return InboundMessage(user_id=self.user_id, content="",
                                  session_id=self.session_id, channel="cli",
                                  metadata={"eof": True})
        return InboundMessage(user_id=self.user_id, content=line,
                              session_id=self.session_id, channel="cli")

    async def send(self, msg: OutboundMessage) -> None:
        text = msg.content or ""
        if msg.cards:
            text += f"\n[卡片] {', '.join(msg.cards.keys())}"
        print(f"教练> {text}")


class AgentHub:
    """渠道中枢：注册多个 Channel，统一入口 dispatch。"""

    def __init__(self):
        self._agent = CoachAgent()
        self._channels: dict[str, Channel] = {}
        self.register(ApiChannel(self._agent))
        self.register(CliChannel())

    def register(self, ch: Channel) -> None:
        self._channels[ch.name] = ch

    def list_channels(self) -> list:
        return [{"name": c.name, "class": type(c).__name__,
                 "doc": (c.__doc__ or "").strip().splitlines()[0]}
                for c in self._channels.values()]

    @property
    def agent(self) -> CoachAgent:
        return self._agent

    def api_channel(self) -> ApiChannel:
        return self._channels["api"]

    async def dispatch_api(self, user_id: int, content: str,
                           session_id: str = "default") -> OutboundMessage:
        return await self._channels["api"].dispatch(
            InboundMessage(user_id=user_id, content=content,
                           session_id=session_id, channel="api")
        )


# 单例：router 与 CLI 共享同一 Agent 实例（记忆 / 推理台账也随之共享）
HUB = AgentHub()
