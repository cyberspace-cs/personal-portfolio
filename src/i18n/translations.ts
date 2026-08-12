export type Language = 'en' | 'zh';

export interface Translations {
  // Navbar
  navAbout: string;
  navSkills: string;
  navExperience: string;
  navProjects: string;
  navEducation: string;
  navContact: string;
  navLearning: string;
  navBriefing: string;
  navBlog: string;

  // Blog
  blogTitle: string;
  blogSubtitle: string;
  blogBack: string;
  blogPublished: string;
  blogReading: string;
  blogTags: string;
  blogEmpty: string;
  blogMinRead: string;

  // Hero
  heroGreeting: string;
  heroDownloadResume: string;
  heroGetInTouch: string;
  heroViewDemos: string;
  heroScroll: string;

  // About
  aboutTitle: string;
  aboutLocation: string;
  aboutContent: string[];

  // Skills
  skillsTitle: string;
  skillsLLM: string;
  skillsTraining: string;
  skillsHarness: string;
  skillsTools: string;

  // Experience
  experienceTitle: string;

  // Projects
  projectsTitle: string;
  projectsCode: string;
  projectsDemo: string;

  // Learning
  learningTitle: string;
  learningSubtitle: string;
  learningRead: string;

  // Education
  educationTitle: string;

  // Contact
  contactTitle: string;
  contactSubtitle: string;
  contactEmail: string;
  contactLocation: string;
  contactSendMessage: string;

  // Footer
  footerBuiltWith: string;
  footerAllRights: string;
}

export const translations: Record<Language, Translations> = {
  en: {
    // Navbar
    navAbout: 'About',
    navSkills: 'Skills',
    navExperience: 'Experience',
    navProjects: 'Projects',
    navEducation: 'Education',
    navContact: 'Contact',
    navLearning: 'Learning',
    navBriefing: 'AI Briefing',
    navBlog: 'Blog',

    // Hero
    heroGreeting: "Hello, I'm",
    heroDownloadResume: 'Download Resume',
    heroGetInTouch: 'Get in Touch',
    heroViewDemos: 'View Live Demos',
    heroScroll: 'Scroll',

    // About
    aboutTitle: 'About Me',
    aboutLocation: 'Location',
    aboutContent: [
      "I'm an LLM Agent Engineer focused on turning large-model capabilities into production-grade, observable, self-improving agent systems. My technical core spans RAG, Agent orchestration, SFT and RL alignment.",
      "I follow the frontier of Agent engineering — Harness Engineering and Self-Evolving Agents: through state persistence, error self-healing, tool-permission governance and full-chain observability, I turn uncontrolled generative AI into stable, reliable productivity tools.",
      "Off work, I read the latest Agent / RL papers, contribute to open source, and distill engineering practice into reusable Harness components — always curious about the boundary between model capability and systems engineering.",
    ],

    // Skills
    skillsTitle: 'Skills & Technologies',
    skillsLLM: 'LLM & Agent',
    skillsTraining: 'Training & Alignment',
    skillsHarness: 'Agent Eng · Harness/Loop',
    skillsTools: 'Engineering & Infra',

    // Experience
    experienceTitle: 'Work Experience',

    // Projects
    projectsTitle: 'Featured Projects',
    projectsCode: 'Code',
    projectsDemo: 'Demo',

    // Learning
    learningTitle: 'Learning Resources',
    learningSubtitle: 'Curated open-source courses and tutorials I am studying to deepen my LLM & Agent skills.',
    learningRead: 'Read',

    // Education
    educationTitle: 'Education',

    // Contact
    contactTitle: 'Get In Touch',
    contactSubtitle: "I'm always open to discussing new projects, creative ideas, or opportunities to be part of your vision. Feel free to reach out!",
    contactEmail: 'Email',
    contactLocation: 'Location',
    contactSendMessage: 'Send me a message',

    // Footer
    footerBuiltWith: 'Built with',
    footerAllRights: 'All rights reserved.',

    // Blog
    blogTitle: 'Blog',
    blogSubtitle: 'Notes on LLM, Agents, and the road to embodied intelligence.',
    blogBack: 'Back to Blog',
    blogPublished: 'Published',
    blogReading: 'Reading',
    blogTags: 'Tags',
    blogEmpty: 'No posts yet.',
    blogMinRead: 'min read',
  },

  zh: {
    // Navbar
    navAbout: '关于',
    navSkills: '技能',
    navExperience: '经历',
    navProjects: '项目',
    navEducation: '教育',
    navContact: '联系',
    navLearning: '学习资料',
    navBriefing: 'AI 简报',
    navBlog: '博客',

    // Hero
    heroGreeting: '你好，我是',
    heroDownloadResume: '下载简历',
    heroGetInTouch: '联系我',
    heroViewDemos: '查看实时 Demo',
    heroScroll: '滚动',

    // About
    aboutTitle: '关于我',
    aboutLocation: '位置',
    aboutContent: [
      '我是一名大模型 Agent 开发工程师，专注将大语言模型能力工程化落地为可生产、可观测、可进化的智能体系统。技术主线围绕 RAG、Agent 编排、SFT 与 RL 对齐展开。',
      '我关注 Agent 工程的前沿范式——Harness Engineering 与 Self-Evolving Agent：通过状态持久化、错误自愈、工具权限管控与全链路可观测，把不可控的生成式 AI 变为稳定的生产力工具。',
      '工作之余，我喜欢研读最新的 Agent / RL 论文、参与开源，并把工程实践沉淀为可复用的 Harness 组件。始终对模型能力与系统工程的边界保持好奇。',
    ],

    // Skills
    skillsTitle: '技能 & 技术',
    skillsLLM: '大模型 & Agent',
    skillsTraining: '模型训练与对齐',
    skillsHarness: 'Agent 工程 · Harness/Loop',
    skillsTools: '工程与部署',

    // Experience
    experienceTitle: '工作经历',

    // Projects
    projectsTitle: '精选项目',
    projectsCode: '代码',
    projectsDemo: '演示',

    // Learning
    learningTitle: '学习资料',
    learningSubtitle: '我正在学习的开源课程与教程，用于深入大模型与智能体相关技能。',
    learningRead: '阅读',

    // Education
    educationTitle: '教育背景',

    // Contact
    contactTitle: '联系我',
    contactSubtitle: '我始终乐于讨论新项目、创意想法，或成为您愿景一部分的机会。随时联系我！',
    contactEmail: '邮箱',
    contactLocation: '位置',
    contactSendMessage: '给我发消息',

    // Footer
    footerBuiltWith: '使用',
    footerAllRights: '版权所有。',

    // Blog
    blogTitle: '博客',
    blogSubtitle: '关于大模型、智能体，以及通往具身智能之路的思考与笔记。',
    blogBack: '返回博客',
    blogPublished: '发布于',
    blogReading: '阅读',
    blogTags: '标签',
    blogEmpty: '暂无文章。',
    blogMinRead: '分钟阅读',
  },
};
