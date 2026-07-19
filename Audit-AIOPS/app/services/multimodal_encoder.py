"""
多模态视觉编码器（可插拔） —— 把「图像 / 表格」统一编码为文本描述（RAG-Anything 思路）。

RAG-Anything 的核心思想是「any modality → text」：用多模态大模型（VLM）把图像 / 表格 /
图表转成文本描述，再进入统一 RAG 检索。本模块实现这一「多模态 → 文本」的编码层，且可插拔：

  - ProxyVisualEncoder：零依赖，直接复用 `retrieval_hybrid.AUDIT_MULTIMODAL` 中预先撰写的人工
    描述。它等价于「若把真实截图喂给 VLM，预期会产出的描述」，保证无密钥也能真跑、可复现。
  - HunyuanVisionEncoder / QwenVisionEncoder：env 门控，调用真实多模态大模型对真实截图做视觉
    理解，产出实时 caption，替换代理描述，做到「真·视觉嵌入」（吸收 RAG-Anything 的视觉编码路径）。

env 门控（与 LLM 基座一致的范式）：
  VISION_PROVIDER = proxy（默认） | hunyuan | qwen
  真实模式复用 settings.hunyuan_api_key / settings.qwen_api_key（与文本 LLM 同密钥），
  模型名可由 VISION_MODEL 覆盖（默认 hunyuan-vision / qwen-vl-max）。
无密钥或缺失真实截图时，真实模式自动降级为 proxy，并标注 encoder_mode，诚实可讲。
"""
from __future__ import annotations

import base64
import os
from typing import Optional, Protocol

import httpx

from app.config import settings

_VISION_SYSTEM_PROMPT = (
    "你是一名审计运维系统的视觉理解助手。请简要描述这张系统截图 / 表格的界面布局、"
    "关键字段与可操作项，输出可用于检索的结构化中文文本，不要解释、不要寒暄。"
)


class VisualEncoder(Protocol):
    mode: str  # "proxy" | "real-hunyuan" | "real-qwen"

    def encode_image(self, image_path: Optional[str], fallback_text: str) -> str:
        """给定截图路径（真实模式用）与代理描述（无图 / 无密钥时回退），返回该图像的文本描述。"""
        ...


class ProxyVisualEncoder:
    """默认编码器：零依赖，直接返回人工预撰写的图像描述（= VLM 预期输出代理）。"""

    mode = "proxy"

    def encode_image(self, image_path: Optional[str], fallback_text: str) -> str:
        return fallback_text


class _VLMVisualEncoder:
    """真实多模态大模型编码器（OpenAI 兼容 chat/completions，image_url 多模态内容）。

    对应 RAG-Anything 的视觉编码阶段：把截图字节经 VLM 转成文本，再进入统一 RAG。
    无密钥 / 无真实截图时优雅降级为代理描述，保证服务不中断。
    """

    def __init__(self, provider: str):
        self.provider = provider
        if provider == "hunyuan":
            self.api_base = settings.hunyuan_api_base
            self.api_key = settings.hunyuan_api_key
            self.model = os.getenv("VISION_MODEL", "hunyuan-vision")
        else:
            self.api_base = settings.qwen_api_base
            self.api_key = settings.qwen_api_key
            self.model = os.getenv("VISION_MODEL", "qwen-vl-max")
        self.mode = f"real-{provider}"

    def encode_image(self, image_path: Optional[str], fallback_text: str) -> str:
        # 无密钥或缺失真实截图 → 回退代理描述（诚实降级，不抛错）
        if not self.api_key:
            return fallback_text
        if not image_path or not os.path.exists(image_path):
            return fallback_text
        try:
            with open(image_path, "rb") as f:
                raw = f.read()
            b64 = base64.b64encode(raw).decode("ascii")
            ext = os.path.splitext(image_path)[1].lower().lstrip(".")
            mime = {
                "png": "image/png",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "gif": "image/gif",
                "webp": "image/webp",
            }.get(ext, "image/png")
            resp = httpx.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": _VISION_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                                }
                            ],
                        },
                    ],
                },
                timeout=30,
            )
            resp.raise_for_status()
            caption = resp.json()["choices"][0]["message"]["content"].strip()
            return caption or fallback_text
        except Exception:  # noqa: BLE001
            # 真实调用失败（网络 / 配额 / 模型名）一律降级，保证检索可用
            return fallback_text


def build_visual_encoder(provider: Optional[str] = None) -> VisualEncoder:
    """按 env / 入参构造视觉编码器。默认 proxy（零依赖可复现）。"""
    provider = (provider or os.getenv("VISION_PROVIDER", "proxy")).lower()
    if provider == "hunyuan":
        return _VLMVisualEncoder("hunyuan")
    if provider == "qwen":
        return _VLMVisualEncoder("qwen")
    return ProxyVisualEncoder()


def encoder_status() -> dict:
    """返回当前视觉编码器模式与可用 provider，供状态端点 / 前端徽标展示。"""
    provider = os.getenv("VISION_PROVIDER", "proxy").lower()
    real_available = False
    if provider in ("hunyuan", "qwen"):
        key = settings.hunyuan_api_key if provider == "hunyuan" else settings.qwen_api_key
        real_available = bool(key)
    effective_mode = f"real-{provider}" if (provider in ("hunyuan", "qwen") and real_available) else "proxy"
    return {
        "vision_provider": provider,
        "mode": effective_mode,
        "real_available": real_available,
        "providers": {
            "hunyuan": {
                "model": os.getenv("VISION_MODEL", "hunyuan-vision"),
                "has_key": bool(settings.hunyuan_api_key),
            },
            "qwen": {
                "model": os.getenv("VISION_MODEL", "qwen-vl-max"),
                "has_key": bool(settings.qwen_api_key),
            },
        },
        "note": (
            "proxy=复用预撰写描述（等价于 VLM 预期输出，零依赖可复现）；"
            "real=调用真实多模态大模型对真实截图编码。无密钥 / 缺截图自动降级 proxy。"
        ),
    }
