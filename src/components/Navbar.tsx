import { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { personalInfo } from '../data/portfolio';

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('about');
  const { language, toggleLanguage, t } = useLanguage();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const initials = personalInfo.name.en
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase();

  const navLinks = [
    { href: '#about', label: t.navAbout },
    { href: '#skills', label: t.navSkills },
    { href: '#experience', label: t.navExperience },
    { href: '#projects', label: t.navProjects },
    { href: '#education', label: t.navEducation },
    { href: '#contact', label: t.navContact },
  ];

  useEffect(() => {
    const sections = navLinks.map((link) => link.href.substring(1));
    
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { rootMargin: '-40% 0px -55% 0px', threshold: 0 }
    );

    sections.forEach((id) => {
      const element = document.getElementById(id);
      if (element) observer.observe(element);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-slate-900/80 backdrop-blur-lg border-b border-slate-800'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <a href="#" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-indigo-400 flex items-center justify-center">
              <span className="text-sm font-bold text-white">{initials[0]}</span>
            </div>
            <span className="text-lg font-bold text-slate-100">{initials}.</span>
          </a>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = activeSection === link.href.substring(1);
              return (
                <a
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 rounded-lg text-sm transition-all duration-200 ${
                    isActive
                      ? 'bg-sky-500/15 text-sky-400'
                      : 'text-slate-400 hover:text-sky-400 hover:bg-slate-800/50'
                  }`}
                >
                  {link.label}
                </a>
              );
            })}
            
            {/* Language Toggle */}
            <button
              onClick={toggleLanguage}
              className="ml-4 px-3 py-1.5 rounded-lg border border-slate-600 text-sm text-slate-300 hover:border-sky-400 hover:text-sky-400 transition-all duration-200"
            >
              {language === 'en' ? '中文' : 'EN'}
            </button>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex items-center gap-2 md:hidden">
            <button
              onClick={toggleLanguage}
              className="p-2 rounded-lg border border-slate-600 text-slate-300 hover:border-sky-400 hover:text-sky-400 transition-all duration-200"
            >
              {language === 'en' ? '中' : 'EN'}
            </button>
            <button
              className="p-2 text-slate-400 hover:text-slate-100 transition-colors"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      <div
        className={`md:hidden transition-all duration-300 overflow-hidden ${
          isMobileMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="bg-slate-900/95 backdrop-blur-lg border-t border-slate-800 px-4 py-4">
          <div className="flex flex-col gap-4">
            {navLinks.map((link) => {
              const isActive = activeSection === link.href.substring(1);
              return (
                <a
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-sky-500/15 text-sky-400'
                      : 'text-slate-400 hover:text-sky-400'
                  }`}
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  {link.label}
                </a>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
