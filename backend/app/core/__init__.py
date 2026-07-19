"""Agent 工程内核：Prompt / RAG / Skill / MCP / Context Harness Loop。

所有上层项目（微调平台、RAG、代码助手、多模态、智能客服）共用此内核，
体现「先导入工具，再构造 Agent / 大模型项目」的工程意识。
"""
from .config import *
from .llm import LLMClient, has_llm
from .prompt import PromptRegistry, render
from .context import ContextHarness, estimate_tokens
from .rag import HybridRetriever, Chunk
from .skill import Skill, SkillRegistry
from .mcp import MCPTool, MCPConnector
from .loop import HarnessLoop

__all__ = [
    "LLMClient", "has_llm", "PromptRegistry", "render",
    "ContextHarness", "estimate_tokens", "HybridRetriever", "Chunk",
    "Skill", "SkillRegistry", "MCPTool", "MCPConnector", "HarnessLoop",
]
