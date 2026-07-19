from app.llm.client import LLMClient
from app.services.catalog import CATALOG
from app.services.workorder import create_work_order
from app.agent.memory import memory
from app.models import ChatResponse
from app.skills import resolve_skills, approval_required_skills


class AgentOrchestrator:
    """
    Agent 编排层（项目核心）。
    一次「对话直达工单」的 ReAct 式编排：
      意图识别 Agent -> 规划/拆单 Agent -> 审批路由 Agent -> (执行 Agent)
    并写入记忆系统（短期对话 + 长期工单画像）。

    技能中心（HKUDS / OpenSpace「skill 进化」哲学）：编排层通过技能注册表把
    用户输入解析为可演进的技能，审批类技能与「双人审批 + Checkpoint」对齐。
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def handle(self, message: str, session_id: str) -> ChatResponse:
        memory.add(session_id, "user", message)

        # 0) 技能解析（每条请求都过技能注册表，编排层零改动即可增删能力）
        skills = resolve_skills(message)
        memory.remember_profile(session_id, "matched_skills", [s.id for s in skills])
        needs_approval = any(s.requires_approval for s in skills)

        # 1) 意图识别 Agent
        intents = self.llm.classify_intent(message, CATALOG)

        # 2) 规划/拆单 + 审批路由 Agent
        if intents:
            items = [i for i in CATALOG if i.id in intents]
            wo = create_work_order(items)
            titles = "、".join(i.name for i in items)
            current = next((s.name for s in wo.steps if s.status == "doing"), "执行交付")
            reply = (
                f"已识别您的诉求：{titles}。AI 已自动拆单并生成工单 {wo.id}，"
                f"当前进入「{current}」环节，系统已自动路由审批责任人。"
            )
            memory.add(session_id, "assistant", reply)
            memory.remember_profile(session_id, "last_work_order", wo.id)
            suggestions = [f"查看工单 {wo.id} 进度", "我要催办", "我还想办理其他服务"]
            return ChatResponse(reply=reply, intents=intents, work_order=wo, suggestions=suggestions)

        # 3) 问答类（知识库 RAG 入口）
        ans = self.llm.answer(message)
        memory.add(session_id, "assistant", ans)
        return ChatResponse(
            reply=ans,
            intents=[],
            suggestions=["办理 Ukey 权限调整", "申请计算资源", "预约视频会议"],
        )
