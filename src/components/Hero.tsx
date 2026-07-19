import { Github, Linkedin, Twitter, Mail, ChevronDown, Download, Sparkles } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { personalInfo, socialLinks } from '../data/portfolio';

const iconMap: Record<string, any> = {
  github: Github,
  linkedin: Linkedin,
  twitter: Twitter,
  mail: Mail,
};

export default function Hero() {
  const { t, language } = useLanguage();

  const initials = personalInfo.name.en
    .split(' ')
    .map((n) => n[0])
    .join('');

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Glow Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-[128px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-400/20 rounded-full blur-[128px]" />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Avatar */}
        <div className="mb-8 flex justify-center">
          <div className="relative">
            <div className="w-32 h-32 rounded-full bg-gradient-to-br from-sky-400 to-indigo-400 p-1">
              <div className="w-full h-full rounded-full bg-slate-900 flex items-center justify-center">
                <span className="text-4xl font-bold text-slate-100">{initials}</span>
              </div>
            </div>
            <div className="absolute -bottom-1 -right-1 w-8 h-8 bg-green-500 rounded-full border-4 border-slate-900" />
          </div>
        </div>

        {/* Greeting */}
        <p className="text-sky-400 font-medium mb-2">{t.heroGreeting}</p>

        {/* Name */}
        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-slate-100 mb-4">
          {personalInfo.name[language]}
        </h1>

        {/* Title with Gradient */}
        <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-sky-400 to-indigo-400 bg-clip-text text-transparent mb-6">
          {personalInfo.title[language]}
        </h2>

        {/* Bio */}
        <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          {personalInfo.bio[language]}
        </p>

        {/* Live Demo Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-medium mb-8">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          7 个 AI 项目已上线可交互 Demo
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
          <a
            href={personalInfo.resumeUrl || '#contact'}
            className="px-8 py-3 bg-gradient-to-r from-sky-400 to-indigo-400 text-white font-semibold rounded-lg hover:shadow-lg hover:shadow-sky-400/25 transition-all duration-300 flex items-center gap-2"
          >
            <Download size={18} />
            {t.heroDownloadResume}
          </a>
          <a
            href="/demos/index.html"
            target="_blank"
            rel="noopener noreferrer"
            className="px-8 py-3 bg-gradient-to-r from-emerald-400 to-teal-400 text-slate-900 font-semibold rounded-lg hover:shadow-lg hover:shadow-emerald-400/25 transition-all duration-300 flex items-center gap-2"
          >
            <Sparkles size={18} />
            {t.heroViewDemos}
          </a>
          <a
            href="#contact"
            className="px-8 py-3 border border-slate-600 text-slate-300 font-semibold rounded-lg hover:border-sky-400 hover:text-sky-400 transition-all duration-300"
          >
            {t.heroGetInTouch}
          </a>
        </div>

        {/* Social Links */}
        <div className="flex items-center justify-center gap-4 mb-12">
          {socialLinks.map((link) => {
            const Icon = iconMap[link.icon] || Mail;
            return (
              <a
                key={link.name}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400 hover:text-sky-400 hover:border-sky-400/50 hover:bg-slate-700/50 transition-all duration-300"
                aria-label={link.name}
              >
                <Icon size={18} />
              </a>
            );
          })}
        </div>

        {/* Scroll Indicator */}
        <a
          href="#about"
          className="inline-flex flex-col items-center gap-2 text-slate-500 hover:text-sky-400 transition-colors duration-300 animate-bounce"
        >
          <span className="text-xs uppercase tracking-wider">{t.heroScroll}</span>
          <ChevronDown size={20} />
        </a>
      </div>
    </section>
  );
}
