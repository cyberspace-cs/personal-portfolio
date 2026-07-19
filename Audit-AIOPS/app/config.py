import os
from enum import Enum


class LLMProvider(str, Enum):
    MOCK = "mock"
    HUNYUAN = "hunyuan"
    QWEN = "qwen"


class Settings:
    app_name: str = "审计智能一体化运维平台"
    version: str = "0.2.0"

    # LLM 基座：默认 mock，可切换 腾讯混元 / 阿里通义千问（OpenAI 兼容接口）
    llm_provider: LLMProvider = LLMProvider(os.getenv("LLM_PROVIDER", "mock"))

    hunyuan_api_base: str = os.getenv("HUNYUAN_API_BASE", "https://api.hunyuan.cloud.tencent.com/v1")
    hunyuan_api_key: str = os.getenv("HUNYUAN_API_KEY", "")
    hunyuan_model: str = os.getenv("HUNYUAN_MODEL", "hunyuan-turbo")

    qwen_api_base: str = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "")
    qwen_model: str = os.getenv("QWEN_MODEL", "qwen-plus")

    cors_origins: list = ["*"]

    # 检索 / 向量后端（local 离线零依赖 / st 真实语义向量）
    embedding_backend: str = os.getenv("EMBEDDING_BACKEND", "local")

    # 语音入口（mock 离线 / funasr 真实识别）
    asr_backend: str = os.getenv("ASR_BACKEND", "mock")

    # 审批流对接 OA（mock 内存演示 / mcp 通过 MCP 协议对接真实 OA server）
    oa_backend: str = os.getenv("OA_BACKEND", "mock")
    mcp_oa_server: str = os.getenv("MCP_OA_SERVER", "")

    # 检索 / 向量后端：local（离线零依赖）/ st（sentence-transformers，需权重）
    embedding_backend: str = os.getenv("EMBEDDING_BACKEND", "local")

    # 语音入口：mock（离线）/ funasr（需 funasr + modelscope 与模型权重）
    asr_backend: str = os.getenv("ASR_BACKEND", "mock")

    # 审批流对接 OA：mock（内存演示）/ mcp（通过 MCP 协议对接真实 OA server）
    oa_backend: str = os.getenv("OA_BACKEND", "mock")
    mcp_oa_server: str = os.getenv("MCP_OA_SERVER", "")


settings = Settings()
