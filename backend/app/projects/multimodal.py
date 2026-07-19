"""多模态对话机器人：文本 / 图像 / 语音 交互 + 情感感知。

- 文本：基于情感词典做情感感知（positive/negative/neutral），结合 Persona 生成回复
- 图像：无视觉模型时接受文字描述，返回结构化「视觉理解」分析（诚实标注降级）
- 语音：无 Whisper 时接受已识别文本或返回模拟转录（tools/call 风格）
复用 ContextHarness 管理多轮对话上下文。
"""
import re
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.llm import LLMClient
from app.core.context import ContextHarness
from app.core.prompt import registry

router = APIRouter(prefix="/api/multimodal", tags=["multimodal"])

llm = LLMClient()
_sessions: dict[str, ContextHarness] = {}

POS = ["开心", "高兴", "喜欢", "棒", "感谢", "爱", "满意", "好", "赞", "happy", "love", "great", "thanks", "good"]
NEG = ["生气", "讨厌", "差", "失望", "问题", "错误", "崩溃", "坏", "愁", "angry", "hate", "bad", "error", "sad", "bug"]

registry.register(
    "persona",
    "你是「小元」，一个温和、共情、专业的多模态助手。当前用户情绪：{emotion}。"
    "请据此调整语气：负面情绪多安抚，正面情绪多共鸣。\n用户说：{message}",
)


def detect_emotion(text: str) -> tuple[str, float]:
    t = text.lower()
    p = sum(1 for w in POS if w in t)
    n = sum(1 for w in NEG if w in t)
    if p == n:
        return "neutral", 0.5
    if p > n:
        return "positive", round(0.5 + 0.1 * p, 2)
    return "negative", round(0.5 + 0.1 * n, 2)


def get_harness(sid: str) -> ContextHarness:
    if sid not in _sessions:
        _sessions[sid] = ContextHarness(budget=2000, system="你是多模态助手小元。")
    return _sessions[sid]


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    mode: str = "text"  # text|image|voice


class ImageRequest(BaseModel):
    caption: str  # 图像文字描述（无视觉模型时的输入）
    session_id: str = "default"


class VoiceRequest(BaseModel):
    transcript: Optional[str] = None  # 已识别文本；为空则返回模拟转录
    session_id: str = "default"


@router.post("/chat")
def chat(req: ChatRequest):
    emotion, score = detect_emotion(req.message)
    harness = get_harness(req.session_id)
    harness.add("user", req.message)
    if llm.enabled:
        reply = llm.chat(system=registry.render("persona", emotion=emotion, message=req.message),
                         user=req.message)
    else:
        if emotion == "negative":
            reply = f"我理解您现在可能有些{emotion}，先别着急——能具体说说遇到了什么问题吗？我会陪您一起解决。"
        elif emotion == "positive":
            reply = f"听到您这么开心我也很高兴😊 还有什么想聊或需要帮忙的吗？"
        else:
            reply = "收到～我已经记下了。您希望我从哪方面继续帮您？（规则降级：配置 LLM Key 获得更自然的回复）"
    harness.add("assistant", reply)
    snap = harness.snapshot()
    return {"reply": reply, "emotion": emotion, "emotion_score": score, "mode": req.mode,
            "context_tokens": snap["tokens"]}


@router.post("/analyze-image")
def analyze_image(req: ImageRequest):
    cap = req.caption.strip()
    if not cap:
        return {"objects": [], "scene": "未知", "suggestion": "请提供图像的文字描述（无视觉模型降级模式）。",
                "vision_enabled": False}
    # 规则提取关键词作为「物体」
    words = re.findall(r"[\u4e00-\u9fa5a-zA-Z]+", cap)
    objects = list(dict.fromkeys(words))[:8]
    scene = "室内" if any(w in cap for w in ["房间", "桌", "办公室", "room", "indoor"]) else (
        "室外" if any(w in cap for w in ["天空", "树", "街", "outdoor", "sky"]) else "未明确")
    suggestion = f"基于描述，建议回复用户：「这张图看起来是在{scene}场景，我注意到画面里有{', '.join(objects[:3])}等元素。」"
    return {"objects": objects, "scene": scene, "suggestion": suggestion, "vision_enabled": llm.enabled}


@router.post("/transcribe")
def transcribe(req: VoiceRequest):
    if req.transcript:
        emotion, score = detect_emotion(req.transcript)
        return {"transcript": req.transcript, "emotion": emotion, "emotion_score": score,
                "note": "已接收识别文本（可对接 Whisper 做真实语音识别）。"}
    # 模拟转录
    sample = "我想了解一下你们的产品怎么用"
    return {"transcript": sample, "emotion": "neutral", "emotion_score": 0.5,
            "note": "模拟转录（配置 Whisper/语音 API 后返回真实结果）。"}


@router.get("/health")
def health():
    return {"status": "ok", "project": "multimodal", "llm_enabled": llm.enabled, "sessions": len(_sessions)}
