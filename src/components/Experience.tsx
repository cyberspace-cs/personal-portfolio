import { useScrollAnimationStagger } from '../hooks/useScrollAnimation';
import { useLanguage } from '../context/LanguageContext';
import { experiences } from '../data/portfolio';
import { Briefcase } from 'lucide-react';

export default function Experience() {
  const { ref, visibleItems } = useScrollAnimationStagger(experiences.length, { threshold: 0.1 });
  const { t, language } = useLanguage();

  return (
    <section id="experience" className="py-24 relative">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex items-center gap-4 mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-fg">{t.experienceTitle}</h2>
          <div className="flex-1 h-px bg-gradient-to-r from-line to-transparent" />
        </div>

        {/* Timeline */}
        <div ref={ref} className="relative">
          {/* Timeline Line */}
          <div className="absolute left-0 md:left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-accent via-accent-2 to-line transform md:-translate-x-px" />

          {/* Experience Cards */}
          <div className="space-y-12">
            {experiences.map((exp, index) => {
              const isLeft = index % 2 === 0;

              return (
                <div
                  key={exp.company[language]}
                  className={`relative flex flex-col md:flex-row gap-8 items-start md:items-center ${
                    visibleItems[index]
                      ? 'opacity-100 translate-y-0'
                      : 'opacity-0 translate-y-8'
                  } transition-all duration-700`}
                  style={{ transitionDelay: `${index * 200}ms` }}
                >
                  {/* Timeline Dot */}
                  <div className="absolute left-0 md:left-1/2 w-4 h-4 rounded-full bg-accent border-4 border-bg transform -translate-x-1/2 md:-translate-x-1/2 z-10">
                    <div className="absolute inset-0 rounded-full bg-accent animate-ping opacity-50" />
                  </div>

                  {/* Content Card */}
                  <div className={`md:w-1/2 pl-8 md:pl-0 ${isLeft ? 'md:pr-12' : 'md:pl-12'}`}>
                    <div className="p-6 rounded-xl bg-surface/50 border border-line hover:border-accent/30 transition-all duration-300 group">
                      {/* Header */}
                      <div className="flex items-start gap-4 mb-4">
                        <div className="p-2 rounded-lg bg-surface-2 text-accent">
                          <Briefcase size={20} />
                        </div>
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-fg group-hover:text-accent transition-colors">
                            {exp.position[language]}
                          </h3>
                          <p className="text-muted text-sm">{exp.company[language]}</p>
                        </div>
                      </div>

                      {/* Period */}
                      <p className="text-xs text-faint uppercase tracking-wider mb-4">
                        {exp.period[language]}
                      </p>

                      {/* Description */}
                      <ul className="space-y-2">
                        {exp.description.map((desc, i) => (
                          <li key={i} className="text-muted text-sm flex items-start gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 flex-shrink-0" />
                            {desc[language]}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Spacer for opposite side */}
                  <div className={`hidden md:block md:w-1/2 ${isLeft ? '' : 'order-first'}`} />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
