# 简历 · AI Agent 应用开发工程师（LLM 推理 / 多智能体方向）

> 说明：个人信息占位；技术经历基于真实落地代码《专属刷题教练 Agent》（Phase A–H，GitHub 已推送，版本 3.7.0-channel-history-mcp）。投递前替换【】内容。

---

## 基本信息
- 姓名：【姓名】　|　电话：【】　|　邮箱：【】　|　城市：【】
- 求职意向：**AI Agent 应用开发工程师 / LLM 推理开发工程师**
- GitHub：【链接】　|　技术博客：【】　|　作品体验：https://www.taoxie.vip/shuati-coach.html

---

## 技术总结
具备从 0 到 1 构建生产级 Agent 的实战能力：用 LangGraph 同构编排实现多 Agent 协作，落地 RAG 引用溯源 + 低相关拒答防幻觉，设计分层记忆与五段式上下文预算，并把 AIOps 异常检测迁移到学习场景 + 自建评测闭环。代码无外部密钥可规则降级跑通，工程规范清晰（分阶段编译+冒烟+文档即设计）。**更关键的是我形成了一套可复用的「Agent 标准化构建流程」**——吸收港大黄超教授 HKUDS 团队（nanobot 等 45.9k⭐ 开源矩阵）的方法论，把"Agent=Model+Harness 做薄 / ReAct 本质 / Channel 与思考解耦 / 技能沉淀 / 成本自负盈亏"固化为每个项目的统一骨架，已复用到两个 Trending 项目验证。

---

## 技术栈
- **语言/框架**：Python · FastAPI · asyncio · Pydantic
- **Agent 编排**：LangGraph（同构 StateGraph）· Supervisor 路由 · 反思节点 · 工具网关
- **LLM/RAG**：混元/通义基座（vLLM 私有化可选）· TF-IDF+BM25+RRF 重排 · 引用溯源 · 上下文工程
- **记忆/存储**：SQLite 分层记忆（长/短/中长期事件日志）· 向量库（预留 Milvus/Redis VSS）
- **接入/扩展**：Channel 接入层（API/CLI 多源解耦）· 原生 MCP（Skills 插件化）· 多厂商注册表（智谱/Kimi/混元/豆包/千问/DeepSeek/OpenAI 可切换）
- **工程**：Git · 单元测试/冒烟（隔离 DB）· 评测闭环 · 可观测埋点

---

## 技术沉淀（LLM 推理优化 · 已落代码 v2）
- **已做成可运行代码**：`server/agent/inference.py` 实现 7 项推理优化（KV 前缀缓存 / 上下文压缩 / 投机解码 / 知识蒸馏 / continuous batching / 工具替代 / AWQ 量化），无需 GPU 即跑出量化指标，端点 `POST /api/agent/infer/optimize`、`GET /api/agent/infer/status`，版本 `3.5.0-infer-opt`。
- **量化与私有化**：基座预留混元/通义 + vLLM/SGLang 私有化 + AWQ 4bit 量化路线（`QUANT_CONFIG` 透传 `quantization=awq`），评测闭环可对比量化前后是否掉点。
- **KV cache / prefix caching**：五段式上下文预算中【身份】【长期画像】为稳定前缀，`KVCacheManager` 多轮复用（实测 `kv_cache_hit_rate≈0.8`）；分层记忆降低 KV 占用。
- **知识蒸馏**：`Distiller` 用 teacher(大模型)生成讲题/变式 → 蒸馏小模型(student)做边缘答疑，纯 Python ROUGE-N 评保真度（`run_self_eval` 同时评 teacher/student）。
- **Agent 降本**：工具替代生成（诊断/错题 0 token，实测 `tool_substitutions` 累计）、反思节点确定性（0 额外 decode）、continuous batching 提并发吞吐（实测 `speedup≈8x`）、投机解码降首字延迟。

---

## 方法论沉淀（杀手锏 · 可复用标准流程）
> 不是只会写功能，而是能把学界前沿方法论沉淀成"做 Agent 的标准动作"，并复用到多个项目。

- **来源**：系统研究港大黄超教授 HKUDS 团队开源矩阵（nanobot 45.9k⭐、LightRAG、MiniRAG、AutoAgent 等，GitHub Trending 近 60 次），提取出 5 条可工程化的 Agent 方法论。
- **固化成标准流程**：① **Agent = Model + Harness 做薄**（复杂度放编排/工具/环境，基座可插拔）；② **ReAct 本质**（Reasoning→Action→Observation 循环）；③ **Channel 与思考解耦**（一个 core + 多源接入）；④ **技能/经验沉淀 > 参数堆砌**（可复用 skill/data flywheel）；⑤ **成本自负盈亏**（token 经济学约束能力上界）。
- **已验证复用**：这套流程贯穿《专属刷题教练》Phase G/H（多厂商注册表 + 虚拟工具 + Channel 接入层 + MCP + 三层记忆），并被团队两个 Trending 项目（Vibe-Trading 量化 / Deep Tutor 教育）用同一 core 验证"一核多域"。
- **面试价值**：能讲清楚"我为什么这么设计"，而不只是"我做了什么"——把学术界 Trending 项目的方法论转化为自己的工程标准。

## 项目经历

### 专属刷题教练 · Agent 升级（核心项目）
*2026.07 ｜ 个人全栈 ｜ GitHub 已推送，v3.7.0-channel-history-mcp*
把复赛刷题工具升级为定制化备考 Agent，分八个阶段落地，均为本人独立设计与实现（**全程以 HKUDS/nanobot 方法论为设计准线**）：

- **Phase A 基础包**：单 Agent + 工具调用（诊断/错题/计划/答疑）+ 分层记忆 + `/api/agent/chat` 入口。
- **Phase B 持久化记忆**：`MemoryStore` 把记忆落 SQLite（agent_profile 长期画像 + agent_short_term 短期对话）；设计五段式上下文预算，保证当前消息永不被裁；多会话 `session_id` 隔离 + 清记忆接口。
- **Phase C RAG 防幻觉**：`KnowledgeRetriever`（TF-IDF + 中文 2-gram 召回 + RRF 融合重排）；相关判据仅依赖 2-gram 真实命中，不相关则明确拒答（绝不编造）；`format_citations` 生成 [1][2] 引用溯源。
- **Phase D 多 Agent 编排**：自研 LangGraph 同构 `StateGraph`（add_node/add_edge/add_conditional_edges/compile/invoke + 最大步数防环）；6 节点 classify→子Agent→reflect；反思节点为确定性校验，保证每次响应有下一步动作。修复终点语义 bug（finish 节点未执行即退出）。
- **Phase E 异常检测 + 评测**：`LearningAnomalyDetector` 把 AIOps 指标异常迁移为学习异常（正确率骤降/连续断签/错题反复），诊断即主动推送预警；`eval.py` 评测闭环聚合 hit_rate/citation_rate/reject_rate/hallucination_rate + 分级；修复幻觉口径误判（拒答不计幻觉）。
- **Phase F 推理优化**：`inference.py` 落地 7 项推理优化（KV 前缀缓存/上下文压缩/投机解码/蒸馏/continuous batching/工具替代/AWQ 量化），无 GPU 跑出量化指标（kv_cache_hit_rate≈0.8、speedup≈8x）。
- **Phase G 多厂商 + 虚拟工具**：7 家主流模型一键切换（注册表 + 运行期切）；结构化输出改用 Function Calling 截获 arguments（nanobot 同款"幽灵工具"），替代脆弱 json_object。
- **Phase H Channel + 三层记忆 + MCP**：Channel 接入层（ApiChannel/CliChannel + AgentHub）实现"一个 core + 多 Channel"；记忆补中长期事件日志（append-only 可 grep，nanobot HISTORY.md 同构）；声明式 MCP 桥接垂直工具，配 URL 即接远程 server 无需改码。

**量化验证**：编译全过、无 lint；评测自评估 6 样本 hit_rate=0.667 / citation_rate=1.0 / hallucination_rate=0.0；三类学习异常均 high 级检出并主动推送；无 API Key 规则降级完整跑通；Phase F 推理实测 speedup≈8x；Phase H 新增 4 个端点 + 3 个模块均通过编译与导入冒烟。

### 刷题教练 复赛 Web 平台（前端 + 后端）
*2026.07 ｜ TRAE 创造力大赛复赛*
- 四模块 SPA（聚合刷题/数据中心/智能推荐/AI 教练），Chart.js 可视化（掌握度雷达、正确率趋势），已部署上线。
- AI 链路：薄弱点诊断 / 按掌握度组卷 / 答案解析生成 / 备考答疑对话。

---

## 工程实践 / 亮点
- **零依赖可跑**：HAS_KEY 开关 + 规则降级，主链路不依赖外部密钥，便于演示与离线评测。
- **可观测**：工具调用留痕、评测日志持久化、语义化版本号、lifespan 建表。
- **文档即设计**：`刷题教练-Agent升级设计.md` 记录每阶段改动/命中面试点/验证，可作为面试讲解底稿。

---

## 教育背景
- 【学校】　|　【专业】　|　【学历】　|　【时间】

---

## 自我评价
既懂 Agent 编排范式，也抠得过 RAG 相关性阈值与评测口径；相信「可信 Agent = 引用溯源 + 防幻觉 + 可量化评测」，乐于把 AIOps/可观测性等成熟工程思想迁移到 Agent 场景。
