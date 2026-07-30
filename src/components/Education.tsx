import { useScrollAnimation } from '../hooks/useScrollAnimation';
import { useLanguage } from '../context/LanguageContext';
import { education } from '../data/portfolio';
import { GraduationCap, Award, FlaskConical } from 'lucide-react';

export default function Education() {
  const { ref, isVisible } = useScrollAnimation({ threshold: 0.2 });
  const { t, language } = useLanguage();

  return (
    <section id="education" className="py-24 relative">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex items-center gap-4 mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-fg">{t.educationTitle}</h2>
          <div className="flex-1 h-px bg-gradient-to-r from-line to-transparent" />
        </div>

        {/* Education Cards */}
        <div
          ref={ref}
          className={`space-y-6 transition-all duration-700 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          {education.map((edu, index) => (
            <div
              key={edu.school[language]}
              className="relative p-6 rounded-xl bg-surface/50 border border-line hover:border-accent/30 transition-all duration-300 group"
              style={{ transitionDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div className="p-3 rounded-xl bg-surface-2 text-accent group-hover:bg-accent/10 transition-colors">
                  <GraduationCap size={24} />
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2">
                    <h3 className="text-xl font-semibold text-fg group-hover:text-accent transition-colors">
                      {edu.school[language]}
                    </h3>
                    <span className="text-sm text-faint">{edu.period[language]}</span>
                  </div>

                  <p className="text-muted mb-1">{edu.degree[language]} · {edu.major[language]}</p>

                  {/* Research Direction */}
                  {edu.research && (
                    <div className="flex items-center gap-2 mt-3 text-sm">
                      <FlaskConical size={14} className="text-accent-2" />
                      <span className="text-fg">{edu.research[language]}</span>
                    </div>
                  )}

                  {/* Honors */}
                  {edu.honors && (
                    <div className="flex items-start gap-2 mt-3 text-sm">
                      <Award size={14} className="text-amber-400 mt-0.5" />
                      <span className="text-muted">{edu.honors[language]}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Decorative element */}
              <div className="absolute -bottom-2 -right-2 w-16 h-16 border border-line/50 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
