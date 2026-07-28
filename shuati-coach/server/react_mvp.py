"""W1 反向吃透小练 · 手写 ReAct Agent MVP（复刻 ai-agent-book Ch1 K1-K4）。

纯标准库实现（urllib），无需安装任何依赖，直接 `python react_mvp.py` 即可。
LLM 配置从环境变量读取，与原项目 agent.llm 的解析逻辑一致：
  优先 LLM_PROVIDER 指定厂商；否则自动选第一个配置了 Key 的厂商。
  支持：ZHIPU_API_KEY(智谱) / HUNYUAN_API_KEY(腾讯混元) / DEEPSEEK_API_KEY
        / MOONSHOT_API_KEY(Kimi) / ARK_API_KEY(豆包) / DASHSCOPE_API_KEY(通义)
        / OPENAI_API_KEY；可用 <PROVIDER>_MODEL / <PROVIDER>_API_BASE 覆盖。

运行：
    cd server
    $env:ZHIPU_API_KEY="你的key"      # PowerShell 示例
    python react_mvp.py

预期现象：
    第 1 轮模型返回 tool_calls（不返回正文） → 执行工具
    第 2 轮模型"看到"工具结果后才给出最终答案
    （对照 ai-agent-book Ch1 K2 ReAct 三步 + K4 消融：去掉工具结果会无限循环）
"""
import json
import os
import sys
import urllib.request
import urllib.error

# Windows 控制台默认 GBK，无法打印部分 emoji/生僻字；强制 stdout 用 utf-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# 与 agent.llm.PROVIDERS 对齐的精简解析（仅取运行所需字段）
_PROVIDERS = {
    "zhipu":     {"api_base": "https://open.bigmodel.cn/api/paas/v4", "key_envs": ["ZHIPU_API_KEY", "GLM_API_KEY"], "default_model": "glm-4.6"},
    "hunyuan":   {"api_base": "https://api.hunyuan.cloud.tencent.com/v1", "key_envs": ["HUNYUAN_API_KEY"], "default_model": "hunyuan-turbos-latest"},
    "deepseek":  {"api_base": "https://api.deepseek.com/v1", "key_envs": ["DEEPSEEK_API_KEY"], "default_model": "deepseek-chat"},
    "moonshot":  {"api_base": "https://api.moonshot.cn/v1", "key_envs": ["MOONSHOT_API_KEY", "KIMI_API_KEY"], "default_model": "kimi-k2-0905-preview"},
    "doubao":    {"api_base": "https://ark.cn-beijing.volces.com/api/v3", "key_envs": ["ARK_API_KEY", "DOUBAO_API_KEY"], "default_model": "doubao-seed-1-6-250615"},
    "qwen":      {"api_base": "https://dashscope.aliyun.com/compatible-mode/v1", "key_envs": ["DASHSCOPE_API_KEY", "QWEN_API_KEY"], "default_model": "qwen-plus"},
    "openai":    {"api_base": "https://api.openai.com/v1", "key_envs": ["OPENAI_API_KEY", "API_KEY"], "default_model": "gpt-4o-mini"},
}


def _resolve():
    want = os.getenv("LLM_PROVIDER", "").strip().lower()
    order = ([want] if want in _PROVIDERS else []) + list(_PROVIDERS)
    for name in order:
        spec = _PROVIDERS[name]
        for env in spec["key_envs"]:
            key = os.getenv(env, "")
            if key:
                return {
                    "name": name,
                    "api_base": os.getenv(f"{name.upper()}_API_BASE", spec["api_base"]),
                    "api_key": key,
                    "model": os.getenv(f"{name.upper()}_MODEL", spec["default_model"]),
                }
    return None


_CFG = _resolve()
HAS_KEY = _CFG is not None


# K1 静态前缀的一部分：工具定义（真实项目里换成你的工具 schema）
TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询某城市当前天气",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}]


def get_weather(city: str) -> str:
    """工具的真实执行体（在模型之外）。mock 实现。"""
    return json.dumps({"temp": 28, "sky": "晴"})


def run_react(user_msg: str, max_rounds: int = 5):
    # K1 上下文 = 静态前缀(系统提示 + 工具) + 轨迹(messages 累积)
    messages = [
        {"role": "system", "content": "你是助手，需要时调用工具获取信息。"},
        {"role": "user", "content": user_msg},
    ]
    url = f'{_CFG["api_base"].rstrip("/")}/chat/completions'
    for i in range(max_rounds):
        print(f"\n=== 第 {i + 1} 轮 ===")
        req = urllib.request.Request(
            url,
            data=json.dumps({
                "model": _CFG["model"],
                "messages": messages,
                "tools": TOOLS,
                "tool_choice": "auto",
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f'Bearer {_CFG["api_key"]}',
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                msg = json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            raise SystemExit(f"LLM 调用失败 {e.code}: {body[:300]}")
        messages.append(msg)  # 把模型回复(含 reasoning/tool_calls)追加进轨迹

        if msg.get("tool_calls"):  # 模型决定"做"
            for tc in msg["tool_calls"]:
                args = json.loads(tc["function"]["arguments"])
                print(f"  → 模型调用工具: {tc['function']['name']}({args})")
                result = get_weather(args["city"])  # K3 执行工具
                messages.append({  # K3 结果回上下文（"看"）
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })
                print(f"  → 工具返回: {result}")
            continue  # 带结果再循环一轮
        else:
            print(f"  → 最终回答: {msg['content']}")  # 不再调工具 = 任务完成
            return msg["content"]
    print("  → 达到最大轮数仍未给最终答案（无限循环，对应 K4 消融实验）")
    return None


if __name__ == "__main__":
    if not HAS_KEY:
        raise SystemExit(
            "未检测到任何厂商 API Key。请先设置 ZHIPU_API_KEY / HUNYUAN_API_KEY / "
            "DEEPSEEK_API_KEY / OPENAI_API_KEY 等环境变量之一，再运行本脚本。"
        )
    print(f"激活厂商: {_CFG['name']} / model={_CFG['model']}")
    run_react("北京天气怎么样？")
