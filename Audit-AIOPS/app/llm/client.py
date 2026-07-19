import os
import re
import json
import httpx
from app.config import settings
from app.models import ServiceItem
from app.llm.cache import llm_cache


class LLMClient:
    """
    LLM 客户端抽象层。
    - 默认 provider=mock：用关键词/模板模拟 Agent 的意图识别与问答，便于无密钥跑通编排逻辑。
    - 配置 HUNYUAN_API_KEY / QWEN_API_KEY 后切换为真实大模型（OpenAI 兼容 Chat Completions）。
    所有上层（Agent 编排层）只依赖本接口，模型可热插拔。
    """

    def __init__(self):
        self.provider = settings.llm_provider

    # ---------- 真实模型调用（OpenAI 兼容） ----------
    def _chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        if self.provider == "mock":
            return ""
        # —— 推理加速：应用层 KV/Prompt Cache ——
        # 相同/近似提示直接复用上一次推理结果，避免重复调用，降低 TTFT 与成本。
        cached = llm_cache.get(self.provider, system, user)
        if cached is not None:
            return cached

        base = settings.hunyuan_api_base if self.provider == "hunyuan" else settings.qwen_api_base
        key = settings.hunyuan_api_key if self.provider == "hunyuan" else settings.qwen_api_key
        model = settings.hunyuan_model if self.provider == "hunyuan" else settings.qwen_model
        if not key:
            return "（未配置 API Key，请设置 HUNYUAN_API_KEY / QWEN_API_KEY）"
        try:
            resp = httpx.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "temperature": temperature,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=30,
            )
            text = resp.json()["choices"][0]["message"]["content"]
            llm_cache.put(self.provider, system, user, text)
            return text
        except Exception as e:  # noqa: BLE001
            return f"（调用{self.provider}失败：{e}）"

    # ---------- 意图识别：映射自然语言 -> 服务项 id ----------
    def classify_intent(self, message: str, catalog: list[ServiceItem]) -> list[str]:
        if self.provider != "mock":
            sys_p = (
                "你是审计运维平台的意图识别器。根据用户诉求，从给定服务目录中挑选相关服务项 id，"
                "只返回 JSON 数组，例如 [\"ukey\",\"mail\"]，不要解释。"
            )
            ids = "\n".join(f"- {i.id}: {i.name}" for i in catalog)
            out = self._chat(sys_p, f"服务目录:\n{ids}\n\n用户诉求: {message}")
            try:
                m = re.search(r"\[.*\]", out, re.S)
                return json.loads(m.group(0)) if m else []
            except Exception:  # noqa: BLE001
                return []

        # ---- Mock：关键词匹配，保证 Demo 可离线跑通 ----
        msg = message.lower()
        matched: list[str] = []
        for item in catalog:
            for kw in self._kw(item):
                if kw.lower() in msg:
                    matched.append(item.id)
                    break
        return matched

    def _kw(self, item: ServiceItem) -> list[str]:
        alias = {
            "ukey": ["ukey", "密钥", "key", "介质", "usb"],
            "perm": ["权限", "角色", "账号权限", "授权"],
            "mail": ["邮件", "mail", "邮箱", "容量"],
            "resource": ["计算", "存储", "资源", "发放", "申领", "配额"],
            "ups": ["ups", "应急", "演练"],
            "lottery": ["抽奖", "年会"],
            "web": ["网站", "改版", "门户", "专网", "网页"],
            "terminal": ["终端", "领用", "维修", "笔记本", "电脑"],
            "meeting": ["会议", "视频会议", "预约", "开会"],
            "backup": ["备份", "恢复", "容灾"],
            "devops": ["设备运维", "硬件", "服务器", "存储设备"],
            "appops": ["应用系统", "应用运维", "业务系统"],
            "platops": ["平台", "中间件", "基础软件", "数据库"],
        }
        return [item.name] + item.name.split() + alias.get(item.id, [])

    # ---------- 知识问答（RAG 入口，Demo 用模板模拟） ----------
    def answer(self, question: str) -> str:
        if self.provider != "mock":
            return self._chat(
                "你是审计运维平台的知识助手，基于运维手册与审计制度作答，关键结论附引用来源。",
                question,
            )
        q = question.lower()
        if "工单" in q or "进度" in q:
            return "您可在「我的工单」查看进度卡片：各审批节点状态、责任人与预计耗时一目了然，并支持一键直达责任人催办。"
        if "ukey" in q:
            return "Ukey 用于审计人员身份认证与权限介质管理。制作/调整/回收均可在服务目录提交，系统自动走运维主管与安全管理员审批。"
        if "审批" in q:
            return "平台按事项自动拆分审批流：例如借终端开视频会并联网，会自动生成终端领用、打印机、联网三条审批并分别路由责任人。"
        if "监控" in q or "异常" in q:
            return "智能监控基于 Prometheus 指标 + 异常检测，异常事件可自动生成工单。当前今日异常事件已较昨日下降 40%。"
        return "（演示）已基于运维知识库检索到相关内容。您可进一步描述具体诉求，我将为您生成服务单或转人工协助。"
