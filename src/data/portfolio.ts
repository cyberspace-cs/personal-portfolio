import { Language } from '../i18n/translations';

export interface SocialLink {
  name: string;
  url: string;
  icon: string;
}

export interface Skill {
  name: string;
  level?: number;
}

export interface SkillCategory {
  titleKey: string;
  skills: Skill[];
}

export interface LocalizedString {
  en: string;
  zh: string;
}

export interface Experience {
  company: LocalizedString;
  position: LocalizedString;
  period: LocalizedString;
  description: LocalizedString[];
}

export interface Project {
  name: LocalizedString;
  description: LocalizedString;
  tech: string[];
  github?: string;
  demo?: string;
  icon: string;
}

export interface Education {
  school: LocalizedString;
  degree: LocalizedString;
  major: LocalizedString;
  period: LocalizedString;
  honors?: LocalizedString;
  research?: LocalizedString;
}

export interface LearningResource {
  name: LocalizedString;
  description: LocalizedString;
  org: string;
  topics: string[];
  github: string;
  website?: string;
  icon: string;
}

export interface PersonalInfo {
  name: LocalizedString;
  title: LocalizedString;
  bio: LocalizedString;
  location: LocalizedString;
  email: string;
  resumeUrl?: string;
  avatar?: string;
}

export function getLocalized<T extends LocalizedString>(item: T, lang: Language): string {
  return item[lang];
}

export const personalInfo: PersonalInfo = {
  name: {
    en: "Tao Xie",
    zh: "谢韬",
  },
  title: {
    en: "LLM Agent Engineer",
    zh: "大模型 Agent 开发工程师",
  },
  bio: {
    en: "Focused on turning large language models into production-grade, observable and self-improving Agent systems — spanning RAG, Agent orchestration, SFT and RL alignment, with a frontier focus on Agent self-evolution and Harness/Loop engineering.",
    zh: "专注将大语言模型工程化落地为可生产、可观测、可进化的智能体系统——覆盖 RAG、Agent 编排、SFT 与 RL 对齐，并聚焦 Agent 自进化与 Harness/Loop 工程等前沿方向。",
  },
  location: {
    en: "San Francisco, CA",
    zh: "中国 · 北京",
  },
  email: "2252125665@qq.com",
  resumeUrl: "/resume.pdf",
};

export const socialLinks: SocialLink[] = [
  { name: "GitHub", url: "https://github.com/cyberspace-cs/personal-portfolio", icon: "github" },
  { name: "Twitter", url: "https://github.com/cyberspace-cs", icon: "twitter" },
  { name: "Email", url: "mailto:2252125665@qq.com", icon: "mail" },
];

export const skillCategories: SkillCategory[] = [
  {
    titleKey: "skillsLLM",
    skills: [
      { name: "LLM / GPT / LLaMA", level: 92 },
      { name: "RAG (混合检索 + 重排)", level: 90 },
      { name: "Agent / Multi-Agent", level: 90 },
      { name: "Function Calling / MCP", level: 88 },
      { name: "Prompt / Context Engineering", level: 90 },
    ],
  },
  {
    titleKey: "skillsTraining",
    skills: [
      { name: "SFT / LoRA / QLoRA", level: 88 },
      { name: "RLHF / DPO / RL", level: 85 },
      { name: "训练数据构造与评测", level: 86 },
      { name: "PyTorch / DeepSpeed / FSDP", level: 88 },
      { name: "模型蒸馏与推理优化", level: 84 },
    ],
  },
  {
    titleKey: "skillsHarness",
    skills: [
      { name: "Agent Harness 架构", level: 88 },
      { name: "Self-Evolving Agent", level: 85 },
      { name: "LangGraph / LangChain", level: 90 },
      { name: "Memory / 状态持久化", level: 87 },
      { name: "可观测性 LangSmith / Prometheus", level: 83 },
    ],
  },
  {
    titleKey: "skillsTools",
    skills: [
      { name: "Python", level: 95 },
      { name: "TypeScript / React", level: 85 },
      { name: "FastAPI / 异步后端", level: 90 },
      { name: "vLLM / TGI 部署", level: 84 },
      { name: "Docker / Kubernetes", level: 83 },
    ],
  },
];

export const experiences: Experience[] = [
  {
    company: { en: "Tencent", zh: "腾讯" },
    position: { en: "Agent Engineer", zh: "Agent 开发工程师" },
    period: { en: "2026.08 - Present", zh: "2026.08 - 至今" },
    description: [
      {
        en: "Focus on Agent self-evolution and Harness/Loop engineering, building a generate-verify-reflect loop that lets agents continuously self-optimize as models iterate.",
        zh: "聚焦 Agent 自进化与 Harness/Loop 工程，构建「生成-验证-反思」闭环，使智能体在模型迭代中持续自我优化。",
      },
      {
        en: "Designed a multi-Agent collaboration framework (Manager-Workers) with task orchestration, memory isolation and cross-review to raise complex task completion rate.",
        zh: "设计多 Agent 协作框架（Manager-Workers），实现任务编排、记忆隔离与结果交叉评审，提升复杂任务完成率。",
      },
      {
        en: "Drove model training & alignment: built training sets from business data, applied SFT and RL to improve domain task completion and tool-call success, and established auto + human eval.",
        zh: "推进模型训练与对齐：基于业务数据构造训练集，进行 SFT 与 RL 提升领域任务完成率与工具调用成功率，建立自动评测 + 人工评测体系。",
      },
      {
        en: "Shipped production-grade Agents with sandbox isolation, resume-from-checkpoint, safety guardrails and graceful degradation for high-concurrency online services.",
        zh: "工程化落地生产级 Agent：沙箱隔离、断点续跑、安全护栏与降级策略，支撑高并发线上服务。",
      },
    ],
  },
  {
    company: { en: "ByteDance", zh: "字节跳动" },
    position: { en: "AI Agent Engineer", zh: "AI Agent 开发工程师" },
    period: { en: "2025.07 - 2026.07", zh: "2025.07 - 2026.07" },
    description: [
      {
        en: "Designed and built LLM Agent systems using ReAct / Plan-Act-Observe patterns, endowing models with tool use, multi-step planning and self-reflection.",
        zh: "负责大模型 Agent 系统的设计与开发，基于 ReAct / Plan-Act-Observe 范式构建具备工具调用、多步规划与自我反思能力的智能体。",
      },
      {
        en: "Led RAG retrieval optimization (hybrid BM25 + vector search, Rerank, citation tracing) to improve answer accuracy and traceability.",
        zh: "主导 RAG 检索链路优化（混合检索 BM25+向量、Rerank 重排序、引用溯源），提升回答准确率与可追溯性。",
      },
      {
        en: "Implemented Agent Harness engineering: state persistence, error self-healing, tool-permission governance and full-chain observability (LangSmith / Prometheus).",
        zh: "落地 Agent Harness 工程：状态持久化、错误自愈、工具权限管控与全链路可观测（LangSmith / Prometheus）。",
      },
      {
        en: "Iterated model capabilities: constructed training data from business scenarios, ran SFT / LoRA fine-tuning and RLHF / DPO alignment, and built up an evaluation system.",
        zh: "参与模型能力迭代：基于业务场景构造训练数据，进行 SFT / LoRA 微调与 RLHF / DPO 对齐，沉淀评测体系。",
      },
    ],
  },
];

const REPO = "https://github.com/cyberspace-cs/personal-portfolio";

// 该站点已配置 SITE_ACCESS_PASSWORD 门禁，仅授权（知晓密码）用户可访问 demo。

export const projects: Project[] = [
  {
    name: { en: "LLM Fine-tuning Platform", zh: "大模型微调平台" },
    description: {
      en: "End-to-end platform for LLM fine-tuning with LoRA/QLoRA support: data ingestion, live training curves, adapter export and vLLM deployment.",
      zh: "端到端大模型微调平台，支持LoRA/QLoRA：数据接入、实时训练曲线、Adapter导出与vLLM部署全流程。",
    },
    tech: ["PyTorch", "LoRA", "QLoRA", "vLLM", "FastAPI", "Docker"],
    github: REPO,
    demo: "/demos/llm-finetune-studio/",
    icon: "sparkles",
  },
  {
    name: { en: "Enterprise RAG System", zh: "企业级RAG系统" },
    description: {
      en: "Knowledge-based Q&A with hybrid search (BM25 + vector), multi-document understanding and citation tracing.",
      zh: "基于知识库的问答系统，支持混合检索（BM25+向量）、多文档理解与引用溯源。",
    },
    tech: ["Hybrid Search", "BM25", "FastAPI", "Citation", "Context"],
    github: REPO,
    demo: "/demos/rag-knowledge-hub/",
    icon: "search",
  },
  {
    name: { en: "AI Code Assistant", zh: "AI代码助手" },
    description: {
      en: "Coding assistant with generation / completion / refactoring / explanation, driven by Skill routing and an MCP tool connector.",
      zh: "代码助手，支持生成/补全/重构/解释，由 Skill 路由与 MCP 工具连接器驱动。",
    },
    tech: ["AST", "Skill Routing", "MCP", "FastAPI"],
    github: REPO,
    demo: "/demos/ai-code-copilot/",
    icon: "code",
  },
  {
    name: { en: "Multi-modal Dialogue Bot", zh: "多模态对话机器人" },
    description: {
      en: "Conversational AI with text emotion awareness, image understanding and voice transcription in one Context Harness Loop.",
      zh: "对话AI，集成文本情感感知、图像理解与语音转录，统一于 Context Harness Loop。",
    },
    tech: ["Emotion NLP", "FastAPI", "Context Loop"],
    github: REPO,
    demo: "/demos/multimodal-chat-hub/",
    icon: "message-circle",
  },
  {
    name: { en: "AI Customer Service", zh: "智能客服" },
    description: {
      en: "Intent-routed customer service agent combining Skill routing, MCP external tool calls and FAQ RAG over a Context loop.",
      zh: "意图路由智能客服，融合 Skill 路由、MCP 外部工具调用与 FAQ 知识库 RAG，闭环对话。",
    },
    tech: ["Skill", "MCP", "RAG", "FastAPI"],
    github: REPO,
    demo: "/demos/smart-service-desk/",
    icon: "bot",
  },
  {
    name: { en: "Audit-AIOPS", zh: "Audit-AIOPS 审计异常检测" },
    description: {
      en: "Enterprise audit-log anomaly detection Agent: log template parsing, LLM-based anomaly detection, root-cause analysis, alert convergence and explainable reporting, with MCP tool integration.",
      zh: "企业审计日志异常检测 Agent：日志模板解析、大模型异常检测、根因分析、告警收敛与可解释报告，集成 MCP 工具调用。",
    },
    tech: ["Log Parse", "LLM Anomaly", "Root-Cause", "MCP", "FastAPI"],
    github: REPO,
    demo: "/demos/audit-aiops.html",
    icon: "activity",
  },
  {
    name: { en: "AI Recruitment Intelligence", zh: "AI 研发招聘情报站" },
    description: {
      en: "Campus vs social hiring headcount for AI R&D roles across BAT, ByteDance and DeepSeek — official-verified, with post-count vs headcount distinguished.",
      zh: "BAT、字节、DeepSeek 校招与社招 AI 研发岗名额与需求横向对比，数据官网核对，严格区分岗位数与招人数口径。",
    },
    tech: ["Recruit Intel", "Data Viz", "Standalone HTML"],
    github: REPO,
    demo: "/demos/recruit-2026.html",
    icon: "bar-chart",
  },
  {
    name: { en: "AI Quiz Coach", zh: "专属刷题教练" },
    description: {
      en: "Multi-source question bank aggregator for exam prep (postgrad, civil service, tech interviews) with smart recommendations, wrong-question review and progress analytics.",
      zh: "面向考研、考公、大厂面试备考的多源题库聚合智能刷题平台，支持个性化推荐、错题复盘与学习进度可视化分析。",
    },
    tech: ["React", "Chart.js", "Tailwind CSS", "SPA"],
    github: REPO,
    demo: "/shuati-coach.html",
    icon: "graduation-cap",
  },
  {
    name: { en: "Sakura Campus Sim", zh: "樱花校园模拟" },
    description: {
      en: "A wholesome, no-pressure campus life simulator for kids: collect falling sakura petals, attend class, make friends, dress up, feed the cat and finish daily quests — all rendered in pure Canvas 2D.",
      zh: "为小朋友打造的治愈系校园生活模拟：捡樱花花瓣、上课答题、交朋友、换装、喂小猫、完成每日小任务，全程用纯 Canvas 2D 手绘，无广告无联网。",
    },
    tech: ["Canvas 2D", "Vanilla JS", "WebAudio", "localStorage", "SPA"],
    github: REPO,
    demo: "/demos/sakura-campus/",
    icon: "flower-2",
  },
];

export const education: Education[] = [
  {
    school: { en: "Peking University", zh: "北京大学" },
    degree: { en: "Master", zh: "硕士" },
    major: { en: "Software Engineering", zh: "软件工程" },
    period: { en: "2022.09 - 2025.06", zh: "2022.09 - 2025.06" },
    honors: { en: "PKU Outstanding Student, Jiukun Scholarship, Social Work Award", zh: "北京大学三好学生、九坤奖学金、社会工作奖" },
    research: { en: "LLM Applications & Agent Workflow", zh: "大模型应用与智能体（Agent）工作流" },
  },
  {
    school: { en: "Shandong University", zh: "山东大学" },
    degree: { en: "Bachelor", zh: "学士" },
    major: { en: "Cybersecurity", zh: "网络空间安全" },
    period: { en: "2018.09 - 2022.06", zh: "2018.09 - 2022.06" },
    honors: { en: "National First Prize in Information Security Competition", zh: "全国大学生信息安全竞赛一等奖（国家级）" },
  },
];

export const learningResources: LearningResource[] = [
  {
    name: { en: "Happy-LLM", zh: "Happy-LLM 大模型教程" },
    description: {
      en: "Datawhale's open-source course 'Build LLMs from Scratch' — from Transformer principles to pretraining, SFT, RLHF alignment and deployment.",
      zh: "Datawhale 开源教程《从零开始构建大模型》——从 Transformer 原理到预训练、微调(SFT)、对齐(RLHF)与部署落地。",
    },
    org: "Datawhale",
    topics: ["Transformer", "Pretraining", "SFT", "RLHF", "RAG", "Deployment"],
    github: "https://github.com/datawhalechina/happy-llm",
    website: "/learning/happy-llm/README.md",
    icon: "book-open",
  },
  {
    name: { en: "Hello-Agents", zh: "Hello-Agents 智能体教程" },
    description: {
      en: "Datawhale's 'Build Agents from Scratch' — principles and practice of LLM-powered agents: tool use, memory, planning and multi-agent collaboration.",
      zh: "Datawhale《从零开始构建智能体》——智能体原理与实践，覆盖工具调用、记忆机制、规划推理与多智能体协作。",
    },
    org: "Datawhale",
    topics: ["Agent", "Tool Use", "Memory", "Planning", "Multi-Agent"],
    github: "https://github.com/datawhalechina/hello-agents",
    website: "/learning/hello-agents/README.md",
    icon: "bot",
  },
];
