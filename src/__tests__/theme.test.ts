import { describe, it, expect, beforeEach } from 'vitest';
import { applyThemeToDocument } from '../context/ThemeContext';

describe('主题应用逻辑（不破布局的前提：class/dataset 正确切换）', () => {
  beforeEach(() => {
    document.documentElement.className = '';
    document.documentElement.removeAttribute('data-palette');
  });

  it('auto + 系统深色 => 加 .dark，data-palette=tech', () => {
    // 模拟系统偏好深色
    window.matchMedia = ((q: string) => ({
      matches: q.includes('dark'),
      media: q,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    })) as any;

    applyThemeToDocument('auto', 'tech');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(document.documentElement.getAttribute('data-palette')).toBe('tech');
  });

  it('auto + 系统浅色 => 不加 .dark', () => {
    window.matchMedia = ((q: string) => ({
      matches: !q.includes('dark'),
      media: q,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    })) as any;

    applyThemeToDocument('auto', 'warm');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(document.documentElement.getAttribute('data-palette')).toBe('warm');
  });

  it('手动 light => 不加 .dark（无论系统偏好）', () => {
    window.matchMedia = ((q: string) => ({
      matches: q.includes('dark'),
      media: q,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    })) as any;

    applyThemeToDocument('light', 'tech');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('手动 dark => 加 .dark（无论系统偏好）', () => {
    window.matchMedia = ((q: string) => ({
      matches: false,
      media: q,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    })) as any;

    applyThemeToDocument('dark', 'warm');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(document.documentElement.getAttribute('data-palette')).toBe('warm');
  });

  it('切换时不会残留旧的 data-palette', () => {
    applyThemeToDocument('auto', 'tech');
    applyThemeToDocument('dark', 'warm');
    expect(document.documentElement.getAttribute('data-palette')).toBe('warm');
    // dark 始终存在
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });
});
