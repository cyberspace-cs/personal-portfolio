import { useScrollAnimation } from '../hooks/useScrollAnimation';
import { useLanguage } from '../context/LanguageContext';
import { personalInfo, socialLinks } from '../data/portfolio';
import { Mail, MapPin, Github, Linkedin, Twitter } from 'lucide-react';

const iconMap: Record<string, any> = {
  github: Github,
  linkedin: Linkedin,
  twitter: Twitter,
  mail: Mail,
};

export default function Contact() {
  const { ref, isVisible } = useScrollAnimation({ threshold: 0.2 });
  const { t, language } = useLanguage();

  return (
    <section id="contact" className="py-24 relative bg-surface/30">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-bg/50 to-transparent" />

      <div
        ref={ref}
        className={`relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 transition-all duration-700 ${
          isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
        }`}
      >
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-fg mb-4">{t.contactTitle}</h2>
          <p className="text-muted max-w-2xl mx-auto">
            {t.contactSubtitle}
          </p>
        </div>

        {/* Contact Cards */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {/* Email */}
          <div className="p-6 rounded-xl bg-surface/50 border border-line hover:border-accent/30 transition-all duration-300 group">
            <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4 group-hover:bg-accent/20 transition-colors">
              <Mail size={24} className="text-accent" />
            </div>
            <h3 className="text-sm text-faint uppercase tracking-wider mb-1">{t.contactEmail}</h3>
            <a
              href={`mailto:${personalInfo.email}`}
              className="text-fg hover:text-accent transition-colors break-all"
            >
              {personalInfo.email}
            </a>
          </div>

          {/* Location */}
          <div className="p-6 rounded-xl bg-surface/50 border border-line hover:border-accent/30 transition-all duration-300 group">
            <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4 group-hover:bg-accent/20 transition-colors">
              <MapPin size={24} className="text-accent" />
            </div>
            <h3 className="text-sm text-faint uppercase tracking-wider mb-1">{t.contactLocation}</h3>
            <p className="text-fg">{personalInfo.location[language]}</p>
          </div>

          {/* Social Links */}
          {socialLinks.slice(0, 2).map((link) => {
            const Icon = iconMap[link.icon] || Mail;
            return (
              <div
                key={link.name}
                className="p-6 rounded-xl bg-surface/50 border border-line hover:border-accent/30 transition-all duration-300 group"
              >
                <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4 group-hover:bg-accent/20 transition-colors">
                  <Icon size={24} className="text-accent" />
                </div>
                <h3 className="text-sm text-faint uppercase tracking-wider mb-1">{link.name}</h3>
                <a
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-fg hover:text-accent transition-colors"
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
            className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-accent to-accent-2 text-on-accent font-semibold rounded-lg hover:shadow-lg hover:shadow-accent/25 transition-all duration-300 hover:-translate-y-0.5"
          >
            <Mail size={18} />
            {t.contactSendMessage}
          </a>
        </div>
      </div>
    </section>
  );
}
