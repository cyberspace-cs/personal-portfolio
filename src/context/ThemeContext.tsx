import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react';

export type ThemeMode = 'auto' | 'light' | 'dark';
export type ThemePalette = 'tech' | 'warm';

interface ThemeContextType {
  mode: ThemeMode;
  palette: ThemePalette;
  /** 实际生效的深浅（mode=auto 时由系统决定） */
  resolvedDark: boolean;
  setMode: (m: ThemeMode) => void;
  setPalette: (p: ThemePalette) => void;
  toggleMode: () => void;
}

const STORAGE_MODE = 'theme-mode';
const STORAGE_PALETTE = 'theme-palette';

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

function getSystemDark(): boolean {
  if (typeof window === 'undefined' || !window.matchMedia) return false;
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

/** 在 React 挂载前由 index.html 内联脚本调用，避免首屏闪烁 */
export function applyThemeToDocument(mode: ThemeMode, palette: ThemePalette) {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  const isDark = mode === 'dark' || (mode === 'auto' && getSystemDark());
  root.classList.toggle('dark', isDark);
  root.setAttribute('data-palette', palette);
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem(STORAGE_MODE) as ThemeMode | null;
    return saved === 'light' || saved === 'dark' || saved === 'auto'
      ? saved
      : 'auto';
  });

  const [palette, setPaletteState] = useState<ThemePalette>(() => {
    const saved = localStorage.getItem(STORAGE_PALETTE) as ThemePalette | null;
    return saved === 'warm' ? 'warm' : 'tech';
  });

  const [systemDark, setSystemDark] = useState<boolean>(getSystemDark);

  // 监听系统深浅变化（仅 auto 模式需要）
  useEffect(() => {
    if (!window.matchMedia) return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e: MediaQueryListEvent) => setSystemDark(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const resolvedDark = mode === 'dark' || (mode === 'auto' && systemDark);

  useEffect(() => {
    localStorage.setItem(STORAGE_MODE, mode);
    const root = document.documentElement;
    root.classList.toggle('dark', resolvedDark);
  }, [mode, resolvedDark]);

  useEffect(() => {
    localStorage.setItem(STORAGE_PALETTE, palette);
    document.documentElement.setAttribute('data-palette', palette);
  }, [palette]);

  const setMode = (m: ThemeMode) => setModeState(m);
  const setPalette = (p: ThemePalette) => setPaletteState(p);
  const toggleMode = () =>
    setModeState((prev) => (prev === 'dark' ? 'light' : 'dark'));

  return (
    <ThemeContext.Provider
      value={{ mode, palette, resolvedDark, setMode, setPalette, toggleMode }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
