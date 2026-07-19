"""
算法侧 R&D（二）：模型剪枝（Magnitude Pruning）——在「审计运维意图识别」的
Student 分类器上**真实可跑、可复现、可度量**（纯 numpy，无需 GPU / 框架）。

为什么这样设计（面试可讲）：
  剪枝与量化是「模型压缩」的两条正交路线：量化降的是「每个权重的比特数」，
  剪枝降的是「非零权重的个数」。对稀疏度高的层，用稀疏存储（值 + 索引）能进一步减小
  体积、减少乘加次数。工程上常见「先剪枝再量化」的组合拳。
  本脚本对蒸馏后的 Student 权重做**非结构化幅度剪枝**：按 |w| 从小到大置零，
  扫描不同稀疏度，度量「稀疏度 ↑ 时精度如何变化」，并给出在容忍掉点内的最大稀疏度、
  对应的稀疏存储体积与理论乘加削减比。

产出：sft/data/prune_report.json（被 /api/opt/prune-report 与前端可视化页读取）

跑法：
  python sft/prune.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

# 复用 distill_compress 的公共函数（同一套特征/训练/评测口径）
from distill_compress import (
    _load, _featurize, _train_softmax, _predict, _acc, DATA_DIR,
)

REPORT = DATA_DIR / "prune_report.json"


def _prune_by_magnitude(W: np.ndarray, sparsity: float) -> np.ndarray:
    """非结构化幅度剪枝：把 |W| 最小的 sparsity 比例权重置零，返回剪枝后的权重副本。"""
    if sparsity <= 0:
        return W.copy()
    flat = np.abs(W).ravel()
    k = int(len(flat) * sparsity)
    if k <= 0:
        return W.copy()
    thresh = np.partition(flat, k)[k]  # 第 k 小的幅度作为阈值
    Wp = W.copy()
    Wp[np.abs(Wp) < thresh] = 0.0
    return Wp


def _sparse_bytes(W: np.ndarray) -> int:
    """稀疏存储体积估算（COO：每个非零 = 4B 值 + 4B 列索引 + 行指针忽略）。"""
    nnz = int(np.count_nonzero(W))
    return nnz * (4 + 4)


def main():
    Xtr_txt, ytr = _load(DATA_DIR / "train.jsonl")
    Xte_txt, yte = _load(DATA_DIR / "test.jsonl")
    if not Xtr_txt:
        print("[!] 未找到训练数据，请先运行 python sft/dataset.py")
        return

    labels = sorted(set(ytr) | set(yte))
    lab2id = {l: i for i, l in enumerate(labels)}
    n_cls = len(labels)
    ytr_id = np.array([lab2id[y] for y in ytr])
    yte_id = np.array([lab2id[y] for y in yte])
    Ytr_oh = np.eye(n_cls, dtype=np.float32)[ytr_id]

    STUDENT_DIM = 512
    print(f"样本：train={len(ytr)} test={len(yte)} | 意图类别={n_cls} | Student dim={STUDENT_DIM}")

    Xtr = _featurize(Xtr_txt, STUDENT_DIM)
    Xte = _featurize(Xte_txt, STUDENT_DIM)

    # 训练一个稠密 Student（全量数据），作为剪枝基线
    W, b = _train_softmax(Xtr, Ytr_oh, n_cls, epochs=120, lr=0.5)
    dense_acc = _acc(_predict(Xte, W, b), yte_id)
    dense_nnz = int(np.count_nonzero(W))
    dense_bytes = int(W.nbytes)  # fp32 dense

    print(f"\n稠密基线：acc={dense_acc:.4f}  params={W.size}  size={dense_bytes/1024:.1f}KB")
    print("\n==================  幅度剪枝 稀疏度扫描  ==================")
    print(f"{'sparsity':>9} | {'test_acc':>8} | {'nnz':>7} | {'sparse_KB':>9} | {'Δacc':>7}")

    sweep = []
    TOL = 0.01  # 容忍掉点 1pt
    best_sparsity = 0.0
    for sp in [0.0, 0.5, 0.7, 0.8, 0.9, 0.95, 0.98, 0.99, 0.995, 0.999]:
        Wp = _prune_by_magnitude(W, sp)
        acc = _acc(_predict(Xte, Wp, b), yte_id)
        nnz = int(np.count_nonzero(Wp))
        sbytes = _sparse_bytes(Wp)
        dacc = acc - dense_acc
        sweep.append({
            "sparsity": sp,
            "test_acc": round(acc, 4),
            "nnz": nnz,
            "sparse_kb": round(sbytes / 1024, 1),
            "acc_delta_vs_dense": round(dacc, 4),
        })
        if acc >= dense_acc - TOL:
            best_sparsity = max(best_sparsity, sp)
        print(f"{sp:>9.3f} | {acc:>8.4f} | {nnz:>7} | {sbytes/1024:>8.1f}K | {dacc:>+7.4f}")

    # 在容忍掉点内的最大稀疏度对应指标
    best = next(s for s in reversed(sweep) if s["sparsity"] == best_sparsity)
    mac_reduction = round(1.0 / (1.0 - best_sparsity), 1) if best_sparsity < 1 else float("inf")

    report = {
        "task": "审计运维意图识别（14 类）",
        "method": "非结构化幅度剪枝（Magnitude Pruning）",
        "framework": "纯 numpy，无 GPU / 无框架，CPU 秒级复现",
        "dense_baseline": {
            "test_acc": round(dense_acc, 4),
            "params": int(W.size),
            "size_kb": round(dense_bytes / 1024, 1),
            "nnz": dense_nnz,
        },
        "sweep": sweep,
        "tolerance_pt": TOL,
        "best_sparsity_within_tol": best_sparsity,
        "best": best,
        "theoretical_mac_reduction": mac_reduction,  # 稀疏乘加削减比（1/(1-稀疏度)）
        "note": "剪枝降非零权重个数（与量化的降比特正交），高稀疏时配稀疏存储/稀疏算子可进一步减小体积与乘加次数；工程常用「先剪枝再量化」组合。",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("--------------------------------------------------------------------------")
    print(f"容忍掉点 {TOL*100:.0f}pt 内最大稀疏度：{best_sparsity*100:.0f}%  "
          f"(acc={best['test_acc']:.4f}, 稀疏存储 {best['sparse_kb']}KB, 理论乘加削减 {mac_reduction}x)")
    print(f"报告已写入：{REPORT}")


if __name__ == "__main__":
    main()
