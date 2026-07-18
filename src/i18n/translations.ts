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

  // Hero
  heroGreeting: string;
  heroDownloadResume: string;
  heroGetInTouch: string;
  heroScroll: string;

  // About
  aboutTitle: string;
  aboutLocation: string;
  aboutContent: string[];

  // Skills
  skillsTitle: string;
  skillsLLM: string;
  skillsML: string;
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

    // Hero
    heroGreeting: "Hello, I'm",
    heroDownloadResume: 'Download Resume',
    heroGetInTouch: 'Get in Touch',
    heroScroll: 'Scroll',

    // About
    aboutTitle: 'About Me',
    aboutLocation: 'Location',
    aboutContent: [
      "I'm a passionate full-stack developer with over 5 years of experience building web applications that make a difference. My journey in tech started with a curiosity about how things work on the web, which evolved into a career crafting digital experiences.",
      'I specialize in building scalable applications using modern technologies like React, TypeScript, and Node.js. I believe in writing clean, maintainable code and creating intuitive user interfaces that delight users.',
      "When I'm not coding, you'll find me exploring new technologies, contributing to open-source projects, or sharing knowledge through tech blogs. I'm always excited to take on new challenges and collaborate with creative teams.",
    ],

    // Skills
    skillsTitle: 'Skills & Technologies',
    skillsLLM: 'LLM & AI',
    skillsML: 'Machine Learning',
    skillsTools: 'Tools & Frameworks',

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

    // Hero
    heroGreeting: '你好，我是',
    heroDownloadResume: '下载简历',
    heroGetInTouch: '联系我',
    heroScroll: '滚动',

    // About
    aboutTitle: '关于我',
    aboutLocation: '位置',
    aboutContent: [
      '我是一名专注于大语言模型的算法工程师，拥有5年以上NLP和AI领域的研究与工程经验。我的技术之旅始于对自然语言理解的好奇，后来逐渐深入到大模型研发与应用的前沿领域。',
      '我专注于大模型的微调、对齐、推理优化以及RAG等方向，擅长将前沿研究成果转化为可落地的产品。我相信技术应当服务于人，致力于打造真正有价值的AI系统。',
      '当我不做研究时，你会发现我在阅读最新的AI论文、参与开源项目，或在技术社区分享见解。我始终对新的研究方向和技术突破保持着浓厚的兴趣。',
    ],

    // Skills
    skillsTitle: '技能 & 技术',
    skillsLLM: '大模型 & AI',
    skillsML: '机器学习',
    skillsTools: '工具 & 框架',

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
  },
};
