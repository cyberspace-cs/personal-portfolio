export const STATUS_META: Record<string, { label: string; cls: string }> = {
  upcoming: { label: '即将开始', cls: 'text-neon-amber border-neon-amber/40 bg-neon-amber/10' },
  ongoing: { label: '进行中', cls: 'text-neon-green border-neon-green/40 bg-neon-green/10' },
  ended: { label: '已结束', cls: 'text-slate-400 border-slate-500/30 bg-slate-500/10' },
}

export const MODE_META: Record<string, { label: string }> = {
  online: { label: '线上' },
  offline: { label: '线下' },
  hybrid: { label: '线上+线下' },
}

export function statusLabel(s: string) {
  return STATUS_META[s]?.label ?? s
}
export function modeLabel(m: string) {
  return MODE_META[m]?.label ?? m
}

// 聚合来源 → 彩色标签配色（按关键词匹配，保证每个来源有稳定专属色）
export const SOURCE_META: { re: RegExp; cls: string }[] = [
  { re: /和鲸|heikesong|黑客松/i, cls: 'text-neon-cyan border-neon-cyan/40 bg-neon-cyan/10' },
  { re: /biendata/i, cls: 'text-neon-violet border-neon-violet/40 bg-neon-violet/10' },
  { re: /赛氪|saikr/i, cls: 'text-neon-amber border-neon-amber/40 bg-neon-amber/10' },
  { re: /kaggle/i, cls: 'text-neon-blue border-neon-blue/40 bg-neon-blue/10' },
  { re: /阿里|天池|aliyun|tianchi/i, cls: 'text-orange-300 border-orange-300/40 bg-orange-300/10' },
  { re: /datafountain|数据[iI]?(?:湖|谷|竞赛)/i, cls: 'text-teal-300 border-teal-300/40 bg-teal-300/10' },
]
export function sourceTagClass(name = '') {
  const m = SOURCE_META.find((x) => x.re.test(name))
  return m?.cls ?? 'text-neon-azure border-neon-azure/40 bg-neon-azure/10'
}

export function fmtDate(s: string | null | undefined) {
  if (!s) return '待定'
  return s
}

// 根据标题生成稳定的渐变封面（无图时使用）
export function coverGradient(seed: string) {
  let h = 0
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0
  const a = h % 360
  const b = (a + 60) % 360
  return `linear-gradient(135deg, hsl(${a} 70% 22%), hsl(${b} 75% 14%))`
}

// 从 url 提取域名（去 www.），用于官网 favicon
export function domainOf(url?: string): string {
  if (!url) return ''
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return ''
  }
}

// 官网自有 favicon（直接用官方域名的 /favicon.ico，国内可访问，不依赖被墙的第三方图床）
export function faviconFor(url?: string): string {
  const d = domainOf(url)
  if (!d) return ''
  return `https://${d}/favicon.ico`
}

// 站点首字（favicon 加载失败时的文字兜底，保证始终有可见标识）
export function initialOf(source?: string, url?: string): string {
  const s = (source || domainOf(url) || '?').trim()
  const m = s.match(/[一-龥A-Za-z0-9]/)
  const ch = m ? m[0] : s[0] || '?'
  return ch.toUpperCase()
}
