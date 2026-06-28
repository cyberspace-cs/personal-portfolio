import { useScrollAnimation } from '../hooks/useScrollAnimation';
import { useLanguage } from '../context/LanguageContext';
import { personalInfo } from '../data/portfolio';

export default function About() {
  const { ref, isVisible } = useScrollAnimation({ threshold: 0.2 });
  const { t, language } = useLanguage();

  const initials = personalInfo.name.en
    .split(' ')
    .map((n) => n[0])
    .join('');

  return (
    <section id="about" className="py-24 relative">
      <div
        ref={ref}
        className={`max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 transition-all duration-700 ${
          isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
        }`}
      >
        {/* Section Header */}
        <div className="flex items-center gap-4 mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-100">{t.aboutTitle}</h2>
          <div className="flex-1 h-px bg-gradient-to-r from-slate-700 to-transparent" />
        </div>

        <div className="grid md:grid-cols-3 gap-8 items-start">
          {/* Avatar */}
          <div className="md:col-span-1 flex justify-center md:justify-start">
            <div className="relative">
              <div className="w-48 h-48 rounded-2xl bg-gradient-to-br from-sky-400/20 to-indigo-400/20 p-1">
                <div className="w-full h-full rounded-xl bg-slate-800 flex items-center justify-center">
                  <span className="text-6xl font-bold bg-gradient-to-br from-sky-400 to-indigo-400 bg-clip-text text-transparent">
                    {initials}
                  </span>
                </div>
              </div>
              {/* Decorative elements */}
              <div className="absolute -top-4 -right-4 w-16 h-16 border border-sky-400/30 rounded-xl -z-10" />
              <div className="absolute -bottom-4 -left-4 w-12 h-12 bg-indigo-400/20 rounded-lg -z-10" />
            </div>
          </div>

          {/* Content */}
          <div className="md:col-span-2 space-y-6">
            {t.aboutContent.map((paragraph, index) => (
              <p
                key={index}
                className="text-slate-400 leading-relaxed"
                style={{
                  transitionDelay: `${index * 100}ms`,
                }}
              >
                {paragraph}
              </p>
            ))}

            {/* Quick Info */}
            <div className="grid grid-cols-2 gap-4 pt-4">
              <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">{t.aboutLocation}</p>
                <p className="text-slate-200">{personalInfo.location[language]}</p>
              </div>
              <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">{t.contactEmail}</p>
                <p className="text-slate-200 truncate">{personalInfo.email}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
