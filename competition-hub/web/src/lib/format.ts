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

// 从 url 提取域名（去 www.），用于官网 Logo / favicon
export function domainOf(url?: string): string {
  if (!url) return ''
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return ''
  }
}

// 官网真实 Logo（Clearbit，矩形大图，最接近"官网图片"观感）
export function logoFor(url?: string): string {
  const d = domainOf(url)
  if (!d) return ''
  return `https://logo.clearbit.com/${d}?size=128`
}

// 兜底 favicon（Clearbit 失败时使用）
export function faviconFor(url?: string): string {
  const d = domainOf(url)
  if (!d) return ''
  return `https://www.google.com/s2/favicons?domain=${d}&sz=128`
}
