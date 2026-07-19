# 简历 · AI Agent 应用开发工程师（打磨版 / 基础通用）

> 本版为分厂定制的总基线。生成器（resume-generator）按此结构化内容 + 各厂 JD 画像重排重帧，产出 22 份分厂 docx。
> 打磨点：ATS 关键词前置（LangGraph/LangChain/RAG/Multi-Agent/MCP/Function Calling/FastAPI）、每条经历补「落地四件套」、突出开源复用、补 2026 新标配词（MCP/Dify/AutoGen）、量化指标统一口径。

---

**【姓名】** ｜ 【电话】 ｜ 【邮箱】 ｜ 深圳 · 本科 · 3 年经验
GitHub: github.com/【id】 · 作品集: portfolio.【domain】 · 博客: 【domain】

**求职意向**：大模型 Agent 应用开发工程师（按投递厂改写，见分厂 docx）

## 个人总结
AI Agent 应用开发工程师，3 年 LLM 应用落地经验。主导「专属刷题教练」从复赛工具升级为定制化备考 Agent（LangGraph 编排 + 混元/通义基座 + MCP 工具网关 + 分层记忆 + RAG 引用溯源 + 反思防环 + 评测闭环）；工程复用两个 GitHub Trending 开源项目同源 core，零外部 API 依赖可规则降级运行，推理链路量化提速≈8x、KV Cache 命中≈0.8。熟悉字节/腾讯/智谱技术栈同构实现，具备 Agent 框架、RAG 防幻觉、多智能体编排、推理优化与评测体系设计能力。

## 技术栈（按厂重排，基础序）
- **编排与框架**：LangGraph · LangChain · AutoGen · CrewAI
- **RAG 与检索**：RAG · 向量检索(Milvus/Elasticsearch) · TF-IDF+2-gram+RRF 混合召回 · 引用溯源/事实核查 · HyDE/Query 改写
- **Agent 能力**：Multi-Agent 编排 · MCP 工具网关 · Function Calling · Planning/Execution · Memory 分层记忆 · Reflection 反思防环 · Agent 评测(SWE-Bench 同构)
- **模型与训练**：LLM 微调(SFT/LoRA) · RLHF/DPO · Post-training · 模型蒸馏/量化(AWQ/GPTQ) · 长文本上下文预算
- **工程**：Python · FastAPI · Go · Java · Docker · Kubernetes · Redis · MySQL · 高并发/分布式 · vLLM · 可观测(Prometheus)
- **产品与协作**：需求拆解 · 竞品分析 · 指标设计 · 低代码生态 · AI 产品闭环

## 核心能力与方法论
- Agent 框架设计：基于 LangGraph 实现 Supervisor 多 Agent 协作 + MemorySaver 分层记忆 + 反思节点防环，同比 AutoGen/CrewAI 同构。
- RAG 防幻觉与引用溯源：TF-IDF+2-gram+RRF 混合召回 + 事实核查，citation_rate=1.0、hallucination_rate=0.0。
- 推理优化：vLLM/continuous batching + KV Cache 复用 + INT8 量化，speedup≈8x、kv_cache_hit_rate≈0.8。
- 评测闭环：离线（命中/引用/拒答/幻觉四率）+ 在线（A/B + 可观测），对齐 SWE-Bench/TAU-Bench 工程化思路。
- 工程落地：零依赖规则降级、两开源项目同源复用、编译全过、成本自负盈亏。

## 项目经历：专属刷题教练 · 定制化备考 Agent（v3.1.0-agent-mem）
个人项目（复赛作品升级）｜ LangGraph · 混元/通义 · MCP · SQLite ｜ 2024.06 – 至今

- **Phase A · Agent 编排与 MCP 工具网关**：LangGraph 搭 Supervisor 多 Agent（llm/memory/tools/orchestrator/router）；MCP 风格工具网关统一 Function Calling；无 Key 时规则降级，可用性 100%。
- **Phase B · 分层记忆与多轮上下文预算**：记忆落 SQLite；五段式上下文预算 build_context，长文本可控。
- **Phase C · RAG 引用溯源与防幻觉**：TF-IDF+2-gram+RRF 混合召回；citation_rate=1.0、hallucination_rate=0.0，已上线。
- **Phase D · 多 Agent 编排与反思防环**：Supervisor 拆解→Worker 并行→Synthesizer 汇总；反思节点防矛盾与死循环。
- **Phase E · 评测闭环（离线+在线）**：hit_rate=0.667 / citation_rate=1.0 / reject_rate=0.0 / hallucination_rate=0.0；在线 A/B + Prometheus 可观测。
- **Phase F · 推理优化**：vLLM/continuous batching + KV Cache 复用 + INT8 量化 + 投机解码，speedup≈8x、kv_cache_hit_rate≈0.8。
- **Phase G · 多厂商注册表与结构化输出**：混元/智谱/通义/DeepSeek/Kimi 统一接口；Function Calling/JSON Schema + 端侧移动答疑。
- **Phase H · MCP 生态与开源复用（2026 新标配）**：接入 MCP；复用两个 GitHub Trending 开源项目同源 core。

**量化验证**：citation_rate=1.0 · hallucination_rate=0.0 ｜ hit_rate=0.667 ｜ speedup≈8x · kv_cache_hit_rate≈0.8 ｜ 两个开源项目 GitHub Trending

**工程实践**：零依赖规则降级（可用性 100%）｜ Prometheus 可观测 + A/B ｜ CI 编译全过、类型安全

## 个人作品集网站（React + Vite + TypeScript）
组件化作品集，承载刷题教练与开源项目展示，已部署可访问；TS 强类型、构建优化、响应式。

---
*分厂定制版见 `简历生成器/generate.js` 产出（字节 Seed / 腾讯混元 / 智谱 / Kimi / DeepSeek / 京东 / 快手 / 阶跃星辰 / 宇树 / 智元 / 银河通用 / 阿里通义 / 百度 / MiniMax / 百川 / 商汤 / 美团 / 星海图 / 星动纪元 / 灵初智能）。*
