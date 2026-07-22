import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, ExternalLink, Eye, MapPin, CalendarDays, Trophy, Building2, Tag, Clock } from 'lucide-react'
import { api } from '../lib/api'
import type { Category, Competition } from '../lib/types'
import { StatusBadge, CompetitionCard, FavoriteHeart } from '../components/CompetitionCard'
import { MODE_META, fmtDate } from '../lib/format'
import { useAuth } from '../lib/auth'
import { useUI } from '../lib/ui'
import { Loader2 } from 'lucide-react'

export function CompetitionDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const { openLogin, toast } = useUI()
  const [c, setC] = useState<Competition | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [related, setRelated] = useState<Competition[]>([])
  const [loading, setLoading] = useState(true)
  const [favLoading, setFavLoading] = useState(false)

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [id])

  useEffect(() => {
    let active = true
    setLoading(true)
    Promise.all([api.getCompetition(Number(id)), api.getCategories()])
      .then(async ([comp, cats]) => {
        if (!active) return
        setC(comp)
        setCategories(cats)
        const cat = cats.find((x) => x.id === comp.category_id)
        if (cat) {
          const rel = await api.listCompetitions({ category: cat.slug, page_size: 4 })
          if (active) setRelated(rel.items.filter((x) => x.id !== comp.id).slice(0, 3))
        }
      })
      .catch(() => active && setC(null))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [id])

  async function toggleFavorite() {
    if (!c) return
    if (!user) {
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
      setC({ ...c, is_favorited: !c.is_favorited })
    } catch (e: any) {
      toast(e?.message || '操作失败', 'err')
    } finally {
      setFavLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="grid place-items-center py-32 text-neon-cyan">
        <Loader2 className="animate-spin" size={28} />
      </div>
    )
  }
  if (!c) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-24 text-center">
        <p className="text-slate-400">竞赛不存在或已下架。</p>
        <Link to="/" className="btn-ghost mt-4">
          <ArrowLeft size={15} /> 返回列表
        </Link>
      </div>
    )
  }

  const meta = [
    { icon: Building2, label: '主办方', value: c.organizer || '—' },
    { icon: MapPin, label: '地点', value: c.location || '待定' },
    { icon: Tag, label: '形式', value: MODE_META[c.mode]?.label ?? c.mode },
    { icon: Trophy, label: '奖金', value: c.prize || '荣誉证书' },
    { icon: CalendarDays, label: '开始时间', value: fmtDate(c.start_date) },
    { icon: CalendarDays, label: '结束时间', value: fmtDate(c.end_date) },
    { icon: Clock, label: '报名截止', value: fmtDate(c.reg_deadline) },
    { icon: Eye, label: '浏览量', value: String(c.views) },
  ]

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <Link to="/" className="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-neon-cyan">
        <ArrowLeft size={15} /> 返回竞赛列表
      </Link>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div>
          <div className="relative mb-5 h-44 w-full overflow-hidden rounded-2xl" style={{ background: c.cover || 'linear-gradient(135deg,#1d4ed8,#38bdf8)' }}>
            <div className="absolute inset-0 cyber-grid opacity-30" />
            <div className="absolute left-4 top-4 flex items-center gap-2">
              <span className="rounded-md bg-black/40 px-2 py-1 text-xs font-medium text-white backdrop-blur">
                {c.category_name || '综合'}
              </span>
              <StatusBadge status={c.status} />
            </div>
            {c.featured && (
              <span className="absolute bottom-4 left-4 rounded bg-neon-violet/80 px-2 py-0.5 text-[11px] font-semibold text-white">
                精选推荐
              </span>
            )}
          </div>

          <h1 className="text-2xl font-bold leading-tight text-white">{c.title}</h1>
          <p className="mt-2 text-sm text-slate-400">{c.summary}</p>

          {c.tags.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {c.tags.map((t) => (
                <span key={t} className="chip !py-1 text-[11px]">
                  #{t}
                </span>
              ))}
            </div>
          )}

          <div className="glass mt-6 p-5">
            <h2 className="mb-3 text-sm font-semibold text-white">竞赛详情</h2>
            <div className="space-y-3 text-sm leading-relaxed text-slate-300">
              {c.description
                ? c.description.split('\n').filter(Boolean).map((p, i) => <p key={i}>{p}</p>)
                : <p className="text-slate-500">暂无详细介绍。</p>}
            </div>
          </div>

          {related.length > 0 && (
            <div className="mt-8">
              <h2 className="mb-3 text-sm font-semibold text-white">同类推荐</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {related.map((r) => (
                  <CompetitionCard key={r.id} c={r} />
                ))}
              </div>
            </div>
          )}
        </div>

        <aside className="space-y-4">
          <div className="glass-strong sticky top-20 p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">操作</span>
              <FavoriteHeart active={c.is_favorited} onClick={toggleFavorite} size={20} />
            </div>
            {c.source_url && (
              <a href={c.source_url} target="_blank" rel="noreferrer" className="btn-primary mt-3 w-full">
                <ExternalLink size={16} /> 前往官网 / 报名
              </a>
            )}
            <button className="btn-ghost mt-2 w-full" onClick={toggleFavorite} disabled={favLoading}>
              {c.is_favorited ? '取消收藏' : '收藏竞赛'}
            </button>
          </div>

          <div className="glass p-5">
            <h2 className="mb-3 text-sm font-semibold text-white">关键信息</h2>
            <dl className="space-y-3 text-sm">
              {meta.map((m) => (
                <div key={m.label} className="flex items-start gap-2.5">
                  <m.icon size={16} className="mt-0.5 text-neon-cyan" />
                  <div>
                    <dt className="text-[11px] text-slate-500">{m.label}</dt>
                    <dd className="text-slate-200">{m.value}</dd>
                  </div>
                </div>
              ))}
            </dl>
          </div>
        </aside>
      </div>
    </div>
  )
}
