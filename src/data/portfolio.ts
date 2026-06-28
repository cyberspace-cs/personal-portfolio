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
  email: "tao.xie@example.dev",
  resumeUrl: "/resume.pdf",
};

export const socialLinks: SocialLink[] = [
  { name: "GitHub", url: "https://github.com", icon: "github" },
  { name: "LinkedIn", url: "https://linkedin.com", icon: "linkedin" },
  { name: "Twitter", url: "https://twitter.com", icon: "twitter" },
  { name: "Email", url: "mailto:tao.xie@example.dev", icon: "mail" },
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

export const projects: Project[] = [
  {
    name: { en: "LLM Fine-tuning Platform", zh: "大模型微调平台" },
    description: {
      en: "End-to-end platform for LLM fine-tuning with LoRA/QLoRA support, covering data processing to deployment.",
      zh: "端到端大模型微调平台，支持LoRA/QLoRA，涵盖数据处理到部署全流程。",
    },
    tech: ["PyTorch", "LoRA", "vLLM", "FastAPI", "Docker"],
    github: "https://github.com",
    demo: "https://demo.com",
    icon: "sparkles",
  },
  {
    name: { en: "Enterprise RAG System", zh: "企业级RAG系统" },
    description: {
      en: "Knowledge-based Q&A system with hybrid search, multi-document understanding, and citation support.",
      zh: "基于知识库的问答系统，支持混合搜索、多文档理解和引用溯源。",
    },
    tech: ["LangChain", "ChromaDB", "BGE", "FastAPI", "PostgreSQL"],
    github: "https://github.com",
    demo: "https://demo.com",
    icon: "search",
  },
  {
    name: { en: "AI Code Assistant", zh: "AI代码助手" },
    description: {
      en: "Intelligent coding assistant with code generation, completion, and refactoring capabilities.",
      zh: "智能代码助手，支持代码生成、补全和重构功能。",
    },
    tech: ["CodeLlama", "Tree-sitter", "VS Code", "LSP"],
    github: "https://github.com",
    demo: "https://demo.com",
    icon: "code",
  },
  {
    name: { en: "Multi-modal Dialogue Bot", zh: "多模态对话机器人" },
    description: {
      en: "Conversational AI supporting text, image, and voice interactions with emotional awareness.",
      zh: "支持文本、图像和语音交互的对话AI，具备情感感知能力。",
    },
    tech: ["GPT-4V", "Whisper", "LangChain", "Redis"],
    github: "https://github.com",
    demo: "https://demo.com",
    icon: "message-circle",
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
