# 向港大黄超团队（HKUDS）与 nanobot 学习 · 迁移分析

> 用户要求：认真研究港大黄超教授（HKU Data Intelligence Lab / HKUDS）的项目与 **nanobot**，
> 把其中可迁移的思路迁移学习到 Audit-AIOPS。本文做系统梳理 + 优先级行动项。
> 背景：黄超团队开源矩阵（LightRAG / RAG-Anything / MiniRAG / AutoAgent / CLI-Anything / OpenSpace / nanobot / AI-Trader 等）累计 Star 数十万、GitHub Trending 近 60 次；用户提到的两位 03 后队友项目 **Vibe-Trading / OpenHarness** 同日登上 Tutor/HF Trending 第一、第二，同属该生态的方法论谱系。

---

## 1. 核心人物与项目族

**黄超（Chao Huang）**：香港大学计算与数据科学学院助理教授，Data Intelligence Lab 负责人。研究方向 LLM / AI Agent / 图机器学习。核心工程哲学：

- **Agent = Model + Harness**：把 Agent 做「轻」做「薄」，复杂度放在 harness（编排/工具/环境），而非堆模型。
- **CLI 是 Agent 原生交互**：与其让 Agent 模仿人类 GUI，不如让软件原生说 Agent 的语言（CLI-Anything）。
- **skill 进化 > 参数/工作流进化**：把经验沉淀成可复用 skill，泛化性最强（OpenSpace）。
- **ReAct 是 Agent 本质**：Reasoning→Action→Observation 的 while 循环，大道至简。
- **成本控制（Token 经济学）**：Agent 必须「自负盈亏」，在追求能力上界时压住 token 成本。
- **ToB 生产级稳定**：ToC 容错高，ToB 对交付准确性/稳定性要求极严。

### 1.1 可直接借鉴的项目

| 项目 | 是什么 | 与 Audit-AIOPS 的相关性 |
|---|---|---|
| **LightRAG** | 图结构 RAG：实体/关系抽取 + 图索引 + 图增强检索 | 高。我们当前是 TF-IDF+FAISS+RRF 扁平检索，可加图层处理「审批流/资产/责任人」的实体关系 |
| **RAG-Anything** | 多模态 RAG：统一知识图谱处理文本+图+表+公式 | 中高。审计文档含大量表格/图表，多模态解析是刚需 |
| **MiniRAG** | 极简 RAG，强调 CPU 友好、轻量可复现 | 高。与我们「纯 numpy/CPU 秒级可复现」哲学完全一致，可作为检索层轻量化范本 |
| **AutoAgent** | 零代码、全自动 LLM Agent 框架（自然语言建 Agent） | 中。我们的 Agent 编排层可借鉴其「工具/工作流自动生成」思路 |
| **CLI-Anything** | 把专业软件包装成 CLI 供 Agent 驱动 | 中。审计场景对接 OA/ITSM 等系统，CLI-native 适配比 GUI 自动化更稳更省 token |
| **OpenSpace** | 基于 skill 的 Agent 自进化（wiki 式多粒度 skill 检索） | 高。可把我们的「优化工作流 / 审批路由经验」沉淀为 skill，形成数据飞轮 |
| **nanobot** | 超轻量通用 Agent（~4000 行、MCP-native、多通道、ReAct、prompt cache） | 极高。本身就是「Model+Harness 做薄」的范本，架构可直接对标我们的 Agent 层 |

---

## 2. 迁移映射表（HKUDS 思想 → Audit-AIOPS 落点）

| HKUDS / nanobot 思想 | Audit-AIOPS 当前状态 | 迁移动作 | 优先级 |
|---|---|---|---|
| **Agent = Model + Harness，做薄** | Agent 编排层已有意图→拆单→路由→记忆 | 明确把「编排/工具网关/审批/Checkpoint」定义为 harness，与基座解耦（已部分做到，需文档强化） | P0（叙事） |
| **ReAct 本质循环** | orchestrator 已是 ReAct 式 | 在 `agent-demo.html` 显式标注 Reasoning/Action/Observation 三阶段 | P1 |
| **nanobot 的轻量 Agent 循环 + prompt cache** | 已有 `llm/cache.py` 语义/Prompt 缓存 | ✅已加前缀 KV-Cache 强化（Prompt/Prefix cache），`sft/prompt_cache.py` 仿真：命中率 99.75%、TTFT↓87.7%、月省 ¥1,496 prefill（与 cache.py 构成两层缓存） | P1（⭐已落地） |
| **LightRAG 图 RAG** | 扁平 TF-IDF+FAISS+RRF → ✅已加实体共现图+双层检索第三路 | 检索可沿「审批流→责任人→资产」关系链推理（图扩散多召回） | P1（⭐已落地） |
| **RAG-Anything 多模态** | 纯文本知识库 → ✅已加多模态元数据检索层 | 把表格/截图纳入统一检索；视觉编码已做成可插拔（proxy / 混元视觉 / 千问-VL），配密钥 + 真实截图即真·视觉嵌入 | P2（⭐已落地，含可插拔真实编码） |
| **MiniRAG 极简 CPU 友好** | 已有 CPU 可复现优化 demo | 把优化实验台定位为「MiniRAG 式极简可复现」范本，强化面试差异点 | P0（叙事） |
| **OpenSpace skill 进化** | 优化工作流记在 MEMORY.md | ✅已建 `app/skills/registry.py` 领域技能注册表（8 技能：触发/是否需审批/工具/版本/演进来源），编排层零改动即可增删；前端技能中心面板 | P1（⭐已落地） |
| **CLI-Anything Agent-native** | OA 对接走 MCP 适配层 | 对内部 OA/ITSM 增加 CLI/API-native 适配（比 GUI 自动化稳），降低 token 与出错率 | P2 |
| **成本控制（Token 经济学）** | 有缓存但无成本量化 → ✅已加成本量化 | `/api/opt/cost-report` + 实验台 §8「单轮 token 成本 / 降本计算器」，呼应黄超「自负盈亏」 | P1（⭐已落地） |
| **ToB 生产级稳定** | 有双人审批 + Checkpoint | 在面经强调「ToB 容错远低于 ToC，故我们加双人审批与 Checkpoint 恢复」 | P0（叙事） |

---

## 3. 优先级行动项（建议执行顺序）

### P0 · 叙事对齐（立即可做，无需写代码）
1. 在 README / 面试准备总览 把架构明确表述为 **「Model + Harness」**：基座（混元/千问）是 Model，编排/工具/审批/缓存是 Harness。
2. 把优化实验台对标 **MiniRAG 式极简可复现**，把「五条优化线 + 企业级并行」包装为 **「压缩在前、并行在后」** 企业核心范式（见 `docs/enterprise-parallel-compression.md`）。
3. 面经加入 **ToB 生产级稳定** 论点：双人审批 + Checkpoint 恢复，正是吸收黄超「ToC 容错高、ToB 严」的判断。

### P1 · 高价值增强（值得做）
4. **图 RAG 升级**（吸收 LightRAG）：✅ **已落地**。在 `retrieval_hybrid.py` 加「审计实体共现图（GraphIndex）+ 双层检索（具体实体 + 图扩散）」作为第三路，与 TF-IDF/FAISS 三路 RRF 融合；实体抽取用审计领域词典（17 实体 / 108 边 / 中枢「审批」），纯 CPU 可复现，实测 6/6 查询有图扩散多召回增益（平均 +2.33 篇）。端点 `/api/knowledge/graph`、`/api/opt/graph-rag-report`，演示页 `/knowledge-hybrid.html` 三列对比，文档 `docs/graph-rag.md`。
5. **prompt cache 强化**（吸收 nanobot）：✅ **已落地**。在 `sft/prompt_cache.py` 仿真「长稳定系统前缀 + 短多变 query」流量，前缀 KV-Cache 命中率 99.75%、TTFT↓87.7%、月省 ¥1,496 prefill 算力；端点 `/api/opt/prompt-cache-report` + 实验台 `/optimization.html` §9；与 `cache.py`（应用层精确+语义响应缓存）构成两层缓存。
6. **skill 沉淀机制**（吸收 OpenSpace）：✅ **已落地**。新建 `app/skills/registry.py` 领域技能注册表（8 技能：审批路由/工单拆单/知识问答/监控告警/服务目录/工单推进/审计留痕/语音入口），每技能含触发意图、是否需双人审批、工具、版本与演进来源；编排层 `resolve_skills()` 零改动增删能力，审批技能与双人审批+Checkpoint 对齐；端点 `/api/skills` + `/agent-demo.html` 技能中心面板，文档 `docs/skills.md`。

### P2 · 前瞻探索（按需）
7. **多模态 RAG**（吸收 RAG-Anything）：✅ **已落地**。在 `retrieval_hybrid.py` 加 `MultimodalRetriever`，把文档附带的「表格/截图描述」作为多模态元数据纳入统一检索（内置审计样本：Ukey 制作截图、权限变更表、资产台账、留痕截图等），端点 `/api/knowledge/multimodal`、演示页 `/knowledge-hybrid.html` 多模态区块。真实视觉编码需接混元多模态/千问-VL，本环境以描述文本代理、零依赖可复现。
8. **CLI-native 适配**（吸收 CLI-Anything）：对内部系统提供 CLI/API-native 接口，替代 GUI 自动化。

---

## 4. 我们已经「天然对齐」的点（面试可直接说）

- **ReAct 编排**：orchestrator 的 意图→拆单→路由→记忆 就是 Reasoning→Action→Observation。
- **轻量可复现**：五条优化线全用纯 numpy/CPU 跑通，与 MiniRAG「极简 CPU 友好」同源。
- **缓存降本**：语义/Prompt 缓存 = 黄超强调的「成本控制 / 自负盈亏」。
- **生产级稳定**：双人审批 + Checkpoint 恢复 = ToB 严要求。
- **MCP 演进**：OA 对接走 MCP 适配层，与 nanobot 的 MCP-native 思路一致。

> 一句话总结迁移逻辑：**黄超团队证明「把 Agent 做薄、把复杂度放进 harness、用 skill 沉淀经验、用 CLI 说 Agent 的语言、用成本约束能力上界」能做出登顶 Trending 的生产级 Agent；Audit-AIOPS 吸收这套哲学，把审计领域 Agent 的 harness（编排/审批/缓存/检索）做厚做稳，把基座做薄可插拔，并用「压缩+并行」把推理成本打下来。**

---

## 5. 参考链接（公开来源）

- HKUDS GitHub：https://github.com/HKUDS （LightRAG / RAG-Anything / MiniRAG / AutoAgent / nanobot / OpenSpace 等）
- nanobot：https://github.com/HKUDS/nanobot  · 文档 https://nanobot.wiki
- 黄超主页 / Data Intelligence Lab：https://sites.google.com/view/chaoh
- LightRAG 论文：arXiv:2410.05779
