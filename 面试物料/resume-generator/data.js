// 打磨后的简历结构化数据（两份方向：engineer / pm）
// 所有数字指标为固定资产，分厂复用。

export const contact = {
  name: "【姓名】",
  phone: "【电话】",
  email: "【邮箱】",
  base: "深圳 | 本科 | 3 年经验",
  links: "GitHub: github.com/【id】 · 作品集: portfolio.【domain】 · 博客: 【domain】",
};

// ============ 工程方向：大模型 Agent 应用开发工程师 ============
export const engineer = {
  summary:
    "AI Agent 应用开发工程师，3 年 LLM 应用落地经验。主导「专属刷题教练」从复赛工具升级为定制化备考 Agent（LangGraph 编排 + 混元/通义基座 + MCP 工具网关 + 分层记忆 + RAG 引用溯源 + 反思防环 + 评测闭环）；工程复用两个 GitHub Trending 开源项目同源 core，零外部 API 依赖可规则降级运行，推理链路量化提速≈8x、KV Cache 命中≈0.8。熟悉字节/腾讯/智谱技术栈同构实现，具备 Agent 框架、RAG 防幻觉、多智能体编排、推理优化与评测体系设计能力。",

  // 技术栈按类目，生成时按公司优先级重排类目
  techStack: {
    编排与框架: ["LangGraph", "LangChain", "AutoGen", "CrewAI"],
    RAG与检索: ["RAG", "向量检索(Milvus/Elasticsearch)", "TF-IDF+2-gram+RRF 混合召回", "引用溯源/事实核查", "HyDE/Query 改写"],
    Agent能力: ["Multi-Agent 编排", "MCP 工具网关", "Function Calling", "Planning/Execution", "Memory 分层记忆", "Reflection 反思防环", "Agent 评测(SWE-Bench 同构)"],
    模型与训练: ["LLM 微调(SFT/LoRA)", "RLHF/DPO", "Post-training", "模型蒸馏/量化(AWQ/GPTQ)", "长文本上下文预算"],
    工程: ["Python", "FastAPI", "Go", "Java", "Docker", "Kubernetes", "Redis", "MySQL", "高并发/分布式", "vLLM", "可观测(Prometheus)"],
    产品与协作: ["需求拆解", "竞品分析", "指标设计", "低代码生态", "AI 产品闭环"],
  },

  方法论: [
    "Agent 框架设计：基于 LangGraph 实现 Supervisor 多 Agent 协作 + MemorySaver 分层记忆 + 反思节点防环，同比 AutoGen/CrewAI 同构。",
    "RAG 防幻觉与引用溯源：TF-IDF+2-gram+RRF 混合召回 + 事实核查，citation_rate=1.0、hallucination_rate=0.0。",
    "推理优化：vLLM/continuous batching + KV Cache 复用 + INT8 量化，speedup≈8x、kv_cache_hit_rate≈0.8。",
    "评测闭环：离线（命中/引用/拒答/幻觉四率）+ 在线（A/B + 可观测），对齐 SWE-Bench/TAU-Bench 工程化思路。",
    "工程落地：零依赖规则降级、两开源项目同源复用、编译全过、成本自负盈亏。",
  ],

  project: {
    title: "专属刷题教练 · 定制化备考 Agent（v3.1.0-agent-mem）",
    meta: "个人项目（复赛作品升级）| LangGraph · 混元/通义 · MCP · SQLite | 2024.06 – 至今",
    phases: {
      A: {
        title: "Agent 编排与 MCP 工具网关",
        bullets: [
          "用 LangGraph 搭 Supervisor 多 Agent：llm/memory/tools/orchestrator/router 五模块，MemorySaver 分层记忆（profile/short_term）。",
          "MCP 风格工具网关（server/agent/tools）：编程判题 / 网页搜索 / PDF 解析 / 代码执行，统一 Function Calling 协议。",
          "无外部 API Key 时规则降级：纯检索 + RAG 兜底，可用性 100%。",
        ],
      },
      B: {
        title: "分层记忆与多轮上下文预算",
        bullets: [
          "记忆落 SQLite（agent_profile + agent_short_term 表），lifespan 初始化建表。",
          "五段式上下文预算 build_context：系统/画像/短期/检索/工具结果分段，长文本可控、成本可估。",
        ],
      },
      C: {
        title: "RAG 引用溯源与防幻觉",
        bullets: [
          "TF-IDF + 2-gram + RRF 混合召回，检索段落带引用标号。",
          "答题末段强制附引文 + 事实核查，citation_rate=1.0、hallucination_rate=0.0，已上线。",
        ],
      },
      D: {
        title: "多 Agent 编排与反思防环",
        bullets: [
          "Supervisor 拆解子任务→Worker 并行→Synthesizer 汇总；反思节点校验矛盾并回退重规划。",
          "循环检测 + 拒绝兜底，避免 Agent 死循环；同比 AutoGen/CrewAI 同构。",
        ],
      },
      E: {
        title: "评测闭环（离线 + 在线）",
        bullets: [
          "离线四维：hit_rate=0.667 / citation_rate=1.0 / reject_rate=0.0 / hallucination_rate=0.0。",
          "在线 A/B + Prometheus 可观测（latency/QPS/命中），对齐 SWE-Bench 工程化思路。",
        ],
      },
      F: {
        title: "推理优化",
        bullets: [
          "vLLM/continuous batching + KV Cache 复用 + INT8 量化 + 投机解码，speedup≈8x、kv_cache_hit_rate≈0.8。",
          "Benchmark 化推理链路，成本自负盈亏。",
        ],
      },
      G: {
        title: "多厂商注册表与结构化输出",
        bullets: [
          "多厂商 LLM 注册表（混元 / 智谱 / 通义 / DeepSeek / Kimi 等）统一接口，按场景选型。",
          "结构化输出（Function Calling / JSON Schema）+ 端侧移动答疑（量化蒸馏）。",
        ],
      },
      H: {
        title: "MCP 生态与开源复用（2026 新标配）",
        bullets: [
          "接入 MCP 协议，工具即插即用；规划 RAG→Supervisor+反思→学习异常检测（AIOps 迁移）评测闭环。",
          "工程复用两个 GitHub Trending 开源项目同源 core（vibe-coding 验证），0→1 提效。",
        ],
      },
    },
    quant: [
      "citation_rate=1.0 · hallucination_rate=0.0（RAG 防幻觉，已上线）",
      "hit_rate=0.667（事实命中，可测）",
      "speedup≈8x · kv_cache_hit_rate≈0.8（推理优化）",
      "两个开源项目 GitHub Trending（同源 core 复用）",
    ],
  },

  web: {
    title: "个人作品集网站（React + Vite + TypeScript）",
    meta: "个人项目 | React · Vite · TypeScript | 2025",
    bullets: [
      "组件化作品集，承载刷题教练与开源项目展示，已部署可访问。",
      "工程化：TS 强类型、构建优化、响应式，承载面试亮点展示。",
    ],
  },

  工程实践: [
    "零依赖规则降级：无 Key 仍可跑，可用性 100%。",
    "可观测：Prometheus 采集 latency/QPS/命中，支持 A/B 实验。",
    "CI：编译全过、类型安全、单测覆盖核心链路。",
  ],
};

// ============ 产品方向：AI 产品经理 ============
export const pm = {
  summary:
    "AI 产品经理（技术背景），3 年 LLM 应用落地经验，能把技术能力翻译成产品价值。主导「专属刷题教练」从复赛工具升级为定制化备考 Agent：以用户痛点（刷题为辅、陪练/诊断/规划为刚需）为起点，定义 Agent 产品定位与四类痛点解法，落地 RAG 引用溯源、分层记忆、多 Agent 陪练、评测闭环，并用两开源项目同源复用验证 0→1 效率。熟悉低代码/生态、可解释、竞品分析与指标设计，能和技术团队同频推进 Agent 产品（对齐京东低代码、百度 AppBuilder 类产品岗）。",

  核心能力: [
    "需求洞察与产品定义：从复赛发帖文案与用户反馈提炼四类痛点，定义「备考 Agent」而非「刷题工具」。",
    "竞品与技术同频：理解 LangGraph/MCP/RAG/多 Agent 技术边界，能写 PRD 并评估技术可行性。",
    "指标与评测设计：定义 hit/citation/reject/hallucination 四率 + A/B，用数据驱动迭代。",
    "低代码与生态思维：规划工具即插即用（MCP）、用户自建 Agent 生态（对齐京东低代码方向）。",
    "0→1 落地：两开源项目同源复用，成本自负盈亏，技术+产品双闭环。",
  ],

  project: {
    title: "专属刷题教练 · 定制化备考 Agent（产品视角）",
    meta: "个人项目（复赛作品升级）| Agent 产品 · RAG 可解释 · 多 Agent 陪练 | 2024.06 – 至今",
    phases: {
      A: {
        title: "产品定义：Agent 编排与工具生态",
        bullets: [
          "Supervisor 多 Agent = 陪练 / 诊断 / 规划三角色，解决「单轮问答≠备考」痛点。",
          "工具网关 = 用户可扩展能力（编程判题 / 搜索 / PDF），低代码生态雏形。",
        ],
      },
      B: {
        title: "个性化：分层记忆与连续诊断",
        bullets: [
          "分层记忆 = 用户长期画像 + 短期对话，支撑个性化陪练与连续诊断。",
          "上下文预算打通长文本，控制成本同时保证体验。",
        ],
      },
      C: {
        title: "信任建设：RAG 引用溯源",
        bullets: [
          "答案可解释、可溯源，解决用户「凭什么信你」的信任痛点。",
          "citation_rate=1.0、hallucination_rate=0.0，成为产品核心卖点。",
        ],
      },
      D: {
        title: "体验升级：多 Agent 陪练 + 反思",
        bullets: [
          "多 Agent 模拟面试 / 对抗练习，比单轮问答更接近真实备考。",
          "反思节点防矛盾，提升回答一致性，降低用户纠错成本。",
        ],
      },
      E: {
        title: "数据驱动：评测闭环",
        bullets: [
          "用四率 + A/B 量化产品效果，反推功能优先级与留存策略。",
          "可观测看板支撑运营决策。",
        ],
      },
      F: {
        title: "降本提质：推理优化",
        bullets: [
          "推理优化让免费用户也能用上高质量陪练，扩大漏斗顶部。",
          "成本自负盈亏，验证商业化可行。",
        ],
      },
      G: {
        title: "选型自由：多厂商注册表",
        bullets: [
          "不绑定单一模型，按场景选型（混元 / 通义 / 智谱…），降低供应链风险。",
          "结构化输出支撑稳定产品交互。",
        ],
      },
      H: {
        title: "平台化：MCP 生态与开源复用",
        bullets: [
          "MCP 工具即插即用，规划用户自建 Agent 生态。",
          "两开源项目同源复用，验证 0→1 产品迭代效率。",
        ],
      },
    },
    quant: [
      "citation_rate=1.0 · hallucination_rate=0.0（可解释卖点）",
      "hit_rate=0.667（回答质量基线）",
      "推理优化 speedup≈8x（免费用户可用高质量陪练）",
      "两开源项目 GitHub Trending（0→1 验证）",
    ],
  },

  web: {
    title: "个人作品集网站（产品展示）",
    meta: "个人项目 | React · Vite | 2025",
    bullets: [
      "承载刷题教练与开源项目展示，作为面试作品集与产品叙事载体。",
      "负责信息架构与交互设计，体现产品 Sense。",
    ],
  },

  行业洞察: [
    "具身智能 / 多模态 Agent 是 2026 招聘新热点（宇树、智元、阶跃星辰等）。",
    "低代码 + 自然语言构建 Agent 成为大厂标配（京东、百度 AppBuilder）。",
    "Agent 评测从「能跑」走向「可量化、可 A/B」（SWE-Bench/TAU-Bench 工程化）。",
  ],
};
