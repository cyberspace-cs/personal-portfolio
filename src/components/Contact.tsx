import { useScrollAnimation } from '../hooks/useScrollAnimation';
import { useLanguage } from '../context/LanguageContext';
import { personalInfo, socialLinks } from '../data/portfolio';
import { Mail, MapPin, Github, Linkedin, Twitter } from 'lucide-react';

const iconMap: Record<string, React.ComponentType<{ size?: number }>> = {
  github: Github,
  linkedin: Linkedin,
  twitter: Twitter,
  mail: Mail,
};

export default function Contact() {
  const { ref, isVisible } = useScrollAnimation({ threshold: 0.2 });
  const { t, language } = useLanguage();

  return (
    <section id="contact" className="py-24 relative bg-slate-800/30">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-900/50 to-transparent" />
      
      <div
        ref={ref}
        className={`relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 transition-all duration-700 ${
          isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
        }`}
      >
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-100 mb-4">{t.contactTitle}</h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            {t.contactSubtitle}
          </p>
        </div>

        {/* Contact Cards */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {/* Email */}
          <div className="p-6 rounded-xl bg-slate-800/50 border border-slate-700 hover:border-sky-400/30 transition-all duration-300 group">
            <div className="w-12 h-12 rounded-xl bg-sky-400/10 flex items-center justify-center mb-4 group-hover:bg-sky-400/20 transition-colors">
              <Mail size={24} className="text-sky-400" />
            </div>
            <h3 className="text-sm text-slate-500 uppercase tracking-wider mb-1">{t.contactEmail}</h3>
            <a
              href={`mailto:${personalInfo.email}`}
              className="text-slate-200 hover:text-sky-400 transition-colors break-all"
            >
              {personalInfo.email}
            </a>
          </div>

          {/* Location */}
          <div className="p-6 rounded-xl bg-slate-800/50 border border-slate-700 hover:border-sky-400/30 transition-all duration-300 group">
            <div className="w-12 h-12 rounded-xl bg-sky-400/10 flex items-center justify-center mb-4 group-hover:bg-sky-400/20 transition-colors">
              <MapPin size={24} className="text-sky-400" />
            </div>
            <h3 className="text-sm text-slate-500 uppercase tracking-wider mb-1">{t.contactLocation}</h3>
            <p className="text-slate-200">{personalInfo.location[language]}</p>
          </div>

          {/* Social Links */}
          {socialLinks.slice(0, 2).map((link) => {
            const Icon = iconMap[link.icon] || Mail;
            return (
              <div
                key={link.name}
                className="p-6 rounded-xl bg-slate-800/50 border border-slate-700 hover:border-sky-400/30 transition-all duration-300 group"
              >
                <div className="w-12 h-12 rounded-xl bg-sky-400/10 flex items-center justify-center mb-4 group-hover:bg-sky-400/20 transition-colors">
                  <Icon size={24} className="text-sky-400" />
                </div>
                <h3 className="text-sm text-slate-500 uppercase tracking-wider mb-1">{link.name}</h3>
                <a
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-200 hover:text-sky-400 transition-colors"
                >
                  @{link.name.toLowerCase()}
                </a>
              </div>
            );
          })}
        </div>

        {/* CTA */}
        <div className="text-center">
          <a
            href={`mailto:${personalInfo.email}`}
            className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-sky-400 to-indigo-400 text-white font-semibold rounded-lg hover:shadow-lg hover:shadow-sky-400/25 transition-all duration-300 hover:-translate-y-0.5"
          >
            <Mail size={18} />
            {t.contactSendMessage}
          </a>
        </div>
      </div>
    </section>
  );
}
