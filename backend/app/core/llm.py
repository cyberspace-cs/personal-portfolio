"""LLM 客户端：优先调用 OpenAI 兼容接口，未配置 Key 时进入规则降级（rule-based fallback）。

降级模式下返回结构稳定、可脱稿讲解的占位回答，保证 demo 在无 Key 环境下也能完整跑通。
"""
import json
import urllib.request
from .config import OPENAI_API_KEY, OPENAI_BASE_URL, MODEL_NAME


def has_llm() -> bool:
    return bool(OPENAI_API_KEY)


def chat(system: str | None, user: str, *, json_mode: bool = False, temperature: float = 0.7) -> str:
    if has_llm():
        return _call_openai(system, user, json_mode=json_mode, temperature=temperature)
    return _fallback(system, user, json_mode=json_mode)


def _call_openai(system, user, *, json_mode, temperature) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    body = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except Exception:
        return _fallback(system, user, json_mode=json_mode)


def _fallback(system, user, *, json_mode) -> str:
    """无 Key 时的确定性降级回答。"""
    topic = (user or "").strip().replace("\n", " ")[:120]
    if json_mode:
        return json.dumps(
            {
                "answer": f"[规则降级] 已收到任务：{topic}。配置 OPENAI_API_KEY 后可获得真实模型生成结果。",
                "thoughts": "当前为无 Key 降级模式，返回结构化占位。",
                "confidence": 0.4,
            },
            ensure_ascii=False,
        )
    return (
        f"[规则降级模式] 针对「{topic}」的回答：\n"
        "当前后端未配置大模型 API Key，已返回基于内置规则的占位结果。"
        "在项目根目录设置 OPENAI_API_KEY 与 OPENAI_BASE_URL 后，将自动切换为真实模型生成。"
    )


class LLMClient:
    """轻量封装，便于各项目统一调用。"""

    def chat(self, user: str, *, system: str | None = None, json_mode: bool = False, temperature: float = 0.7) -> str:
        return chat(system, user, json_mode=json_mode, temperature=temperature)

    @property
    def enabled(self) -> bool:
        return has_llm()
