"""运行时配置：读取环境变量，缺省进入规则降级模式（无需任何 API Key 即可运行）。"""
import os

# 可选：配置 OpenAI 兼容端点即可启用真实大模型（不配置则所有项目规则降级运行）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

# Context 预算（token 估算）
DEFAULT_CONTEXT_BUDGET = int(os.getenv("CTX_BUDGET", "4000"))
