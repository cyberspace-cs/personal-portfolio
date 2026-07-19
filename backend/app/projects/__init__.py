"""各项目路由聚合。每个项目模块导出 `router` (FastAPI APIRouter)。"""
from .finetune import router as finetune_router
from .rag import router as rag_router
from .codeassistant import router as code_router
from .multimodal import router as multimodal_router
from .chatbot import router as chatbot_router

__all__ = [
    "finetune_router",
    "rag_router",
    "code_router",
    "multimodal_router",
    "chatbot_router",
]
