"""
Agent 技能中心 · 领域技能注册表
===========================

呼应港大黄超团队 HKUDS / OpenSpace 的「skill 进化」哲学：把 Agent 的能力
拆成**可独立演进、可版本化、可组合**的技能（skill），而非写死在编排逻辑里。
每个技能自带：触发意图、是否需要审批、所用工具、版本与演进来源。

本模块是平台能力的「单一事实来源」：
  - AgentOrchestrator 通过 resolve_skills(text) 把用户输入映射到技能；
  - /api/skills 端点把它暴露给前端「Agent 技能中心」面板；
  - 新增/迭代能力 = 往 SKILLS 里加一条/升一版，编排层零改动即可生效
    （这正是 OpenSpace「skill 越用越聪明」在工程上的落地）。

零依赖、纯 Python、进程内可测。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Skill:
    id: str
    name: str
    category: str
    description: str
    triggers: list[str]                       # 触发关键词 / 意图
    requires_approval: bool = False           # 是否进入双人审批流
    approval_note: str = ""
    tools: list[str] = field(default_factory=list)   # 该技能调用的工具/系统
    version: str = "1.0"
    evolved_from: str = ""                    # 演进来源（OpenSpace skill 进化）

    def matches(self, text: str) -> bool:
        t = text.lower()
        return any(trig.lower() in t for trig in self.triggers)


# —— 审计领域技能清单（与 13 项服务目录 / 编排层能力对齐）——
SKILL_DEFS: list[Skill] = [
    Skill(
        id="approval_routing", name="审批路由", category="审批与合规",
        description="按服务目录自动匹配各工单的审批节点链，拆分双人审批责任人。",
        triggers=["审批", "批准", "同意", "签字", "报备", "复核"],
        requires_approval=True, approval_note="高合规操作，进入双人审批 + Checkpoint。",
        tools=["OA-MCP", "工单系统", "服务目录"], version="1.2", evolved_from="",
    ),
    Skill(
        id="workorder_decompose", name="工单拆单", category="编排",
        description="一句话识别多意图，拆分为独立工单并分别建单、自动路由。",
        triggers=["办理", "申请", "开通", "预约", "借用", "我要", "帮我"],
        tools=["服务目录", "工单系统", "LLM 意图识别"], version="1.1", evolved_from="",
    ),
    Skill(
        id="knowledge_qa", name="知识问答（多路 RAG）", category="知识",
        description="审计知识库问答：关键词 + 混合 RRF + 图 RAG + 多模态 RAG 四路统一检索。",
        triggers=["怎么", "如何", "什么是", "规定", "流程", "规范", "查一下", "依据"],
        tools=["混合检索", "图 RAG", "多模态 RAG", "知识库"], version="1.3",
        evolved_from="关键词检索 v1.0 → 混合 RAG v1.1 → 图+多模态 RAG v1.3",
    ),
    Skill(
        id="monitor_alert", name="监控告警", category="运维",
        description="读取运维监控指标与异常列表，主动推送风险与处置建议。",
        triggers=["监控", "告警", "异常", "指标", "CPU", "内存", "宕机", "趋势"],
        tools=["监控服务", "时序数据库"], version="1.0",
    ),
    Skill(
        id="catalog_nav", name="服务目录导航", category="导航",
        description="13 项审计支持 / 日常运维服务直达，按分组与关键词快速定位。",
        triggers=["服务", "目录", "能办", "提供", "有哪些", "入口"],
        tools=["服务目录"], version="1.0",
    ),
    Skill(
        id="workorder_advance", name="工单推进 / 催办", category="编排",
        description="推进工单状态机、催办待办、查询进度，对接 OA 审批状态。",
        triggers=["进度", "催办", "到哪", "推进", "跟进", "状态", "查询工单"],
        tools=["工单系统", "OA-MCP"], version="1.1", evolved_from="",
    ),
    Skill(
        id="audit_trail", name="审计留痕", category="审批与合规",
        description="把关键操作写入合规留痕，形成可审计、不可篡改的记录链。",
        triggers=["留痕", "记录", "审计", "溯源", "归档", "凭证"],
        requires_approval=True, approval_note="留痕写入属高合规写操作，需审批。",
        tools=["留痕服务", "日志"], version="1.0",
    ),
    Skill(
        id="voice_entry", name="语音入口", category="交互",
        description="ASR 语音转写后直接喂给编排层生成工单，低门槛直达服务。",
        triggers=["语音", "说话", "录音", "口述"],
        tools=["ASR 转写"], version="1.0",
    ),
    Skill(
        id="oa_cli", name="OA-CLI 原生工具", category="集成",
        description="把 OA 审批/工单/目录/监控操作封装为统一 CLI 式命令（oa approval submit / oa workorder advance / oa catalog list …），Agent 像在终端敲命令一样原生驱动 OA，无 GUI 自动化、省 token、可审计。",
        triggers=["oa", "提交审批", "查审批", "推进工单", "服务目录", "告警", "命令", "cli"],
        tools=["oa_approval_submit", "oa_approval_query", "oa_approval_approve",
               "oa_workorder_advance", "oa_catalog_list", "oa_alert_raise"],
        version="1.0", evolved_from="CLI-Anything（HKUDS）",
    ),
]


def list_skills() -> list[Skill]:
    return SKILL_DEFS


def get_skill(skill_id: str) -> Optional[Skill]:
    return next((s for s in SKILL_DEFS if s.id == skill_id), None)


def resolve_skills(text: str) -> list[Skill]:
    """把用户输入解析为命中的技能列表（按 triggers 匹配）。

    用于编排层把「一句话」映射到可执行技能，也用于前端技能中心高亮。
    """
    return [s for s in SKILL_DEFS if s.matches(text)]


def approval_required_skills() -> list[Skill]:
    return [s for s in SKILL_DEFS if s.requires_approval]


def to_payload(s: Skill) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "category": s.category,
        "description": s.description,
        "triggers": s.triggers,
        "requires_approval": s.requires_approval,
        "approval_note": s.approval_note,
        "tools": s.tools,
        "version": s.version,
        "evolved_from": s.evolved_from,
    }
