import { Building2, Crown, User, ArrowLeftRight, ShieldCheck } from 'lucide-react'
import type { SearchHit } from '../mock/data'

export const KIND_META: Record<SearchHit['kind'], { label: string; icon: typeof Building2; tint: string }> = {
  company: { label: '查公司', icon: Building2, tint: 'text-sky-400 bg-sky-500/10' },
  boss: { label: '查老板', icon: Crown, tint: 'text-amber-400 bg-amber-500/10' },
  person: { label: '查人员', icon: User, tint: 'text-violet-400 bg-violet-500/10' },
  flow: { label: '查流水', icon: ArrowLeftRight, tint: 'text-cyan-400 bg-cyan-500/10' },
  social: { label: '查社保', icon: ShieldCheck, tint: 'text-emerald-400 bg-emerald-500/10' },
}
