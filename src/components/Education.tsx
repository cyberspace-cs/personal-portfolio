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
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-100">{t.educationTitle}</h2>
          <div className="flex-1 h-px bg-gradient-to-r from-slate-700 to-transparent" />
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
              className="relative p-6 rounded-xl bg-slate-800/50 border border-slate-700 hover:border-sky-400/30 transition-all duration-300 group"
              style={{ transitionDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div className="p-3 rounded-xl bg-slate-700/50 text-sky-400 group-hover:bg-sky-400/10 transition-colors">
                  <GraduationCap size={24} />
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2">
                    <h3 className="text-xl font-semibold text-slate-100 group-hover:text-sky-400 transition-colors">
                      {edu.school[language]}
                    </h3>
                    <span className="text-sm text-slate-500">{edu.period[language]}</span>
                  </div>
                  
                  <p className="text-slate-400 mb-1">{edu.degree[language]} · {edu.major[language]}</p>

                  {/* Research Direction */}
                  {edu.research && (
                    <div className="flex items-center gap-2 mt-3 text-sm">
                      <FlaskConical size={14} className="text-indigo-400" />
                      <span className="text-slate-300">{edu.research[language]}</span>
                    </div>
                  )}

                  {/* Honors */}
                  {edu.honors && (
                    <div className="flex items-start gap-2 mt-3 text-sm">
                      <Award size={14} className="text-amber-400 mt-0.5" />
                      <span className="text-slate-400">{edu.honors[language]}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Decorative element */}
              <div className="absolute -bottom-2 -right-2 w-16 h-16 border border-slate-700/50 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
