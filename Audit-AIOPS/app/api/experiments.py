"""
科研实验记录智能体 · API 路由（AdventureX 黑客松原型）

端点（全部挂载于 /api/experiments，端口 8001）：
- POST /upload        真实文件上传入库（.md/.txt/.csv/.json/.jsonl/截图），multipart，核心"真实数据接入"
- GET  /list          已接入实验记录清单
- POST /query         基于用户真实数据的接地问答（带引用、可追溯）
- GET  /graph         科研实体共现图（跨实验关联可视化数据）
- GET  /metrics       平台效果指标（记录数/实体数/跨实验关联/重复预警/估算节省时间）
- POST /seed          加载示例实验（真实文件落盘后入库），一键体验
- DELETE /{rec_id}    删除某条记录

设计哲学与既有平台一致：可插拔、纯 CPU 可复现、零外部依赖即可真跑；真实数据驱动、回答接地不幻觉。
"""

import json
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.experiment_store import ExperimentStore, seed_experiments

exp_router = APIRouter()

# 模块级单例（演示用，进程内共享；与 extra_router 中的 _hybrid 等一致）
_store = ExperimentStore()


class ExpQuery(BaseModel):
    question: str
    top_k: int = 3


class SeedRequest(BaseModel):
    force: bool = False  # 是否先清空再加载


@exp_router.post("/api/experiments/upload")
async def upload(file: UploadFile = File(...)):
    """真实用户数据接入：上传实验记录文件 → 解析/实体抽取/入库，返回新记录与最新效果指标。

    支持 .md/.txt/.csv/.json/.jsonl 文本记录，以及 .png/.jpg 等截图（经视觉编码转文本后入库）。
    """
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="空文件，请上传真实实验数据。")
    try:
        rec = _store.ingest_file(file.filename or "untitled", data)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"入库失败：{e}")
    return {"status": "ok", "record": rec, "metrics": _store.metrics()}


@exp_router.get("/api/experiments/list")
def list_records():
    """已接入实验记录清单（不含正文，便于前端列表展示）。"""
    return {
        "total": len(_store.records),
        "records": [
            {
                "id": r["id"],
                "title": r["title"],
                "kind": r.get("kind"),
                "source_file": r.get("source_file"),
                "entities": r.get("entities", [])[:12],
                "created_at": r.get("created_at"),
            }
            for r in _store.records
        ],
    }


@exp_router.post("/api/experiments/query")
def query(req: ExpQuery):
    """基于用户真实数据的接地问答：检索命中即引用原始记录，未命中如实告知，绝不编造。"""
    return _store.query(req.question, req.top_k)


@exp_router.get("/api/experiments/graph")
def graph():
    """科研实体共现图：节点=实体（含出现记录数），边=同实验共现，供前端力导向可视化。"""
    return _store.graph()


@exp_router.get("/api/experiments/metrics")
def metrics():
    """平台效果指标：随真实上传数据实时计算，是平台价值的直接证据。"""
    return _store.metrics()


@exp_router.post("/api/experiments/seed")
def seed(req: SeedRequest):
    """加载示例实验（真实文件落盘后入库），一键体验真实接入与效果量化。"""
    n = seed_experiments(_store, force=req.force)
    return {"status": "ok", "seeded": n, "metrics": _store.metrics()}


@exp_router.delete("/api/experiments/{rec_id}")
def delete(rec_id: str):
    """删除某条实验记录（含落盘索引同步）。"""
    removed = _store.delete(rec_id)
    if removed == 0:
        raise HTTPException(status_code=404, detail=f"未找到记录 {rec_id}")
    return {"status": "ok", "removed": removed, "metrics": _store.metrics()}
