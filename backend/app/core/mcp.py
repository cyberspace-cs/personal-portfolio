"""MCP 工具连接器：以 JSON-RPC 风格模拟 Model Context Protocol 的工具调用。

每个外部能力（查订单、查库存、调 API）都注册为一个 MCPTool，
Agent 通过 tools/list 发现、通过 tools/call 调用，解耦「模型」与「外部系统」。
"""
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class MCPTool:
    name: str
    description: str
    schema: dict  # 输入参数 JSON Schema（简化版）
    handler: Callable[[dict], Any]


class MCPConnector:
    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}

    def register(self, tool: MCPTool) -> None:
        self._tools[tool.name] = tool

    def register_fn(self, name: str, description: str, schema: dict, fn: Callable[[dict], Any]) -> None:
        self.register(MCPTool(name=name, description=description, schema=schema, handler=fn))

    def list_tools(self) -> list[dict]:
        """等价 MCP tools/list。"""
        return [
            {"name": t.name, "description": t.description, "inputSchema": t.schema}
            for t in self._tools.values()
        ]

    def invoke(self, name: str, arguments: dict | None = None) -> dict:
        """等价 MCP tools/call，返回标准结果结构。"""
        tool = self._tools.get(name)
        if not tool:
            return {"isError": True, "content": [{"type": "text", "text": f"未知工具: {name}"}]}
        try:
            result = tool.handler(arguments or {})
            return {"isError": False, "content": [{"type": "text", "text": str(result)}]}
        except Exception as e:  # noqa: BLE001
            return {"isError": True, "content": [{"type": "text", "text": f"工具执行失败: {e}"}]}
