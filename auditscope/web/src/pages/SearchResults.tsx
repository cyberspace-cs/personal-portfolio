import { useEffect, useMemo, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { Navbar } from '../components/Navbar'
import { GlobalSearch } from '../components/GlobalSearch'
import { RiskBadge } from '../components/RiskBadge'
import { KIND_META } from '../components/Kinds'
import { CardSkeleton } from '../components/Skeleton'
import { search, ask } from '../api/client'
import { Sparkles, Loader2, ExternalLink } from 'lucide-react'
import type { SearchHit } from '../mock/data'

type Tab = SearchHit['kind'] | 'all'
const TABS: { key: Tab; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'company', label: '查公司' },
  { key: 'boss', label: '查老板' },
  { key: 'person', label: '查人员' },
  { key: 'flow', label: '查流水' },
  { key: 'social', label: '查社保' },
]

export function SearchResults() {
  const [params] = useSearchParams()
  const nav = useNavigate()
  const q = params.get('q') ?? ''
  const [hits, setHits] = useState<SearchHit[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<Tab>('all')

  const [ai, setAi] = useState<{ answer: string; refs: string[] } | null>(null)
  const [aiLoading, setAiLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    search(q).then(h => { setHits(h); setLoading(false) })
  }, [q])

  const filtered = useMemo(
    () => (tab === 'all' ? hits : hits.filter(h => h.kind === tab)),
    [hits, tab],
  )
  const counts = useMemo(() => {
    const c: Record<string, number> = { all: hits.length }
    hits.forEach(h => (c[h.kind] = (c[h.kind] ?? 0) + 1))
    return c
  }, [hits])

  const runAi = () => {
    setAiLoading(true); setAi(null)
    ask(q || '对当前结果给出审计关注要点').then(r => { setAi(r); setAiLoading(false) })
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-6">
        <div className="max-w-3xl">
          <GlobalSearch loading={loading} />
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_320px]">
          {/* 左侧：结果列表 */}
          <section>
            <div className="mb-4 flex flex-wrap gap-2">
              {TABS.map(t => (
                <button
                  key={t.key}
                  onClick={() => setTab(t.key)}
                  className={`rounded-full border px-3 py-1.5 text-sm transition-colors cursor-pointer ${
                    tab === t.key ? 'border-brand-primary bg-brand-primary/10 text-white' : 'border-line bg-bg-800/50 text-slate-300 hover:text-white'
                  }`}
                >
                  {t.label} <span className="text-slate-500">{counts[t.key] ?? 0}</span>
                </button>
              ))}
            </div>

            {loading ? (
              <div className="space-y-3">
                {[0, 1, 2].map(i => <CardSkeleton key={i} />)}
              </div>
            ) : filtered.length === 0 ? (
              <div className="rounded-xl border border-line bg-bg-800/50 p-10 text-center text-slate-400">未找到与「{q}」相关的记录</div>
            ) : (
              <div className="space-y-3">
                {filtered.map(h => {
                  const m = KIND_META[h.kind]
                  const Icon = m.icon
                  return (
                    <div key={h.id} className="group cursor-pointer rounded-xl border border-line bg-bg-800/60 p-5 transition-colors hover:border-brand-primary/50">
                      <div className="flex items-start gap-3">
                        <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-lg ${m.tint}`}><Icon className="h-5 w-5" /></span>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="truncate text-base font-medium text-slate-100">{h.title}</h3>
                            <RiskBadge risk={h.risk} />
                          </div>
                          <p className="mt-0.5 text-sm text-slate-400">{h.sub}</p>
                          <p className="mt-1 text-xs text-slate-500">{m.label} · ID {h.id}</p>
                        </div>
                        <ExternalLink className="h-4 w-4 text-slate-600 group-hover:text-slate-300" />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </section>

          {/* 右侧：AI RAG 问答面板 */}
          <aside className="lg:sticky lg:top-20 lg:self-start">
            <div className="rounded-xl border border-line bg-bg-800/60 p-5">
              <div className="flex items-center gap-2 text-sm font-medium text-slate-100">
                <Sparkles className="h-4 w-4 text-brand-accent" /> 智能审计助手
              </div>
              <p className="mt-1 text-xs text-slate-400">基于检索证据，给出审计关注要点与引用。</p>
              <button
                onClick={runAi}
                disabled={aiLoading}
                className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg bg-brand-accent/90 px-3 py-2 text-sm font-medium text-bg-900 transition-colors hover:bg-brand-accent disabled:opacity-60 cursor-pointer"
              >
                {aiLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                分析「{q || '当前结果'}」
              </button>
              {ai && (
                <div className="mt-4 animate-fadeup rounded-lg border border-line bg-bg-900/50 p-3 text-sm leading-relaxed text-slate-200">
                  {ai.answer}
                  {ai.refs.length > 0 && (
                    <div className="mt-3 border-t border-line pt-2 text-xs text-slate-400">
                      引用：{ai.refs.join('，')}
                    </div>
                  )}
                </div>
              )}
            </div>
          </aside>
        </div>
      </main>
    </div>
  )
}
