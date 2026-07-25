import { useState, useEffect } from 'react';
import { Menu, X, Sun, Moon, Palette } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { personalInfo } from '../data/portfolio';

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('about');
  const { language, toggleLanguage, t } = useLanguage();
  const { mode, palette, setMode, setPalette } = useTheme();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks: { href: string; label: string; external?: boolean }[] = [
    { href: '#about', label: t.navAbout },
    { href: '#skills', label: t.navSkills },
    { href: '#experience', label: t.navExperience },
    { href: '#projects', label: t.navProjects },
    { href: '#learning', label: t.navLearning },
    { href: '#education', label: t.navEducation },
    { href: '#contact', label: t.navContact },
    { href: '/ai-briefing.html', label: t.navBriefing, external: true },
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

  const ThemeControls = ({ mobile = false }: { mobile?: boolean }) => (
    <div className={`flex items-center gap-2 ${mobile ? '' : 'ml-2'}`}>
      {/* 深浅切换：auto / light / dark 循环 */}
      <button
        onClick={() =>
          setMode(mode === 'auto' ? 'light' : mode === 'light' ? 'dark' : 'auto')
        }
        className="p-2 rounded-lg border border-line text-muted hover:border-accent hover:text-accent transition-all duration-200"
        title={
          mode === 'auto'
            ? '跟随系统（点击切换浅色）'
            : mode === 'light'
              ? '浅色（点击切换深色）'
              : '深色（点击跟随系统）'
        }
        aria-label="切换深浅模式"
      >
        {mode === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
      </button>

      {/* 风格切换：科技蓝 / 暖色 */}
      <button
        onClick={() => setPalette(palette === 'tech' ? 'warm' : 'tech')}
        className="p-2 rounded-lg border border-line text-muted hover:border-accent hover:text-accent transition-all duration-200"
        title={palette === 'tech' ? '科技蓝（点击切换暖色）' : '暖色（点击切换科技蓝）'}
        aria-label="切换配色风格"
      >
        <Palette size={16} />
      </button>
    </div>
  );

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-bg/80 backdrop-blur-lg border-b border-line'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <a href="#" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-accent-2 flex items-center justify-center">
              <span className="text-sm font-bold text-on-accent">T</span>
            </div>
            <span className="text-lg font-bold text-fg">Tao Xie</span>
          </a>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = activeSection === link.href.substring(1);
              return (
                <a
                  key={link.href}
                  href={link.href}
                  {...(link.external
                    ? { target: '_blank', rel: 'noopener noreferrer' }
                    : {})}
                  className={`px-3 py-1.5 rounded-lg text-sm transition-all duration-200 ${
                    isActive
                      ? 'bg-accent/15 text-accent'
                      : 'text-muted hover:text-accent hover:bg-surface-2/50'
                  } ${link.external ? 'border border-accent/30 hover:border-accent' : ''}`}
                >
                  {link.label}
                </a>
              );
            })}

            {/* Language Toggle */}
            <button
              onClick={toggleLanguage}
              className="ml-2 px-3 py-1.5 rounded-lg border border-line text-sm text-muted hover:border-accent hover:text-accent transition-all duration-200"
            >
              {language === 'en' ? '中文' : 'EN'}
            </button>

            <ThemeControls />
          </div>

          {/* Mobile Menu Button */}
          <div className="flex items-center gap-2 md:hidden">
            <button
              onClick={toggleLanguage}
              className="p-2 rounded-lg border border-line text-muted hover:border-accent hover:text-accent transition-all duration-200"
            >
              {language === 'en' ? '中' : 'EN'}
            </button>
            <ThemeControls mobile />
            <button
              className="p-2 text-muted hover:text-fg transition-colors"
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
        <div className="bg-bg/95 backdrop-blur-lg border-t border-line px-4 py-4">
          <div className="flex flex-col gap-4">
            {navLinks.map((link) => {
              const isActive = activeSection === link.href.substring(1);
              return (
                <a
                  key={link.href}
                  href={link.href}
                  {...(link.external
                    ? { target: '_blank', rel: 'noopener noreferrer' }
                    : {})}
                  className={`px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-accent/15 text-accent'
                      : 'text-muted hover:text-accent'
                  } ${link.external ? 'border border-accent/30' : ''}`}
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
