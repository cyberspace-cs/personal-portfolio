import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { Category, Competition, CompetitionListResp, Stats } from '../lib/types'
import { Hero } from '../components/Hero'
import { FilterBar } from '../components/FilterBar'
import { CompetitionCard } from '../components/CompetitionCard'
import { Pagination } from '../components/Pagination'
import { useAuth } from '../lib/auth'
import { useUI } from '../lib/ui'
import { Loader2, SearchX } from 'lucide-react'

const PAGE_SIZE = 9

export function HomePage() {
  const { user, token } = useAuth()
  const { openLogin, toast } = useUI()
  const [categories, setCategories] = useState<Category[]>([])
  const [stats, setStats] = useState<Stats>()
  const [data, setData] = useState<CompetitionListResp>({
    items: [],
    total: 0,
    page: 1,
    page_size: PAGE_SIZE,
    total_pages: 1,
  })
  const [loading, setLoading] = useState(true)

  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const [status, setStatus] = useState('')
  const [mode, setMode] = useState('')
  const [sort, setSort] = useState('latest')
  const [page, setPage] = useState(1)
  const [favLoading, setFavLoading] = useState(false)

  useEffect(() => {
    api.getCategories().then(setCategories).catch(() => {})
    api.getStats().then(setStats).catch(() => {})
  }, [])

  useEffect(() => {
    let active = true
    const t = setTimeout(() => {
      setLoading(true)
      api
        .listCompetitions({ q: query, category, status, mode, sort, page, page_size: PAGE_SIZE })
        .then((res) => active && setData(res))
        .catch(() => active && setData({ items: [], total: 0, page: 1, page_size: PAGE_SIZE, total_pages: 1 }))
        .finally(() => active && setLoading(false))
    }, query ? 300 : 0)
    return () => {
      active = false
      clearTimeout(t)
    }
  }, [query, category, status, mode, sort, page])

  async function toggleFavorite(c: Competition) {
    if (!user || !token) {
      openLogin()
      return
    }
    setFavLoading(true)
    try {
      if (c.is_favorited) {
        await api.removeFavorite(c.id)
        toast('已取消收藏', 'ok')
      } else {
        await api.addFavorite(c.id)
        toast('已加入收藏', 'ok')
      }
      setData((d) => ({
        ...d,
        items: d.items.map((x) => (x.id === c.id ? { ...x, is_favorited: !x.is_favorited } : x)),
      }))
    } catch (e: any) {
      toast(e?.message || '操作失败', 'err')
    } finally {
      setFavLoading(false)
    }
  }

  function resetPage<T>(setter: (v: T) => void) {
    return (v: T) => {
      setter(v)
      setPage(1)
    }
  }

  return (
    <div>
      <Hero query={query} onQuery={setQuery} onSearch={() => setPage(1)} stats={stats} />

      <div className="mx-auto max-w-6xl px-4 py-8">
        <FilterBar
          categories={categories}
          activeCategory={category}
          onCategory={resetPage(setCategory)}
          status={status}
          onStatus={resetPage(setStatus)}
          mode={mode}
          onMode={resetPage(setMode)}
          sort={sort}
          onSort={setSort}
        />

        <div className="mb-4 flex items-center justify-between text-sm text-slate-400">
          <span>
            共 <span className="font-semibold text-neon-cyan">{data.total}</span> 场竞赛
          </span>
          {(query || category || status || mode) && (
            <button
              className="text-xs text-slate-500 hover:text-neon-cyan"
              onClick={() => {
                setQuery('')
                setCategory('')
                setStatus('')
                setMode('')
                setPage(1)
              }}
            >
              清除筛选
            </button>
          )}
        </div>

        {loading ? (
          <div className="grid place-items-center py-24 text-neon-cyan">
            <Loader2 className="animate-spin" />
          </div>
        ) : data.items.length === 0 ? (
          <div className="grid place-items-center py-24 text-center text-slate-500">
            <SearchX size={40} className="mb-3 opacity-60" />
            <p>没有匹配的竞赛，换个关键词或筛选条件试试。</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((c) => (
              <CompetitionCard key={c.id} c={c} onToggleFavorite={toggleFavorite} favLoading={favLoading} />
            ))}
          </div>
        )}

        <Pagination page={data.page} totalPages={data.total_pages} onChange={setPage} />
      </div>
    </div>
  )
}
