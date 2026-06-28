import { useScrollAnimationStagger } from '../hooks/useScrollAnimation';
import { useLanguage } from '../context/LanguageContext';
import { skillCategories } from '../data/portfolio';

export default function Skills() {
  const { ref, visibleItems } = useScrollAnimationStagger(skillCategories.length, { threshold: 0.1 });
  const { t } = useLanguage();

  return (
    <section id="skills" className="py-24 relative bg-slate-800/30">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-900/50 to-transparent" />
      
      <div ref={ref} className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex items-center gap-4 mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-100">{t.skillsTitle}</h2>
          <div className="flex-1 h-px bg-gradient-to-r from-slate-700 to-transparent" />
        </div>

        {/* Skill Categories */}
        <div className="grid md:grid-cols-3 gap-8">
          {skillCategories.map((category, categoryIndex) => (
            <div
              key={category.titleKey}
              className={`p-6 rounded-xl bg-slate-800/50 border border-slate-700 hover:border-sky-400/30 transition-all duration-500 ${
                visibleItems[categoryIndex]
                  ? 'opacity-100 translate-y-0'
                  : 'opacity-0 translate-y-8'
              }`}
              style={{ transitionDelay: `${categoryIndex * 150}ms` }}
            >
              <h3 className="text-lg font-semibold text-slate-100 mb-6 flex items-center gap-2">
                <span className="w-1 h-6 bg-gradient-to-b from-sky-400 to-indigo-400 rounded-full" />
                {t[category.titleKey as keyof typeof t] as string}
              </h3>
              
              <div className="space-y-4">
                {category.skills.map((skill, skillIndex) => (
                  <div key={skill.name} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-300">{skill.name}</span>
                      {skill.level && (
                        <span className="text-slate-500">{skill.level}%</span>
                      )}
                    </div>
                    {skill.level && (
                      <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-sky-400 to-indigo-400 rounded-full transition-all duration-1000"
                          style={{
                            width: visibleItems[categoryIndex]
                              ? `${skill.level}%`
                              : '0%',
                            transitionDelay: `${(categoryIndex * 150) + (skillIndex * 100)}ms`,
                          }}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Tech Stack Icons (optional visual element) */}
        <div className="mt-12 flex flex-wrap justify-center gap-4">
          {skillCategories.flatMap((cat) => cat.skills).slice(0, 8).map((skill) => (
            <span
              key={skill.name}
              className="px-4 py-2 rounded-lg bg-slate-800/50 border border-slate-700 text-slate-400 text-sm hover:text-sky-400 hover:border-sky-400/30 transition-all duration-300"
            >
              {skill.name}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
