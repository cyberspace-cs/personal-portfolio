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
    en: "LLM Algorithm Engineer",
    zh: "大模型算法工程师",
  },
  bio: {
    en: "Passionate about advancing large language model capabilities and building intelligent AI systems that bridge the gap between cutting-edge research and real-world applications.",
    zh: "致力于推动大语言模型能力的发展，构建智能AI系统，弥合前沿研究与实际应用之间的差距。",
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
      { name: "LLaMA / GPT", level: 90 },
      { name: "Fine-tuning", level: 85 },
      { name: "RAG", level: 88 },
      { name: "Prompt Engineering", level: 92 },
      { name: "Alignment", level: 80 },
    ],
  },
  {
    titleKey: "skillsML",
    skills: [
      { name: "PyTorch", level: 90 },
      { name: "TensorFlow", level: 80 },
      { name: "Transformers", level: 92 },
      { name: "Deep Learning", level: 88 },
      { name: "NLP", level: 90 },
    ],
  },
  {
    titleKey: "skillsTools",
    skills: [
      { name: "Python", level: 95 },
      { name: "CUDA / GPU", level: 82 },
      { name: "Docker", level: 85 },
      { name: "LangChain", level: 88 },
      { name: "vLLM", level: 80 },
    ],
  },
];

export const experiences: Experience[] = [
  {
    company: { en: "ByteDance", zh: "字节跳动" },
    position: { en: "LLM Algorithm Engineer", zh: "大模型算法工程师" },
    period: { en: "2025.07 - Present", zh: "2025.07 - 至今" },
    description: [
      {
        en: "Working on large language model research and applications",
        zh: "从事大语言模型研究与应用的相关工作",
      },
    ],
  },
  {
    company: { en: "Kunlun Tech", zh: "昆仑万维" },
    position: { en: "AI Game Algorithm Intern", zh: "AI游戏算法实习生" },
    period: { en: "2023.09 - 2024.03", zh: "2023.09 - 2024.03" },
    description: [
      {
        en: "Developed AI algorithms for game applications",
        zh: "开发游戏应用中的AI算法",
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
