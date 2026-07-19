"""Context Harness：上下文预算管理。

负责把 system / history / tools / 当前任务 组装进有限 token 预算，
超预算时按「保留系统指令 + 最近 N 轮」策略裁剪，体现 Context 工程意识。
"""


def estimate_tokens(text: str) -> int:
    """粗略 token 估算（中文约 1.5 字/token，英文约 4 字符/token，统一用 len/4 近似）。"""
    if not text:
        return 0
    return max(1, len(text) // 4)


class ContextHarness:
    def __init__(self, budget: int = 4000, system: str = "") -> None:
        self.budget = budget
        self.system = system
        self.history: list[dict] = []  # {"role","content"}
        self.tools_hint: str = ""

    def set_system(self, s: str) -> None:
        self.system = s

    def add(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})

    def set_tools_hint(self, hint: str) -> None:
        self.tools_hint = hint

    def assemble(self) -> tuple[str, int]:
        """返回 (组装后的 prompt, 估算 token)。超预算时裁剪旧历史。"""
        parts = []
        if self.system:
            parts.append(f"# System\n{self.system}")
        if self.tools_hint:
            parts.append(f"# Available Tools\n{self.tools_hint}")
        # 从最近往最旧尝试塞入历史，超出则丢弃最旧
        kept: list[str] = []
        used = estimate_tokens("\n\n".join(parts))
        for msg in reversed(self.history):
            line = f"# {msg['role']}\n{msg['content']}"
            t = estimate_tokens(line)
            if used + t > self.budget and kept:
                break
            kept.insert(0, line)
            used += t
        prompt = "\n\n".join(parts + kept)
        return prompt, estimate_tokens(prompt)

    def snapshot(self) -> dict:
        prompt, tok = self.assemble()
        return {"prompt": prompt, "tokens": tok, "budget": self.budget, "turns": len(self.history)}
