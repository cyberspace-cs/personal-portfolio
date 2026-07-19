"""
审批流接 OA 的 MCP 适配层（Adapter）。

设计目标（面试可讲）：
- 平台「自动拆分审批流程」后，需要把各审批节点推送到真实 OA / 审批中心执行。
- 用 **适配器模式** 隔离「平台内部工单状态机」与「外部 OA 系统」：
  - MockOAClient：演示用，内存模拟 OA 受理/审批回调，零外部依赖；
  - McpOAClient：通过 MCP（Model Context Protocol）调用外部 OA 暴露的 tools，
    平台作为 MCP client，OA 作为 MCP server 暴露 submit_approval / query_status / approve 等工具。
- MCP 是 Agent 生态标准协议（对应岗位要求中的 MCP / tool use），这里把「审批流」做成可被
  Agent 编排层以统一协议调用的外部工具，体现架构的开放性与可扩展性。

说明：真实 OA 的 MCP server 由对方提供；本层只定义协议与 client 骨架，
不内置任何第三方 OA SDK，避免强耦合。
"""

from typing import Dict, List, Optional, Protocol


class OAClient(Protocol):
    def submit_approval(self, node: Dict) -> Dict:
        """提交一个审批节点到 OA，返回 OA 侧单据号与状态。"""
        ...

    def query_status(self, oa_ticket: str) -> Dict:
        ...

    def approve(self, oa_ticket: str, approver: str, decision: str) -> Dict:
        ...


class MockOAClient:
    """演示用 OA：内存记账，支持受理与回调审批。"""

    def __init__(self):
        self._store: Dict[str, Dict] = {}
        self._seq = 0

    def submit_approval(self, node: Dict) -> Dict:
        self._seq += 1
        ticket = f"OA-{self._seq:05d}"
        rec = {
            "oa_ticket": ticket,
            "node": node.get("name"),
            "owner": node.get("owner"),
            "status": "pending",
        }
        self._store[ticket] = rec
        return rec

    def query_status(self, oa_ticket: str) -> Dict:
        return self._store.get(oa_ticket, {"oa_ticket": oa_ticket, "status": "not_found"})

    def approve(self, oa_ticket: str, approver: str, decision: str) -> Dict:
        rec = self._store.get(oa_ticket)
        if not rec:
            return {"oa_ticket": oa_ticket, "status": "not_found"}
        rec["status"] = "approved" if decision == "approve" else "rejected"
        rec["approver"] = approver
        return rec


class McpOAClient:
    """
    通过 MCP 协议对接真实 OA（预留）。
    启用条件：部署环境存在 OA 方提供的 MCP server（暴露 submit_approval / query_status / approve 等 tools），
    并通过 settings.mcp_oa_server 配置端点（如 stdio 命令或 SSE URL）。
    本类仅定义协议骨架，实际 transport 在部署时绑定。
    """

    def __init__(self, server_endpoint: str = ""):
        self.server_endpoint = server_endpoint
        # 真实实现：在此初始化 MCP client session（如 mcp 官方 SDK 的 stdio/sse client）。
        # 例如：
        #   from mcp import ClientSession, StdioServerParameters
        #   self._session = await ClientSession(...)
        self._available_tools = ["submit_approval", "query_status", "approve"]

    def _ensure_session(self):
        # 部署时实现：lazy 建立 MCP session
        if not hasattr(self, "_session") or self._session is None:
            raise RuntimeError(
                "McpOAClient 需要真实 OA 的 MCP server 端点。演示请使用 mock；"
                "部署时参考 README「审批流接真实 OA（MCP）」配置 server_endpoint 并实现 session 绑定。"
            )

    def submit_approval(self, node: Dict) -> Dict:
        self._ensure_session()
        # result = await self._session.call_tool("submit_approval", node)
        # return result
        raise NotImplementedError("MCP transport 在部署时绑定真实 OA server 后实现。")

    def query_status(self, oa_ticket: str) -> Dict:
        self._ensure_session()
        raise NotImplementedError

    def approve(self, oa_ticket: str, approver: str, decision: str) -> Dict:
        self._ensure_session()
        raise NotImplementedError


def build_oa_client(backend: str = "mock", server_endpoint: str = "") -> OAClient:
    if backend == "mcp":
        return McpOAClient(server_endpoint)
    return MockOAClient()
