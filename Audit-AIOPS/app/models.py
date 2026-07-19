from pydantic import BaseModel
from typing import Optional, List, Dict
from enum import Enum


class ServiceCategory(str, Enum):
    AUDIT_SUPPORT = "audit_support"
    OPS = "ops"


class ServiceItem(BaseModel):
    id: str
    name: str
    category: ServiceCategory
    group: str
    desc: str
    icon: str
    approval_chain: List[str] = []
    automated: bool = False
    # ===== 蓝鲸经验细化字段（均可选，向后兼容） =====
    sla_hours: Dict[str, float] = {}        # 解决时限（小时）：{P0,P1,P2,P3}
    self_service: bool = False               # 终端用户可门户自助提交（免人工分派）
    monitor_metrics: List[str] = []          # 日常运维类：纳管的监控指标
    request_fields: List[str] = []           # 工单模板关键字段（点选式提交）
    pain_point: str = ""                     # 面向用户的真实痛点
    ai_value: str = ""                        # 智能体 / AIOps 赋能价值
    monthly_volume: int = 0                  # 典型月单量（真实感）


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class WorkOrderStep(BaseModel):
    name: str
    status: str  # done / doing / wait
    owner: Optional[str] = None
    time: Optional[str] = None


class WorkOrder(BaseModel):
    id: str
    title: str
    category: str
    steps: List[WorkOrderStep] = []
    status: str = "processing"
    created_at: str


class ChatResponse(BaseModel):
    reply: str
    intents: List[str] = []
    work_order: Optional[WorkOrder] = None
    suggestions: List[str] = []
    session_id: Optional[str] = None


class MonitorMetrics(BaseModel):
    anomalies_today: int
    online_devices: int
    auto_rate: int
    avg_duration_h: float
    trend: List[float] = []


class KnowledgeRequest(BaseModel):
    question: str


class KnowledgeResponse(BaseModel):
    answer: str
    sources: List[str] = []
    retrieved: List[dict] = []  # RAG 检索命中：{title, snippet, score, entities, via, layer, encoder_mode}
    graph: Optional[dict] = None  # 图 RAG 可解释素材：{query_entities, expanded_entities, edges}
    encoder_mode: str = ""  # 多模态 RAG 当前视觉编码模式：proxy / real-hunyuan / real-qwen
