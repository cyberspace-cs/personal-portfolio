"""MCP 适配层：把垂直领域工具（行情 / 题库 / 考纲源）以 MCP 协议接入 Agent。

设计对标 nanobot 的「原生 MCP / Skills 插件化」：垂直能力以工具注入，核心不膨胀。
本模块做成**声明式 MCP 桥**，不依赖第三方 MCP SDK（保持零依赖、可编译、可运行）：

  - MCPToolSpec：工具声明（name / description / input_schema / source）
  - MCPBridge：
      * register_builtin(spec, func)：注册内置 MCP 兼容工具（演示用，如考纲检索 / 题库检索）
      * list_tools()：聚合内置工具 +（配置了 MCP_SERVER_URL 时）远程工具
      * call(tool_name, arguments)：内置直接 func(arguments)；远程走 HTTP JSON-RPC tools/call
  - 降级：远程不可达时返回错误提示，内置工具始终可用。

接真实垂直 MCP server（行情 / 题库 / 考纲）只需设置环境变量 MCP_SERVER_URL
（和可选 MCP_SERVER_KEY），无需改代码——这正是「核心 Harness + 垂直 Skills」的架构红利。

   内置示例工具（证明 MCP 范式已打通）：
     exam_syllabus         按备考分类检索考纲概览（考研 / 考公 / 大厂）
     question_bank_search  按知识点检索垂直题库（对接业务库 questions 表）
"""
import json
import os
from dataclasses import dataclass

import httpx


@dataclass
class MCPToolSpec:
    name: str
    description: str
    input_schema: dict
    source: str = "builtin"   # builtin | remote


class MCPBridge:
    """声明式 MCP 桥：内置工具 + 可选远程 MCP server（HTTP JSON-RPC）。"""

    def __init__(self):
        self._builtins: dict[str, tuple[MCPToolSpec, callable]] = {}
        self._register_default_builtins()

    # ---------------------------------------------------------------
    # 注册 / 列举
    # ---------------------------------------------------------------
    def register_builtin(self, spec: MCPToolSpec, func: callable) -> None:
        self._builtins[spec.name] = (spec, func)

    def _register_default_builtins(self) -> None:
        self.register_builtin(
            MCPToolSpec(
                "exam_syllabus",
                "按备考分类检索考纲概览（考研 / 考公 / 大厂）。",
                {"type": "object",
                 "properties": {"cat": {"type": "string",
                                         "description": "考研 / 考公 / 大厂"}},
                 "required": ["cat"]},
                "builtin",
            ),
            self._tool_exam_syllabus,
        )
        self.register_builtin(
            MCPToolSpec(
                "question_bank_search",
                "按知识点检索垂直题库题目（对接业务库 questions 表）。",
                {"type": "object",
                 "properties": {"topic": {"type": "string",
                                          "description": "知识点关键词"},
                                "limit": {"type": "integer", "default": 5}},
                 "required": ["topic"]},
                "builtin",
            ),
            self._tool_question_bank_search,
        )

    async def list_tools(self) -> list:
        specs = [self._spec_to_dict(s) for s, _ in self._builtins.values()]
        remote_url = os.getenv("MCP_SERVER_URL")
        if remote_url:
            try:
                specs.extend(await self._remote_list(remote_url))
            except Exception:
                pass  # 远程不可达不阻塞，内置工具仍可用
        return specs

    @staticmethod
    def _spec_to_dict(s: MCPToolSpec) -> dict:
        return {"name": s.name, "description": s.description,
                "input_schema": s.input_schema, "source": s.source}

    # ---------------------------------------------------------------
    # 调用
    # ---------------------------------------------------------------
    async def call(self, tool_name: str, arguments: dict) -> dict:
        if tool_name in self._builtins:
            spec, func = self._builtins[tool_name]
            try:
                res = func(**(arguments or {}))
                if hasattr(res, "__await__"):
                    res = await res
                return {"ok": True, "source": "builtin",
                        "tool": tool_name, "result": res}
            except Exception as e:
                return {"ok": False, "source": "builtin",
                        "tool": tool_name, "error": str(e)}
        remote_url = os.getenv("MCP_SERVER_URL")
        if remote_url:
            try:
                return await self._remote_call(remote_url, tool_name, arguments or {})
            except Exception as e:
                return {"ok": False, "source": "remote",
                        "tool": tool_name, "error": str(e)}
        return {"ok": False, "error": f"未找到 MCP 工具：{tool_name}",
                "available": list(self._builtins)}

    # ---------------------------------------------------------------
    # 内置工具实现（垂直能力示例）
    # ---------------------------------------------------------------
    def _tool_exam_syllabus(self, cat: str) -> dict:
        syllabus = {
            "考研": "考研考纲：政治（马哲、近代史、思修、毛中特、当代）、英语（词汇、语法、阅读、写作）、"
                    "数学（高数、线代、概率统计）、计算机专业课。",
            "考公": "考公考纲：行测（常识判断、言语理解、数量关系、判断推理、资料分析）、"
                    "申论（归纳概括、对策建议、公文写作、大作文）、公共基础（法律、公文、时政）。",
            "大厂": "大厂技术岗考纲：数据结构与算法、操作系统、计算机网络、数据库、系统设计、"
                    "编程语言（Python / Java）、前端基础。",
        }
        return {"cat": cat,
                "outline": syllabus.get(cat, "未知分类，可选：考研 / 考公 / 大厂")}

    def _tool_question_bank_search(self, topic: str, limit: int = 5) -> dict:
        from database import get_db
        conn = get_db()
        rows = conn.execute(
            "SELECT id, stem, topic FROM questions WHERE topic LIKE ? LIMIT ?",
            (f"%{topic}%", limit),
        ).fetchall()
        conn.close()
        return {"topic": topic, "count": len(rows),
                "items": [dict(r) for r in rows]}

    # ---------------------------------------------------------------
    # 远程 MCP（HTTP JSON-RPC 2.0，兼容标准 MCP server）
    # ---------------------------------------------------------------
    @staticmethod
    def _remote_headers() -> dict:
        headers = {"Content-Type": "application/json"}
        key = os.getenv("MCP_SERVER_KEY", "")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return headers

    async def _remote_list(self, url: str) -> list:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, headers=self._remote_headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            tools = data.get("result", {}).get("tools", [])
            return [{
                "name": t.get("name"),
                "description": t.get("description", ""),
                "input_schema": t.get("inputSchema", {}),
                "source": "remote",
            } for t in tools]

    async def _remote_call(self, url: str, tool_name: str, arguments: dict) -> dict:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                   "params": {"name": tool_name, "arguments": arguments}}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=self._remote_headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            return {"ok": True, "source": "remote",
                    "tool": tool_name, "result": data.get("result", {})}
