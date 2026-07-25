import { useScrollAnimationStagger } from '../hooks/useScrollAnimation';
import { useLanguage } from '../context/LanguageContext';
import { learningResources } from '../data/portfolio';
import { Github, ExternalLink, BookOpen, Bot } from 'lucide-react';

const iconMap: Record<string, any> = {
  'book-open': BookOpen,
  'bot': Bot,
};

export default function Learning() {
  const { ref, visibleItems } = useScrollAnimationStagger(learningResources.length, { threshold: 0.1 });
  const { t, language } = useLanguage();

  return (
    <section id="learning" className="py-24 relative bg-surface/30">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-bg/50 to-transparent" />

      <div ref={ref} className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex items-center gap-4 mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-fg">{t.learningTitle}</h2>
          <div className="flex-1 h-px bg-gradient-to-r from-line to-transparent" />
        </div>

        <p className="text-muted text-sm mb-10 max-w-2xl leading-relaxed">
          {t.learningSubtitle}
        </p>

        {/* Learning Grid */}
        <div className="grid md:grid-cols-2 gap-8">
          {learningResources.map((resource, index) => {
            const Icon = iconMap[resource.icon] || BookOpen;

            return (
              <div
                key={resource.name[language]}
                className={`group relative p-6 rounded-xl bg-surface/50 border border-line hover:border-accent/50 transition-all duration-500 hover:-translate-y-1 ${
                  visibleItems[index]
                    ? 'opacity-100 translate-y-0'
                    : 'opacity-0 translate-y-8'
                }`}
                style={{ transitionDelay: `${index * 150}ms` }}
              >
                {/* Org Badge + Icon */}
                <div className="flex items-center justify-between mb-6">
                  <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-accent/20 to-accent-2/20 flex items-center justify-center group-hover:from-accent/30 group-hover:to-accent-2/30 transition-all">
                    <Icon size={28} className="text-accent" />
                  </div>
                  <span className="px-3 py-1 rounded-full bg-surface-2/50 text-fg text-xs font-medium">
                    {resource.org}
                  </span>
                </div>

                {/* Title + Description */}
                <h3 className="text-xl font-semibold text-fg mb-3 group-hover:text-accent transition-colors">
                  {resource.name[language]}
                </h3>
                <p className="text-muted text-sm mb-4 leading-relaxed">
                  {resource.description[language]}
                </p>

                {/* Topics */}
                <div className="flex flex-wrap gap-2 mb-6">
                  {resource.topics.map((topic) => (
                    <span
                      key={topic}
                      className="px-3 py-1 rounded-full bg-surface-2/50 text-fg text-xs font-medium"
                    >
                      {topic}
                    </span>
                  ))}
                </div>

                {/* Links */}
                <div className="flex items-center gap-4">
                  <a
                    href={resource.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-muted hover:text-accent transition-colors"
                  >
                    <Github size={16} />
                    <span>{t.projectsCode}</span>
                  </a>
                  {resource.website && (
                    <a
                      href={resource.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-muted hover:text-accent transition-colors"
                    >
                      <ExternalLink size={16} />
                      <span>{t.learningRead}</span>
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
