"""
算法侧 R&D（三）：投机解码 / 推测解码（Speculative Decoding）——
用字符级 n-gram 语言模型**真实可跑、可复现、可度量**地演示核心思想（纯 numpy，无 GPU / 框架）。

为什么这样设计（面试可讲）：
  自回归解码每生成 1 个 token 就要跑 1 次大模型（Target），延迟被「串行的大模型调用次数」卡住。
  投机解码用一个便宜的小模型（Draft）一次性「猜」k 个 token，再让大模型**一次并行前向**校验这 k 个：
  从头比对，接受最长的一致前缀；第一个不一致处用大模型自己的结果纠正。
  只要草稿命中率够高，就能用「更少的大模型调用次数」生成同样多的 token —— 输出分布与 Target 单独解码**完全一致**（无损加速）。

  本脚本：
    Target = 字符三元组（order-2）模型（更准、更贵）
    Draft  = 字符二元组（order-1）模型（更省、更快）
    对比「纯自回归（每步 1 次 Target）」 vs 「投机解码（每轮 1 次 Target 并行校验 k 个）」，
    度量：草稿接受率、Target 调用次数、理论加速比（Target 调用为主导成本时）。

产出：sft/data/speculative_report.json（被 /api/opt/speculative-report 与前端可视化页读取）

跑法：
  python sft/speculative.py
"""
from __future__ import annotations

import json
import time
from collections import defaultdict, Counter
from pathlib import Path

import numpy as np

from distill_compress import _load, DATA_DIR

REPORT = DATA_DIR / "speculative_report.json"


class NGram:
    """字符级 n-gram 语言模型（greedy argmax 下一个字符）。order=1→bigram，order=2→trigram。"""

    def __init__(self, order: int):
        self.order = order
        self.table: dict[str, Counter] = defaultdict(Counter)

    def fit(self, texts):
        for t in texts:
            t = "^" * self.order + (t or "") + "$"
            for i in range(len(t) - self.order):
                ctx = t[i:i + self.order]
                nxt = t[i + self.order]
                self.table[ctx][nxt] += 1
        return self

    def next_char(self, ctx: str) -> str:
        ctx = ctx[-self.order:]
        c = self.table.get(ctx)
        if not c:
            # 回退：用更短上下文里最常见的字符
            return "$"
        return c.most_common(1)[0][0]


def autoregressive(target: NGram, prompt: str, n_new: int):
    """纯自回归：每生成 1 字符 = 1 次 Target 调用。返回 (生成串, target_calls)。"""
    seq = prompt
    calls = 0
    for _ in range(n_new):
        nxt = target.next_char(seq)
        calls += 1
        if nxt == "$":
            break
        seq += nxt
    return seq[len(prompt):], calls


def speculative(target: NGram, draft: NGram, prompt: str, n_new: int, k: int = 4):
    """投机解码：Draft 一次提议 k 个字符，Target 并行校验（1 次调用等价校验 k+1 个位置）。
    接受最长一致前缀；首个不一致处用 Target 结果纠正。输出与纯 Target 自回归完全一致（无损）。
    返回 (生成串, target_calls, draft_calls, accepted, proposed)。
    """
    seq = prompt
    target_calls = 0
    draft_calls = 0
    accepted = 0
    proposed = 0
    produced = 0
    while produced < n_new:
        # 1) Draft 连续提议 k 个字符
        draft_seq = seq
        proposals = []
        for _ in range(k):
            d = draft.next_char(draft_seq)
            draft_calls += 1
            proposals.append(d)
            draft_seq += d
        proposed += len(proposals)

        # 2) Target 一次并行校验：逐位置比对 Target 的 argmax 与 Draft 提议
        target_calls += 1  # 一轮并行前向（真实系统里是一次 batched forward）
        cur = seq
        matched = 0
        for d in proposals:
            t = target.next_char(cur)
            if t == d and t != "$":
                cur += d
                matched += 1
                produced += 1
                if produced >= n_new:
                    break
            else:
                # 首个不一致：采用 Target 的结果（纠正），本轮结束
                if t != "$" and produced < n_new:
                    cur += t
                    produced += 1
                break
        accepted += matched
        # 结束条件：Target 想停
        if cur == seq:  # 一个都没产出（Target 直接给 $）
            break
        seq = cur

    return seq[len(prompt):], target_calls, draft_calls, accepted, proposed


def main():
    Xtr_txt, _ = _load(DATA_DIR / "train.jsonl")
    Xte_txt, _ = _load(DATA_DIR / "test.jsonl")
    if not Xtr_txt:
        print("[!] 未找到训练数据，请先运行 python sft/dataset.py")
        return

    corpus = Xtr_txt + Xte_txt
    target = NGram(order=2).fit(corpus)  # trigram：更准更贵
    draft = NGram(order=1).fit(corpus)   # bigram：更省更快

    # 用测试集里若干提示前缀做生成对比
    rng = np.random.default_rng(7)
    prompts = []
    for t in Xte_txt:
        if len(t) >= 6:
            prompts.append(t[:3])
    rng.shuffle(prompts)
    prompts = prompts[:60] or ["我要申"]

    N_NEW = 24
    K = 4

    # 一致性校验 + 计数
    tot_ar_calls = 0
    tot_sp_target = 0
    tot_sp_draft = 0
    tot_accepted = 0
    tot_proposed = 0
    identical = 0
    for p in prompts:
        ar_txt, ar_calls = autoregressive(target, p, N_NEW)
        sp_txt, sp_t, sp_d, acc, prop = speculative(target, draft, p, N_NEW, k=K)
        tot_ar_calls += ar_calls
        tot_sp_target += sp_t
        tot_sp_draft += sp_d
        tot_accepted += acc
        tot_proposed += prop
        if ar_txt == sp_txt:
            identical += 1

    accept_rate = tot_accepted / max(tot_proposed, 1)
    # 加速比：以 Target 调用为主导成本（大模型 >> 小模型）
    speedup_target_only = tot_ar_calls / max(tot_sp_target, 1)
    # 计入 Draft 成本（假设 Draft 成本 = Target 的 1/8）
    draft_cost_ratio = 1 / 8
    eff_cost_sp = tot_sp_target + tot_sp_draft * draft_cost_ratio
    speedup_effective = tot_ar_calls / max(eff_cost_sp, 1e-6)

    report = {
        "method": "投机解码 / 推测解码（Speculative Decoding）",
        "framework": "纯 numpy 字符级 n-gram 模拟，无 GPU / 无框架，CPU 秒级复现",
        "models": {
            "target": "字符 trigram（order-2，更准更贵）",
            "draft": "字符 bigram（order-1，更省更快）",
        },
        "config": {"prompts": len(prompts), "n_new_per_prompt": N_NEW, "draft_k": K,
                    "assumed_draft_cost_ratio": draft_cost_ratio},
        "result": {
            "autoregressive_target_calls": int(tot_ar_calls),
            "speculative_target_calls": int(tot_sp_target),
            "speculative_draft_calls": int(tot_sp_draft),
            "accept_rate": round(accept_rate, 4),
            "speedup_target_calls_only": round(speedup_target_only, 2),
            "speedup_effective_with_draft_cost": round(speedup_effective, 2),
            "output_identical_ratio": round(identical / len(prompts), 4),
        },
        "note": "投机解码是「无损」加速：输出分布与 Target 单独解码一致（本模拟中 argmax 完全一致）。"
                "接受率越高、加速越大；草稿模型越接近目标（可用蒸馏得到的小模型当 Draft），命中率越高。",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("==================  投机解码（Speculative Decoding）  ==================")
    print(f"提示数={len(prompts)}  每条生成={N_NEW}  草稿步长 k={K}")
    print(f"自回归 Target 调用总数     : {tot_ar_calls}")
    print(f"投机解码 Target 调用总数   : {tot_sp_target}   (Draft 调用 {tot_sp_draft})")
    print(f"草稿接受率                 : {accept_rate*100:.1f}%")
    print(f"加速比（仅算 Target 调用） : {speedup_target_only:.2f}x")
    print(f"加速比（计入 Draft 成本）  : {speedup_effective:.2f}x")
    print(f"输出与自回归完全一致比例   : {identical/len(prompts)*100:.1f}%  （无损加速验证）")
    print(f"\n报告已写入：{REPORT}")


if __name__ == "__main__":
    main()
