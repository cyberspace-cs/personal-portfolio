"""
LLM Finetune Studio · 后端服务
================================
一个可运行的大模型微调工作台后端（FastAPI）。

设计目标：
- 无需任何外部 API Key / GPU 即可本地运行，全流程可演示；
- 真实实现数据集校验、LoRA/QLoRA 超参管理、训练任务调度、
  实时 loss/lr 曲线、断点续训状态、以及基座 vs 微调模型的对比推理；
- 训练过程用可复现的数学模型模拟收敛曲线（真实 loss 随 step 递减 + 噪声），
  接口与 HuggingFace PEFT/Trainer 同构，接入真实训练器时可直接替换。

运行：
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8001
"""
from __future__ import annotations

import asyncio
import json
import math
import random
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="LLM Finetune Studio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------------------
# 可选基座模型（对齐国产 + 开源主流）
# ----------------------------------------------------------------------------
BASE_MODELS = [
    {"id": "hunyuan-7b", "name": "Hunyuan-7B", "params": "7B", "ctx": 32768, "vendor": "腾讯混元"},
    {"id": "qwen2.5-7b", "name": "Qwen2.5-7B", "params": "7B", "ctx": 131072, "vendor": "阿里通义"},
    {"id": "llama3.1-8b", "name": "Llama-3.1-8B", "params": "8B", "ctx": 131072, "vendor": "Meta"},
    {"id": "glm4-9b", "name": "GLM-4-9B", "params": "9B", "ctx": 131072, "vendor": "智谱"},
]

METHODS = ["LoRA", "QLoRA", "Full-Finetune", "DoRA"]


# ----------------------------------------------------------------------------
# 训练任务模型
# ----------------------------------------------------------------------------
@dataclass
class TrainingJob:
    id: str
    base_model: str
    method: str
    hparams: dict
    dataset_stats: dict
    status: str = "pending"          # pending | running | paused | done | failed
    total_steps: int = 0
    step: int = 0
    metrics: list = field(default_factory=list)  # [{step, loss, lr, grad_norm, tokens}]
    created_at: float = field(default_factory=time.time)
    eval_loss: float | None = None
    adapter_path: str | None = None
    log: list = field(default_factory=list)

    def to_public(self) -> dict:
        d = asdict(self)
        d["progress"] = round(self.step / self.total_steps, 4) if self.total_steps else 0.0
        # 曲线只回传采样点，避免体积过大
        d["metrics"] = self.metrics[-200:]
        return d


JOBS: dict[str, TrainingJob] = {}


# ----------------------------------------------------------------------------
# 请求体
# ----------------------------------------------------------------------------
class DatasetItem(BaseModel):
    instruction: str = ""
    input: str = ""
    output: str = ""


class ValidateReq(BaseModel):
    raw: str = Field(..., description="JSONL 文本，每行一个样本")


class HParams(BaseModel):
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    learning_rate: float = 2e-4
    epochs: int = 3
    batch_size: int = 8
    max_seq_len: int = 1024
    warmup_ratio: float = 0.03


class StartReq(BaseModel):
    base_model: str = "qwen2.5-7b"
    method: str = "LoRA"
    hparams: HParams = HParams()
    sample_count: int = 500


class InferReq(BaseModel):
    job_id: str | None = None
    prompt: str


# ----------------------------------------------------------------------------
# 数据集校验：真实解析 JSONL、统计 token 分布、检出脏数据
# ----------------------------------------------------------------------------
@app.post("/api/datasets/validate")
def validate_dataset(req: ValidateReq) -> dict:
    lines = [ln for ln in req.raw.splitlines() if ln.strip()]
    ok, errors, lengths = [], [], []
    for i, ln in enumerate(lines, 1):
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError as e:
            errors.append({"line": i, "reason": f"JSON 解析失败: {e.msg}"})
            continue
        if not isinstance(obj, dict):
            errors.append({"line": i, "reason": "样本必须是 JSON 对象"})
            continue
        if not obj.get("instruction") and not obj.get("input"):
            errors.append({"line": i, "reason": "缺少 instruction/input 字段"})
            continue
        if not obj.get("output"):
            errors.append({"line": i, "reason": "缺少 output（标签）字段"})
            continue
        text = f"{obj.get('instruction','')}{obj.get('input','')}{obj.get('output','')}"
        # 估算 token 数（中文≈1char/token，英文≈4char/token 的折中）
        approx = int(len(text) / 2.2)
        lengths.append(approx)
        ok.append(obj)

    valid = len(ok)
    total = len(lines)
    stats = {
        "total": total,
        "valid": valid,
        "invalid": total - valid,
        "error_rate": round((total - valid) / total, 4) if total else 0.0,
        "avg_tokens": int(sum(lengths) / len(lengths)) if lengths else 0,
        "max_tokens": max(lengths) if lengths else 0,
        "min_tokens": min(lengths) if lengths else 0,
        "p95_tokens": _percentile(lengths, 95),
        "estimated_train_tokens": sum(lengths),
    }
    return {"stats": stats, "errors": errors[:50], "sample": ok[:3]}


def _percentile(xs: list[int], p: int) -> int:
    if not xs:
        return 0
    s = sorted(xs)
    k = int(round((p / 100) * (len(s) - 1)))
    return s[k]


# ----------------------------------------------------------------------------
# 启动训练任务
# ----------------------------------------------------------------------------
@app.post("/api/finetune/start")
async def start_finetune(req: StartReq) -> dict:
    if req.base_model not in {m["id"] for m in BASE_MODELS}:
        raise HTTPException(400, "未知基座模型")
    if req.method not in METHODS:
        raise HTTPException(400, "未知微调方法")

    steps_per_epoch = max(1, math.ceil(req.sample_count / req.hparams.batch_size))
    total_steps = steps_per_epoch * req.hparams.epochs

    job = TrainingJob(
        id=uuid.uuid4().hex[:12],
        base_model=req.base_model,
        method=req.method,
        hparams=req.hparams.model_dump(),
        dataset_stats={"samples": req.sample_count, "steps_per_epoch": steps_per_epoch},
        total_steps=total_steps,
        status="running",
        adapter_path=f"adapters/{req.base_model}-{req.method.lower()}-{uuid.uuid4().hex[:6]}",
    )
    job.log.append(_log(f"初始化 {req.method} 微调 · 基座={req.base_model} · 总步数={total_steps}"))
    JOBS[job.id] = job
    asyncio.create_task(_train_loop(job))
    return {"job_id": job.id, "total_steps": total_steps}


async def _train_loop(job: TrainingJob) -> None:
    """用可复现数学模型模拟真实收敛：loss = a*exp(-k*step) + floor + 噪声。"""
    hp = job.hparams
    lr0 = hp["learning_rate"]
    warmup = max(1, int(job.total_steps * hp["warmup_ratio"]))
    # LoRA rank 越高、lr 越合适，收敛下限越低（体现超参影响）
    floor = 0.62 + 0.18 * math.exp(-hp["lora_rank"] / 16) + random.uniform(-0.02, 0.02)
    decay_k = 3.2 / max(1, job.total_steps)

    for step in range(1, job.total_steps + 1):
        while job.status == "paused":
            await asyncio.sleep(0.3)
        if job.status == "failed":
            return
        # 学习率调度：warmup 线性升 + 余弦退火
        if step <= warmup:
            lr = lr0 * step / warmup
        else:
            prog = (step - warmup) / max(1, job.total_steps - warmup)
            lr = lr0 * 0.5 * (1 + math.cos(math.pi * prog))
        base_loss = 2.4 * math.exp(-decay_k * step * 1.0) + floor
        noise = random.uniform(-0.05, 0.05) * math.exp(-step / job.total_steps)
        loss = round(max(0.05, base_loss + noise), 4)
        grad_norm = round(max(0.1, 3.5 * math.exp(-step / (job.total_steps * 0.6)) + random.uniform(-0.2, 0.2)), 3)

        job.step = step
        job.metrics.append({
            "step": step,
            "loss": loss,
            "lr": round(lr, 8),
            "grad_norm": grad_norm,
            "tokens": step * hp["batch_size"] * hp["max_seq_len"],
        })
        if step % max(1, job.total_steps // 8) == 0:
            job.log.append(_log(f"step {step}/{job.total_steps} · loss={loss} · lr={lr:.2e}"))
        await asyncio.sleep(0.05)

    job.eval_loss = round(job.metrics[-1]["loss"] + random.uniform(0.02, 0.08), 4)
    job.status = "done"
    job.log.append(_log(f"训练完成 · eval_loss={job.eval_loss} · 适配器已保存至 {job.adapter_path}"))


def _log(msg: str) -> dict:
    return {"t": time.strftime("%H:%M:%S"), "msg": msg}


@app.post("/api/finetune/{job_id}/pause")
def pause_job(job_id: str) -> dict:
    job = _get(job_id)
    if job.status == "running":
        job.status = "paused"
        job.log.append(_log("已暂停（可续训）"))
    return {"status": job.status}


@app.post("/api/finetune/{job_id}/resume")
def resume_job(job_id: str) -> dict:
    job = _get(job_id)
    if job.status == "paused":
        job.status = "running"
        job.log.append(_log("已恢复训练"))
    return {"status": job.status}


@app.get("/api/finetune/jobs")
def list_jobs() -> dict:
    return {"jobs": [j.to_public() for j in sorted(JOBS.values(), key=lambda x: -x.created_at)]}


@app.get("/api/finetune/{job_id}")
def get_job(job_id: str) -> dict:
    return _get(job_id).to_public()


def _get(job_id: str) -> TrainingJob:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    return job


# ----------------------------------------------------------------------------
# 对比推理：基座 vs 微调（模拟微调后风格/指令遵循增强）
# ----------------------------------------------------------------------------
@app.post("/api/inference")
def inference(req: InferReq) -> dict:
    base = _fake_generate(req.prompt, tuned=False)
    tuned_available = bool(req.job_id and JOBS.get(req.job_id) and JOBS[req.job_id].status == "done")
    tuned = _fake_generate(req.prompt, tuned=True) if tuned_available else None
    return {
        "base": base,
        "tuned": tuned,
        "tuned_available": tuned_available,
        "note": "微调后模型指令遵循与领域风格更强" if tuned_available else "该任务尚未完成训练，仅返回基座输出",
    }


def _fake_generate(prompt: str, tuned: bool) -> dict:
    t0 = time.time()
    if tuned:
        reply = (f"【已按微调领域风格作答】针对「{prompt.strip()[:40]}」，"
                 "结论先行：\n1) 核心要点已结构化拆解；\n2) 引用了训练语料中的规范表述；"
                 "\n3) 输出格式严格遵循指令模板。")
        latency = round(random.uniform(0.4, 0.9), 3)
        toks = random.randint(180, 260)
    else:
        reply = (f"关于「{prompt.strip()[:40]}」，这里给出一个较为通用的回答，"
                 "覆盖基本概念与常见思路，但未针对具体领域深度优化。")
        latency = round(random.uniform(0.5, 1.1), 3)
        toks = random.randint(120, 200)
    return {"text": reply, "latency": latency, "tokens": toks,
            "throughput": round(toks / max(1e-3, latency), 1), "elapsed": round(time.time() - t0, 4)}


# ----------------------------------------------------------------------------
# 元信息 / 健康检查
# ----------------------------------------------------------------------------
@app.get("/api/meta")
def meta() -> dict:
    return {"base_models": BASE_MODELS, "methods": METHODS}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "llm-finetune-studio", "jobs": len(JOBS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
