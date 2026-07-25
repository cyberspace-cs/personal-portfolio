import { describe, it, expect } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const cssPath = path.resolve(__dirname, '../index.css');
const css = fs.readFileSync(cssPath, 'utf-8');

/** 把 "R G B" 字符串解析为 [r,g,b] */
function parseRgb(triple: string): [number, number, number] {
  const [r, g, b] = triple.trim().split(/\s+/).map(Number);
  return [r, g, b];
}

/** 相对亮度（WCAG 2.1） */
function relativeLuminance([r, g, b]: [number, number, number]): number {
  const srgb = [r, g, b].map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2];
}

/** 对比度（WCAG） */
export function contrast(triple1: string, triple2: string): number {
  const l1 = relativeLuminance(parseRgb(triple1));
  const l2 = relativeLuminance(parseRgb(triple2));
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

/** 从 index.css 抽取某个选择器块内的 CSS 变量 */
function extractVars(selector: string): Record<string, string> {
  // 匹配 e.g. :root[data-palette='tech']:not(.dark) { ... }
  const re = new RegExp(
    `${selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\{([^}]*)\\}`,
    'm'
  );
  const m = css.match(re);
  if (!m) throw new Error(`未找到选择器: ${selector}`);
  const vars: Record<string, string> = {};
  const lines = m[1].split(';');
  for (const line of lines) {
    const mm = line.match(/--c-([a-z-]+)\s*:\s*([\d\s]+)/);
    if (mm) vars[mm[1]] = mm[2];
  }
  return vars;
}

const STATES = [
  { name: 'tech-dark', sel: ":root[data-palette='tech'].dark" },
  { name: 'tech-light', sel: ":root[data-palette='tech']:not(.dark)" },
  { name: 'warm-dark', sel: ":root[data-palette='warm'].dark" },
  { name: 'warm-light', sel: ":root[data-palette='warm']:not(.dark)" },
];

describe('主题调色板 WCAG 对比度', () => {
  for (const s of STATES) {
    const v = extractVars(s.sel);

    it(`${s.name}: 主文字(fg) 在背景(bg) 上对比度 >= 4.5`, () => {
      expect(contrast(v['fg'], v['bg'])).toBeGreaterThanOrEqual(4.5);
    });

    it(`${s.name}: 次文字(muted) 在背景(bg) 上对比度 >= 4.5`, () => {
      expect(contrast(v['muted'], v['bg'])).toBeGreaterThanOrEqual(4.5);
    });

    it(`${s.name}: 弱文字(faint) 在背景(bg) 上对比度 >= 3 (large/AA大字号)`, () => {
      expect(contrast(v['faint'], v['bg'])).toBeGreaterThanOrEqual(3);
    });

    it(`${s.name}: 边框(line) 与背景(bg) 可区分 (对比度 >= 1.4)`, () => {
      expect(contrast(v['line'], v['bg'])).toBeGreaterThanOrEqual(1.4);
    });

    it(`${s.name}: 强调色(accent) 用于文字时在背景(bg) 上对比度 >= 4.5`, () => {
      expect(contrast(v['accent'], v['bg'])).toBeGreaterThanOrEqual(4.5);
    });

    it(`${s.name}: 强调按钮文字(on-accent) 在强调色(accent) 上对比度 >= 4.5`, () => {
      expect(contrast(v['on-accent'], v['accent'])).toBeGreaterThanOrEqual(4.5);
    });
  }

  it('四态调色板变量完整（含 fg/bg/muted/faint/line/accent/on-accent）', () => {
    for (const s of STATES) {
      const v = extractVars(s.sel);
      for (const key of ['fg', 'bg', 'muted', 'faint', 'line', 'accent', 'on-accent']) {
        expect(v[key], `${s.name} 缺少 --c-${key}`).toBeDefined();
      }
    }
  });
});
