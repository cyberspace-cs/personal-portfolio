import { Search, Sparkles } from 'lucide-react'
import type { Stats } from '../lib/types'

export function Hero({
  query,
  onQuery,
  onSearch,
  stats,
}: {
  query: string
  onQuery: (v: string) => void
  onSearch?: () => void
  stats?: Stats
}) {
  return (
    <section className="relative overflow-hidden border-b border-white/10">
      <div className="absolute inset-0 cyber-grid opacity-30" />
      <div className="absolute -left-20 top-0 h-64 w-64 rounded-full bg-neon-cyan/20 blur-3xl" />
      <div className="absolute -right-10 top-10 h-72 w-72 rounded-full bg-neon-violet/20 blur-3xl" />
      <div className="relative mx-auto max-w-6xl px-4 py-14 text-center">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-neon-cyan/30 bg-neon-cyan/10 px-3 py-1 text-xs font-medium text-neon-cyan">
          <Sparkles size={13} /> AI 自动聚合 · 实时更新赛事库
        </span>
        <h1 className="mt-4 text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
          竞赛<span className="neon-text text-neon-cyan">雷达</span>
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-sm text-slate-400">
          自动搜寻全球黑客松、Kaggle 数据竞赛、算法大赛、CTF、AI 大模型与创新创业赛事，
          一站聚合呈现 —— 让你不再错过属于你的下一个舞台。
        </p>

        <div className="mx-auto mt-7 flex max-w-xl items-center gap-2 rounded-2xl border border-white/10 bg-ink-900/70 p-2 backdrop-blur">
          <Search size={18} className="ml-2 text-slate-400" />
          <input
            value={query}
            onChange={(e) => onQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (document.getElementById('do-search') as HTMLButtonElement)?.click()}
            placeholder="搜索竞赛名称、主办方、关键词…"
            className="flex-1 bg-transparent px-2 py-2 text-sm text-white outline-none placeholder:text-slate-500"
          />
          <button id="do-search" className="btn-primary" onClick={() => onSearch?.()}>
            搜索
          </button>
        </div>

        {stats && (
          <div className="mx-auto mt-8 grid max-w-2xl grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { k: '竞赛总数', v: stats.total },
              { k: '进行中', v: stats.ongoing },
              { k: '即将开始', v: stats.upcoming },
              { k: '分类', v: stats.categories },
            ].map((s) => (
              <div key={s.k} className="glass px-3 py-3">
                <div className="text-2xl font-bold text-white">{s.v}</div>
                <div className="text-[11px] text-slate-400">{s.k}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
