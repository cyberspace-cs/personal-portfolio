"""
强化学习对齐（RLHF）偏好优化 · 纯 numpy/CPU 可复现仿真
================================================================

把「大模型对齐」从 PPO 到 DPO 再到 GRPO 的演进，落到一个 2D 偏好分类任务上，
用 numpy 真跑、可复现、秒级完成，并输出结构化报告供前端可视化与面试讲解。

为什么用 2D 偏好任务？
- 对齐的本质是「在偏好数据/环境反馈下，把策略 π_θ 调整到更符合人类/AI 偏好的方向」。
- 我们用一个 4 维特征 φ(x,y)=[x;y]（x=提示，y=候选回答 embedding），
  地面真值方向 w* 定义「什么是好回答」。三种方法都据此训练同一类线性策略 π_θ，
  从而可比：谁收敛更快、更稳、需要多少「在线采样」与「额外模型」。

三种方法（均优化 π_θ，但机制不同）：
1) DPO（Direct Preference Optimization，2023）
   - 输入：离线偏好对 (x, y_w, y_l)，无需奖励模型、无需在线采样。
   - 机制：用「策略与参考策略的 logprob 差」构造隐式奖励，做分类式损失。
   - 公式：L = -E log σ( β·[(logπ_θ(y_w|x)-logπ_ref(y_w|x)) - (logπ_θ(y_l|x)-logπ_ref(y_l|x))] )
   - 优点：离线、稳定、只 2 个模型（policy+ref）、省显存、易复现。
   - 缺点：受静态偏好数据质量限制、无法在线探索新行为、可能过拟合偏好。

2) PPO（RLHF 经典，2017/2022）
   - 输入：在线环境（用奖励模型 RM 打分），需 4 个模型（policy/value/ref/RM）。
   - 机制：采样 → RM 给奖励 → 带基线 + KL 惩罚的裁剪代理目标（clipped surrogate）更新。
   - 优点：可在线探索、上限高、能用可验证奖励。
   - 缺点：训练不稳、显存大、超参敏感、工程复杂。

3) GRPO（Group Relative Policy Optimization，2024，DeepSeek-R1）
   - 输入：在线环境，但「去掉 value 模型」，用同 prompt 的 G 个采样输出的组内相对优势。
   - 机制：对每组采样 {y_1..y_G}，优势 A_i=(r_i-μ_g)/σ_g，再裁剪更新。
   - 优点：比 PPO 省一个 value 模型（显存/工程更轻），适合可验证奖励（math/code）。
   - 缺点：每个 prompt 需多次采样（group size），吞吐与采样预算更高。

输出：sft/data/rl_report.json —— 含三法的最终准确率、收敛步数、稳定性、loss/acc 曲线、
对比表、以及「上下游关系（Pretrain→SFT→RM→对齐→部署优化）」阐述，供 rl-alignment.html 渲染。
"""

import json
import os
import datetime
from typing import Dict, List

import numpy as np

_BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_BASE, "data")
REPORT_FILE = os.path.join(DATA_DIR, "rl_report.json")

K = 6                 # 候选回答数（固定词表）
DIM = 4              # 特征维度 φ(x,y)=[x;y]，x,y ∈ R^2
TRAIN_PAIRS = 240
TEST_PAIRS = 120
STEPS = 300
SEED = 20260720


def _features(x: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """φ(x,y)=[x;y]，返回 (K, DIM)。"""
    return np.concatenate([np.tile(x, (K, 1)), Y], axis=1)


def _logprobs(theta: np.ndarray, F: np.ndarray) -> np.ndarray:
    z = F @ theta
    z = z - z.max()
    e = np.exp(z)
    return z - np.log(e.sum())


def _make_pairs(w_star: np.ndarray, Y: np.ndarray, n: int, rng: np.random.RandomState):
    """生成偏好对：y_w 优于 y_l 当且仅当 w_star·φ(x,y_w) > w_star·φ(x,y_l)。"""
    pairs = []
    for _ in range(n):
        x = rng.randn(2) * 0.8
        i, j = rng.choice(K, 2, replace=False)
        fw = w_star @ _features(x, Y)[i]
        fl = w_star @ _features(x, Y)[j]
        if fw >= fl:
            yw, yl = i, j
        else:
            yw, yl = j, i
        pairs.append((x, yw, yl))
    return pairs


def _acc_of(theta: np.ndarray, Y: np.ndarray, pairs):
    """策略隐式偏好是否匹配地面真值（更高 π_θ(y_w) 即判定为偏好 y_w）。"""
    if not pairs:
        return 0.0
    ok = 0
    for x, yw, yl in pairs:
        F = _features(x, Y)
        lp = _logprobs(theta, F)
        if lp[yw] >= lp[yl]:
            ok += 1
    return ok / len(pairs)


def _dpo(w_star, Y, train, test, rng):
    theta = (rng.randn(DIM) * 0.1).astype(np.float64)
    theta0 = theta.copy()                       # 冻结参考策略
    lr, beta = 0.06, 0.6
    acc_curve, loss_curve = [], []
    steps_to_90 = None
    for step in range(STEPS):
        # 小批量
        idx = rng.choice(len(train), size=min(32, len(train)), replace=False)
        g = np.zeros(DIM)
        loss = 0.0
        for i in idx:
            x, yw, yl = train[i]
            F = _features(x, Y)
            lp = _logprobs(theta, F)
            diff = (lp[yw] - lp[yl]) - (lp[yw] - lp[yl])  # 占位，下面用 ref 差
            # 隐式奖励差（含参考策略）
            r = beta * ((lp[yw] - theta0 @ F[yw]) - (lp[yl] - theta0 @ F[yl]))
            # dL/dθ = (σ(r)-1)·β·(f_w - f_l)
            f_diff = F[yw] - F[yl]
            g += (1.0 / (1.0 + np.exp(-r)) - 1.0) * beta * f_diff
            loss += -np.log(1.0 / (1.0 + np.exp(-r)))
        theta -= lr * g / len(idx)
        acc = _acc_of(theta, Y, test)
        acc_curve.append(round(acc, 4))
        loss_curve.append(round(float(loss) / len(idx), 4))
        if steps_to_90 is None and acc >= 0.90:
            steps_to_90 = step + 1
    return {
        "final_acc": round(_acc_of(theta, Y, test), 4),
        "steps_to_90": steps_to_90,
        "stability": round(float(np.std(acc_curve[-20:])), 4),
        "acc_curve": acc_curve,
        "loss_curve": loss_curve,
        "online_sampling": False,
        "extra_models": "ref 仅冻结（不训练）",
        "needs_reward_model": False,
    }


def _ppo(w_star, Y, train, test, rng):
    theta = (rng.randn(DIM) * 0.1).astype(np.float64)
    theta0 = theta.copy()
    v = np.zeros(2)                              # value 网络（线性，基线是 PPO 独有负担）
    lr, beta_kl, eps = 0.08, 0.01, 0.2
    acc_curve, loss_curve = [], []
    steps_to_90 = None
    for step in range(STEPS):
        x, _, _ = train[rng.randint(len(train))]
        F = _features(x, Y)
        lp = _logprobs(theta, F)
        # 在线采样一个回答
        probs = np.exp(lp - lp.max()); probs /= probs.sum()
        yi = rng.choice(K, p=probs)
        # 奖励模型 RM = w_star·φ（地面真值方向，仅打分用）
        r = float(np.tanh(w_star @ F[yi]))
        baseline = float(v @ x)
        adv = r - baseline
        # 裁剪代理目标
        lp_old = _logprobs(theta, F)[yi]
        ratio = np.exp(lp[yi] - lp_old)
        unclipped = ratio * adv
        clipped = np.clip(ratio, 1 - eps, 1 + eps) * adv
        obj = -min(unclipped, clipped)           # 负号：最小化
        # 梯度（对选中的 yi）
        f = F[yi]
        d_obj = -(1.0 if unclipped <= clipped else 0.0) * adv * ratio * f
        # KL 惩罚项（对整体分布）
        kl_grad = beta_kl * (np.exp(lp)[:, None] * (F - (np.exp(lp)[:, None] * F).sum(0))) .sum(0)
        theta -= lr * (d_obj + kl_grad)
        # 更新 value
        v -= 0.08 * (baseline - r) * x
        acc = _acc_of(theta, Y, test)
        acc_curve.append(round(acc, 4))
        loss_curve.append(round(float(obj), 4))
        if steps_to_90 is None and acc >= 0.90:
            steps_to_90 = step + 1
    return {
        "final_acc": round(_acc_of(theta, Y, test), 4),
        "steps_to_90": steps_to_90,
        "stability": round(float(np.std(acc_curve[-20:])), 4),
        "acc_curve": acc_curve,
        "loss_curve": loss_curve,
        "online_sampling": True,
        "extra_models": "value 网络 + ref（PPO 需 4 模型：policy/value/ref/RM）",
        "needs_reward_model": True,
    }


def _grpo(w_star, Y, train, test, rng, G=4):
    theta = (rng.randn(DIM) * 0.1).astype(np.float64)
    theta0 = theta.copy()
    lr, beta_kl, eps = 0.05, 0.02, 0.2
    acc_curve, loss_curve = [], []
    steps_to_90 = None
    for step in range(STEPS):
        x, _, _ = train[rng.randint(len(train))]
        F = _features(x, Y)
        lp = _logprobs(theta, F)
        probs = np.exp(lp - lp.max()); probs /= probs.sum()
        ys = rng.choice(K, size=G, replace=True, p=probs)
        rewards = np.array([float(np.tanh(w_star @ F[y])) for y in ys])
        mu, sd = rewards.mean(), rewards.std() + 1e-8
        # 组内相对优势（GRPO 关键：无需 value 网络）
        advs = (rewards - mu) / sd
        lp_old = _logprobs(theta, F)
        g = np.zeros(DIM)
        obj = 0.0
        for yi, adv in zip(ys, advs):
            ratio = np.exp(lp[yi] - lp_old[yi])
            unclipped = ratio * adv
            clipped = np.clip(ratio, 1 - eps, 1 + eps) * adv
            obj += -min(unclipped, clipped)
            use = 1.0 if unclipped <= clipped else 0.0
            g += -(use * adv * ratio) * F[yi]
        obj /= G
        g /= G
        # KL 惩罚
        kl_grad = beta_kl * (np.exp(lp)[:, None] * (F - (np.exp(lp)[:, None] * F).sum(0))).sum(0)
        theta -= lr * (g + kl_grad)
        acc = _acc_of(theta, Y, test)
        acc_curve.append(round(acc, 4))
        loss_curve.append(round(float(obj), 4))
        if steps_to_90 is None and acc >= 0.90:
            steps_to_90 = step + 1
    return {
        "final_acc": round(_acc_of(theta, Y, test), 4),
        "steps_to_90": steps_to_90,
        "stability": round(float(np.std(acc_curve[-20:])), 4),
        "acc_curve": acc_curve,
        "loss_curve": loss_curve,
        "online_sampling": True,
        "extra_models": "无 value 网络（仅 policy+ref，group-relative 基线）",
        "needs_reward_model": True,
    }


def run_alignment(seed: int = SEED) -> Dict:
    """运行 DPO/PPO/GRPO 仿真，返回完整报告 dict。"""
    rng = np.random.RandomState(seed)
    w_star = rng.randn(DIM); w_star /= np.linalg.norm(w_star)
    Y = rng.randn(K, 2)
    train = _make_pairs(w_star, Y, TRAIN_PAIRS, rng)
    test = _make_pairs(w_star, Y, TEST_PAIRS, rng)

    dpo = _dpo(w_star, Y, train, test, rng)
    ppo = _ppo(w_star, Y, train, test, rng)
    grpo = _grpo(w_star, Y, train, test, rng)

    comparison = [
        {"method": "PPO (RLHF)", "mode": "在线 RL", "final_acc": ppo["final_acc"],
         "steps_to_90": ppo["steps_to_90"], "stability": ppo["stability"],
         "extra_models": ppo["extra_models"], "sampling": "需在线采样",
         "pros": "可在线探索、上限高、适配可验证奖励", "cons": "4 模型、训练不稳、超参敏感、显存大"},
        {"method": "DPO (2023)", "mode": "离线偏好", "final_acc": dpo["final_acc"],
         "steps_to_90": dpo["steps_to_90"], "stability": dpo["stability"],
         "extra_models": dpo["extra_models"], "sampling": "纯离线数据",
         "pros": "稳定、省显存(2 模型)、易复现、无 reward 循环", "cons": "受静态偏好数据质量限制、无法探索"},
        {"method": "GRPO (2024)", "mode": "在线 RL", "final_acc": grpo["final_acc"],
         "steps_to_90": grpo["steps_to_90"], "stability": grpo["stability"],
         "extra_models": grpo["extra_models"], "sampling": "需在线采样(G 个)",
         "pros": "去 value 模型(省显存)、适合 math/code 可验证奖励", "cons": "每 prompt 多次采样、采样预算高"},
    ]

    pipeline = [
        {"stage": "1. Pretrain（预训练）", "io": "海量无标注语料 → Base Model",
         "desc": "自监督学习语言/世界知识，得到基座模型。对齐的「上游」，决定模型能力天花板。"},
        {"stage": "2. SFT（监督微调）", "io": "(指令, 回答) 数据集 → SFT Model",
         "desc": "用人工/蒸馏指令数据教会模型「遵循指令、输出规范格式」，是对齐的起点。"},
        {"stage": "3. Reward Model（奖励模型）", "io": "人类偏好对 (chosen/rejected) → RM",
         "desc": "用 Bradley-Terry 训练一个标量奖励模型，给回答打分。PPO/GRPO 的在线奖励来源；DPO 不需要。"},
        {"stage": "4. 对齐（RLHF / DPO / GRPO）", "io": "SFT Model + RM/偏好 → Aligned Model",
         "desc": "核心：把策略 π_θ 调整到符合偏好。PPO 在线 RL 需 RM+value+ref；DPO 离线直接用偏好；GRPO 用组内相对优势去 value。"},
        {"stage": "5. 部署优化（本项目定位）", "io": "Aligned Model → 低成本高并发服务",
         "desc": "蒸馏/INT8/剪枝/投机解码/Prompt Cache 把对齐好的模型高效 serve（见优化实验台）。整条链路的「最下游」。"},
    ]

    return {
        "meta": {
            "task": "2D 偏好分类（对齐方法的统一可比测试台）",
            "feature_dim": DIM, "candidates": K,
            "train_pairs": TRAIN_PAIRS, "test_pairs": TEST_PAIRS, "steps": STEPS,
            "seed": seed,
            "note": "纯 numpy/CPU 仿真：三种方法训练同一类线性策略 π_θ，比较收敛/稳定/所需机制。",
        },
        "methods": {"dpo": dpo, "ppo": ppo, "grpo": grpo},
        "comparison": comparison,
        "pipeline": pipeline,
        "takeaways": [
            "上下游关系：Pretrain→SFT→(RM)→对齐(PPO/DPO/GRPO)→部署优化 是一条单向依赖链；"
            "越往下游越贴近「可用、可上线」，本项目落在最下游——把对齐好的模型低成本 serve 出来。",
            "DPO 用「离线偏好 + 隐式奖励」替代 PPO 的「在线 RL + 显式 RM + value」，少两个模型、更稳更易复现；"
            "代价是无法在线探索新行为，质量受偏好数据上限约束。",
            "GRPO 保留 PPO 的在线探索能力，但用「组内相对优势」去掉 value 网络，显存与工程更轻，"
            "特别适合可验证奖励（数学/代码/工具调用），已被 DeepSeek-R1 验证。",
            "工程取舍：追求稳定与低成本 → DPO；追求上限与可验证奖励 → GRPO/PPO；"
            "我们的推理优化层（蒸馏/量化/投机解码）对任何对齐产物都通用，是「对齐之后」必做的降本增效。",
        ],
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    rep = run_alignment()
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print("RL 对齐报告已生成：", REPORT_FILE)
    m = rep["methods"]
    for k in ("dpo", "ppo", "grpo"):
        print(f"  {k.upper():4s} final_acc={m[k]['final_acc']:.3f} steps_to_90={m[k]['steps_to_90']} stability={m[k]['stability']:.4f}")


if __name__ == "__main__":
    main()
