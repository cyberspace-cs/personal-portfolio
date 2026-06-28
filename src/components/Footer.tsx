import { Github, Linkedin, Twitter, Mail, Heart } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { personalInfo, socialLinks } from '../data/portfolio';

const iconMap: Record<string, any> = {
  github: Github,
  linkedin: Linkedin,
  twitter: Twitter,
  mail: Mail,
};

export default function Footer() {
  const { t, language } = useLanguage();
  const currentYear = new Date().getFullYear();

  const initials = personalInfo.name.en
    .split(' ')
    .map((n) => n[0])
    .join('');

  return (
    <footer className="py-8 border-t border-slate-800">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Logo & Copyright */}
          <div className="flex items-center gap-4">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-indigo-400 flex items-center justify-center">
              <span className="text-xs font-bold text-white">{initials}</span>
            </div>
            <p className="text-sm text-slate-500">
              © {currentYear} {personalInfo.name[language]}. {t.footerAllRights}
            </p>
          </div>

          {/* Social Links */}
          <div className="flex items-center gap-3">
            {socialLinks.map((link) => {
              const Icon = iconMap[link.icon] || Mail;
              return (
                <a
                  key={link.name}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center text-slate-500 hover:text-sky-400 hover:bg-slate-700 transition-all duration-300"
                  aria-label={link.name}
                >
                  <Icon size={16} />
                </a>
              );
            })}
          </div>

          {/* Built with */}
          <p className="text-sm text-slate-500 flex items-center gap-1">
            {t.footerBuiltWith} <Heart size={14} className="text-red-500" /> using React & Tailwind
          </p>
        </div>
      </div>
    </footer>
  );
}
