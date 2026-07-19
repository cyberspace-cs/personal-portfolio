"""Prompt 模板引擎：极简 {var} 占位替换 + 全局模板注册表。

强调「Prompt 是第一公民的工程意识」——所有项目的提示词集中管理、可评审、可溯源。
"""
import re
from typing import Dict, Any

_VAR = re.compile(r"\{(\w+)\}")


def render(template: str, **kwargs: Any) -> str:
    def repl(m: re.Match) -> str:
        key = m.group(1)
        return str(kwargs[key]) if key in kwargs else m.group(0)

    return _VAR.sub(repl, template)


class PromptRegistry:
    def __init__(self) -> None:
        self._t: Dict[str, str] = {}

    def register(self, name: str, template: str) -> None:
        self._t[name] = template

    def get(self, name: str) -> str:
        return self._t.get(name, "")

    def render(self, name: str, **kwargs: Any) -> str:
        return render(self._t.get(name, ""), **kwargs)

    def names(self):
        return list(self._t.keys())


# 全局注册表（各项目向其注册模板）
registry = PromptRegistry()
