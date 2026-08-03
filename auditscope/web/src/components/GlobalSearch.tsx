import { Search, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { KIND_META } from './Kinds'
import type { SearchHit } from '../mock/data'

const QUICK = [
  { q: '星河智能', hint: '查公司 / 老板' },
  { q: '李文博', hint: '查老板 / 风险' },
  { q: '云栖数据', hint: '高风险企业' },
  { q: '公转私', hint: '查异常流水' },
]

export function GlobalSearch({ loading, onResults }: { loading?: boolean; onResults?: (h: SearchHit[]) => void }) {
  const [q, setQ] = useState('')
  const nav = useNavigate()
  const submit = (val: string) => {
    const v = val.trim()
    if (!v) return
    nav(`/search?q=${encodeURIComponent(v)}`)
  }
  return (
    <div className="w-full">
      <form
        onSubmit={e => { e.preventDefault(); submit(q) }}
        className="group flex items-center gap-3 rounded-2xl border border-line bg-bg-800/70 px-4 py-3.5 shadow-glow backdrop-blur transition-colors focus-within:border-brand-primary/60"
      >
        <Search className="h-5 w-5 text-slate-400" />
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="输入公司名 / 老板姓名 / 人员 / 流水关键词，如「星河智能」「李文博」「公转私」"
          aria-label="综合查询"
          className="w-full bg-transparent text-[15px] text-slate-100 placeholder:text-slate-500 outline-none"
        />
        <button
          type="submit"
          disabled={loading}
          className="flex items-center gap-1.5 rounded-xl bg-brand-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-primary/90 disabled:opacity-60 cursor-pointer"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          查询
        </button>
      </form>
      <div className="mt-3 flex flex-wrap gap-2">
        {QUICK.map(k => (
          <button
            key={k.q}
            onClick={() => { setQ(k.q); submit(k.q) }}
            className="rounded-full border border-line bg-bg-800/50 px-3 py-1 text-xs text-slate-300 transition-colors hover:border-brand-accent/50 hover:text-white cursor-pointer"
          >
            {k.q} <span className="text-slate-500">· {k.hint}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

export { KIND_META }
