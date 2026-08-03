"""配置：环境变量驱动，缺省走本地演示模式（内存兜底，无需 PG/Milvus/Redis）。"""
from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # 数据库 / 中间件
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./auditscope.db")  # 演示用 sqlite 兜底
    milvus_host: str = os.getenv("MILVUS_HOST", "")
    milvus_port: int = int(os.getenv("MILVUS_PORT", "19530"))
    redis_url: str = os.getenv("REDIS_URL", "")

    # 模型（缺省进入降级规则模式，不报错）
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base: str = os.getenv("DEEPSEEK_BASE", "https://api.deepseek.com")
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "")
    qwen_base: str = os.getenv("QWEN_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    # 特性开关
    use_redis: bool = bool(redis_url)
    use_milvus: bool = bool(milvus_host)


settings = Settings()
