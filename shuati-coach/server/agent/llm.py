"""多模型 LLM 调用层：统一 OpenAI 兼容协议，支持一键切换主流大模型。

内置厂商（均为 OpenAI 兼容 /chat/completions，可直接切换）：
  - zhipu     智谱 GLM        https://open.bigmodel.cn/api/paas/v4
  - moonshot  Kimi(Moonshot)  https://api.moonshot.cn/v1
  - hunyuan   腾讯混元         https://api.hunyuan.cloud.tencent.com/v1
  - doubao    字节豆包(Ark)    https://ark.cn-beijing.volces.com/api/v3
  - qwen      阿里千问/通义     https://dashscope.aliyun.com/compatible-mode/v1
  - deepseek  DeepSeek        https://api.deepseek.com/v1
  - openai    OpenAI          https://api.openai.com/v1

选择激活厂商的优先级：
  1) 环境变量 LLM_PROVIDER 指定的厂商（若其配置了 Key）；
  2) 否则自动选「第一个配置了 Key」的厂商；
  3) 都没有 -> 无 Key，call_llm 返回空串，由调用方降级为规则模式。

每个厂商可用以下环境变量覆盖默认值：
  <PROVIDER>_API_KEY   例如 ZHIPU_API_KEY / MOONSHOT_API_KEY / HUNYUAN_API_KEY /
                            ARK_API_KEY / DASHSCOPE_API_KEY / DEEPSEEK_API_KEY / OPENAI_API_KEY
  <PROVIDER>_MODEL     覆盖默认模型名，例如 ZHIPU_MODEL=glm-4.6
  <PROVIDER>_API_BASE  覆盖默认地址（自建网关/代理时）

同时兼容历史变量 API_BASE / API_KEY / MODEL（作为 custom 厂商兜底）。
"""
import json
import os
import re
import httpx

# ================================================================
# 厂商注册表：每项定义地址、Key 环境变量候选、默认模型、是否支持 json_mode
# ================================================================
PROVIDERS = {
    "zhipu": {
        "label": "智谱 GLM",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "key_envs": ["ZHIPU_API_KEY", "GLM_API_KEY"],
        "default_model": "glm-4.6",          # 新一代旗舰；便宜可用 glm-4-flash
        "supports_json": True,
    },
    "moonshot": {
        "label": "Kimi (Moonshot)",
        "api_base": "https://api.moonshot.cn/v1",
        "key_envs": ["MOONSHOT_API_KEY", "KIMI_API_KEY"],
        "default_model": "kimi-k2-0905-preview",  # K2 新模型；稳妥可用 moonshot-v1-8k
        "supports_json": True,
    },
    "hunyuan": {
        "label": "腾讯混元",
        "api_base": "https://api.hunyuan.cloud.tencent.com/v1",
        "key_envs": ["HUNYUAN_API_KEY"],
        "default_model": "hunyuan-turbos-latest",  # 最新 turbos；轻量可用 hunyuan-lite
        "supports_json": True,
    },
    "doubao": {
        "label": "字节豆包 (火山方舟 Ark)",
        "api_base": "https://ark.cn-beijing.volces.com/api/v3",
        "key_envs": ["ARK_API_KEY", "DOUBAO_API_KEY"],
        # 豆包需填「接入点 endpoint id」或模型名，用 DOUBAO_MODEL 覆盖
        "default_model": "doubao-seed-1-6-250615",
        "supports_json": True,
    },
    "qwen": {
        "label": "阿里千问 / 通义",
        "api_base": "https://dashscope.aliyun.com/compatible-mode/v1",
        "key_envs": ["DASHSCOPE_API_KEY", "QWEN_API_KEY"],
        "default_model": "qwen-plus",        # 旗舰可用 qwen-max / qwen3-max
        "supports_json": True,
    },
    "deepseek": {
        "label": "DeepSeek",
        "api_base": "https://api.deepseek.com/v1",
        "key_envs": ["DEEPSEEK_API_KEY"],
        "default_model": "deepseek-chat",
        "supports_json": True,
    },
    "openai": {
        "label": "OpenAI",
        "api_base": "https://api.openai.com/v1",
        "key_envs": ["OPENAI_API_KEY", "API_KEY"],
        "default_model": "gpt-4o-mini",
        "supports_json": True,
    },
}


def _resolve_key(spec: dict) -> str:
    for env in spec["key_envs"]:
        v = os.getenv(env, "")
        if v:
            return v
    return ""


def _resolve_provider(name: str) -> dict:
    """把一个厂商名解析成运行期配置（读环境变量覆盖），返回 dict。"""
    spec = PROVIDERS[name]
    pu = name.upper()
    return {
        "name": name,
        "label": spec["label"],
        "api_base": os.getenv(f"{pu}_API_BASE", spec["api_base"]),
        "api_key": _resolve_key(spec),
        "model": os.getenv(f"{pu}_MODEL", spec["default_model"]),
        "supports_json": spec["supports_json"],
    }


def _pick_active() -> dict:
    """按优先级选出激活厂商配置。"""
    # 1) 显式指定
    want = os.getenv("LLM_PROVIDER", "").strip().lower()
    if want in PROVIDERS:
        cfg = _resolve_provider(want)
        if cfg["api_key"]:
            return cfg
    # 2) 自动选第一个有 Key 的
    for name in PROVIDERS:
        cfg = _resolve_provider(name)
        if cfg["api_key"]:
            return cfg
    # 3) 历史变量兜底（自定义 OpenAI 兼容网关）
    legacy_key = os.getenv("API_KEY", "")
    if legacy_key:
        return {
            "name": "custom",
            "label": "自定义 (OpenAI 兼容)",
            "api_base": os.getenv("API_BASE", "https://api.openai.com/v1"),
            "api_key": legacy_key,
            "model": os.getenv("MODEL", "gpt-3.5-turbo"),
            "supports_json": True,
        }
    # 4) 无 Key：降级
    fallback = want if want in PROVIDERS else "zhipu"
    cfg = _resolve_provider(fallback)
    return cfg


_ACTIVE = _pick_active()

# 向后兼容的导出（inference.py / main.py 等仍可直接使用）
LLM_CONFIG = {
    "API_BASE": _ACTIVE["api_base"],
    "API_KEY": _ACTIVE["api_key"],
    "MODEL": _ACTIVE["model"],
    "PROVIDER": _ACTIVE["name"],
}
HAS_KEY = bool(_ACTIVE["api_key"])
ACTIVE_PROVIDER = _ACTIVE["name"]


def list_providers() -> list:
    """列出所有内置厂商及其是否已配置 Key、是否为当前激活厂商。"""
    out = []
    for name, spec in PROVIDERS.items():
        cfg = _resolve_provider(name)
        out.append({
            "name": name,
            "label": spec["label"],
            "model": cfg["model"],
            "api_base": cfg["api_base"],
            "configured": bool(cfg["api_key"]),
            "active": name == _ACTIVE["name"],
            "key_envs": spec["key_envs"],
        })
    return out


def active_provider() -> dict:
    """返回当前激活厂商的可展示信息（不含 Key 明文）。"""
    return {
        "name": _ACTIVE["name"],
        "label": _ACTIVE.get("label", _ACTIVE["name"]),
        "model": _ACTIVE["model"],
        "api_base": _ACTIVE["api_base"],
        "has_key": HAS_KEY,
    }


def switch_provider(name: str) -> dict:
    """运行期切换激活厂商（需该厂商已配置 Key），返回新激活信息。"""
    global _ACTIVE, LLM_CONFIG, HAS_KEY, ACTIVE_PROVIDER
    name = (name or "").strip().lower()
    if name not in PROVIDERS:
        raise ValueError(f"未知厂商：{name}；可选 {list(PROVIDERS)}")
    cfg = _resolve_provider(name)
    if not cfg["api_key"]:
        raise ValueError(f"厂商 {name} 未配置 Key（设置 {PROVIDERS[name]['key_envs']} 其一）")
    _ACTIVE = cfg
    LLM_CONFIG = {"API_BASE": cfg["api_base"], "API_KEY": cfg["api_key"],
                  "MODEL": cfg["model"], "PROVIDER": cfg["name"]}
    HAS_KEY = True
    ACTIVE_PROVIDER = cfg["name"]
    return active_provider()


async def call_llm(system: str, user: str, max_tokens: int = 800,
                   json_mode: bool = False, provider: str = None) -> str:
    """调用聊天补全，返回纯文本。无 Key 时返回空串（由调用方降级）。

    - provider: 可临时指定厂商名（如 "moonshot"），默认用激活厂商；
    - 全部走 OpenAI 兼容 /chat/completions，多厂商协议一致。
    """
    cfg = _ACTIVE
    if provider:
        p = provider.strip().lower()
        if p in PROVIDERS:
            cfg = _resolve_provider(p)
    if not cfg["api_key"]:
        return ""
    url = f'{cfg["api_base"].rstrip("/")}/chat/completions'
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.5,
        "max_tokens": max_tokens,
    }
    if json_mode and cfg.get("supports_json", True):
        payload["response_format"] = {"type": "json_object"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            headers={"Content-Type": "application/json",
                     "Authorization": f'Bearer {cfg["api_key"]}'},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def call_llm_tool(system: str, user: str, tool_name: str, tool_schema: dict,
                        max_tokens: int = 800, provider: str = None) -> dict:
    """虚拟工具范式（Virtual Tools）：用 Function Calling 约束结构化输出，而非 response_format=json_object。

    很多厂商对 json_object 支持不稳定（返回带 ```json 包裹、字段漂移），而 Function Calling 协议
    对参数有严格 JSON 约束且被所有 OpenAI 兼容端点统一支持。我们**不真正执行**该工具，只截获 LLM
    返回的 ``tool_calls[0].function.arguments`` 作为结构化数据——这正是 nanobot（HKUDS/nanobot）用的
    「幽灵工具」技巧：用协议层而非 Prompt 指令来约束输出形状。

    返回解析后的 dict；无 Key 或解析失败返回 {}（由调用方降级）。
    """
    cfg = _ACTIVE
    if provider:
        p = provider.strip().lower()
        if p in PROVIDERS:
            cfg = _resolve_provider(p)
    if not cfg["api_key"]:
        return {}
    url = f'{cfg["api_base"].rstrip("/")}/chat/completions'
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.5,
        "max_tokens": max_tokens,
        "tools": [{
            "type": "function",
            "function": {
                "name": tool_name,
                "description": "按给定 JSON schema 输出结构化结果",
                "parameters": tool_schema,
            },
        }],
        "tool_choice": {"type": "function", "function": {"name": tool_name}},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            headers={"Content-Type": "application/json",
                     "Authorization": f'Bearer {cfg["api_key"]}'},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        msg = data.get("choices", [{}])[0].get("message", {})
        # 1) 优先取 tool_calls 的 arguments（虚拟工具主路径）
        tool_calls = msg.get("tool_calls") or []
        if tool_calls:
            args = tool_calls[0].get("function", {}).get("arguments", "{}")
            parsed = _safe_json(args)
            if parsed is not None:
                return parsed
        # 2) 兼容没返回 tool_calls 时直接吐 JSON 文本
        return _safe_json(msg.get("content", "")) or {}


def _safe_json(text: str):
    """稳妥解析 JSON：直接 loads，失败再正则抽取首个 {...}。"""
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r'\{.*\}', text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None
