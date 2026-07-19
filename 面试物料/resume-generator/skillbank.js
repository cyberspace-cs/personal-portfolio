// 面试题库 + 话术（基于 2026 公开经验帖整理：字节Agent四面21题、小林coding Agent16/RAG20/工具调用16/工程22、具身智能Gank面经、DeepSeek模型专项）
// 每题含：q(题目) / a(答题方向，1-2行)。按类目组织，适配包按厂抽取。

export const CAT_TITLE = {
  PROMPT: "Prompt 工程与输出控制",
  RAG: "RAG 检索增强",
  AGENT: "Agent 系统设计",
  TOOL: "工具调用 / MCP / 协议",
  TRAIN: "训练 / 微调 / 对齐",
  INFER: "推理优化与部署",
  ENGINEER: "工程落地与系统能力",
  EMBODIED: "具身智能专项",
  PM: "AI 产品经理专项",
};

export const bank = {
  PROMPT: [
    { q: "Prompt Engineering 的核心目标？为什么同一件事换个说法效果差十倍？", a: "把意图翻译成模型最易理解的形式；模糊 Prompt 概率分散，精准 Prompt 概率集中到目标路径。" },
    { q: "System Prompt / Few-shot / Chain-of-Thought(CoT) 分别解决什么问题？", a: "System 定角色风格(全程生效)；Few-shot 对齐格式/模式；CoT 把复杂推理中间步骤写出以纠偏。" },
    { q: "Token、上下文窗口、上下文腐化(Lost in the Middle)是什么？", a: "Token 是最小单位；窗口是单次可见总量；早期内容被后续稀释导致注意力下降即上下文腐化，需精准控制窗口内容。" },
    { q: "什么是 Structured Output？如何控制模型输出？", a: "强制 JSON/固定格式；用 JSON Schema 约束比纯 Prompt 稳定，下游才能自动解析（聊天→系统的关键）。" },
    { q: "如何降低模型幻觉？", a: "组合：RAG 供事实、Function Calling 查实时、Structured Output 限格式、Prompt 声明不知就说不知、多轮/双模型 fact-check。" },
  ],
  RAG: [
    { q: "RAG 原理与全链路？", a: "切分→Embedding→向量库→检索→重排→拼上下文→生成；落地链路要可观测可评估。" },
    { q: "文档如何切分？Chunk 大小怎么定？", a: "512-1024 Token、重叠 50-100；太细丢上下文、太粗不精准，按召回效果调。" },
    { q: "Embedding 选型与向量数据库？", a: "Milvus/Pinecone/Weaviate 做相似度检索；语义近则向量近，支持跨语言召回。" },
    { q: "混合检索怎么做？", a: "向量(语义)+关键词(精确) 用 RRF 倒数排名融合，比单一检索显著更好。" },
    { q: "Query 改写 / HyDE 是什么？", a: "HyDE 先生成假答案再用其 Embedding 检索，与真实文档语义更接近，召回更准。" },
    { q: "Rerank 怎么做、为什么需要？", a: "Bi-Encoder 快但不精，用 Cross-Encoder 重排把相关项前置，提升答案相关性。" },
    { q: "如何缓解 RAG 幻觉 / 做引用溯源？", a: "检索段落带引用标号 + 末尾强制附引文 + 事实核查；citation_rate/hallucination_rate 量化。" },
    { q: "RAG 效果如何评估？", a: "召回率/答案相关性/忠实度(是否编造)；离线四率 + 在线 A/B。" },
  ],
  AGENT: [
    { q: "什么是 Agent？与大模型本质不同？", a: "Agent = 思维链 + Function Calling + 循环；模型自主决定下一步，而非逐步指挥（概率性自主运行）。" },
    { q: "Agent 核心组件？", a: "规划(Planning) + 记忆(Memory) + 工具(Tools) + 执行(Execution) + 反思(Reflection)。" },
    { q: "Workflow / Agent / Tools 区别？", a: "Tools 是原子能力；Workflow 是固定编排(确定性)；Agent 是模型动态决策(概率性)。" },
    { q: "ReAct 是什么、如何实现？", a: "Reason+Act 交替：先推理再调工具观察结果，循环至完成；实现上每轮输出 Thought/Action/Observation。" },
    { q: "ReAct / Plan-and-Execute / Reflection 区别与选型？", a: "ReAct 边想边做(简单)；Plan-and-Execute 先整体规划再执行(复杂长任务)；Reflection 加自评纠偏(质量要求高)。" },
    { q: "复杂任务如何拆分？为什么要拆分？", a: "拆成明确输入输出的子任务，便于校验/并行/回滚；单任务失败不影响整体。" },
    { q: "记忆机制如何设计(短期/长期)？", a: "短期=最近N轮+工作记忆(关键约束)；长期=向量库/SQLite 外部存储按需检索；分层+衰减。" },
    { q: "记忆压缩有哪些方法？", a: "滑动窗口、对话摘要、关键信息提取(决策/约束/偏好每轮注入)、向量库检索长期。" },
    { q: "多 Agent 如何协作与动态切换？", a: "Supervisor 拆任务→Worker 并行→Synthesizer 汇总；消息队列解耦；按任务复杂度动态选子 Agent。" },
    { q: "为什么有时手搓 Agent 而非用框架？", a: "框架有抽象开销/黑盒；手搓对循环、记忆、工具调用完全可控，便于调试与极致优化。" },
    { q: "如何赋予 LLM 规划能力？", a: "Prompt 引导分步 + 外部 Planner/ReAct + 任务树；复杂场景用 Plan-and-Execute。" },
    { q: "反思机制是什么、为什么、怎么实现？", a: "让模型/独立检查 Agent 复盘输出矛盾并回退重规划；防环防偏；节点校验+循环检测。" },
    { q: "如何解决上下文漂移？", a: "每轮注入原始目标 + 阶段性总结 + 上下文压缩 + 独立监督 Agent 拉回。" },
    { q: "如何防止工具调用幻觉？", a: "严格工具 Schema + 工具白名单(执行层拦截未注册) + 参数校验(类型/枚举)。" },
  ],
  TOOL: [
    { q: "Function Calling 与 RAG 区别联系？何时用哪个？", a: "FC 调实时/结构化接口并执行；RAG 补私有/离线知识。实时或执行→FC；领域知识→RAG；常组合。" },
    { q: "MCP 是什么、解决什么问题？", a: "工具标准化接口，AI 的「USB-C」；工具实现一次协议，所有模型可用，换模型不改工具。" },
    { q: "Skill 与 MCP 区别？", a: "MCP=工具层标准化；Skill=能力层封装复用(能做什么/输入输出/依赖工具)，即插即用。" },
    { q: "Agent 如何设计能力复用与 Skill 管理？", a: "注册表自动发现 + 版本管理 + 组合编排 + 权限隔离 + 热插拔。" },
    { q: "A2A 协议 / LLM 网关是什么？", a: "A2A 解决 Agent 间协作通信；LLM 网关统一鉴权/限流/路由/观测多模型调用。" },
    { q: "SSE / WebSocket 区别？", a: "SSE 单向服务器推(适合流式生成)；WebSocket 全双工(适合双向交互)。" },
    { q: "Harness 概念与实现？", a: "Agent 的运行骨架(上下文管理/工具调度/循环控制)；需清楚记忆机制、工具调用、上下文管理实现。" },
  ],
  TRAIN: [
    { q: "微调 vs RAG 场景区别？", a: "让模型「知道新知识」用 RAG；「学会新能力/稳定风格推理」用微调。多数应用 RAG 优先。" },
    { q: "SFT vs RLHF 哪个适合快速迭代？破局点？", a: "SFT 快(几小时)；RLHF 对齐偏好但链路长。破局：SFT 重数据质量；RLHF 走向可验证奖励(Verifiable Reward)。" },
    { q: "LoRA 是什么？", a: "低秩适配，冻结原权重只训低秩矩阵，省显存可热插拔，适合垂域快速微调。" },
    { q: "RLHF / DPO / GRPO 区别？为何 DeepSeek 用 GRPO？", a: "RLHF 需 Reward Model+PPO；DPO 直接偏好对齐；GRPO 用组内相对优势、去掉 Critic 模型，更稳定省资源。" },
    { q: "Post-training 是什么？", a: "预训练后对齐阶段(SFT+RLHF/DPO)，让模型符合指令与人类偏好、适配业务。" },
  ],
  INFER: [
    { q: "如何降低推理成本？", a: "模型选择(小模型做简任务) + KV Cache + 量化(INT8/INT4) + 批处理(continuous batching)。" },
    { q: "KV Cache 是什么、为什么重要？", a: "缓存历史 Token 的 K/V 避免重复计算，自回归生成最基础也最明显的加速。" },
    { q: "量化怎么做、精度损失？", a: "FP16→INT8/INT4，精度损失有限但速度与显存大幅下降；AWQ/GPTQ 保关键权重。" },
    { q: "vLLM / continuous batching 是什么？", a: "vLLM 用 PagedAttention 管理 KV；continuous batching 动态拼请求提升 GPU 利用率。" },
    { q: "混合路由与限流器为什么重要？", a: "简单任务走小模型省成本、复杂走大模型保质量；令牌桶限流防 429，关键路径优先。" },
    { q: "端侧部署怎么做？", a: "量化+蒸馏压缩模型，配合推理框架(如 ONNX/TFLite)在移动/边缘跑，低延迟。" },
  ],
  ENGINEER: [
    { q: "Agent 执行链路如何设计、保证连续任务正确？", a: "输入→规划→拆子任务→执行→汇总→判完成；状态持久化+Checkpoint+结果校验+超时重试+人工介入点。" },
    { q: "长任务如何保证不偏离目标？", a: "每轮注入原始目标 + 阶段自查 + 外部监督 Agent + 任务分解 + 上下文压缩。" },
    { q: "工具调用安全如何做(Key泄露/敏感信息/Prompt注入)？", a: "Key 不进上下文(执行层注入)+最小权限+输出过滤+Prompt注入检测+审计日志。" },
    { q: "传统 Web 与 AI Agent 应用区别？", a: "Web 确定性/可单测；Agent 概率性/循环态/成本按 Token/靠评估与 Bad Case。" },
    { q: "如何评估生成模型多样性与准确性？", a: "多样性 CLIP Score 方差/FID；准确性 CLIP Score+人工+A/B；Bad Case 分析闭环。" },
  ],
  EMBODIED: [
    { q: "大模型装进机器人与纯软件 Agent 有何不同？", a: "感知需3D视觉+Affordance；控制输出 Action Token 且面临低频推理(1-5Hz)vs高频控制(>500Hz)；幻觉会撞人需硬件级安全；数据饥渴需仿真飞轮。" },
    { q: "分层(Pipeline) vs 端到端(VLA/RT-2)架构区别？", a: "Pipeline 感知-规划-控制分离、可解释可控；VLA 图像+语言直接映射 Action Token，端到端泛化但难调试。" },
    { q: "如何解决真实数据稀缺？", a: "Sim-to-Real(域随机化/系统辨识)+模仿学习预热+强化学习微调+合成数据填补物理荒漠。" },
    { q: "RT-1 与 RT-2 核心区别？为何 RT-2 是 VLA？", a: "RT-1 输出离散动作；RT-2 把动作也 Token 化进同一个 VL 模型自回归预测，打通文本与动作。" },
    { q: "Affordance(可供性)是什么？", a: "物体能被如何操作的知识(如海绵是软的、可抓取)；LLM 语义需对齐重力/臂展等物理常识防幻觉动作。" },
    { q: "频率失配(1Hz大脑 vs 500Hz身体)如何解决？", a: "分层混合：慢思考(VLA/LLM)做高层决策 + 快执行(MPC/PID)做底层控制，解耦。" },
    { q: "如何防止大模型幻觉伤人？", a: "安全过滤器+动力学校验+看门狗机制+多模态一致性校验，硬件级兜底。" },
    { q: "如何评估具身模型好坏？只看 PPL 够吗？", a: "不够；看任务成功率(Success Rate)/完成度/泛化，结合仿真与真机指标。" },
  ],
  PM: [
    { q: "如何定义一款 Agent 产品？", a: "从用户真实痛点出发(非技术炫技)；定义角色边界、何时用工具、如何评估效果，而非「套个聊天框」。" },
    { q: "如何设计 Agent 产品指标？", a: "四率(命中/引用/拒答/幻觉)+A/B+留存/转化；用数据反推功能优先级。" },
    { q: "竞品分析怎么做？", a: "按能力/场景/定价/生态拆维度，找差异化切入点(如可解释、低代码、垂域)。" },
    { q: "低代码/自然语言构建 Agent 的产品价值？", a: "抹平技术鸿沟，让业务/非技术同学自助搭建，沉淀 Agent 生态与留存。" },
    { q: "技术团队冲突如何同频推进？", a: "用 PRD+技术边界共识+指标对齐；能读得懂 LangGraph/MCP/RAG 以评估可行性。" },
    { q: "0→1 产品如何验证？", a: "MVP+开源复用快速验证，成本自负盈亏；用数据证明需求与商业化可行。" },
    { q: "Agent 产品如何做可解释与信任？", a: "引用溯源、过程可见、可纠错；信任是 C 端留存核心卖点。" },
  ],
};

// ===== STAR 话术：结合本项目(刷题教练→定制化备考 Agent v3.1.0-agent-mem) =====
// 每题：ask(面试官可能问) + star(S/T/A/R 四段，引用 data.js 的 Phase 与量化)
export const starScripts = [
  {
    tag: "项目总览",
    ask: "请介绍一个你最自豪的 Agent 项目。",
    star: `S(背景)：复赛「专属刷题教练」只是单轮问答工具，用户反馈「刷题为辅、陪练/诊断/规划才是刚需」。
T(任务)：把它升级为定制化备考 Agent，要可陪练、可追溯、可多轮、可在无 API Key 下运行。
A(行动)：用 LangGraph 搭 Supervisor 多 Agent(llm/memory/tools/orchestrator/router 五模块)；MCP 风格工具网关统一 Function Calling；SQLite 落分层记忆；RAG(TF-IDF+2-gram+RRF)做引用溯源；反思节点防环；离线四率+在线 A/B 评测闭环。
R(结果)：citation_rate=1.0、hallucination_rate=0.0(已上线)；hit_rate=0.667；推理 speedup≈8x、kv_cache_hit≈0.8；工程复用两个 GitHub Trending 开源项目同源 core，零依赖规则降级可用性 100%。`,
  },
  {
    tag: "技术挑战",
    ask: "你遇到的最大技术挑战是什么？怎么解决的？",
    star: `S：RAG 在备考场景一旦编造知识点会直接误导用户，信任崩塌。
T：要把「幻觉率」压到可上线水平并能量化。
A：检索段落带引用标号 + 答案末段强制附引文 + 事实核查节点；混合召回(TF-IDF+2-gram+RRF)提升相关段命中；离线监控 hallucination_rate。
R：hallucination_rate=0.0、citation_rate=1.0，成为产品核心卖点(可解释信任)。`,
  },
  {
    tag: "评测体系",
    ask: "你如何做 Agent 评测？",
    star: `S：Agent 效果不能只「能跑」，需可量化可迭代。
T：建立可对比的评测体系指导迭代。
A：离线四率(hit/citation/reject/hallucination) + 在线 A/B + Prometheus 可观测(latency/QPS/命中)；对齐 SWE-Bench/TAU-Bench 工程化思路。
R：用数据反推功能优先级，拒绝兜底与反思节点据此上线，质量可测可控。`,
  },
  {
    tag: "多Agent",
    ask: "多 Agent 怎么设计？为什么不用单一 Agent？",
    star: `S：单 Agent 在长任务里易上下文漂移、难并行。
T：需要角色分工与防环。
A：Supervisor 拆子任务→Worker 并行(陪练/诊断/规划)→Synthesizer 汇总；反思节点校验矛盾并回退重规划；循环检测+拒绝兜底防死循环；同比 AutoGen/CrewAI 同构。
R：复杂备考任务一致性提升，用户纠错成本下降。`,
  },
  {
    tag: "推理优化",
    ask: "推理优化你做过什么？",
    star: `S：高质量陪练成本高，免费用户难用。
T：在保质量前提下降本提速。
A：vLLM/continuous batching + KV Cache 复用 + INT8 量化 + 投机解码；Benchmark 化推理链路。
R：speedup≈8x、kv_cache_hit≈0.8，免费用户也能用高质量陪练，扩大漏斗顶部。`,
  },
  {
    tag: "产品思维(PM)",
    ask: "你如何定义 Agent 产品并验证需求？",
    star: `S：复赛发帖文案显示用户痛点是「陪练/诊断/规划」而非刷题。
T：定义「备考 Agent」而非「刷题工具」。
A：四类痛点解法(RAG 可解释/分层记忆/多 Agent 陪练/评测闭环)；两开源项目同源复用验证 0→1；指标驱动迭代。
R：可解释成为卖点，推理优化让免费用户可用，验证商业化可行(成本自负盈亏)。`,
  },
  {
    tag: "工程落地",
    ask: "Agent 系统如何保证连续任务正确与可降级？",
    star: `S：无 API Key 或工具失败会导致系统不可用。
T：保证高可用与正确性。
A：状态持久化+Checkpoint；工具白名单+参数校验防调用幻觉；无 Key 时纯检索+RAG 规则降级；可观测采集全链路。
R：规则降级可用性 100%，关键路径不卡死。`,
  },
  {
    tag: "职业规划",
    ask: "为什么选 Agent 应用开发 / 为什么投我们？",
    star: `S：看到 2026 招聘从「大模型基础」转向「AI 应用落地」，Agent 是核心。
T：希望在最落地、最需要工程深度的团队打磨。
A：已具备 Agent 框架/RAG 防幻觉/多 Agent/推理优化/评测闭环全链路经验，且持续跟进 MCP/Skill 等 2026 新标配。
R：希望把可量化、可降级的 Agent 落地方法论带到贵司 {岗位}。`,
  },
];

// 反问清单（面试官问「你有什么想问的」）
export const reverseQuestions = [
  "该岗位负责的 Agent 业务当前最痛的点是「能力」还是「落地/成本」？团队更看重哪块？",
  "Agent 评测体系现状：是离线四率为主，还是已有在线 A/B / 可观测看板？",
  "技术栈是否会走向 MCP / Skill 标准化？工具接入是框架封装还是自研 Harness？",
  "当前推理成本与并发压力如何？是否有端侧/量化部署需求？",
  "这个岗位 0→1 还是 1→N？OKR 更偏业务指标还是技术基建？",
  "团队协作上，算法/工程/产品如何分工？产品经理是否参与 Agent 评测指标定义？",
];
