"""大模型微调平台：端到端 LoRA/QLoRA 微调 MVP。

覆盖：数据接入与校验 → 训练任务（后台线程模拟真实 loss 收敛）→ 实时指标 →
导出 adapter 配置 → 部署命令（vLLM / peft）。无 GPU/模型依赖也可完整演示。
"""
import json
import math
import random
import threading
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.llm import LLMClient

router = APIRouter(prefix="/api/finetune", tags=["finetune"])

llm = LLMClient()
_jobs: dict[str, dict] = {}
_lock = threading.Lock()


# ---------------- 数据模型 ----------------
class IngestRequest(BaseModel):
    content: str  # JSONL / Alpaca JSON / CSV(text,label)
    format: str = "auto"  # auto|alpaca|jsonl|csv


class TrainConfig(BaseModel):
    base_model: str = "Qwen2.5-3B-Instruct"
    method: str = "LoRA"  # LoRA | QLoRA
    r: int = 8
    alpha: int = 16
    dropout: float = 0.05
    lr: float = 2e-4
    epochs: int = 3
    batch_size: int = 4
    max_seq_len: int = 2048
    data_ref: str = ""  # ingest 返回的 dataset_id


class ChatRequest(BaseModel):
    message: str


# ---------------- 工具函数 ----------------
def _parse_dataset(content: str, fmt: str) -> tuple[list[dict], str]:
    content = content.strip()
    samples: list[dict] = []
    detected = fmt
    if fmt == "auto":
        if content.startswith("["):
            detected = "alpaca"
        elif "\n" in content and content.lstrip().startswith("{"):
            detected = "jsonl"
        elif "," in content.splitlines()[0] if content else False:
            detected = "csv"
        else:
            detected = "alpaca"
    if detected == "alpaca":
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                data = data.get("data", [data])
            for row in data:
                samples.append({
                    "instruction": row.get("instruction", ""),
                    "input": row.get("input", ""),
                    "output": row.get("output", ""),
                })
        except Exception:
            pass
    elif detected == "jsonl":
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                samples.append({
                    "instruction": row.get("instruction") or row.get("prompt", ""),
                    "input": row.get("input", ""),
                    "output": row.get("output") or row.get("response", ""),
                })
            except Exception:
                continue
    else:  # csv: text,label
        lines = [l for l in content.splitlines() if l.strip()]
        for l in lines:
            parts = l.split(",", 1)
            samples.append({"instruction": parts[0], "input": "", "output": parts[1] if len(parts) > 1 else ""})
    samples = [s for s in samples if s["instruction"] or s["output"]]
    return samples, detected


def _build_prompt(s: dict) -> str:
    if s["input"]:
        return f"### 指令\n{s['instruction']}\n\n### 输入\n{s['input']}\n\n### 回答\n{s['output']}"
    return f"### 指令\n{s['instruction']}\n\n### 回答\n{s['output']}"


def _estimate_gpu_mem(method: str, base_model: str, batch: int) -> str:
    # 粗略估算
    base = 6.0 if "3B" in base_model else (12.0 if "7B" in base_model else 3.0)
    if method == "QLoRA":
        base *= 0.33  # 4-bit 量化
    base += batch * 0.4
    return f"~{base:.1f} GB"


# ---------------- 路由 ----------------
@router.post("/ingest")
def ingest(req: IngestRequest):
    samples, fmt = _parse_dataset(req.content, req.format)
    if not samples:
        raise HTTPException(status_code=400, detail="无法解析到有效样本，请检查数据格式（Alpaca JSON / JSONL / CSV）。")
    total_tokens = sum(len(_build_prompt(s)) // 4 for s in samples[:200])
    avg_len = total_tokens // max(1, min(len(samples), 200))
    dataset_id = f"ds_{int(time.time())}"
    with _lock:
        _jobs[dataset_id] = {"kind": "dataset", "samples": samples[:50], "count": len(samples), "format": fmt}
    return {
        "dataset_id": dataset_id,
        "format": fmt,
        "num_samples": len(samples),
        "avg_tokens": avg_len,
        "preview": samples[:3],
    }


@router.post("/train")
def train(cfg: TrainConfig):
    ds = _jobs.get(cfg.data_ref)
    if not ds or ds.get("kind") != "dataset":
        raise HTTPException(status_code=400, detail="请先 /ingest 获得有效的 dataset_id。")
    steps_per_epoch = max(1, len(ds["samples"]) * 10 // cfg.batch_size)  # 用预览样本放大近似
    total_steps = steps_per_epoch * cfg.epochs
    job_id = f"job_{int(time.time())}"
    job = {
        "job_id": job_id,
        "status": "running",
        "progress": 0.0,
        "step": 0,
        "total_steps": total_steps,
        "loss_curve": [],
        "config": cfg.model_dump(),
        "gpu_mem": _estimate_gpu_mem(cfg.method, cfg.base_model, cfg.batch_size),
        "started_at": datetime.now().isoformat(),
    }
    with _lock:
        _jobs[job_id] = job

    def _run():
        rng = random.Random(hash(job_id) & 0xFFFF)
        loss0 = 2.3
        decay = 4.0 / max(1, total_steps)
        for i in range(1, total_steps + 1):
            noise = rng.uniform(-0.05, 0.05)
            loss = max(0.2, loss0 * math.exp(-decay * i) + noise + (0.02 if cfg.method == "QLoRA" else 0))
            time.sleep(0.01)  # 控制演示节奏
            with _lock:
                j = _jobs[job_id]
                j["step"] = i
                j["progress"] = round(i / total_steps, 4)
                j["loss_curve"].append(round(loss, 4))
                if i == total_steps:
                    j["status"] = "done"
                    j["final_loss"] = round(loss, 4)

    threading.Thread(target=_run, daemon=True).start()
    return {"job_id": job_id, "total_steps": total_steps, "gpu_mem": job["gpu_mem"]}


@router.get("/train/{job_id}")
def train_status(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job or "loss_curve" not in job:
        raise HTTPException(status_code=404, detail="任务不存在。")
    job = {k: v for k, v in job.items() if k != "samples"}
    return job


@router.get("/train/{job_id}/export")
def export_adapter(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在。")
    cfg = job["config"]
    adapter = {
        "base_model": cfg["base_model"],
        "peft_type": "LORA",
        "quantization": "nf4" if cfg["method"] == "QLoRA" else None,
        "r": cfg["r"],
        "lora_alpha": cfg["alpha"],
        "lora_dropout": cfg["dropout"],
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        "bias": "none",
        "task_type": "CAUSAL_LM",
    }
    return {"adapter_config": adapter, "method": cfg["method"]}


@router.get("/train/{job_id}/deploy")
def deploy(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在。")
    cfg = job["config"]
    name = cfg["base_model"].lower().replace("/", "-")
    vllm_cmd = f"vllm serve {cfg['base_model']} --lora-modules adapter1=/path/to/adapter --enable-lora"
    api_snippet = (
        "from peft import PeftModel\n"
        "from transformers import AutoModelForCausalLM, AutoTokenizer\n"
        f"base = AutoModelForCausalLM.from_pretrained('{cfg['base_model']}')\n"
        "model = PeftModel.from_pretrained(base, '/path/to/adapter')\n"
        "tokenizer = AutoTokenizer.from_pretrained('/path/to/adapter')\n"
        "model.eval()"
    )
    return {"vllm_command": vllm_cmd, "adapter_name": f"{name}-adapter", "inference_snippet": api_snippet}


@router.get("/health")
def health():
    return {"status": "ok", "project": "finetune", "llm_enabled": llm.enabled}
