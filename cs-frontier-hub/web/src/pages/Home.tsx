import { useEffect, useMemo, useState } from 'react'
import { Search, TrendingUp, Layers, Boxes, ArrowRight, Sparkles } from 'lucide-react'
import { api } from '../lib/api'
import { ensureSession, getSessionId } from '../lib/session'
import type { Category, Item, Stats } from '../lib/types'
import { Sidebar } from '../components/Sidebar'
import { ItemCard } from '../components/ItemCard'

const SORTS = [
  { v: 'latest', label: '最新' },
  { v: 'stars', label: 'Star 数' },
  { v: 'views', label: '热度' },
  { v: 'title', label: '名称' },
]

export function Home() {
  const [categories, setCategories] = useState<Category[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [items, setItems] = useState<Item[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)

  const [q, setQ] = useState('')
  const [debounced, setDebounced] = useState('')
  const [category, setCategory] = useState('')
  const [sourceType, setSourceType] = useState('')
  const [sort, setSort] = useState('latest')

  const sessionId = getSessionId()

  useEffect(() => {
    api.getCategories().then(setCategories)
    api.getStats().then(setStats)
    ensureSession().catch(() => {})
  }, [])

  useEffect(() => {
    const t = setTimeout(() => setDebounced(q), 300)
    return () => clearTimeout(t)
  }, [q])

  // 任意筛选变化 -> 重置到第 1 页并重新拉取
  useEffect(() => {
    setPage(1)
  }, [debounced, category, sourceType, sort])

  useEffect(() => {
    setLoading(true)
    api
      .listItems({
        q: debounced,
        category,
        source_type: sourceType,
        sort,
        page,
        page_size: 12,
        session_id: sessionId,
      })
      .then((r) => {
        setTotal(r.total)
        setItems((prev) => (page === 1 ? r.items : [...prev, ...r.items]))
        setTotal(r.total)
      })
      .finally(() => setLoading(false))
  }, [debounced, category, sourceType, sort, page, sessionId])

  const featured = useMemo(
    () => items.filter((i) => i.featured).slice(0, 3),
    [items],
  )
  const showFeatured = !debounced && !category && !sourceType && page === 1

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      {/* Hero */}
      <section className="relative mb-10 overflow-hidden rounded-3xl border p-8 sm:p-12">
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-accent/20 blur-3xl" />
        <div className="absolute -bottom-24 -left-10 h-56 w-56 rounded-full bg-accent-2/20 blur-3xl" />
        <div className="relative">
          <span className="badge border-accent/30 bg-accent/10 text-accent">
            <Sparkles size={13} /> 前沿技术 · 实时聚合
          </span>
          <h1 className="mt-4 max-w-3xl text-3xl font-extrabold leading-tight sm:text-5xl">
            计算机 / <span className="neon">Agent · LLM · AI</span> 前沿知识聚合
          </h1>
          <p className="mt-3 max-w-2xl text-muted">
            收录 GPU 算子、Triton、推理引擎、Agent 框架、MCP、RAG、强化学习、混元 AI Infra、顶会前沿等方向，
            聚合 GitHub 高星项目、开源资料与前沿产品。
          </p>

          {/* 搜索 */}
          <div className="mt-6 flex max-w-2xl items-center gap-2 rounded-2xl border bg-surface p-2 shadow-glow">
            <Search size={18} className="ml-2 text-muted" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="搜索项目、模型、框架、关键词，如 vLLM、MCP、DeepSeek、Triton…"
              className="flex-1 bg-transparent px-1 py-2 text-sm outline-none"
            />
            {q && (
              <button onClick={() => setQ('')} className="btn-ghost h-8 !px-3 text-xs">
                清空
              </button>
            )}
          </div>

          {/* 统计 */}
          {stats && (
            <div className="mt-6 flex flex-wrap gap-3 text-sm">
              <Stat Icon={Boxes} label="前沿条目" value={stats.total} />
              <Stat Icon={Layers} label="技术分类" value={stats.categories} />
              <Stat Icon={TrendingUp} label="趋势中" value={stats.trending} />
            </div>
          )}
        </div>
      </section>

      {/* 精选 */}
      {showFeatured && featured.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 flex items-center gap-2 text-lg font-bold">
            <Sparkles size={18} className="text-accent" /> 编辑精选
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {featured.map((i) => (
              <ItemCard key={i.id} item={i} />
            ))}
          </div>
        </section>
      )}

      {/* 主体：侧栏 + 列表 */}
      <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
        <div className="lg:sticky lg:top-20 lg:self-start">
          <Sidebar
            categories={categories}
            activeCategory={category}
            onSelectCategory={setCategory}
            sourceType={sourceType}
            onSelectSource={setSourceType}
          />
        </div>

        <div>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-muted">
              共 <span className="font-semibold text-fg">{total}</span> 条结果
              {category && ' · 已筛选分类'}
              {sourceType && ' · 已筛选类型'}
              {debounced && ` · 关键词「${debounced}」`}
            </p>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted">排序</span>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value)}
                className="input !w-auto !py-1.5 text-sm"
              >
                {SORTS.map((s) => (
                  <option key={s.v} value={s.v}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {loading && page === 1 ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="card h-44 animate-pulse opacity-60" />
              ))}
            </div>
          ) : items.length === 0 ? (
            <div className="card flex flex-col items-center gap-2 py-16 text-center text-muted">
              <Search size={28} />
              <p>没有找到匹配的前沿信息，换个关键词试试？</p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {items.map((i) => (
                <ItemCard key={i.id} item={i} />
              ))}
            </div>
          )}

          {/* 分页 */}
          {items.length < total && (
            <div className="mt-6 flex justify-center">
              <button className="btn-primary" disabled={loading} onClick={() => setPage((p) => p + 1)}>
                {loading ? '加载中…' : '加载更多'} <ArrowRight size={15} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Stat({ Icon, label, value }: { Icon: any; label: string; value: number }) {
  return (
    <div className="flex items-center gap-2 rounded-xl border bg-surface px-3 py-2">
      <Icon size={16} className="text-accent" />
      <span className="font-bold text-fg">{value}</span>
      <span className="text-muted">{label}</span>
    </div>
  )
}
