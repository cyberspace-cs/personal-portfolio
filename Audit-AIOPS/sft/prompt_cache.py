"""
Prompt Cache（前缀 / KV-Cache）强化仿真 · 纯 numpy / CPU 可复现
=================================================================

面试与研发亮点（呼应黄超「成本控制 · 自负盈亏」哲学）：
把大模型服务端的 **prefix / KV cache** 思想落到可量化的工程指标上——
审计运维场景中，每一次对话都带着一份**很长且稳定的系统前缀**（审计规范 +
角色设定 + 政策文件摘要），而用户 query 很短且多变。若每次都对这份长达上千
token 的前缀重新做 prefill，是巨大的算力浪费。

本脚本仿真「前缀缓存」：
  - 同一份系统前缀第二次起**直接复用已计算的 KV**，跳过前缀 prefill；
  - 仅对用户 query 部分做计算 + 一次极小的缓存读取开销；
  - 统计：前缀缓存命中率、节省 token、节省 prefill 时延、节省成本。

与本项目既有 cache.py（应用层 精确+语义 响应缓存）形成**两层缓存架构**：
  ① 服务端 prefix/KV cache（本脚本量化，省 prefill 算力）
  ② 应用层 精确+语义 响应缓存（cache.py，省整次推理）
两者叠加 → 高频/近义审计问答成本与首字延迟（TTFT）同时下降。

运行（managed python，含 numpy）：
  python sft/prompt_cache.py
产出：sft/data/prompt_cache_report.json
"""
from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
DATA.mkdir(parents=True, exist_ok=True)
OUT = DATA / "prompt_cache_report.json"

# —— 仿真参数（演示口径，可解释、可复现）——
PREFIX_TOKENS = 1500        # 稳定系统前缀长度（审计规范+角色+政策摘要）
QUERY_TOKENS = 120          # 单轮用户 query 平均长度
DISTINCT_PREFIXES = 5       # 审计 5 个业务域，各有独立系统前缀
TOTAL_REQUESTS = 2000       # 一轮流量中的请求数
MS_PER_1K_TOKENS = 12.0     # prefill 算力：每 1k token 约 12ms（CPU/Mock 演示口径）
SELFHOST_PRICE_PER_1K = 0.0002   # 自托管单价（元 / 1k tokens），对应成本报告
CACHE_READ_FACTOR = 0.05    # 命中前缀缓存后仍需一次极小读取开销（占前缀算力 5%）
MONTHLY_REQUESTS_W = 500    # 月请求量（万次），对应成本报告


def simulate(seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
    # 构造请求流：先保证每个前缀各出现一次（必 miss），其余按 zipf 倾斜分布
    prefixes = list(range(DISTINCT_PREFIXES))
    rest = rng.choice(prefixes, size=TOTAL_REQUESTS - DISTINCT_PREFIXES, p=_zipf(prefixes))
    flow = np.array(prefixes + list(rest), dtype=int)

    seen = set()
    is_hit = np.zeros(TOTAL_REQUESTS, dtype=bool)
    for i, p in enumerate(flow):
        if p in seen:
            is_hit[i] = True
        else:
            seen.add(p)

    hits = int(is_hit.sum())
    misses = TOTAL_REQUESTS - hits
    hit_rate = hits / TOTAL_REQUESTS

    # 无缓存基线：每请求都计算 prefix+query
    prefix_compute_ms = PREFIX_TOKENS / 1000.0 * MS_PER_1K_TOKENS
    query_compute_ms = QUERY_TOKENS / 1000.0 * MS_PER_1K_TOKENS
    baseline_ms_per_req = prefix_compute_ms + query_compute_ms

    # 命中前缀缓存：仅 query 计算 + 极小缓存读取
    cached_ms_per_hit = query_compute_ms + prefix_compute_ms * CACHE_READ_FACTOR
    # 实际平均时延
    saved_per_hit_ms = baseline_ms_per_req - cached_ms_per_hit
    latency_saved_ms = hits * saved_per_hit_ms
    avg_latency_ms = (misses * baseline_ms_per_req + hits * cached_ms_per_hit) / TOTAL_REQUESTS
    ttft_reduction_pct = (baseline_ms_per_req - avg_latency_ms) / baseline_ms_per_req

    # token 节省
    tokens_saved = hits * PREFIX_TOKENS
    total_tokens_no_cache = TOTAL_REQUESTS * (PREFIX_TOKENS + QUERY_TOKENS)
    tokens_saved_pct = tokens_saved / total_tokens_no_cache

    # 成本节省（自托管口径）
    cost_saved = tokens_saved / 1000.0 * SELFHOST_PRICE_PER_1K
    monthly_req = MONTHLY_REQUESTS_W * 10000
    monthly_hits = int(round(hit_rate * monthly_req))
    monthly_tokens_saved = monthly_hits * PREFIX_TOKENS
    monthly_cost_saved = monthly_tokens_saved / 1000.0 * SELFHOST_PRICE_PER_1K

    # 累计节省曲线（每 40 个请求采样一次，供前端条形/折线图）
    cum = np.cumsum(np.where(is_hit, PREFIX_TOKENS, 0))
    step = max(1, TOTAL_REQUESTS // 50)
    idx = list(range(0, TOTAL_REQUESTS, step))
    if idx[-1] != TOTAL_REQUESTS - 1:
        idx.append(TOTAL_REQUESTS - 1)
    series = [{"req": int(i + 1), "cum_saved_tokens": int(cum[i])} for i in idx]

    return {
        "task": "审计运维场景 · Prompt/Prefix KV-Cache 强化（前缀复用仿真）",
        "framework": "pure python + numpy (CPU)",
        "summary": {
            "total_requests": TOTAL_REQUESTS,
            "distinct_prefixes": DISTINCT_PREFIXES,
            "prefix_cache_hits": hits,
            "prefix_cache_misses": misses,
            "prefix_cache_hit_rate": round(hit_rate, 4),
            "prefix_tokens_per_request": PREFIX_TOKENS,
            "query_tokens_per_request": QUERY_TOKENS,
            "tokens_saved": tokens_saved,
            "tokens_saved_pct": round(float(tokens_saved_pct), 4),
            "latency_saved_ms": round(latency_saved_ms, 1),
            "avg_latency_ms": round(avg_latency_ms, 2),
            "ttft_reduction_pct": round(float(ttft_reduction_pct), 4),
            "cost_saved_selfhost": round(cost_saved, 6),
            "monthly_cost_saved_at_500w": round(monthly_cost_saved, 2),
        },
        "assumptions": {
            "prefix_tokens": PREFIX_TOKENS,
            "query_tokens": QUERY_TOKENS,
            "distinct_prefixes": DISTINCT_PREFIXES,
            "total_requests": TOTAL_REQUESTS,
            "ms_per_1k_tokens": MS_PER_1K_TOKENS,
            "cache_read_factor": CACHE_READ_FACTOR,
            "selfhost_price_per_1k": SELFHOST_PRICE_PER_1K,
            "monthly_requests_w": MONTHLY_REQUESTS_W,
        },
        "caching_layers": [
            {"layer": 1, "name": "服务端 prefix/KV cache", "what": "复用系统前缀的 prefill KV，跳过前缀重算",
             "quantified_by": "本脚本（命中率/省 token/省 prefill 时延）"},
            {"layer": 2, "name": "应用层 精确+语义 响应缓存", "what": "相同/近似 prompt 直接复用推理结果（cache.py）",
             "quantified_by": "/api/llm/cache/stats（命中率/累计省时）"},
        ],
        "series": series,
        "note": (
            "演示估算口径：prefix/query token 数、distinct 前缀数、prefill 算力(12ms/1k)与自托管单价"
            "为假设值；命中率由流量结构（5 业务域 × 2000 请求，zipf 倾斜）真实仿真得出。"
            "前缀缓存命中率≈" + f"{(hit_rate*100):.2f}%" + "，月度（500万请求）可省约 ¥"
            + f"{monthly_cost_saved:,.0f}" + " 的 prefill 算力，呼应黄超「成本控制·自负盈亏」——"
            "把大模型成本压到可私有化、可量化的水平。"
        ),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def _zipf(prefixes):
    n = len(prefixes)
    w = np.array([1.0 / (i + 1) for i in range(n)], dtype=float)
    return (w / w.sum()).tolist()


def main():
    rep = simulate()
    OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    s = rep["summary"]
    print("✅ Prompt Cache 仿真完成 →", OUT)
    print(f"   前缀缓存命中率 : {s['prefix_cache_hit_rate']*100:.2f}%")
    print(f"   节省 token      : {s['tokens_saved']:,}（占全量 {s['tokens_saved_pct']*100:.1f}%）")
    print(f"   节省 prefill    : {s['latency_saved_ms']:.0f} ms / 本轮")
    print(f"   TTFT 下降       : {s['ttft_reduction_pct']*100:.1f}%")
    print(f"   月省 prefill 成本(500万请求): ¥{s['monthly_cost_saved_at_500w']:,.0f}")


if __name__ == "__main__":
    main()
