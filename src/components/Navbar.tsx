import { useState, useEffect } from 'react';
import { Menu, X, Sun, Moon, Palette } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { personalInfo } from '../data/portfolio';

type NavItem = {
  id?: string; // 首页内锚点
  to?: string; // 路由
  href?: string; // 外链
  label: string;
  external?: boolean;
};

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

  const navLinks: NavItem[] = [
    { id: 'about', label: t.navAbout },
    { id: 'skills', label: t.navSkills },
    { id: 'experience', label: t.navExperience },
    { id: 'projects', label: t.navProjects },
    { id: 'learning', label: t.navLearning },
    { id: 'education', label: t.navEducation },
    { id: 'contact', label: t.navContact },
    { to: '/blog', label: t.navBlog },
    { href: '/ai-briefing.html', label: t.navBriefing, external: true },
  ];

  useEffect(() => {
    const ids = navLinks.map((l) => l.id).filter(Boolean) as string[];
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

    ids.forEach((id) => {
      const element = document.getElementById(id);
      if (element) observer.observe(element);
    });

    return () => observer.disconnect();
  }, []);

  const ThemeControls = ({ mobile = false }: { mobile?: boolean }) => (
    <div className={`flex items-center gap-2 ${mobile ? '' : 'ml-2'}`}>
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

  const renderLink = (link: NavItem, mobile = false) => {
    const isActive = link.id ? activeSection === link.id : false;
    const base = `px-3 py-1.5 rounded-lg text-sm transition-all duration-200 ${
      isActive
        ? 'bg-accent/15 text-accent'
        : 'text-muted hover:text-accent hover:bg-surface-2/50'
    } ${link.external ? 'border border-accent/30 hover:border-accent' : ''}`;
    const mobileBase = `px-3 py-2 rounded-lg transition-colors ${
      isActive ? 'bg-accent/15 text-accent' : 'text-muted hover:text-accent'
    } ${link.external ? 'border border-accent/30' : ''}`;

    if (link.to) {
      return (
        <Link key={link.label} to={link.to} className={mobile ? mobileBase : base}>
          {link.label}
        </Link>
      );
    }
    if (link.href) {
      return (
        <a
          key={link.label}
          href={link.href}
          target="_blank"
          rel="noopener noreferrer"
          className={mobile ? mobileBase : base}
        >
          {link.label}
        </a>
      );
    }
    // 首页内锚点：用 /#id 形式，确保在任意路由下都能回到首页对应区块
    return (
      <a
        key={link.label}
        href={`/#${link.id}`}
        className={mobile ? mobileBase : base}
        onClick={() => mobile && setIsMobileMenuOpen(false)}
      >
        {link.label}
      </a>
    );
  };

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
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-accent-2 flex items-center justify-center">
              <span className="text-sm font-bold text-on-accent">T</span>
            </div>
            <span className="text-lg font-bold text-fg">Tao Xie</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => renderLink(link))}

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
            {navLinks.map((link) => renderLink(link, true))}
          </div>
        </div>
      </div>
    </nav>
  );
}
