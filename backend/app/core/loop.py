"""Context Harness Loop：Agent 的核心编排循环（工程化意识的核心）。

一次完整 loop = Plan → Act → Observe → Reflect → (必要时 Re-Plan) → Final。
每一步都经过 Context Harness 预算裁剪，并把观察写回上下文，形成「带记忆的闭环」。
"""
from typing import Any, Callable, Optional
from .context import ContextHarness
from .llm import LLMClient
from .skill import SkillRegistry
from .mcp import MCPConnector
from .prompt import render


class HarnessLoop:
    """通用 Agent 编排器。

    params:
      task:        用户任务
      harness:     Context Harness（管理 system / history / tools / 预算）
      llm:         LLMClient
      skills:      SkillRegistry（可选）
      mcp:         MCPConnector（可选）
      planner:     自定义规划函数(task, ctx_prompt)->str（可选，默认用 LLM）
      max_steps:   最大循环步数
    """

    def __init__(
        self,
        harness: ContextHarness,
        llm: LLMClient,
        skills: Optional[SkillRegistry] = None,
        mcp: Optional[MCPConnector] = None,
        max_steps: int = 4,
    ) -> None:
        self.harness = harness
        self.llm = llm
        self.skills = skills or SkillRegistry()
        self.mcp = mcp or MCPConnector()
        self.max_steps = max_steps

    def run(self, task: str, on_step: Optional[Callable[[dict], None]] = None) -> dict:
        self.harness.add("user", task)
        trace: list[dict] = []
        final_answer = ""

        for step in range(1, self.max_steps + 1):
            ctx_prompt, tokens = self.harness.assemble()
            # ---- Plan ----
            plan = self.llm.chat(
                system="你是任务规划器。基于上下文，用一句话说明这一步要做什么。",
                user=f"上下文:\n{ctx_prompt}\n\n请规划第{step}步。",
            )
            # ---- Act：先尝试 Skill 路由，再尝试 MCP，最后用 LLM 直接作答 ----
            skill = self.skills.route(task + " " + plan)
            action_type = "llm"
            observation = ""
            if skill:
                observation = str(skill.run(task, {"plan": plan, "step": step}))
                action_type = f"skill:{skill.name}"
            else:
                # 让 LLM 直接产出回答（也可能是最终答案）
                observation = self.llm.chat(
                    system=self.harness.system,
                    user=f"{ctx_prompt}\n\n请直接给出当前可交付的结果。",
                )
                action_type = "llm"
            # ---- Observe ----
            self.harness.add("observation", f"[{action_type}] {observation}")
            # ---- Reflect ----
            reflect = self.llm.chat(
                system="你是反思器。判断任务是否已完成（completed/incomplete）并简述原因。",
                user=f"任务: {task}\n最新观察: {observation}\n状态?",
            )
            done = ("completed" in reflect.lower()) or step == self.max_steps
            record = {
                "step": step,
                "tokens": tokens,
                "plan": plan,
                "action": action_type,
                "observation": observation[:500],
                "reflect": reflect,
                "done": done,
            }
            trace.append(record)
            if on_step:
                on_step(record)
            final_answer = observation
            if done:
                break

        return {"task": task, "answer": final_answer, "trace": trace, "steps": len(trace)}


# 便于演示的提示词
PLAN_PROMPT = "请将复杂任务拆解为可执行的步骤。"
