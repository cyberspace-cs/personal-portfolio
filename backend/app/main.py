"""统一后端入口：聚合 5 个项目路由 + CORS + 根健康端点。

运行：uvicorn app.main:app --reload --port 8000  （在 backend/ 目录下）
演示页面（demos/*.html）通过 http://localhost:8000 调用本服务。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.llm import has_llm
from app.projects import (
    finetune_router,
    rag_router,
    code_router,
    multimodal_router,
    chatbot_router,
)

app = FastAPI(
    title="AI 项目统一后端",
    description="刷题教练作者的大模型/Agent 项目后端：微调平台 / RAG / 代码助手 / 多模态 / 智能客服。"
                "内置 Agent 工程内核（Prompt/RAG/Skill/MCP/Context Harness Loop）。",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(finetune_router)
app.include_router(rag_router)
app.include_router(code_router)
app.include_router(multimodal_router)
app.include_router(chatbot_router)


@app.get("/")
def root():
    return {
        "service": "ai-projects-backend",
        "version": "1.0.0",
        "llm_enabled": has_llm(),
        "projects": ["finetune", "rag", "code", "multimodal", "chatbot"],
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_enabled": has_llm()}
