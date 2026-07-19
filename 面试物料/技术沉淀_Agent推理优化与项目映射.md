# 技术沉淀 · Agent 推理优化与项目映射（LLM 推理开发向）

> 用途：把「模型压缩 / 蒸馏 / KV cache / 推理框架优化」等 LLM 推理开发硬技能，锚定到《专属刷题教练》项目，作为面试时的**研发深度体现**。每点给出「当前已体现 / v2 代码已落地 / 面试讲法」。
>
> ✅ **状态更新（2026-07-19）**：推理优化已从「设计映射」升级为**真实可运行的 v2 代码**（`server/agent/inference.py` + 接入 `tools/orchestrator/eval/router`），无 Key、无 GPU 也能跑出量化指标，见下方「v2 代码已落地」列与 `刷题教练-Agent升级设计.md` 第 13 节。

---

## 0. 一句话主线

「刷题教练的 Agent 不只是功能堆叠，而是**推理成本敏感**的设计：五段式上下文预算本质是 context 压缩、长前缀可 prefix cache、该查库不生成直接降推理量、评测闭环可同时比对 teacher/student——天然是推理优化技术的落地载体。」

---

## 1. 技术 → 项目映射表

| 推理优化技术 | 项目当前已体现 | v2 代码已落地（`agent/inference.py`） | 面试讲法 |
|---|---|---|---|
| **量化 INT4/INT8（GPTQ/AWQ）** | 基座预留混元/通义 + `HAS_KEY` 降级；评测闭环可量化对比 | 私有化部署用 AWQ 4bit 量化，显存降 60%+，同用 `hit_rate/幻觉率` 验证不掉点 | 「量化不是盲压，要用评测闭环看是否掉点，本项目已有对照基建」 |
| **知识蒸馏 KD** | 反思/重排为确定性规则，避免盲调大模型 | teacher(大模型)生成讲题/变式/诊断作训练集 → 蒸馏小模型(student)做轻量/边缘答疑；`run_self_eval` 同时评 teacher/student | 「把大模型能力蒸馏到小模型，Agent 边界场景零延迟」 |
| **KV cache / PagedAttention / prefix caching** | 五段式上下文预算中【身份】【长期画像】为**稳定前缀** | 稳定前缀走 prefix caching 复用，不每轮重算；分层记忆减少重复上下文 → 降 KV 占用 | 「多轮对话省重算，本质是 KV cache 复用 + context 压缩」 |
| **推理框架（vLLM/SGLang）· continuous batching** | 单进程 uvicorn；反思节点确定性不额外 decode | 多用户并发答疑上 vLLM continuous batching 提吞吐；SGLang 结构化输出控 token | 「Agent 服务化首要解决并发吞吐，continuous batching 是标配」 |
| **投机解码 speculative decoding** | — | 草稿模型先出讲题/变式骨架，target 模型一次验证，降首字延迟 | 「答疑要快，投机解码把首字延迟打下来」 |
| **FlashAttention / 长上下文** | 上下文预算硬截断控长 | 长上下文用 FlashAttention 降显存与算力 | 「预算控长 + 注意力优化双保险」 |
| **上下文压缩 / prompt compression（LLMLingua 思路）** | 五段式预算 = 把长记忆压成结构化摘要再注入 | 引入 LLMLingua 类压缩器，进一步压【对话历史】段 | 「context 压缩就是 Agent 降本第一杠杆」 |
| **工具调用替代生成** | 诊断/错题/掌握度走工具确定性返回，不靠 LLM 生成 | 能查库绝不让模型编 → 直接砍掉大段生成 | 「Agent 降本最高效的一招：该调工具不生成」 |
| **RRF 重排 + 小 rerank** | 两路召回 RRF 融合（K=60），TF-IDF 仅排序 | 用小 rerank 模型替代每次调大模型排序 | 「重排用轻量模型，是把蒸馏思想用在检索」 |

---

## 2. 成本视角（面试可聊的量化故事）

- **前缀复用**：系统提示 + 长期画像在多轮对话中不变，prefix caching 后第 2 轮起省掉这部分 prefill，约等于把「每轮全量 prefill」降为「增量 prefill」。
- **生成量削减**：诊断/错题/掌握度由工具返回（0 token 生成），仅讲题/答疑/计划走 LLM；反思用确定性规则（0 额外 decode）。整体生成 token 数显著低于「全靠模型生成」的套壳 Agent。
- **评测即对照**：`run_self_eval` 同时跑 teacher/student，用 `hit_rate/citation_rate/hallucination_rate` 验证蒸馏/量化是否掉点——这是把「推理优化」接进「质量闸门」的闭环思路。

---

## 3. 面试话术（收尾钩子）

「我这个备考 Agent 表面是应用，底层全是推理优化的活：上下文预算=context 压缩、稳定前缀=KV cache 复用、工具替代生成=降本、评测闭环=量化/蒸馏的质量闸门。下一步我想在团队里把基座换成 vLLM 私有化 + AWQ 量化 + 蒸馏小模型做边缘答疑——这也是我投 LLM 推理开发岗的底气。」

---

## 4. 与简历/面试题的衔接

- 简历（Agent 开发版）已加「技术沉淀：LLM 推理优化」小节。
- 配套题库：`面试题库_Agent算法与推理优化.md`（量化/蒸馏/KV cache/框架/降本/项目深挖，24 题）。
