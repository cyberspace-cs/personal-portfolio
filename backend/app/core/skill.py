"""Skill 注册与路由：把可复用能力（工具/动作）注册为 Skill，并按语义关键词路由。

Agent 不需要每次重写逻辑——用 Skill 表达「能力」，用路由表达「何时用哪个能力」。
"""
from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class Skill:
    name: str
    description: str
    keywords: list[str]
    run: Callable[[str, dict], Any]


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: list[Skill] = []

    def register(self, skill: Skill) -> None:
        self._skills.append(skill)

    def register_fn(self, name: str, description: str, keywords: list[str], fn: Callable[[str, dict], Any]) -> None:
        self.register(Skill(name=name, description=description, keywords=keywords, run=fn))

    def route(self, text: str) -> Skill | None:
        text_l = (text or "").lower()
        best: Skill | None = None
        best_hits = 0
        for s in self._skills:
            hits = sum(1 for k in s.keywords if k.lower() in text_l)
            if hits > best_hits:
                best_hits = hits
                best = s
        return best

    def list(self) -> list[dict]:
        return [{"name": s.name, "description": s.description, "keywords": s.keywords} for s in self._skills]

    def get(self, name: str) -> Skill | None:
        for s in self._skills:
            if s.name == name:
                return s
        return None

    def __iter__(self):
        return iter(self._skills)
