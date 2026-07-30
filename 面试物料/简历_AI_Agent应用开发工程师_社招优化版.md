# 简历 · AI Agent 应用开发工程师（社招优化版 / Branch A 对齐）

> 优化点（相对基础通用版）：① ATS 关键词前置 + 推理优化工具链补全；② 新增「大模型推理优化与降本」能力块（你强调的技术栈）；
> ③ 项目 Phase F 推理优化拆成可面试追问的具体技术；④ 末尾锚定 Branch A（后训练/Agent/推理 Infra）对口厂与学习路线，
> 让简历与成长路径闭环。固定数字资产统一口径，可直接投递社招。

---

**【姓名】** ｜ 【电话】 ｜ 【邮箱】 ｜ 深圳 · 本科 · 3 年经验
GitHub: github.com/【id】 · 作品集: portfolio.【domain】 · 博客: 【domain】

**求职意向**：大模型 Agent 应用开发工程师（社招 · 对齐 智谱GLM / DeepSeek / 百川智能 / 商汤 算法·后训练·Agent 岗）

## 个人总结
AI Agent 应用开发工程师，3 年 LLM 应用落地经验，且具备**后训练 / 推理优化**的工程深度。主导「专属刷题教练」从复赛工具升级为生产级备考 Agent（LangGraph 编排 + 混元/通义基座 + MCP 工具网关 + 分层记忆 + RAG 引用溯源 + 反思防环 + 评测闭环）；并落地**可运行的推理优化链路**（vLLM continuous batching + KV Cache 复用 + INT8/AWQ 量化 + 投机解码），量化提速≈8x、KV Cache 命中≈0.8、评测不掉点。熟悉字节/腾讯/智谱技术栈同构实现，具备 Agent 框架、RAG 防幻觉、多智能体编排、**后训练数据飞轮（trajectory→SFT/RL）**、推理优化与评测体系设计能力，目标走算法/后训练/RL 方向。

## 技术栈（ATS 前置 · 社招口径）
- **Agent 编排**：LangGraph · LangChain · AutoGen · Multi-Agent 编排 · MCP 工具网关 · Function Calling · Planning/Execution · Reflection 防环
- **RAG 与记忆**：RAG · 向量检索(Milvus/Elasticsearch) · TF-IDF+2-gram+RRF 混合召回 · 引用溯源/事实核查 · HyDE/Query 改写 · 分层记忆
- **后训练 / 对齐**：SFT/LoRA · RLHF/DPO · GRPO · 奖励建模 · trajectory→训练样本数据飞轮 · LLaMA-Factory · TRL · OpenRLHF
- **大模型推理优化**：vLLM(PagedAttention) · SGLang(radix cache) · continuous batching · KV Cache / prefix caching · INT8/AWQ/GPTQ 量化 · 投机解码 · FlashAttention · 上下文压缩(LLMLingua) · 知识蒸馏
- **模型与训练**：LLM 微调(SFT/LoRA) · 模型蒸馏/量化 · 长文本上下文预算 · DeepSpeed/Megatron 同构
- **工程**：Python · FastAPI · Go · Java · Docker · Kubernetes · Redis · MySQL · 高并发/分布式 · 可观测(Prometheus) · Dify 低代码生态

## 核心能力与方法论
- **Agent 框架设计**：基于 LangGraph 实现 Supervisor 多 Agent 协作 + MemorySaver 分层记忆 + 反思节点防环，同比 AutoGen/CrewAI 同构。
- **RAG 防幻觉与引用溯源**：TF-IDF+2-gram+RRF 混合召回 + 事实核查，citation_rate=1.0、hallucination_rate=0.0。
- **后训练数据飞轮**：多 Agent 协作轨迹 → 结构化 trajectory 数据集 → SFT/RL 训练样本，把"用 Agent"升级为"造训练数据"（Branch A 差异化）。
- **大模型推理优化与降本**（重点）：① 推理框架 vLLM/continuous batching 提吞吐；② 稳定前缀走 prefix caching 复用 KV（多轮省重算）；③ AWQ 4bit 量化降显存 60%+ 且评测不掉点；④ 投机解码降首字延迟；⑤ 工具替代生成（诊断/错题 0 token）+ 反思确定性（0 额外 decode）。speedup≈8x、kv_cache_hit_rate≈0.8。
- **评测闭环**：离线（命中/引用/拒答/幻觉四率）+ 在线（A/B + 可观测），对齐 SWE-Bench/TAU-Bench 工程化思路；蒸馏/量化均过同一质量闸门。
- **工程落地**：零依赖规则降级、两开源项目同源复用、编译全过、成本自负盈亏。

## 项目经历：专属刷题教练 · 定制化备考 Agent（v3.1.0-agent-mem）
个人项目（复赛作品升级）｜ LangGraph · 混元/通义 · MCP · vLLM · SQLite ｜ 2024.06 – 至今

- **Phase A · Agent 编排与 MCP 工具网关**：LangGraph 搭 Supervisor 多 Agent（llm/memory/tools/orchestrator/router）；MCP 风格工具网关统一 Function Calling；无 Key 时规则降级，可用性 100%。
- **Phase B · 分层记忆与多轮上下文预算**：记忆落 SQLite；五段式上下文预算 build_context，长文本可控。
- **Phase C · RAG 引用溯源与防幻觉**：TF-IDF+2-gram+RRF 混合召回；citation_rate=1.0、hallucination_rate=0.0，已上线。
- **Phase D · 多 Agent 编排与反思防环**：Supervisor 拆解→Worker 并行→Synthesizer 汇总；反思节点防矛盾与死循环（确定性校验，0 额外 decode）。
- **Phase E · 评测闭环（离线+在线）**：hit_rate=0.667 / citation_rate=1.0 / reject_rate=0.0 / hallucination_rate=0.0；在线 A/B + Prometheus 可观测。
- **Phase F · 大模型推理优化（降本核心）**：vLLM/continuous batching 提吞吐；稳定前缀 prefix caching 复用 KV（kv_cache_hit_rate≈0.8）；AWQ 4bit 量化降显存 60%+；投机解码降首字延迟；context 压缩(五段式预算 + LLMLingua 思路)；工具替代生成(诊断/错题 0 token)。speedup≈8x，量化/蒸馏均过评测闸门不掉点。
- **Phase G · 多厂商注册表与结构化输出**：混元/智谱/通义/DeepSeek/Kimi 统一接口；Function Calling/JSON Schema + 端侧移动答疑。
- **Phase H · MCP 生态与开源复用（2026 新标配）**：接入 MCP；复用两个 GitHub Trending 开源项目同源 core。

**量化验证**：citation_rate=1.0 · hallucination_rate=0.0 ｜ hit_rate=0.667 ｜ 推理 speedup≈8x · kv_cache_hit_rate≈0.8 ｜ 两开源项目 GitHub Trending

**工程实践**：零依赖规则降级（可用性 100%）｜ Prometheus 可观测 + A/B ｜ CI 编译全过、类型安全

## 个人作品集网站（React + Vite + TypeScript）
组件化作品集，承载刷题教练与开源项目展示，已部署可访问；TS 强类型、构建优化、响应式。

---

## 社招投递对口（Branch A · 算法/后训练/RL）
- **智谱GLM** · 后训练/Agent/推理 Infra：https://zhipu-ai.jobs.feishu.cn/ — 强调 trajectory 数据飞轮 + 评测闭环 + 多厂商含智谱。
- **DeepSeek** · 大模型算法/Agent Harness：https://talent.deepseek.com/ — 强调 系统优化 + 推理极致优化 + 开源复用 + 评测。
- **百川智能** · 大模型算法工程：https://www.baichuan-ai.com/ — 强调 SFT/RL 全流程与工程落地。
- **商汤** · 通用智能体/Agent Harness：https://www.sensetime.com/ — 强调 多模态 + GUI Agent + 多 Agent 协作数据。

> 完整 20 厂官方招聘入口、10 周 Branch A 学习路线与可点击资源库见：大厂情报站 `学习路线` Tab（http://localhost:8031）与 `docs/agent-learning-roadmap.md`。
> 简历关键词已对齐 347 份真实 Agent JD 词频（Agent 架构设计 72.9% / Python 57.9% / LLM 55.9% / RAG 47.6% / MCP 14.4% / Dify 15.3% / AutoGen 15.0%）。

---

*分厂定制版见 `简历生成器/generate.js` 产出（字节 Seed / 腾讯混元 / 智谱 / Kimi / DeepSeek / 京东 / 快手 / 阶跃星辰 / 宇树 / 智元 / 银河通用 / 阿里通义 / 百度 / MiniMax / 百川 / 商汤 / 美团 / 星海图 / 星动纪元 / 灵初智能）。*
