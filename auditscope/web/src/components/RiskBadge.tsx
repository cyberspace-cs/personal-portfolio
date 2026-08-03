import type { RiskLevel } from '../mock/data'

const MAP: Record<RiskLevel, { label: string; cls: string; dot: string }> = {
  normal: { label: '正常', cls: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', dot: 'bg-emerald-400' },
  watch: { label: '关注', cls: 'bg-amber-500/10 text-amber-400 border-amber-500/30', dot: 'bg-amber-400' },
  high: { label: '高风险', cls: 'bg-red-500/10 text-red-400 border-red-500/30', dot: 'bg-red-400' },
}

export function RiskBadge({ risk }: { risk: RiskLevel }) {
  const m = MAP[risk]
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${m.cls}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${m.dot}`} />
      {m.label}
    </span>
  )
}
