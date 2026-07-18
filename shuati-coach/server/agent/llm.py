"""轻量 LLM 调用（复用后端环境变量，无 Key 时返回空串由调用方降级）。"""
import os
import httpx

LLM_CONFIG = {
    "API_BASE": os.getenv("API_BASE", "https://api.openai.com/v1"),
    "API_KEY": os.getenv("API_KEY", "") or os.getenv("OPENAI_API_KEY", ""),
    "MODEL": os.getenv("MODEL", "gpt-3.5-turbo"),
}
HAS_KEY = bool(LLM_CONFIG["API_KEY"])


async def call_llm(system: str, user: str, max_tokens: int = 800, json_mode: bool = False) -> str:
    """调用聊天补全，返回纯文本。无 Key 时返回空串。"""
    if not HAS_KEY:
        return ""
    url = f'{LLM_CONFIG["API_BASE"].rstrip("/")}/chat/completions'
    payload = {
        "model": LLM_CONFIG["MODEL"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.5,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            headers={"Content-Type": "application/json", "Authorization": f'Bearer {LLM_CONFIG["API_KEY"]}'},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
