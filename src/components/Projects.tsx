import { useScrollAnimationStagger } from '../hooks/useScrollAnimation';
import { useLanguage } from '../context/LanguageContext';
import { projects } from '../data/portfolio';
import { Github, ExternalLink, Sparkles, Search, Code, MessageCircle, Bot, GraduationCap, Flower2, ShieldCheck } from 'lucide-react';

const iconMap: Record<string, any> = {
  'sparkles': Sparkles,
  'search': Search,
  'code': Code,
  'message-circle': MessageCircle,
  'bot': Bot,
  'graduation-cap': GraduationCap,
  'flower-2': Flower2,
  'shield': ShieldCheck,
};

export default function Projects() {
  const { ref, visibleItems } = useScrollAnimationStagger(projects.length, { threshold: 0.1 });
  const { t, language } = useLanguage();

  return (
    <section id="projects" className="py-24 relative bg-surface/30">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-bg/50 to-transparent" />

      <div ref={ref} className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex items-center gap-4 mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-fg">{t.projectsTitle}</h2>
          <div className="flex-1 h-px bg-gradient-to-r from-line to-transparent" />
        </div>

        {/* Projects Grid */}
        <div className="grid md:grid-cols-2 gap-8">
          {projects.map((project, index) => {
            const Icon = iconMap[project.icon] || Sparkles;

            return (
              <div
                key={project.name[language]}
                className={`group relative p-6 rounded-xl bg-surface/50 border border-line hover:border-accent/50 transition-all duration-500 hover:-translate-y-1 ${
                  visibleItems[index]
                    ? 'opacity-100 translate-y-0'
                    : 'opacity-0 translate-y-8'
                }`}
                style={{ transitionDelay: `${index * 150}ms` }}
              >
                {/* Project Icon */}
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-accent/20 to-accent-2/20 flex items-center justify-center mb-6 group-hover:from-accent/30 group-hover:to-accent-2/30 transition-all">
                  <Icon size={28} className="text-accent" />
                </div>

                {/* Project Info */}
                <h3 className="text-xl font-semibold text-fg mb-3 group-hover:text-accent transition-colors">
                  {project.name[language]}
                </h3>
                <p className="text-muted text-sm mb-4 leading-relaxed">
                  {project.description[language]}
                </p>

                {/* Tech Stack */}
                <div className="flex flex-wrap gap-2 mb-6">
                  {project.tech.map((tech) => (
                    <span
                      key={tech}
                      className="px-3 py-1 rounded-full bg-surface-2/50 text-fg text-xs font-medium"
                    >
                      {tech}
                    </span>
                  ))}
                </div>

                {/* Links */}
                <div className="flex items-center gap-4">
                  {project.github && (
                    <a
                      href={project.github}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-muted hover:text-accent transition-colors"
                    >
                      <Github size={16} />
                      <span>{t.projectsCode}</span>
                    </a>
                  )}
                  {project.demo && (
                    <a
                      href={project.demo}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-muted hover:text-accent transition-colors"
                    >
                      <ExternalLink size={16} />
                      <span>{t.projectsDemo}</span>
                      {project.demo.startsWith('/demos') && (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 text-[10px] font-semibold">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                          LIVE
                        </span>
                      )}
                    </a>
                  )}
                </div>

                {/* Hover Glow Effect */}
                <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-accent/5 to-accent-2/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
