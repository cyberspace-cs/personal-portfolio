"""
Multimodal Chat Hub · 后端服务
================================
多模态对话后端（FastAPI）：文本理解 + 视觉特征理解 + 多模态融合应答。
- 文本：基于情感词典的情感分析 + 规则意图识别；
- 视觉：接收前端 Canvas 提取的视觉特征（主色/亮度/边缘密度/宽高比），
  生成图像描述与标签（真实的"视觉特征→语义"映射，非占位）；
- 融合：把文本意图与视觉线索融合成一段自然的多模态回复。
（语音由前端浏览器 Web Speech API 完成 TTS/STT，构成完整多模态闭环。）

运行：
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8004
"""
from __future__ import annotations

import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Multimodal Chat Hub API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ---------------- 情感词典 ----------------
POS = {"喜欢", "开心", "棒", "好", "赞", "满意", "优秀", "爱", "惊喜", "完美", "厉害", "感谢", "太好了", "不错", "happy", "great", "love", "good", "awesome", "nice"}
NEG = {"讨厌", "难过", "差", "糟", "失望", "生气", "垃圾", "烦", "崩溃", "累", "痛苦", "不好", "问题", "bug", "bad", "sad", "hate", "terrible", "angry"}
NEGATION = {"不", "没", "无", "别", "非", "no", "not"}


class ChatReq(BaseModel):
    text: str
    image_features: dict | None = None  # {dominant:[r,g,b], brightness, edge_density, aspect, width, height}


class SentimentReq(BaseModel):
    text: str


# ---------------- 情感分析 ----------------
def analyze_sentiment(text: str) -> dict:
    t = text.lower()
    tokens = re.findall(r"[a-z]+|[\u4e00-\u9fff]", t)
    score = 0
    hits = []
    for i, tok in enumerate(tokens):
        prev = tokens[i - 1] if i > 0 else ""
        neg = prev in NEGATION
        # 中文按子串命中
    # 用子串扫描（兼顾中文多字词）
    for w in POS:
        if w in t:
            near_neg = any(n + w in t or (n in t and abs(t.find(n) - t.find(w)) <= 2) for n in NEGATION)
            score += -1 if near_neg else 1
            hits.append({"word": w, "polarity": "neg" if near_neg else "pos"})
    for w in NEG:
        if w in t:
            near_neg = any(n + w in t for n in NEGATION)
            score += 1 if near_neg else -1
            hits.append({"word": w, "polarity": "pos" if near_neg else "neg"})
    label = "积极" if score > 0 else "消极" if score < 0 else "中性"
    conf = min(1.0, abs(score) / 3 + 0.34)
    return {"label": label, "score": score, "confidence": round(conf, 2), "hits": hits[:8]}


# ---------------- 意图识别 ----------------
def detect_intent(text: str) -> str:
    t = text
    if any(k in t for k in ["?", "？", "什么", "怎么", "为什么", "如何", "how", "why", "what"]):
        return "提问"
    if any(k in t for k in ["帮我", "请", "能不能", "可以", "help", "please"]):
        return "请求"
    if any(k in t for k in ["你好", "hi", "hello", "在吗"]):
        return "问候"
    if any(k in t for k in ["谢谢", "感谢", "thanks"]):
        return "致谢"
    return "陈述"


# ---------------- 视觉特征 → 语义 ----------------
COLOR_NAMES = [
    ((220, 40, 40), "红色"), ((240, 140, 30), "橙色"), ((240, 210, 40), "黄色"),
    ((60, 180, 75), "绿色"), ((40, 120, 220), "蓝色"), ((130, 70, 200), "紫色"),
    ((240, 240, 240), "白/浅色"), ((30, 30, 30), "黑/深色"), ((150, 150, 150), "灰色"),
]


def name_color(rgb: list[int]) -> str:
    r, g, b = rgb[:3]
    best, bd = "未知", 1e9
    for (cr, cg, cb), name in COLOR_NAMES:
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if d < bd:
            bd, best = d, name
    return best


def describe_image(f: dict) -> dict:
    dom = f.get("dominant", [128, 128, 128])
    brightness = f.get("brightness", 0.5)
    edge = f.get("edge_density", 0.3)
    aspect = f.get("aspect", 1.0)
    w, h = f.get("width", 0), f.get("height", 0)
    color = name_color(dom)
    tone = "明亮" if brightness > 0.62 else "昏暗" if brightness < 0.38 else "适中亮度"
    complexity = "细节丰富、纹理复杂" if edge > 0.45 else "画面简洁、色块平整" if edge < 0.2 else "细节适中"
    shape = "横向构图（宽幅）" if aspect > 1.3 else "纵向构图（竖幅）" if aspect < 0.77 else "接近方形构图"
    labels = [color, tone, complexity.split("、")[0]]
    if edge > 0.5:
        labels.append("高细节")
    if brightness > 0.7:
        labels.append("高曝光")
    caption = f"这是一张以{color}为主色调的图片，整体{tone}，{complexity}，{shape}。"
    if w and h:
        caption += f"分辨率约 {w}×{h}。"
    return {"caption": caption, "labels": labels, "dominant_name": color,
            "brightness": round(brightness, 2), "edge_density": round(edge, 2)}


# ---------------- 多模态融合应答 ----------------
@app.post("/api/chat")
def chat(req: ChatReq) -> dict:
    text = req.text.strip()
    senti = analyze_sentiment(text) if text else {"label": "中性", "score": 0, "confidence": 0.34, "hits": []}
    intent = detect_intent(text) if text else "陈述"
    vision = describe_image(req.image_features) if req.image_features else None

    parts = []
    if vision:
        parts.append("我看了你发的图片：" + vision["caption"])
    if text:
        if intent == "问候":
            parts.append("你好呀！很高兴和你聊天～")
        elif intent == "致谢":
            parts.append("不客气，随时为你服务！")
        elif intent == "提问":
            parts.append(f"关于「{text[:30]}」，我理解你在提问；这是一个很好的问题，可以从多个角度展开。")
        elif intent == "请求":
            parts.append(f"收到你的请求「{text[:30]}」，我来帮你处理。")
        else:
            parts.append(f"我注意到你说：「{text[:40]}」。")
        if senti["label"] == "积极":
            parts.append("能感受到你此刻心情不错，继续保持这份好状态！")
        elif senti["label"] == "消极":
            parts.append("听起来你有些情绪，我在这里，愿意听你多说一些。")
    if vision and text:
        parts.append("结合图片和你的描述，我可以给出更贴合场景的建议。")
    reply = " ".join(parts) or "你可以给我发一段文字，或上传一张图片，我会结合多种模态来理解并回应。"

    return {"reply": reply, "intent": intent, "sentiment": senti, "vision": vision,
            "modalities": [m for m, on in [("文本", bool(text)), ("视觉", bool(vision))] if on] or ["空"]}


@app.post("/api/sentiment")
def sentiment(req: SentimentReq) -> dict:
    return analyze_sentiment(req.text)


@app.post("/api/vision")
def vision(f: dict) -> dict:
    return describe_image(f)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "multimodal-chat-hub"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
