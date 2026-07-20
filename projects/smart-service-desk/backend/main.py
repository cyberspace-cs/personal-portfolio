"""
Smart Service Desk · 后端服务
================================
智能客服后端（FastAPI）。真实实现客服核心链路，无需外部依赖：
  意图路由(订单/退款/物流/投诉/咨询/转人工) → FAQ 语义匹配(TF-IDF) →
  置信度门控(低于阈值转人工) → 快捷动作建议 → 工单创建 → 满意度与坐席指标统计。

运行：
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8005
"""
from __future__ import annotations

import math
import re
import time
import uuid
from collections import Counter

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Smart Service Desk API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CONFIDENCE_THRESHOLD = 0.16

# ---------------- 意图与路由 ----------------
INTENT_RULES = {
    "物流查询": ["物流", "快递", "发货", "到哪", "什么时候到", "运单", "配送", "签收"],
    "退款退货": ["退款", "退货", "退钱", "怎么退", "不想要了", "return", "refund"],
    "订单问题": ["订单", "下单", "支付", "付款", "没付", "改地址", "取消订单"],
    "投诉建议": ["投诉", "差评", "态度", "垃圾", "骗人", "举报", "维权"],
    "产品咨询": ["怎么用", "功能", "支持", "能不能", "规格", "参数", "介绍", "价格", "多少钱"],
    "转人工": ["人工", "客服", "真人", "转接", "找个人"],
}

QUICK_ACTIONS = {
    "物流查询": ["查看物流轨迹", "催发货", "修改收货地址"],
    "退款退货": ["申请退款", "查看退款进度", "退货流程说明"],
    "订单问题": ["查看我的订单", "取消订单", "修改订单"],
    "投诉建议": ["提交投诉工单", "转接主管"],
    "产品咨询": ["查看产品文档", "联系售前"],
    "转人工": ["转接人工客服"],
    "其他": ["浏览常见问题", "转人工客服"],
}


class FAQ:
    def __init__(self, q: str, a: str, cat: str):
        self.id = uuid.uuid4().hex[:8]
        self.q = q
        self.a = a
        self.cat = cat
        self.tokens = tokenize(q + a)
        self.tf = Counter(self.tokens)


class Store:
    def __init__(self):
        self.faqs: list[FAQ] = []
        self.tickets: list[dict] = []
        self.sessions: dict[str, list] = {}
        self.metrics = {"total": 0, "auto_resolved": 0, "escalated": 0, "tickets": 0,
                        "satisfaction_sum": 0, "satisfaction_cnt": 0}

    def idf(self, term: str) -> float:
        n = len(self.faqs) or 1
        df = sum(1 for f in self.faqs if term in f.tf)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))


STORE = Store()


def tokenize(text: str) -> list[str]:
    text = text.lower()
    toks: list[str] = []
    for seg in re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", text):
        if re.match(r"[a-z0-9]+", seg):
            toks.append(seg)
        else:
            toks.extend(list(seg))
            toks.extend(seg[i:i + 2] for i in range(len(seg) - 1))
    return toks


def detect_intent(msg: str) -> tuple[str, float]:
    scores = {}
    for intent, kws in INTENT_RULES.items():
        hit = sum(1 for k in kws if k in msg)
        if hit:
            scores[intent] = hit
    if not scores:
        return "其他", 0.0
    best = max(scores, key=scores.get)
    return best, min(1.0, scores[best] / 2)


def match_faq(msg: str) -> tuple[FAQ | None, float]:
    if not STORE.faqs:
        return None, 0.0
    q_tf = Counter(tokenize(msg))
    best, best_score = None, 0.0
    for f in STORE.faqs:
        dot = sum((q_tf[t] * STORE.idf(t)) * (f.tf[t] * STORE.idf(t)) for t in q_tf if t in f.tf)
        qn = math.sqrt(sum((q_tf[t] * STORE.idf(t)) ** 2 for t in q_tf)) or 1e-9
        cn = math.sqrt(sum((f.tf[t] * STORE.idf(t)) ** 2 for t in f.tf)) or 1e-9
        score = dot / (qn * cn)
        if score > best_score:
            best, best_score = f, score
    return best, best_score


# ---------------- 请求体 ----------------
class ChatReq(BaseModel):
    message: str
    session_id: str = "default"


class TicketReq(BaseModel):
    session_id: str = "default"
    category: str
    content: str
    contact: str = ""


class RateReq(BaseModel):
    score: int  # 1-5


# ---------------- 路由 ----------------
@app.post("/api/chat")
def chat(req: ChatReq) -> dict:
    msg = req.message.strip()
    STORE.metrics["total"] += 1
    intent, intent_conf = detect_intent(msg)
    faq, faq_score = match_faq(msg)

    STORE.sessions.setdefault(req.session_id, []).append({"role": "user", "text": msg})

    escalate = False
    if intent == "转人工" or intent == "投诉建议":
        escalate = True
        reply = ("已为你转接人工客服，坐席将尽快接入。" if intent == "转人工"
                 else "非常抱歉给你带来不好的体验，已为你升级到人工专员处理，并记录本次反馈。")
        matched = None
    elif faq and faq_score >= CONFIDENCE_THRESHOLD:
        reply = faq.a
        matched = {"id": faq.id, "q": faq.q, "category": faq.cat, "score": round(faq_score, 4)}
        STORE.metrics["auto_resolved"] += 1
    else:
        escalate = True
        reply = (f"我理解你想咨询「{intent}」相关问题，但暂时没有匹配到足够确定的答案"
                 f"（置信度 {round(faq_score, 3)} < 阈值 {CONFIDENCE_THRESHOLD}）。"
                 "要不要我为你转接人工客服，或创建一张工单跟进？")
        matched = None

    if escalate:
        STORE.metrics["escalated"] += 1

    actions = QUICK_ACTIONS.get(intent, QUICK_ACTIONS["其他"])
    STORE.sessions[req.session_id].append({"role": "bot", "text": reply})
    return {
        "reply": reply,
        "intent": intent,
        "intent_confidence": round(intent_conf, 2),
        "matched_faq": matched,
        "faq_score": round(faq_score, 4),
        "threshold": CONFIDENCE_THRESHOLD,
        "escalate": escalate,
        "suggested_actions": actions,
    }


@app.post("/api/ticket")
def create_ticket(req: TicketReq) -> dict:
    t = {
        "id": "TK" + uuid.uuid4().hex[:8].upper(),
        "category": req.category,
        "content": req.content,
        "contact": req.contact,
        "status": "待处理",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "session_id": req.session_id,
    }
    STORE.tickets.insert(0, t)
    STORE.metrics["tickets"] += 1
    return {"ticket": t}


@app.get("/api/tickets")
def list_tickets() -> dict:
    return {"tickets": STORE.tickets[:50]}


@app.post("/api/rate")
def rate(req: RateReq) -> dict:
    if not 1 <= req.score <= 5:
        raise HTTPException(400, "评分需在 1-5")
    STORE.metrics["satisfaction_sum"] += req.score
    STORE.metrics["satisfaction_cnt"] += 1
    return {"ok": True, "avg": _avg_sat()}


def _avg_sat() -> float:
    c = STORE.metrics["satisfaction_cnt"]
    return round(STORE.metrics["satisfaction_sum"] / c, 2) if c else 0.0


@app.get("/api/stats")
def stats() -> dict:
    m = STORE.metrics
    total = m["total"] or 1
    return {
        "total": m["total"],
        "auto_resolved": m["auto_resolved"],
        "escalated": m["escalated"],
        "tickets": m["tickets"],
        "resolve_rate": round(m["auto_resolved"] / total, 3),
        "satisfaction": _avg_sat(),
        "faq_count": len(STORE.faqs),
    }


@app.get("/api/faqs")
def list_faqs() -> dict:
    return {"faqs": [{"id": f.id, "q": f.q, "a": f.a, "cat": f.cat} for f in STORE.faqs]}


@app.post("/api/seed")
def seed() -> dict:
    data = [
        ("怎么查看物流信息？", "进入「我的订单」找到对应订单，点击「查看物流」即可看到实时配送轨迹。", "物流查询"),
        ("多久发货？", "现货商品通常 24 小时内发货，预售商品以商品页标注的发货时间为准。", "物流查询"),
        ("如何申请退款？", "在「我的订单」中选择要退款的订单，点击「申请退款」，填写原因并提交，审核通过后 1-3 个工作日原路退回。", "退款退货"),
        ("退货运费谁承担？", "若因质量问题退货，运费由商家承担；若为七天无理由退货，运费由买家承担。", "退款退货"),
        ("可以修改收货地址吗？", "订单未发货前可在「我的订单」中修改收货地址；已发货则需联系客服协助拦截。", "订单问题"),
        ("支持哪些支付方式？", "支持微信支付、支付宝、银行卡及花呗分期等多种支付方式。", "订单问题"),
        ("产品怎么使用？", "每件产品均附带图文使用说明，也可在「帮助中心-产品文档」查看详细教程与视频。", "产品咨询"),
        ("有优惠活动吗？", "关注店铺可第一时间获取满减、优惠券与限时秒杀等活动信息。", "产品咨询"),
    ]
    for q, a, c in data:
        STORE.faqs.append(FAQ(q, a, c))
    return {"added": len(data), "total": len(STORE.faqs)}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "smart-service-desk", "faqs": len(STORE.faqs)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
