# 大模型推理加速与模型优化技术栈（Audit-AIOPS 落地说明）

> 面试与研发双用途文档。本文把「算法优化 / 大模型加速推理优化」中的主流技术，逐一对应到
> Audit-AIOPS 的真实代码实现或上线方案，避免只停留在口头概念。配套面试题见
> `面试-优化技术面试题库.md`。

---

## 0. 为什么要在本项目讲优化

审计运维场景对 **成本、延迟、私有化/合规部署** 敏感：
- 一线同事口语化提诉求，很多是重复问题（"Ukey 怎么申请""审批到哪了"），重复推理是浪费；
- 生产要压低单次调用成本、提升并发；
- 涉密内网倾向私有化小模型，而非每次走公网大模型 API。

因此本项目把"加速推理"拆成 **不碰权重的三类（缓存/批处理/路由）** + **动权重的压缩三类（量化/蒸馏/剪枝）**，形成完整技术栈。

---

## 1. 缓存复用（应用层 KV / Prompt Cache）—— 已实现 ✅

**技术**：KV Cache 本质是复用已计算的 Key/Value 避免重复前向。在应用层同理可复用"已推理过的提示结果"。
**本项目实现**：`app/llm/cache.py`
- `PromptCache`：对 `(provider, system, user)` 归一化哈希做精确 LRU 命中 —— 等价于把 KV 留在提示前缀上。
- `SemanticCache`：用稠密向量表示提示，cos 相似度 ≥ 阈值即复用 —— 放大命中率（问答/意图识别这类高重复场景收益最大）。
- 已接入 `app/llm/client.py` 的 `_chat()`：真实模型调用前先查缓存，命中直接返回，未命中回写。
- 演示端点：`POST /api/llm/cache/demo`（模拟 800ms 推理，二次同/近似提示命中缓存，省去耗时）、`GET /api/llm/cache/stats`（命中率）。

**收益口径**：高频 FAQ 场景命中率可达 30%~70%，等价于把这部分流量的 TTFT 从数百 ms 降到 ~1ms、成本降到 0。

---

## 2. 量化（Quantization）—— 端到端真实可跑 ✅✅

**技术**：把权重从 FP32/FP16 压到 INT8 / NF4(4-bit)，降显存与带宽、提吞吐。
**本项目实现（两层）**：
- **真实可复现（CPU，无需 GPU）**：`sft/distill_compress.py` 对蒸馏出的学生模型权重做 **INT8 对称量化（per-channel scale）**，实测：
  - 体积 fp32 → int8 **≈3.95×**（≈理论 4×）；掉点 **0.0pt**（准确率 100.0% 保持）；
  - 学生 INT8 单样本 CPU 延迟 ~0.0006ms，Teacher→INT8 学生整体 **体积压缩 63×、提速 10.8×、精度保持 100%**。
  - 一行复现：`python sft/distill_compress.py` → 写入 `sft/data/distill_report.json`，前端页 `/optimization.html` 实时读取。
- **大模型上线模板**：训练侧 `sft/train.py` 的 **QLoRA**（NF4+双重量化，单卡 12~16GB 可训 7B~13B）；推理侧 `sft/quantize.py`（4/8-bit 部署，`BitsAndBytesConfig`，可挂 LoRA 适配器）。口径：FP16 7B ≈14GB → 4-bit ≈4~5GB。

---

## 3. 知识蒸馏（Knowledge Distillation）—— 端到端真实可跑 ✅✅

**技术**：用强教师的"软标签"训练小学生，温度 T 软化概率、迁移「暗知识」；标注预算受限时，教师可对未标注样本打软标签（半监督蒸馏），显著提升小模型。
**本项目实现（两层）**：
- **真实可复现（CPU，纯 numpy，无框架）**：`sft/distill_compress.py` 在「审计运维意图识别（14 类，1800/200）」上完整跑通 **Teacher → 蒸馏 → Student → INT8** 链路：
  - Teacher（字符级哈希特征 dim=8192，softmax，全量训练）测试 acc **100.0%**；
  - Student（dim=512）**仅 42 条人工标签** 时 acc **95.0%**；
  - 加入 Teacher 对全量样本的软标签（T=3.0，α 混合）蒸馏后 acc **100.0%** → **蒸馏增益 +5.0pt**；
  - 损失：`α·CE(hard) + (1-α)·T²·CE(soft_teacher)`（经典 Hinton KD，梯度按 T² 缩放）。
  - 复现：`python sft/distill_compress.py`；结果经 `/api/opt/distill-report` 与 `/optimization.html` 可视化。
- **大模型上线模板**：`sft/distill.py`（Qwen-72B/混元 教师 → Qwen2.5-1.5B/0.5B 学生，KL+CE 损失），把意图识别/要素抽取等轻任务蒸馏到可私有化/边缘部署的小模型。

---

## 4. 低参微调（LoRA / QLoRA）—— 已实现 ✅

**技术**：只训低秩适配矩阵，冻结底座，显存友好、可热插拔、多任务并存。
**本项目实现**：`sft/train.py` 的 `LoraConfig`（r=16，target q/k/v/o_proj），与量化（见 2）一体。

---

## 5. 模型剪枝（Pruning）—— 端到端真实可跑 ✅✅

**技术**：结构化/非结构化剪枝去掉冗余权重/注意力头。剪枝降的是「非零权重个数」，与量化的「降比特」正交；高稀疏时配稀疏存储/稀疏算子进一步减体积与乘加次数。
**本项目实现（真实可复现，CPU，纯 numpy）**：`sft/prune.py` 对 Student（dim=512）做 **非结构化幅度剪枝**，按 |w| 从小到大置零，扫描稀疏度得到真实「精度-稀疏度」权衡曲线：

| 稀疏度 | 测试 acc | 非零权重 | 稀疏存储 | Δacc |
|---|---|---|---|---|
| 0% (稠密) | 100.0% | 4662 | 36.4KB | — |
| 90% | 100.0% | 717 | 5.6KB | 0.0 |
| **98%** | **100.0%** | **144** | **1.1KB** | **0.0（拐点前）** |
| 99% | 95.5% | 74 | 0.6KB | −4.5pt |
| 99.5% | 87.5% | 36 | 0.3KB | −12.5pt |
| 99.9% | 44.5% | 8 | 0.1KB | −55.5pt |

- **结论**：容忍掉点 1pt 内最大稀疏度 **98%**，对应 **理论乘加削减 50×**、稀疏存储仅 1.1KB；99% 后精度断崖 —— 这就是可讲的「剪枝拐点」。
- 复现：`python sft/prune.py` → 写 `sft/data/prune_report.json`，经 `/api/opt/prune-report` 与 `/optimization.html` 可视化。
- 工程组合：常用「先剪枝再量化」，本项目 Student 已可 98% 稀疏 + INT8 叠加压缩。

---

## 6. 投机解码（Speculative Decoding）—— 端到端真实可跑 ✅✅

**技术**：用便宜的草稿模型(draft)一次并行猜 k 个 token，昂贵的目标模型(target)一次并行校验、接受最长一致前缀，第一个不一致处用 target 结果纠正 —— 用**更少的大模型调用**生成同样多 token，且**输出分布与 target 单独解码完全一致（无损加速）**。
**本项目实现（真实可复现，CPU，纯 numpy 字符级 n-gram 模拟）**：`sft/speculative.py`
- Target = 字符 trigram（order-2，更准更贵）；Draft = 字符 bigram（order-1，更省更快）；草稿步长 k=4。
- 实测（60 条提示，每条生成 24 字符）：**草稿接受率 39.5%**，Target 调用 410 → **192 次**，**加速比 2.14×**（仅算 Target 调用）/ **1.42×**（Draft 成本按 Target 的 1/8 计）；**输出与自回归 100% 一致（无损验证）**。
- 复现：`python sft/speculative.py` → 写 `sft/data/speculative_report.json`，经 `/api/opt/speculative-report` 与 `/optimization.html` 可视化。
- 与本项目协同：Draft 可直接用第 3 节蒸馏出的小模型（越接近 target 命中率越高），与缓存（见 1）叠加收益。

---

## 7. 批处理与请求路由（Batching / Routing）—— 架构已支撑 ✅

**技术**：连续批处理(continuous batching)提 GPU 利用率；按任务难度路由小/大模型降成本。
**本项目实现**：
- `app/llm/client.py` 的可插拔 provider（mock / 混元 / 千问）——天然支持"简单意图走小模型/规则、复杂问答走大模型"的路由；
- Agent 编排层 `app/agent/orchestrator.py` 把多意图拆成独立事项，天然适合批处理与并行路由。

---

## 8. 企业级并行（流水线 / 模型 / 上下文 / GPU 显存）+ 蒸馏压缩 —— 算法核心主线 ✅（概念仿真）

**技术**：压缩解决「模型小」，并行解决「小模型铺到多卡服务海量并发、把长上下文拆到多卡、把单卡显存打下来」。工业界真实落地顺序固定为 **压缩在前、并行在后**。

**本项目实现（真实可复现，CPU，纯 numpy 概念仿真）**：`sft/parallel.py` 用很小的代码讲清四类范式并和压缩成果组合：

| 范式 | 原理（仿真函数） | 实测 |
|---|---|---|
| 模型并行 / 张量并行 | `model_parallel()`：权重列切 N 卡，All-Gather 拼接 | 8 卡单卡参数比 **12.5%**，输出与单卡逐元素一致 ✓ |
| 流水线并行 | `pipeline_util()`：深度切段 + micro-batch 流水降空泡 | 深度12/微批16/4卡，利用率 **25%→84%（3.4×）** |
| 上下文并行 / 上下文压缩 | `context_parallel()`：长序列 KV 沿序列维切 N 卡 | 序列8192/KV维512，8 卡单卡 KV 比 **12.5%** |
| GPU 显存并行利用 | `memory_budget()`：量化×模型并行×上下文并行组合 | 7B 模型 4×4 并行：fp32 6.8GB → **INT8 1.7GB/卡 → INT4 0.85GB/卡** |

- **组合收益**：量化降比特 × 模型并行分权重 × 上下文并行分 KV，三者乘起来；再叠加本项目蒸馏/剪枝，单张 16/24GB 卡即可服务 7B 级大模型——**企业私有化低显存部署的核心证据**。
- 复现：`python sft/parallel.py` → 写 `sft/data/parallel_report.json`，经 `/api/opt/parallel-report` 与 `/optimization.html` §7 可视化。
- 完整范式与面试话术见 [`docs/enterprise-parallel-compression.md`](enterprise-parallel-compression.md)；向港大黄超团队(HKUDS)/nanobot 迁移学习见 [`docs/hkuds-transfer-learning.md`](hkuds-transfer-learning.md)。

---

## 落地总览（面试一句话）

> Audit-AIOPS 的推理加速是"组合拳"：应用层用 **Prompt/Semantic Cache** 复用高频结果（已实现、可 Demo），
> 训练侧用 **QLoRA** 低显存微调、推理侧用 **4-bit/8-bit 量化** 部署（已落地模板），
> 并用 **知识蒸馏 + INT8 量化 + 幅度剪枝** 把大模型能力压到可私有化的小模型（三条压缩线均端到端实测可复现），生成环节再叠加 **投机解码（无损加速 2.14×）**。
> **核心主线是把压缩后的小模型用「模型并行 + 流水并行 + 上下文并行」铺到多卡**：实测 7B 模型 INT8+4×4 并行单卡仅 1.7GB，fp32 单卡要 6.8GB——即「**压缩在前、并行在后**」的企业私有化落地范式。
> 整体在不牺牲准确率前提下，把高频场景的成本与延迟显著压低，支撑审计内网的合规私有化部署。

---

## 相关文件索引
| 技术 | 文件 | 状态 |
|------|------|------|
| 缓存复用 | `app/llm/cache.py`、`app/api/extra.py`(/api/llm/cache/*) | ✅ 已实现可跑 |
| **蒸馏（端到端实测）** | `sft/distill_compress.py`、`/api/opt/distill-report`、`/optimization.html` | ✅✅ CPU 真实可复现（+5pt 蒸馏增益） |
| **INT8 量化（端到端实测）** | `sft/distill_compress.py` | ✅✅ CPU 真实可复现（3.95× 压缩、0 掉点） |
| 量化（大模型模板） | `sft/quantize.py`、`sft/train.py`(QLoRA) | ✅ 模板可上线 |
| 蒸馏（大模型模板） | `sft/distill.py` | ✅ 模板可上线 |
| 低参微调 | `sft/train.py`(LoRA) | ✅ |
| **剪枝（端到端实测）** | `sft/prune.py`、`/api/opt/prune-report`、`/optimization.html` | ✅✅ CPU 真实可复现（98% 稀疏无损、50× 乘加削减） |
| **投机解码（端到端实测）** | `sft/speculative.py`、`/api/opt/speculative-report`、`/optimization.html` | ✅✅ CPU 真实可复现（接受率 39.5%、2.14× 加速、无损） |
| **企业级并行（概念仿真）** | `sft/parallel.py`、`/api/opt/parallel-report`、`/optimization.html` §7 | ✅ CPU 仿真（模型/流水/上下文并行 + 显存组合预算） |
| 批处理/路由 | `app/llm/client.py`、`app/agent/orchestrator.py` | ✅ 架构支撑 |
| 迁移学习(HKUDS/nanobot) | `docs/hkuds-transfer-learning.md` | ✅ 方法论对齐（P0/P1/P2 行动项） |

## 一键复现（面试现场可跑）
```bash
python sft/dataset.py            # 生成 1800/200 意图数据（若未生成）
python sft/distill_compress.py   # ① Teacher→蒸馏→Student→INT8，打印指标并写报告
python sft/prune.py              # ② 幅度剪枝稀疏度-精度权衡曲线
python sft/speculative.py        # ③ 投机解码接受率与加速比（无损验证）
python sft/parallel.py           # ④ 企业级并行（模型/流水/上下文/GPU显存）+ 蒸馏压缩组合预算
# 浏览器打开 http://127.0.0.1:8001/optimization.html 看六合一可视化 + 缓存加速 Demo
```
