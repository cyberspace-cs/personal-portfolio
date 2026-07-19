# 专属刷题教练 · Agent 升级设计（大厂面试亮点项目）

> 目标：把复赛版「带 AI 功能的刷题工具」升级为 **面向备考场景的定制化多智能体 Agent 平台**，
> 作为 DeepSeek / 智谱 / Kimi / 字节 / 腾讯混元 / 阿里通义 等 **AI Agent 应用开发 / LLM 推理开发** 岗位的面试亮点项目。
> 技术栈来源：复用 Step1-3 从四厂+腾讯+阿里招聘与三份参考 PDF 提取的 Agent/LLM 技术点。

---

## 0. 升级定位（一句话）

**从「工具」到「Agent」**：以 `LangGraph 编排` + `混元/通义基座（可 vLLM 私有化）` + `RAG 知识库` + `分层记忆` 为核心，
把「讲题 / 变式 / 押题 / 答疑 / 薄弱度诊断」统一封装为一个会思考、会调用工具、有记忆、能反思的备考 Agent。

---

## 1. 用户痛点（借鉴《产品定位》四类痛点 + 现有 AI 能力短板）

### 1.1 沿用复赛已验证的四类真实痛点
| 痛点 | 表现 | 现有产品能力 |
|---|---|---|
| 知识记忆与复习规划 | 刷了就忘、凭感觉复习 | 艾宾浩斯自动排期 |
| 错题管理与查找 | 错题散落多 App/Excel | 自动归集错题本 |
| 薄弱点识别 | 70% 时间在刷已会的 | 每次答题重算薄弱度、雷达图 |
| 动力与反馈缺失 | 一个人备考易放弃 | 打卡 streak + 游戏化 |

### 1.2 新增：复赛版「AI 能力短板」（即本次升级要解决的）
| 短板 | 问题 |
|---|---|
| ① 无 Agent 编排 | 讲题/变式/押题是三个**孤立一次性调用**，无法多步推理、不能组合任务 |
| ② 无记忆 | 每次提问都是「失忆」的，不知道用户历史薄弱点/错题上下文 |
| ③ 无 RAG | 讲题只基于单题，无法引用**知识点体系/考纲/用户错题**做有据回答 |
| ④ 无工具化 | 模型不能「调用」掌握度/错题本/题库等内部能力，只能纯生成 |
| ⑤ 无事实核查 | 可能幻觉、无引用溯源，弱监管场景不可信 |
| ⑥ 无异常检测 | 只做统计，不「发现异常」（如某模块正确率骤降、连续三天零打卡） |

> 这六点恰好一一对应 Step1 中四厂 + 腾讯/阿里对 **AI Agent 应用开发岗**的高频要求。

---

## 2. 产品定位升级

- **旧**：多源数据聚合智能备考平台（工具属性）。
- **新**：**你的专属备考 Agent**——比你更懂你的薄弱点，能在一次对话里完成「诊断→讲题→变式→排计划→预警」。
- Slogan：**「不是一个题库，而是一个会陪你复盘、比你更清楚弱在哪的教练。」**

---

## 3. 原型设计（核心交互流）

统一对话入口「教练」，自然语言驱动，卡片式响应：

```
用户："我最近行测好像卡住了，帮我看看"
  → 意图路由：diagnose
  → 工具：get_mastery / get_wrong_book
  → 返回【诊断卡】：最弱 2 模块 + 正确率趋势
  → 反思 Agent：主动补一句"建议先把资料分析的错误题型吃透"
       │
用户："把第 3 题给我讲讲"  (用户刚答错)
  → 意图路由：explain（携带题目上下文）
  → 工具：retrieve_knowledge(考点) + LLM 讲题（标注引用来源）
  → 返回【讲题卡】+ 现场生成 3 道变式【变式卡】
       │
用户："给我排个这周计划"
  → 意图路由：plan
  → 工具：diagnose + LLM 规划（基于真实掌握度）
  → 返回【计划卡】
       │
系统主动推送（学习异常检测）：
  "⚠️ 检测到『概率统计』正确率 3 天下降 20%，已为你加急推送 5 道同类题"
```

---

## 4. 整体架构（四层职责划分）

```
┌──────────────────────────────────────────────────────────────┐
│  业务层（现有 + 新增 Agent 入口）                                │
│  coach.html / 微信小程序  ──►  /api/agent/chat  /api/* 现有     │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│  Agent 编排层（本次升级核心）                                    │
│  Supervisor 路由 ──┬── 诊断 Agent（薄弱度/错题）                 │
│  (LangGraph StateGraph)  ├── 讲题 Agent（RAG+引用溯源）          │
│  工具网关(审批/去重/超时)   ├── 变式 Agent                        │
│  上下文预算(五段式)         ├── 规划 Agent（押题/计划）           │
│  分层记忆(短/长)            └── 反思 Agent（质量校验/主动推送）    │
└───────────────────────────┬──────────────────────────────────┘
                            │  Tool Calling / Function Call / MCP
┌───────────────────────────▼──────────────────────────────────┐
│  LLM 推理层                                                     │
│  基座：腾讯混元 / 阿里通义（vLLM/SGLang 私有化可选）             │
│  Prompt/Context Engineering · RAG（向量+BM25+RRF 重排）· 量化   │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│  数据处理层                                                     │
│  SQLite（users/questions/quiz_records/wrong_book/mastery…）    │
│  向量库（Redis VSS → 预留 Milvus）：知识点/考纲/错题嵌入         │
│  记忆存储 · 题库/错题/掌握度计算 · 学习异常指标采集              │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. 模块说明（各层组件）

### 5.1 Agent 编排层（直接命中 AI Agent 应用开发岗）
| 组件 | 职责 | 技术 |
|---|---|---|
| Supervisor 路由 | 意图识别 → 派发子 Agent | LangGraph Supervisor / 状态图 |
| 诊断 Agent | 调 get_mastery/get_wrong_book，输出最弱模块 | Tool Use + Planning |
| 讲题 Agent | 检索考点知识 → LLM 讲题 → 标注引用 | RAG + 引用溯源 |
| 变式 Agent | 现场生成同考点变式题 | LLM + 考点约束 |
| 规划 Agent | 基于掌握度生成冲刺计划/押题 | LLM + 数据驱动 |
| 反思 Agent | 校验回答、主动预警、补全建议 | 反思/校验节点 |
| 工具网关 | 重复调用拦截、参数校验、高风险审批、超时 | pico 统一网关思想 |
| 上下文预算 | 五段式分层 + 优先级收缩（当前请求永不裁） | pico 分层上下文 |

### 5.2 LLM 推理层
- 基座：混元 / 通义开源权重，vLLM/SGLang 私有化（呼应 LLM 推理开发岗）；无 Key 自动降级。
- RAG：知识点/考纲/错题做 Embedding → 混合检索（向量+BM25）+ RRF 重排 → 引用溯源、低相关拒答（防幻觉）。
- Prompt / Context Engineering：系统提示 + 用户画像 + 记忆注入。

### 5.3 数据处理层
- 复用现有 SQLite 表（users/questions/quiz_records/wrong_book/daily_streaks/exam_records）。
- 新增向量库（知识点、考纲文档、错题解析）做 RAG 检索源。
- 新增「学习异常指标」采集：模块正确率时序、打卡连续性、刷题密度。

### 5.4 业务层
- 现有全部 `/api/*`（登录、题库、错题、打卡、模考、mastery、explain/gen/report/chat）全部保留。
- 新增 `/api/agent/chat`：统一 Agent 入口（对话即服务）。

---

## 6. 技术栈映射表（Step1-3 → 刷题教练模块）

| 岗位核心技能（Step1） | 刷题教练 Agent 模块 | 技术栈 | 对口 |
|---|---|---|---|
| 任务规划 Planning / 多步推理 | 诊断→讲题→变式→计划 多步编排 | LLM + LangGraph StateGraph | ✅ |
| 工具调用 Tool Use / Function Calling | 掌握度/错题本/题库/讲题 工具化 | Function Calling + 工具网关 | ✅ |
| 记忆管理 Memory | 用户画像/历史错题/会话上下文 | 短期滑窗 + 长期记忆（向量/结构化） | ✅ |
| Multi-Agent / A2A | 诊断/讲题/变式/规划/反思 协作 | Supervisor + 子 Agent | ✅ |
| Prompt / RAG / Context Engineering | 讲题引用考纲/错题、防幻觉 | RAG + 重排 + 引用溯源 | ✅ |
| 私有化部署 / 量化 | 混元/通义内网部署 | vLLM/SGLang、量化 | ✅（演示可云 API） |
| 事实核查 / 证据溯源 | 讲题标注来源、低相关拒答 | Fact-checking pipeline | ✅ |
| AIOps 异常检测 | **学习异常检测**（正确率骤降预警） | 时间序列/指标突变检测 | ✅（场景迁移） |
| 评测闭环 | 命中率/引用率/幻觉率评测集 | 评测框架 | 🔲 待补（Phase E） |

---

## 7. 面试叙事差异化亮点

1. **真实落地产品**：复赛已上线、有完整数据闭环（非玩具 Demo），Agent 是其在生产场景的自然演进。
2. **Agent 五件套齐全**：编排 + 工具 + 记忆 + RAG + 反思，覆盖四厂 Agent 岗高频面试点。
3. **强事实 / 可追溯**：讲题标注引用来源、低相关拒答——呼应腾讯混元「垂域+事实核查」与阿里「数据飞轮」。
4. **场景迁移创新**：把 AIOps 的「异常检测/根因分析」迁移到「学习异常检测」，体现业务结合能力（字节 Data AML 同构）。
5. **可审计**：所有 Agent 工具调用留痕（谁、何时、调了什么），既是合规也是差异化。

---

## 8. 落地路线（分阶段，逐步确认）

- **Phase A（已完成骨架）**：单 Agent + 工具调用（diagnose/wrongbook/plan/chat）+ 分层记忆 + `/api/agent/chat` 入口。
- **Phase B（已落地）**：多轮对话深化 + 上下文预算（五段式）+ 长期记忆持久化（SQLite）。
- **Phase C（已落地）**：RAG（知识点/考纲/错题检索 + 引用溯源 + 防幻觉）。
- **Phase D（已落地）**：多 Agent 编排（LangGraph Supervisor 路由）+ 反思 Agent 主动推送。
- **Phase E（已落地）**：学习异常检测（AIOps 迁移）+ 评测闭环（命中率/引用率/幻觉率）。

> 每个 Phase 完成后确认方向，再继续下一阶段（迭代沟通）。

---

## 9. Phase B 落地记录（2026-07-19）

### 9.1 解决了什么
Phase A 的记忆是**纯内存**（dict/deque），服务重启即丢、跨会话失忆，且每次对话把全量上下文塞给 LLM，无成本控制。Phase B 把记忆改为 **SQLite 持久化 + 五段式上下文预算**。

### 9.2 改动文件
| 文件 | 改动 | 命中面试点 |
|---|---|---|
| `agent/memory.py` | 重写为 `MemoryStore`：长期画像存 `agent_profile` 表、短期对话存 `agent_short_term` 表；新增 `build_context()` 五段式预算拼接（身份/长期画像/诊断摘要/对话历史/当前） | Memory + Context Engineering |
| `agent/orchestrator.py` | `CoachAgent` 接入 `MemoryStore`，意图分流后写入长期画像（last_diagnose/last_plan）+ 短期对话；chat 分支注入五段式上下文 | Planning + 记忆闭环 |
| `agent/tools.py` | `chat()` 直接接收五段式 `context` 字符串（无需改签名） | Tool Use |
| `agent/router.py` | 新增 `session_id` 支持**多会话隔离**；新增 `POST /api/agent/session/clear` 清短期记忆（长期画像保留） | 多会话状态管理 |
| `main.py` | `lifespan` 中 `ensure_agent_tables()` 建表；版本升 `3.1.0-agent-mem` | 部署可运维 |

### 9.3 五段式上下文预算（核心）
```
[身份]     你是「专属刷题教练」AI …（≤240 字符）
[长期画像] 用户昵称/备考方向/最近诊断薄弱模块/最近计划重点（≤420）
[诊断摘要] 工具结果摘要（≤520）
[对话历史] 短期滑窗最近 12 轮（≤1500）
[当前]     用户当前说 + 工具摘要（≤1100）
```
- 总预算默认约 3800 字符；每段独立 `_truncate` 限额，保证「当前用户消息」永远不被裁（优先级最高）。
- 短期滑窗：超出 12 轮自动删最旧轮（防止无限增长）。

### 9.4 验证
- `python -m py_compile` 全文件通过。
- 冒烟测试（fallback 模式，无 Key）覆盖：持久化跨实例读取、滑窗截断、五段式上下文拼接、`CoachAgent.handle` 全意图（diagnose/plan/chat）并验证长期画像落盘 → 全部 PASS。

### 9.5 下一步建议
~~Phase C（RAG）：把"讲题/答疑"从单题升级为检索知识点体系+考纲+错题后作答，并标注引用来源、低相关拒答（防幻觉）。这是命中「LLM 算法优化 / RAG / 事实核查」岗的最强单点。~~（已在 Phase C 完成，见第 10 节）

---

## 10. Phase C 落地记录（2026-07-19）

### 10.1 解决了什么
Phase B 的 chat 仍是「纯生成」——基于单轮记忆自由作答，无法引用**知识点体系 / 考纲 / 用户错题**，且存在幻觉风险（无事实约束）。Phase C 引入 **RAG 检索 + 引用溯源 + 低相关拒答**，让答疑「有据可依、无据拒答」。

### 10.2 改动文件
| 文件 | 改动 | 命中面试点 |
|---|---|---|
| `agent/retriever.py`（新） | `TfidfIndex`（纯 Python TF-IDF + 2-gram 关键词召回 + **RRF 融合重排**）；`KnowledgeRetriever`（语料=知识点聚合+三套考纲+用户错题动态注入；`search` 返回 hits 含引用信息；`format_citations` 生成 [1][2] 引用） | RAG + 重排 + 引用溯源 |
| `agent/tools.py` | 新增 `rag_qa()`：检索→若相关则注入引用让 LLM 作答（标注 [n]）/ 无 Key 走模板作答并附来源；**不相关则明确拒答，绝不编造** | Tool Use + 事实核查 |
| `agent/orchestrator.py` | chat 分支改为走 `rag_qa`，回传 `rag={relevant,citations,top_score,threshold,source}` | 编排 + RAG 闭环 |
| `agent/router.py` | 新增 `POST /api/agent/rag` 独立 RAG 端点（便于演示/评测） | API 边界 |
| `main.py` | 版本升 `3.2.0-rag` | 部署可运维 |

### 10.3 防幻觉设计（核心）
- 相关判据**仅依赖中文 2-gram 关键词真实命中**（`bg_overlap >= 1`）；纯 TF-IDF 的 `sim` 仅用于 RRF 排序，**不单独触发相关**——彻底规避「常见字导致高相似度虚高误判」。
- 无关键词重叠 → `relevant=False` → 返回拒答文案（"没找到足够相关资料，先不瞎编"），不调用 LLM 编造。
- 有 Key 时，系统提示强制「仅基于引用内容作答，论断标 [n]，不足则明说」。

### 10.4 RRF 融合重排
两路召回各自排序后融合：`score = Σ 1/(K+rank)`，K=60。语义路（TF-IDF 余弦）+ 关键词路（2-gram 重叠）。生产可替换为「向量库 + BM25 + RRF」同构（设计稿第 5.2 节）。

### 10.5 验证
- `py_compile` 全过。
- 冒烟（fallback，隔离 DB）：知识库 31 文档（28 知识点 + 3 考纲）；相关 query「概率统计 期望方差」命中且 top=topic 概率统计、带来源题 #1；无关 query「今天天气真好」正确拒答（bg_overlap=0）；用户错题动态注入成功；chat 分支 RAG 命中 + 五条引用 + 记忆落盘 2 轮 → 全部 PASS。

### 10.6 下一步建议
~~Phase D（多 Agent 编排）：用 LangGraph 同构的 `StateGraph` 重写编排层，Supervisor 路由 diagnose/wrongbook/plan/rag_qa，并加「反思 Agent」在诊断/计划后主动补建议与预警。~~（已在 Phase D 完成，见第 11 节）

---

## 11. Phase D 落地记录（2026-07-19）

### 11.1 解决了什么
Phase C 的编排仍是 `orchestrator.py` 里一段 `if/elif` 手写调度，子 Agent 之间无显式图关系、反思逻辑散落、无法扩展为多 Agent 协作。Phase D 引入 **LangGraph 同构的 StateGraph 编排层**：Supervisor 按意图路由子 Agent，统一进入「反思 Agent」做质量校验与主动建议。

### 11.2 改动文件
| 文件 | 改动 | 命中面试点 |
|---|---|---|
| `agent/supervisor.py`（新） | `StateGraph` / `CompiledGraph`：与 LangGraph **同构**的 API（`add_node`/`add_edge`/`add_conditional_edges`/`set_entry_point`/`set_finish_point`/`compile`/`invoke`）；节点为 `async fn(state)->dict`，引擎按边推进、条件边路由、带最大步数防环。生产可一键把 import 换为 `langgraph.graph.StateGraph` | Multi-Agent / Supervisor 编排 |
| `agent/orchestrator.py` | `CoachAgent` 重构：意图分类/诊断/错题/计划/RAG问答/反思 拆成 6 个**节点**，用 `StateGraph` 组装（`classify → 条件边 → 子Agent → reflect`）；`handle` 只负责建 state + invoke + 记忆落盘 | 编排即代码 |
| `main.py` | 版本升 `3.3.0-supervisor` | 部署可运维 |

### 11.3 编排图（核心）
```
classify(Supervisor)
   ├─ diagnose → reflect
   ├─ wrongbook → reflect
   ├─ plan → reflect
   └─ chat → rag_qa → reflect
reflect（反思 Agent）：按意图补一句主动建议/追问
```
- 反思 Agent 不是独立 LLM 调用，而是一个**确定性校验节点**：诊断后推计划、计划后推打卡、RAG 后推追问；保证每次响应都有「下一步动作」，符合 Step3「反思/校验」范式。
- 真实场景可在 reflect 节点再挂一个 LLM 自评（如「回答是否基于引用、是否越界」），本实现以确定性规则保证零依赖可跑。

### 11.4 关键修复（重要）
初版 `invoke` 在循环**顶部**判断 `if cur == finish: break`，导致 finish 节点（reflect）**未执行即退出**——反思建议全部丢失。修正为「先执行节点、再判断终点」后，反思追加正常生效。该 bug 也提醒：编排引擎的「终点语义」必须区分「进入即停」与「执行后停」。

### 11.5 验证
- `py_compile` 全过。
- 冒烟（fallback，隔离 DB）：四意图路由正确（diagnose/plan/chat→rag_qa/无关→rag_qa 拒答）；诊断/计划/答疑 三类响应均被反思节点成功追加建议；长期画像（last_diagnose/last_plan）落盘；短期记忆落盘 2 轮 → 全部 PASS。

### 11.6 下一步建议
~~Phase E（学习异常检测 + 评测闭环）：把 AIOps 的「指标突变/异常检测」迁移到「学习异常」（模块正确率骤降、连续断签、错题反复）；并建评测闭环（引用率/幻觉率/命中率），让 Agent 能力可量化。~~（已在 Phase E 完成，见第 12 节）

---

## 12. Phase E 落地记录（2026-07-19）

### 12.1 解决了什么
Phase A-D 已具备「编排 + 工具 + 记忆 + RAG」，但仍是**被动响应**——用户问才答，且能力是黑盒无法量化。Phase E 补齐两块：
- **主动性**：把 AIOps 的「指标异常检测」迁移到「学习异常」，Agent 在诊断时**主动扫描并预警**（正确率骤降 / 连续断签 / 错题反复）。
- **可观测**：建评测闭环，把每次 RAG 调用落库聚合成「能力体检表」（命中率 / 引用率 / 拒答率 / 幻觉率），让 Agent 能力**可量化、可回归**。

### 12.2 改动文件
| 文件 | 改动 | 命中面试点 |
|---|---|---|
| `agent/anomaly.py`（新） | `LearningAnomalyDetector`：三类异常检测——① `accuracy_drop`（时间序列切 baseline/recent 比均值差，指标突降）② `streak_break`（打卡日期连续缺失天数，指标中断）③ `repeat_wrong`（error_count 阈值，指标反复抖动）；带 severity 分级 + 可解释建议 + `format_alert` 主动推送文案 | AIOps 异常检测迁移 / 主动 Agent |
| `agent/eval.py`（新） | 评测闭环：`log_interaction` 每次 RAG 落库 → `evaluate` 聚合命中率/引用率/拒答率/幻觉率 + 分级 A/B/C；`run_self_eval` 内置样本自评估（无需真实流量即可演示） | LLM 评测 / 可观测性 |
| `agent/tools.py` | `rag_qa` 三个返回点统一经 `_record_rag` 落评测日志（不影响主链路） | 埋点闭环 |
| `agent/orchestrator.py` | `_n_diagnose` 节点接入异常检测，诊断即主动推送预警；`cards.anomaly` + `anomaly_alert` 随响应返回 | 主动编排 |
| `agent/router.py` | 新增 `POST /api/agent/anomaly`（异常检测）、`POST /api/agent/eval?run_self=true`（评测闭环） | API 边界 |
| `main.py` | 启动建 `agent_eval_log` 表；版本升 `3.4.0-anomaly` | 部署可运维 |

### 12.3 AIOps → 学习异常 的迁移映射（核心讲法）
| AIOps 指标异常 | 学习异常 | 检测手段 |
|---|---|---|
| 指标突降（如 QPS 骤跌） | 某知识点正确率骤降 | 时间序列切段比均值差，阈值+幅度分级 |
| 指标中断/缺失 | 连续断签（打卡空窗） | 日期序列连续缺失天数（含当前空窗） |
| 指标反复抖动 | 错题反复（顽固薄弱点） | error_count 阈值分级 |
> 生产可无缝替换为 Z-score / EWMA / 孤立森林，`detect()` 接口保持同构。

### 12.4 评测指标定义（可解释）
- 命中率 `hit_rate` = 相关检索数 / 总调用；引用率 `citation_rate` = 带引用作答数 / 相关数；
- 拒答率 `reject_rate` = 不相关拒答 / 总调用（防幻觉健康度）；
- 幻觉率 `hallucination_rate` = 声称作答（source=rag-llm/rag-fallback）却不相关 / 总调用（设计目标 = 0）。

### 12.5 关键修复（重要）
初版幻觉判定把**拒答**样本（`source="rag"`，即未作答的正确防幻觉行为）误算为幻觉，导致 `hallucination_rate` 虚高。修正为**仅统计「声称作答却不相关」**（source ∈ {rag-llm, rag-fallback}），拒答不计。修复后自评估 `hallucination_rate=0`，符合防幻觉设计目标。这也提醒：评测指标的口径定义必须与「系统真实行为语义」严格对齐。

### 12.6 验证
- `py_compile` 全过、无 lint。
- 冒烟（fallback，隔离 DB，造异常数据）：三类异常全部检出（正确率 90%→27% 骤降 high / 连续 7 天断签 high / 错 6 次反复 high）；诊断意图主动推送预警（`anomaly_alert` + `cards.anomaly`）；评测自评估 6 样本 → hit_rate=0.667、citation_rate=1.0、reject_rate=0.333、**hallucination_rate=0.0**、grade=C；评测日志持久化 → 全部 PASS。

### 12.7 全 Phase 收官
Phase A（Agent 基础包）→ B（SQLite 持久化记忆 + 五段式预算）→ C（RAG + 引用 + 防幻觉）→ D（LangGraph 同构编排 + 反思）→ E（学习异常检测 + 评测闭环）全部落地。项目已从「带 AI 的刷题工具」升级为**会编排、有记忆、能检索溯源、会反思、能主动预警、可量化评测**的定制化备考 Agent。

---

## 13. Phase F 落地记录（2026-07-19）：Agent 推理优化（LLM 推理开发向）

### 13.1 解决了什么
前五个 Phase 让 Agent「能用、可量化」，但未触及**推理成本**这一 Agent 应用开发的核心工程问题。Phase F 把面试高频的 LLM 推理优化技术（量化 / 蒸馏 / KV cache / continuous batching / 投机解码 / 上下文压缩 / 工具替代生成）**做成真实可运行的代码**，无需 GPU、无 API Key 也能跑出量化指标，作为「推理开发深度」的直接证据。

新增 `server/agent/inference.py`，并接入既有编排/工具/评测链路。

### 13.2 优化项与实现映射
| 优化技术 | 在本项目的真实实现（`agent/inference.py`） | 可量化指标 |
|---|---|---|
| **KV cache / 前缀缓存** | `KVCacheManager`：五段式上下文的【身份】【长期画像】【诊断摘要】为稳定前缀，多轮复用；若服务端支持 vLLM `prompt_prefix` 则透传，否则本地测算省下的 prompt token | `kv_cache_hit_rate`、`reused_tokens` |
| **上下文压缩** | `compress_context`：长对话历史用 TF-IDF 抽取式摘要瘦身（复用 `TfidfIndex`），超预算即压缩并记账 | `compressed_saved_tokens` |
| **投机解码** | `speculative_decode` + `draft_from_ngram`：草稿小模型(2-gram)先出 token，目标模型按拒绝采样逐位校验 | `spec_accept_rate` |
| **知识蒸馏 KD** | `Distiller`：teacher(大模型)生成讲题/变式 → student(确定性规则)近似；纯 Python ROUGE-N 评保真度 | `kd_pairs`、`rouge2`、`kd_teacher_cost_tokens` |
| **连续批处理** | `InferenceBatcher.run_bench`：串行 vs 一次 gather 对比并发吞吐 | `batch_merged_requests`、`speedup` |
| **工具替代生成** | 诊断/错题本走工具确定性返回（0 token），`mark_tool_substitution` 记账 | `tool_substitutions` |
| **量化 / AWQ** | `QUANT_CONFIG` + `enable_quantization`：私有化部署透传 `quantization=awq`、`bits=4` | `quant_mode` |

### 13.3 改动文件
| 文件 | 改动 |
|---|---|
| `agent/inference.py`（新） | 推理优化层：7 项优化 + `MetricsLedger` 全局台账 + `run_infer_demo` 离线自演示 |
| `agent/tools.py` | 3 个生成型工具走 `optimized_call_llm`（KV 前缀 + 压缩 + token 记账）；诊断/错题本 `mark_tool_substitution` |
| `agent/orchestrator.py` | 意图分类走 `optimized_call_llm` |
| `agent/eval.py` | `evaluate` 输出附 `inference_optimization` 指标 |
| `agent/router.py` | 新增 `POST /api/agent/infer/optimize`（自演示）、`GET /api/agent/infer/status`（台账） |
| `main.py` | 版本升 `3.5.0-infer-opt`；启动打印推理优化模式；`/api/health` 返回 `infer_opt` 开关 |

### 13.4 自演示实测（无 Key / 无 GPU，本机）
调用 `POST /api/agent/infer/optimize` 实测结果：
- KV 前缀缓存：`reused_tokens=96`、`kv_cache_hit_rate=0.8`
- 上下文压缩：`compressed_saved_tokens=766`
- 投机解码：`accept_rate=1.0`（草稿 8 token 全接受）
- 知识蒸馏：`kd_pairs=10`、`rouge2=0.516`（student 对 teacher 保真度）
- 连续批处理：`speedup≈8.3x`（串行 0.125s → 批处理 0.015s）
- 工具替代生成：`tool_substitutions=3`
- 量化：`quant_mode=awq-4bit`（生产透传）

### 13.5 面试讲法
「刷题教练不是堆功能，而是**推理成本敏感**的设计：稳定前缀可 prefix cache、该查库不生成直接砍推理量、上下文预算即 context 压缩、评测闭环可同时比对 teacher/student——这些推理优化技术本来就是 Agent 降本的标配，我已经在代码里把它们跑成可量化的指标。」

---

## 14. Agent-native Harness 参考（nanobot / HKUDS 黄超教授实验室）

### 14.1 背景与定位
团队 Vibe-Trading（量化）与 Deep Tutor（教育）同日登 GitHub 全球 Trending 第一/第二，验证「**一个核心 Harness + 每垂直域一套 Skills/Memory/Tools**」的 Agent-native 打法可行。经调研，港大黄超教授 HKUDS 实验室的 **nanobot**（45.9k⭐，~4000 行可自托管运行时，MIT）正是这一范式的最佳解剖样本——它也是黄超教授系列开源（AutoAgent 一句话造 Agent、DeepCode AI 分析论文代码）的同门。

> 关键澄清：**nanobot 即黄超教授 HKUDS 的项目**；「学习黄超教授项目」与「学习 nanobot」是同一来源。

### 14.2 nanobot 架构 → 刷题教练 映射
| nanobot 模块 | 设计哲学 | 刷题教练 对应 |
|---|---|---|
| **Channel 接入层** | 统一 `Message`，WebUI/CLI/API + 飞书/微信/Telegram… | `coach.html` / 小程序 / `/api/agent/chat`；未来垂直域（Vibe-Trading/Deep Tutor）复用同一 core，仅换 Skills |
| **Bus 总线层**（~45 行异步双队列） | 解耦「通信」与「思考」 | 编排层 `supervisor.py` 的 `StateGraph` 引擎（节点异步推进、条件边路由）同构 |
| **ReAct Loop**（Observe→Reason→Act 状态机） | 核心引擎 | `CoachAgent` 六节点编排 + 反思节点 |
| **虚拟工具范式**（不执行的「幽灵 Function Definition」） | 用 Function Calling 协议约束结构化输出，替代脆弱 Prompt 指令 | **Phase G 已落地**：`llm.call_llm_tool` 替代 `response_format=json_object`（见第 15 节） |
| **三层记忆**（Session/HISTORY.md/MEMORY.md） | 短期+.jsonl、中长期 append-only grep、长期全量注入 | Phase B 已落地：`agent_profile`(长期画像) + `agent_short_term`(短期) + 五段式预算；可进一步补「可 grep 的中长期事件日志」 |
| **Skills + 原生 MCP** | 垂直能力以插件注入 | `agent/tools.py` 工具集 + `rag_qa`；生产可接 MCP 接行情/题库 |
| **Model Freedom** | OpenAI 兼容自定义 providers、本地 Ollama/vLLM、fallback | **Phase G 已落地**：`llm.PROVIDERS` 多厂商注册表（智谱/Kimi/混元/豆包/千问/DeepSeek/OpenAI） |

### 14.3 借鉴要点（用于后续垂直域）
1. **极简可自托管**：核心小而可读（<4000 行），不搞巨石——刷题教练编排层坚持 `StateGraph` 同构、可一键换 LangGraph。
2. **协议层约束输出**：结构化数据交给 Function Calling，不靠 Prompt 硬凑 JSON（这正是 Phase G 的虚拟工具改造动机）。
3. **记忆务实分层**：在 Token 与持久性间找平衡，短期/中长期/长期三档物理分离。
4. **Channel 与思考解耦**：新垂直域（Vibe-Trading/Deep Tutor）只写 Skills+Memory，接入层不动。

---

## 15. Phase G 落地记录（2026-07-19）：多厂商注册表 + 虚拟工具范式

### 15.1 解决了什么
两个工程痛点：
- **单厂商锁定**：原 LLM 调用层（含 `main.py` 的 `AI_CONFIG`）只认一个 OpenAI 兼容端点，无法在智谱/Kimi/混元/豆包/千问/DeepSeek/OpenAI 间切换——与「多基座可切换」的面试叙事脱节。
- **结构化输出脆弱**：`/api/explain|gen|report` 依赖 `response_format=json_object`，部分厂商对该模式支持不稳（返回带 ```json 包裹、字段漂移），易解析失败。

Phase G 把调用层升级为**多厂商注册表 + 虚拟工具范式**：① 7 家主流模型一键切换（环境变量驱动、运行期可切）；② 结构化输出改用 Function Calling 截获 `tool_calls.arguments`，协议层保证严格 JSON。

### 15.2 改动文件
| 文件 | 改动 | 命中面试点 |
|---|---|---|
| `agent/llm.py` | 重写为**多厂商注册表** `PROVIDERS`（智谱/GLM·Kimi/Moonshot·腾讯混元·字节豆包Ark·阿里千问/通义·DeepSeek·OpenAI），统一 OpenAI 兼容 `/chat/completions`；`_pick_active` 按 `LLM_PROVIDER`→首个有 Key→历史变量→降级 选激活厂商；导出 `LLM_CONFIG/HAS_KEY/active_provider/switch_provider/list_providers`（向后兼容 `inference.py`/`main.py`）；新增 `call_llm_tool`（虚拟工具范式） | 多模型基座 / Function Calling / 协议层约束 |
| `agent/router.py` | 新增 `GET /api/agent/providers`（列所有厂商+是否配置 Key+激活态）、`POST /api/agent/providers/switch`（运行期切厂商，需该厂商有 Key） | API 边界 / 模型选择器后端 |
| `main.py` | 删除旧 `AI_CONFIG` 与本地 `call_llm`/`_extract_json`，改用 `agent.llm` 激活配置；`/api/explain|gen|report` 改走 `_structured_llm`→`call_llm_tool`（虚拟工具）；无 Key/解析失败自动降级 `fallback_*`；启动打印激活厂商；`/api/health` 返回 `llm_provider/llm_model/llm_label`；版本升 `3.6.0-harness` | 多厂商 / 结构化输出健壮性 |

### 15.3 多厂商注册表（核心）
- 每个厂商含 `api_base / key_envs / default_model / supports_json`；可用 `<PROVIDER>_API_KEY`、`<PROVIDER>_MODEL`、`<PROVIDER>_API_BASE` 覆盖。
- 激活优先级：`LLM_PROVIDER` 指定 → 自动选第一个配置了 Key 的厂商 → 历史 `API_KEY/API_BASE/MODEL` 兜底（custom）→ 无 Key 降级（调用方走规则模式）。
- 运行期 `switch_provider(name)` 切换（仅限已配置 Key 的厂商），利于演示「同一 Agent 换基座」。

### 15.4 虚拟工具范式（核心）
```python
# llm.py：发一个 function definition，截获 arguments 作为严格结构，不真实执行
payload["tools"] = [{"type":"function","function":{"name":tool_name,"parameters":tool_schema}}]
payload["tool_choice"] = {"type":"function","function":{"name":tool_name}}
# → 取 choices[0].message.tool_calls[0].function.arguments 解析为 dict
```
- 相比 `json_object`：Function Calling 协议对参数有严格 JSON Schema 约束，且被所有 OpenAI 兼容端点统一支持——nanobot 同款「幽灵工具」技巧。
- `main.py` 为 explain/gen/report 各定义一份 JSON Schema（`_EXPLAIN_SCHEMA/_GEN_SCHEMA/_REPORT_SCHEMA`），并在返回空 dict 时回退到确定性 `fallback_*` 模板，保证前端始终可用。

### 15.5 验证
- `python -m py_compile` 全过（`agent/llm.py`、`main.py`、`agent/router.py`），无 lint。
- 接口就绪：`GET /api/agent/providers` 返回激活厂商与各厂商配置态；`POST /api/agent/providers/switch {"provider":"moonshot"}` 在配置 Key 后切到 Kimi；`GET /api/health` 新增 `llm_provider` 字段。
- 降级路径保持：无 Key 时 explain/gen/report 仍走 `fallback_*`，结构化输出失败也自动回退，不破坏前端。

### 15.6 下一步建议
- **Phase H（Channel 接入层）**：把 `coach.html`/小程序/未来 Vibe-Trading/Deep Tutor 统一到「一个 Agent core + 多 Channel」的 nanobot 式接入层，垂直域只注入 Skills+Memory+MCP 工具（呼应第 14 节）。
- **三层记忆补中长期档**：在现有短期(`agent_short_term`)+长期(`agent_profile`)之外，加一层「可 grep 的中长期事件日志」（错题反复/专题突破），贴合 nanobot 的 HISTORY.md 设计。
- **MCP 接垂直工具**：讲题 Agent 接 MCP 接行情/题库/考纲源，复用 nanobot 的 Skills+MCP 扩展机制。

> 以上三项已在 **Phase H** 落地，详见 §16（Channel 接入层）/ §17（三层记忆中期档）/ §18（MCP 接垂直工具）。

---

## 16. Phase H 落地记录（2026-07-19）：Channel 接入层（一个 Agent core + 多 Channel）

### 16.1 解决了什么
之前 CoachAgent 直接被 FastAPI 路由调用，来源（Web / 小程序 / 未来 Vibe-Trading / Deep Tutor）与 Agent 逻辑耦合。要复用到其它垂直域，需为每个域重写接入。

nanobot 的启示：**Channel 接入层把「通信来源」与「思考」解耦**。核心 Agent 只处理统一消息，新渠道注册即插即用。

### 16.2 新增 `agent/channel.py`
| 组件 | 作用 |
|---|---|
| `InboundMessage` / `OutboundMessage` | 渠道无关的入站/出站消息（user_id/content/session_id/channel/extra） |
| `Channel`（基类） | `receive()` / `send()` 抽象 |
| `ApiChannel` | HTTP API 渠道：`dispatch(inbound)` 调 `CoachAgent.handle`，出站经 router 透传 JSON |
| `CliChannel` | 本地 CLI 渠道：`asyncio.to_thread(input)` 读 stdin、`print` 回 stdout，无 Web 也能跑 Agent |
| `AgentHub` | 渠道中枢：注册多 Channel，统一 `dispatch_api()`；单例 `HUB` 被 router 与 CLI 共享同一 Agent 实例 |

### 16.3 改动
- `router.py`：`/api/agent/chat` 改为经 `HUB.dispatch_api(...)`（返回结构不变，前端兼容）；新增 `GET /api/agent/channels`（列 api/cli/未来飞书微信等）。
- 新增 `server/run_agent_cli.py`：本地 CLI runner，`python run_agent_cli.py [user_id]` 直接驱动 Agent，验证 Channel 解耦。
- `main.py` 启动打印接入渠道；`/api/health` 返回 `channels`。

### 16.4 复用价值（面试讲法）
「刷题教练不是为 Web 写的 Agent，而是**一个 Harness**：接入层屏蔽来源，未来 Vibe-Trading/Deep Tutor 直接复用 `CoachAgent` core，只换 Skills+Memory+MCP 工具——这正是我们团队两个 Trending 项目验证过的『一核多域』打法。」

---

## 17. 三层记忆补中长期档（nanobot HISTORY.md 同构）

### 17.1 之前 vs 现在
| 层 | 之前 | 现在 |
|---|---|---|
| 短期 | `agent_short_term`（单 session 滑窗） | 不变 |
| **中长期** | ❌ 缺 | ✅ 新增 `agent_history`（append-only，可 grep） |
| 长期 | `agent_profile`（用户画像） | 不变 |

### 17.2 新增 `agent_history` 表（memory.py）
- 字段：`user_id / session_id / kind / payload / created_at`，`kind` 区分 diagnose/plan/rag/wrongbook/milestone/anomaly。
- `MemoryStore.record_event(kind, payload)`：append-only 写入。
- `MemoryStore.search_history(keyword, limit)`：无 keyword 取最近 N 条；有 keyword 按 `payload LIKE` 模糊检索（**可 grep**）。
- `build_context` 由五段式扩为**六段式**：新增 `[近期事件]` 段（最近 6 条事件摘要），让 Agent 跨会话记住「这周诊断出什么薄弱、定了什么计划」。

### 17.3 落点（orchestrator.py 各节点）
- 诊断 → `record_event("diagnose", "诊断薄弱模块：…")`
- 错题本 → `record_event("wrongbook", "查看高频错题 N 道")`
- 计划 → `record_event("plan", "冲刺重点：…")`
- RAG → `record_event("rag", "RAG相关=True 引用数=N")`

### 17.4 接口与价值
- 新增 `POST /api/agent/history`：检索中长期事件（前端可渲染「学习时间线」）。
- 面试讲法：「记忆不只是多轮上下文，而是**务实分层**：短期保对话、长期保画像、中长期保『发生了什么大事』——后者用 append-only + 关键词检索，比全量重灌更省 token，也比纯向量更可解释。」

---

## 18. MCP 接垂直工具（Skills + MCP 插件化，nanobot 同款）

### 18.1 设计
新增 `agent/mcp.py`：**声明式 MCP 桥**，不依赖第三方 MCP SDK（零依赖、可编译运行）。
- `MCPToolSpec(name/description/input_schema/source)`：工具声明。
- `MCPBridge`：
  - `register_builtin(spec, func)`：注册内置 MCP 兼容工具；
  - `list_tools()`：聚合内置工具 +（配置了 `MCP_SERVER_URL` 时）远程工具；
  - `call(tool, args)`：内置直接 `func(args)`；远程走 HTTP JSON-RPC（`tools/list` / `tools/call`）。
- 降级：远程不可达时返回错误提示，内置工具始终可用。

### 18.2 内置示例工具（证明范式已打通）
| 工具 | 作用 | 对应垂直能力 |
|---|---|---|
| `exam_syllabus` | 按分类检索考纲概览（考研/考公/大厂） | 考纲源 |
| `question_bank_search` | 按知识点检索垂直题库 | 题库源 |

### 18.3 接入方式
- `tools.py` 的 `CoachTools` 内建 `MCPBridge`，暴露 `mcp_call(tool, args)` / `list_mcp_tools()`。
- 新增 `GET /api/agent/mcp/tools`（列内置+远程工具）、`POST /api/agent/mcp/call`（调用工具）。
- 接真实垂直 MCP server（行情/题库/考纲）：仅设 `MCP_SERVER_URL`（+ 可选 `MCP_SERVER_KEY`），**无需改代码**——正是「核心 Harness + 垂直 Skills」红利。

### 18.4 面试讲法
「Agent 的核心不膨胀，垂直能力以 MCP 工具注入：本地用内置工具演示范式，生产接飞书/行情/题库的 MCP server，只改环境变量。这套 Skills+MCP 扩展机制直接复用了 nanobot（HKUDS）的成熟设计。」

---

## 19. 版本与接口清单（截至 Phase H）
- 版本：`3.7.0-channel-history-mcp`（`main.py` / `/api/health`）。
- 新增端点：`GET /api/agent/channels`、`POST /api/agent/history`、`GET /api/agent/mcp/tools`、`POST /api/agent/mcp/call`。
- 新增模块：`agent/channel.py`（Channel 接入层）、`agent/mcp.py`（MCP 桥）、`server/run_agent_cli.py`（CLI 调试）。
- 记忆表新增：`agent_history`（中长期事件日志）。
