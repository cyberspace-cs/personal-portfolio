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


# ─────────────────────────────────────────────────────────────────────────────
# CLI-native OA 工具层（呼应 HKUDS / CLI-Anything）
# -----------------------------------------------------------------------------
# 设计（面试可讲）：
# - CLI 是 Agent 的「原生接口」——文本命令无歧义、省 token、可脚本化、可审计。
#   把 OA 的内部操作暴露为**统一的 CLI 式命令**，Agent 就能像人在终端里敲命令一样
#   原生驱动 OA，而不必依赖 GUI 自动化或硬编码 HTTP 拼装。
# - 每个工具同时有：结构化 schema（name/params）+ 一个 `cli` 自然语言命令模板。
#   编排层既可按 schema 精确调用，也可把 `cli` 直接拼成命令回显给用户，体现「CLI-native」。
# - 真实落地：McpOAClient 即这些命令背后的 MCP server（部署时绑定）；本层用 MockOAClient
#   让整条链路零依赖可演示、可当场跑通。
# ─────────────────────────────────────────────────────────────────────────────

OA_TOOLS: List[Dict] = [
    {
        "name": "oa_approval_submit",
        "summary": "提交一个审批节点到 OA（如 Ukey 制作、权限变更）",
        "cli": "oa approval submit --type <审批类型> --applicant <申请人> --owner <审批责任人> --due <YYYY-MM-DD>",
        "params": [
            {"name": "type", "required": True, "desc": "审批类型，如 ukey / 权限变更 / 资产签收"},
            {"name": "applicant", "required": True, "desc": "申请人姓名"},
            {"name": "owner", "required": True, "desc": "审批责任人"},
            {"name": "due", "required": False, "desc": "截止日期 YYYY-MM-DD"},
        ],
        "_handler": "submit",
    },
    {
        "name": "oa_approval_query",
        "summary": "查询 OA 审批单状态",
        "cli": "oa approval query --ticket <OA-xxxxx>",
        "params": [
            {"name": "ticket", "required": True, "desc": "OA 单据号，如 OA-00001"},
        ],
        "_handler": "query",
    },
    {
        "name": "oa_approval_approve",
        "summary": "审批/驳回一个 OA 审批单（双人审批第二人）",
        "cli": "oa approval approve --ticket <OA-xxxxx> --approver <审批人> --decision <approve|reject>",
        "params": [
            {"name": "ticket", "required": True, "desc": "OA 单据号"},
            {"name": "approver", "required": True, "desc": "审批人"},
            {"name": "decision", "required": True, "desc": "approve 或 reject"},
        ],
        "_handler": "approve",
    },
    {
        "name": "oa_workorder_advance",
        "summary": "推进工单状态机到指定步骤",
        "cli": "oa workorder advance --id <WO-xxx> --step <步骤序号>",
        "params": [
            {"name": "id", "required": True, "desc": "工单号"},
            {"name": "step", "required": True, "desc": "目标步骤序号"},
        ],
        "_handler": "advance",
    },
    {
        "name": "oa_catalog_list",
        "summary": "列出审计支持 / 运维服务目录",
        "cli": "oa catalog list",
        "params": [],
        "_handler": "catalog",
    },
    {
        "name": "oa_alert_raise",
        "summary": "上报一条运维监控告警",
        "cli": "oa alert raise --level <warn|crit> --msg <告警内容>",
        "params": [
            {"name": "level", "required": True, "desc": "warn 或 crit"},
            {"name": "msg", "required": True, "desc": "告警内容"},
        ],
        "_handler": "alert",
    },
]


# 工单/告警的轻量内存状态（演示用，零依赖）
_WORKORDERS: Dict[str, Dict] = {}
_ALERTS: List[Dict] = []


def _dispatch(name: str, args: Dict, oa: Optional[OAClient] = None) -> Dict:
    oa = oa or MockOAClient()
    tool = next((t for t in OA_TOOLS if t["name"] == name), None)
    if not tool:
        return {"ok": False, "error": f"unknown tool: {name}"}
    h = tool["_handler"]
    if h == "submit":
        node = {"name": args.get("type"), "applicant": args.get("applicant"),
                "owner": args.get("owner"), "due": args.get("due")}
        return {"ok": True, "result": oa.submit_approval(node)}
    if h == "query":
        return {"ok": True, "result": oa.query_status(args.get("ticket", ""))}
    if h == "approve":
        return {"ok": True, "result": oa.approve(args.get("ticket", ""),
                                                 args.get("approver", ""), args.get("decision", ""))}
    if h == "advance":
        wid = args.get("id", "")
        _WORKORDERS[wid] = {"id": wid, "step": args.get("step"), "status": "advanced"}
        return {"ok": True, "result": _WORKORDERS[wid]}
    if h == "catalog":
        try:
            from app.services.catalog import CATALOG  # 懒加载，避免循环依赖
            items = [{"id": getattr(c, "id", None), "name": getattr(c, "name", None),
                      "group": getattr(c, "group", None)} for c in CATALOG]
        except Exception:  # noqa: BLE001
            items = []
        return {"ok": True, "result": {"count": len(items), "items": items}}
    if h == "alert":
        rec = {"level": args.get("level"), "msg": args.get("msg"), "status": "raised"}
        _ALERTS.append(rec)
        return {"ok": True, "result": rec}
    return {"ok": False, "error": f"no handler for {name}"}


def list_oa_tools() -> List[Dict]:
    """返回可序列化工具清单（去掉私有 _handler，附带 cli 命令模板）。"""
    out = []
    for t in OA_TOOLS:
        d = {k: v for k, v in t.items() if not k.startswith("_")}
        out.append(d)
    return out


def call_oa_tool(name: str, args: Dict, oa: Optional[OAClient] = None) -> Dict:
    """Agent 原生调用 OA 工具（CLI-Anything 思路：name + args 即一次 CLI 调用）。"""
    return _dispatch(name, args or {}, oa)
