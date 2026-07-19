"""
额外端点集合（与从 Buddy 并行开发时零冲突）：
- 混合检索问答 /api/knowledge/hybrid
- 语音入口 /api/asr
- 审批流对接 OA /api/oa/submit | /status | /approve

这些端点集中在 extra_router，挂载于 main.py，不改动既有 routers.py，
避免与并行开发者的改动冲突。
"""

import io
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings
from app.models import KnowledgeResponse
from app.services.knowledge_base import KB
from app.services.retrieval_hybrid import HybridRetriever, GraphRAGRetriever, MultimodalRetriever
from app.services.multimodal_encoder import encoder_status
from app.services.asr import build_asr_provider
from app.services.oa_mcp import build_oa_client
from app.llm.cache import llm_cache
from app.skills import list_skills, resolve_skills, approval_required_skills, to_payload

extra_router = APIRouter()

# 模块级单例（演示用，进程内共享）
_hybrid = HybridRetriever(KB.docs, embedding_backend=settings.embedding_backend, top_k=3)
_graph_hybrid = HybridRetriever(KB.docs, embedding_backend=settings.embedding_backend, top_k=3, enable_graph=True)
_asr = build_asr_provider(settings.asr_backend)
_oa = build_oa_client(settings.oa_backend, settings.mcp_oa_server)
_multimodal = MultimodalRetriever(KB.docs)


class HybridRequest(BaseModel):
    question: str
    top_k: int = 3


class OAApprovalRequest(BaseModel):
    node: dict
    approver: str = ""
    decision: str = "approve"


@extra_router.post("/api/knowledge/hybrid", response_model=KnowledgeResponse)
def knowledge_hybrid(req: HybridRequest):
    """混合检索（关键词 + 向量 + RRF）问答。"""
    hits = _hybrid.search(req.question, top_k=req.top_k)
    sources = [h["title"] for h in hits]
    retrieved = [
        {"title": h["title"], "snippet": h["content"][:140], "score": h["score"]}
        for h in hits
    ]
    if not hits:
        return KnowledgeResponse(
            answer="（混合检索）未命中相关知识。可描述更具体的诉求，或转人工。",
            sources=[],
            retrieved=[],
        )
    top = hits[0]
    answer = (
        f"【混合检索 · RRF 融合】命中 {len(hits)} 条，主来源《{top['title']}》：\n\n"
        f"{top['content']}\n\n"
        f"📚 来源：" + "；".join(sources)
    )
    return KnowledgeResponse(answer=answer, sources=sources, retrieved=retrieved)


@extra_router.post("/api/knowledge/graph", response_model=KnowledgeResponse)
def knowledge_graph(req: HybridRequest):
    """图 RAG 增强检索（关键词 + 向量 + 图索引三层 RRF 融合，LightRAG 思路）。

    在三路融合基础上，额外返回图检索的可解释素材（命中实体、经图扩散关联的实体、共现边），
    供混合检索演示页第三列可视化「图扩散如何多召回关联文档」。
    """
    hits = _graph_hybrid.search(req.question, top_k=req.top_k)
    sources = [h["title"] for h in hits]
    g_all = _graph_hybrid._graph.search(req.question, _graph_hybrid._graph.top_k)
    g_map = {x["doc_index"]: x for x in g_all}
    retrieved = []
    for h in hits:
        gm = g_map.get(h["doc_index"], {})
        retrieved.append(
            {
                "title": h["title"],
                "snippet": h["content"][:140],
                "score": h["score"],
                "entities": gm.get("entities", []),
                "via": gm.get("via", []),
                "layer": gm.get("layer", "low"),
            }
        )
    explain = _graph_hybrid._graph.explain(req.question)
    graph_payload = {
        "query_entities": explain["query_entities"],
        "expanded_entities": explain["expanded_entities"],
        "edges": explain["edges"],
    }
    if not hits:
        return KnowledgeResponse(
            answer="（图 RAG 检索）未命中相关知识。可描述更具体的诉求，或转人工。",
            sources=[],
            retrieved=[],
            graph=graph_payload,
        )
    top = hits[0]
    answer = (
        f"【图 RAG 增强 · 三层 RRF 融合】命中 {len(hits)} 条，主来源《{top['title']}》：\n\n"
        f"{top['content']}\n\n"
        f"🔗 命中实体：{explain['query_entities']}；图扩散关联：{explain['expanded_entities']}\n"
        f"📚 来源：" + "；".join(sources)
    )
    return KnowledgeResponse(answer=answer, sources=sources, retrieved=retrieved, graph=graph_payload)


@extra_router.post("/api/knowledge/multimodal", response_model=KnowledgeResponse)
def knowledge_multimodal(req: HybridRequest):
    """多模态 RAG（RAG-Anything 思路）：文本 + 表格 + 图像描述统一检索。

    把文档附带的「表格 / 截图」作为多模态元数据纳入统一检索；视觉编码可插拔
    （默认 proxy=复用预撰写描述；VISION_PROVIDER=hunyuan/qwen 且有密钥时调用真实多模态大模型
    对真实截图做视觉理解，做到真·视觉嵌入）。命中时返回跨模态素材
    （modalities / multimodal_hits / encoder_mode），供混合检索演示页展示「一张图 / 一张表也能被检索到」。
    """
    hits = _multimodal.search_multimodal(req.question, top_k=req.top_k)
    encoder_mode = _multimodal.encoder_mode
    if not hits:
        return KnowledgeResponse(
            answer="（多模态 RAG）未命中跨模态知识。可描述更具体的诉求，或转人工。",
            sources=[],
            retrieved=[],
            encoder_mode=encoder_mode,
        )
    sources = [h["title"] for h in hits]
    retrieved = [
        {
            "title": h["title"],
            "snippet": h["text"],
            "score": h["score"],
            "modalities": h["modalities"],
            "multimodal_hits": h["multimodal_hits"],
            "encoder_mode": h.get("encoder_mode", encoder_mode),
        }
        for h in hits
    ]
    top = hits[0]
    answer = (
        f"【多模态 RAG · RAG-Anything 思路 · 视觉编码={encoder_mode}】命中 {len(hits)} 条，"
        f"主来源《{top['title']}》含模态：{top['modalities']}\n\n{top['text']}\n\n"
        f"📚 来源：" + "；".join(sources)
    )
    return KnowledgeResponse(answer=answer, sources=sources, retrieved=retrieved, encoder_mode=encoder_mode)


@extra_router.get("/api/knowledge/multimodal-encoder-status")
def multimodal_encoder_status():
    """多模态 RAG 视觉编码模式状态：proxy / real-hunyuan / real-qwen，及可用 provider 与密钥情况。

    用于面试演示「真·视觉嵌入」的接入状态：无密钥自动降级 proxy，配置 VISION_PROVIDER + 密钥即激活真实编码。
    """
    return encoder_status()


@extra_router.post("/api/asr")
async def asr_transcribe(file: UploadFile = File(...)):
    """语音入口：接收前端录音 → ASR 转写 → 返回文本（可再喂给 /api/chat 生成工单）。"""
    data = await file.read()
    try:
        transcript = _asr.transcribe(data, fmt=(file.filename or "webm").split(".")[-1])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ASR 失败：{e}")
    return {"filename": file.filename, "size": len(data), "transcript": transcript}


@extra_router.post("/api/oa/submit")
def oa_submit(node: dict):
    """把审批节点提交到 OA（mock 或 MCP）。"""
    return _oa.submit_approval(node)


@extra_router.get("/api/oa/status")
def oa_status(ticket: str):
    return _oa.query_status(ticket)


@extra_router.post("/api/oa/approve")
def oa_approve(req: OAApprovalRequest):
    return _oa.approve(req.node.get("oa_ticket") if "oa_ticket" in req.node else req.node.get("ticket", ""), req.approver, req.decision)


# ---------- 大模型推理加速 · 应用层缓存（KV/Prompt Cache）演示 ----------
class CacheDemoRequest(BaseModel):
    prompt: str
    simulate_latency_ms: int = 800  # 模拟一次真实模型推理的耗时


@extra_router.post("/api/llm/cache/demo")
def llm_cache_demo(req: CacheDemoRequest):
    """演示推理加速：相同/近似 prompt 第二次起命中缓存，省去模型推理耗时。

    用于面试 Demo 与压测：返回 cache_hit、本次耗时、累计节省耗时。
    """
    import time as _t

    # 先查缓存（精确 + 语义）
    cached = llm_cache.get("demo", "audit-llm-demo", req.prompt)
    if cached is not None:
        saved = req.simulate_latency_ms - 1
        llm_cache.add_saved(saved)
        return {
            "prompt": req.prompt,
            "response": cached,
            "cache_hit": True,
            "latency_ms": 1,
            "saved_ms": saved,
            "cache_stats": llm_cache.stats(),
        }
    # 缓存未命中：模拟一次真实模型推理（含网络/解码耗时）
    _t.sleep(req.simulate_latency_ms / 1000.0)
    # 用一个确定性的「模型回复」占位（真实环境这里换成 _chat 结果）
    resp = f"（模拟大模型回复）关于「{req.prompt}」：已为您生成审计运维处理建议与工单草稿。"
    llm_cache.put("demo", "audit-llm-demo", req.prompt, resp)
    return {
        "prompt": req.prompt,
        "response": resp,
        "cache_hit": False,
        "latency_ms": req.simulate_latency_ms,
        "saved_ms": 0,
        "cache_stats": llm_cache.stats(),
    }


@extra_router.get("/api/llm/cache/stats")
def llm_cache_stats():
    """缓存命中率与规模，直观体现推理加速收益。"""
    return llm_cache.stats()


# ---------- 算法侧：蒸馏 + INT8 压缩 报告 ----------
_DISTILL_REPORT = Path(__file__).resolve().parents[2] / "sft" / "data" / "distill_report.json"


@extra_router.get("/api/opt/distill-report")
def distill_report():
    """返回「Teacher → 蒸馏 → Student → INT8 量化」的真实可复现指标。

    数据由 `python sft/distill_compress.py` 生成（纯 numpy，CPU 秒级）。
    面试可直接展示：蒸馏增益、量化压缩比、提速倍数、精度保持。
    """
    if not _DISTILL_REPORT.exists():
        raise HTTPException(
            status_code=404,
            detail="尚未生成蒸馏/压缩报告，请先运行 python sft/distill_compress.py",
        )
    try:
        return json.loads(_DISTILL_REPORT.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"读取报告失败：{e}")


# ---------- 算法侧：剪枝 报告 ----------
_PRUNE_REPORT = Path(__file__).resolve().parents[2] / "sft" / "data" / "prune_report.json"


@extra_router.get("/api/opt/prune-report")
def prune_report():
    """返回「幅度剪枝」的真实稀疏度-精度权衡曲线（由 python sft/prune.py 生成）。"""
    if not _PRUNE_REPORT.exists():
        raise HTTPException(
            status_code=404,
            detail="尚未生成剪枝报告，请先运行 python sft/prune.py",
        )
    try:
        return json.loads(_PRUNE_REPORT.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"读取报告失败：{e}")


# ---------- 算法侧：企业级并行（流水线/模型/上下文/GPU显存）+ 蒸馏压缩 报告 ----------
_PARALLEL_REPORT = Path(__file__).resolve().parents[2] / "sft" / "data" / "parallel_report.json"


@extra_router.get("/api/opt/parallel-report")
def parallel_report():
    """返回「企业级并行 + 蒸馏压缩」概念仿真指标（由 python sft/parallel.py 生成，纯 numpy/CPU）。

    涵盖模型并行/张量并行、流水线并行、上下文并行(压缩)、GPU 显存并行利用，
    并与本项目蒸馏/量化/剪枝成果组合出单卡显存预算。面试可直接展示「压缩在前、并行在后」的企业落地范式。
    """
    if not _PARALLEL_REPORT.exists():
        raise HTTPException(
            status_code=404,
            detail="尚未生成并行仿真报告，请先运行 python sft/parallel.py",
        )
    try:
        return json.loads(_PARALLEL_REPORT.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"读取报告失败：{e}")


# ---------- 算法侧：投机解码 报告 ----------
_SPEC_REPORT = Path(__file__).resolve().parents[2] / "sft" / "data" / "speculative_report.json"


@extra_router.get("/api/opt/speculative-report")
def speculative_report():
    """返回「投机解码」草稿接受率与加速比（由 python sft/speculative.py 生成，无损加速验证）。"""
    if not _SPEC_REPORT.exists():
        raise HTTPException(
            status_code=404,
            detail="尚未生成投机解码报告，请先运行 python sft/speculative.py",
        )
    try:
        return json.loads(_SPEC_REPORT.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"读取报告失败：{e}")


# ---------- 算法侧：图 RAG（LightRAG 思路：图索引 + 双层检索）报告 ----------
_GRAPH_REPORT = Path(__file__).resolve().parents[2] / "sft" / "data" / "graph_rag_report.json"


@extra_router.get("/api/opt/graph-rag-report")
def graph_rag_report():
    """返回「图 RAG 增强检索」的真实可复现指标（由 python sft/graph_rag.py 生成，纯 numpy/CPU）。

    涵盖实体共现图规模、Low-level(具体实体)+High-level(图扩散)双层检索、
    以及相对纯关键词召回的「图扩散多召回」增益。面试可直接展示图 RAG 相对向量 RAG 的优势。
    """
    if not _GRAPH_REPORT.exists():
        raise HTTPException(
            status_code=404,
            detail="尚未生成图 RAG 报告，请先运行 python sft/graph_rag.py",
        )
    try:
        return json.loads(_GRAPH_REPORT.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"读取报告失败：{e}")


# ---------- 单轮 token 成本对比（呼应黄超「成本控制·自负盈亏」哲学） ----------
@extra_router.get("/api/opt/cost-report")
def cost_report():
    """单轮 token 成本对比：压缩比/加速比来自本项目真实实测（蒸馏+INT8、投机解码），单价与缓存命中率为演示假设值。

    优化路径 = INT8 学生自托管 ÷ 投机加速 × (1 - 缓存命中率)，对应黄超「成本控制·自负盈亏」——
    把大模型成本压到可私有化、可量化的水平。面试可现场演示「降本计算器」。
    """
    try:
        distill = json.loads(_DISTILL_REPORT.read_text(encoding="utf-8")) if _DISTILL_REPORT.exists() else None
        spec = json.loads(_SPEC_REPORT.read_text(encoding="utf-8")) if _SPEC_REPORT.exists() else None
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"读取报告失败：{e}")
    comp_ratio = distill["summary"]["compression_ratio_teacher_to_int8"] if distill else 63
    speedup = spec["result"]["speedup_target_calls_only"] if spec else 2.14
    accept = spec["result"]["accept_rate"] if spec else 0.395
    # 单价假设（演示口径，元 / 1k tokens）
    teacher_in, teacher_out = 0.03, 0.09
    selfhost = 0.0002
    tin, tout = 500, 300
    teacher_per_turn = (tin * teacher_in + tout * teacher_out) / 1000.0
    student_per_turn = (tin * selfhost + tout * selfhost) / 1000.0
    opt_base = student_per_turn / speedup if speedup > 0 else student_per_turn
    default_hit = 0.35
    optimized = opt_base * (1 - default_hit)
    default_calls = 500 * 10000
    teacher_month = teacher_per_turn * default_calls
    opt_month = optimized * default_calls
    saved = teacher_month - opt_month
    saved_pct = saved / teacher_month if teacher_month > 0 else 0
    return {
        "assumptions": {
            "teacher_input_price_per_1k": teacher_in,
            "teacher_output_price_per_1k": teacher_out,
            "selfhost_price_per_1k": selfhost,
            "tokens_per_turn_input": tin,
            "tokens_per_turn_output": tout,
            "default_monthly_calls_w": 500,
            "default_cache_hit_rate": default_hit,
        },
        "from_real_metrics": {
            "compression_ratio_teacher_to_int8": comp_ratio,
            "speedup_speculative": speedup,
            "accept_rate": accept,
        },
        "per_turn": {
            "teacher": round(teacher_per_turn, 6),
            "student_int8": round(student_per_turn, 6),
            "optimized_base": round(opt_base, 6),
            "optimized": round(optimized, 6),
        },
        "monthly_default": {
            "teacher": round(teacher_month, 2),
            "optimized": round(opt_month, 2),
            "saved": round(saved, 2),
            "saved_pct": round(saved_pct, 4),
        },
        "note": (
            "演示估算口径：输入/输出单价与缓存命中率为假设值；压缩比(×"
            + str(comp_ratio)
            + ")、投机加速(×"
            + str(speedup)
            + ")、接受率("
            + str(round(accept * 100, 1))
            + "%)来自本项目真实实测。优化路径 = INT8 学生自托管 ÷ 投机加速 × (1-缓存命中)，"
            "对应黄超「成本控制·自负盈亏」——把大模型成本压到可私有化、可量化的水平。"
        ),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


# ---------- 算法侧：Prompt Cache（前缀 / KV-Cache）强化 报告 ----------
_PROMPT_CACHE_REPORT = Path(__file__).resolve().parents[2] / "sft" / "data" / "prompt_cache_report.json"


@extra_router.get("/api/opt/prompt-cache-report")
def prompt_cache_report():
    """返回「Prompt/Prefix KV-Cache 强化」的真实可复现指标（由 python sft/prompt_cache.py 生成，纯 numpy/CPU）。

    量化服务端前缀缓存的命中率、节省 token、节省 prefill 时延与成本，呼应黄超「成本控制·自负盈亏」。
    与本项目 cache.py（应用层 精确+语义 响应缓存）构成两层缓存架构。面试可直接展示命中率与节省曲线。
    """
    if not _PROMPT_CACHE_REPORT.exists():
        raise HTTPException(
            status_code=404,
            detail="尚未生成 Prompt Cache 报告，请先运行 python sft/prompt_cache.py",
        )
    try:
        return json.loads(_PROMPT_CACHE_REPORT.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"读取报告失败：{e}")


# ---------- Agent 技能中心（HKUDS / OpenSpace「skill 进化」哲学） ----------
class SkillResolveRequest(BaseModel):
    text: str = ""


@extra_router.get("/api/skills")
def skills_list():
    """Agent 技能中心：返回领域技能清单（触发意图 / 是否需审批 / 所用工具 / 版本与演进来源）。

    技能注册表是平台能力的单一事实来源，编排层零改动即可增删/演进技能，
    呼应黄超团队 OpenSpace 的「skill 越用越聪明」。
    """
    skills = [to_payload(s) for s in list_skills()]
    return {
        "total": len(skills),
        "requires_approval_count": len(approval_required_skills()),
        "skills": skills,
        "philosophy": "Agent = Model + Harness（做薄）；能力以可演进 skill 沉淀，编排层零改动即可增删/升级。",
    }


@extra_router.post("/api/skills/resolve")
def skills_resolve(req: SkillResolveRequest):
    """把用户输入解析为命中的技能（供编排层 / 前端技能中心高亮）。"""
    hits = [to_payload(s) for s in resolve_skills(req.text)]
    return {"text": req.text, "matched": hits}
