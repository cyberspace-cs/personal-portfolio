import { useEffect, useState } from 'react'
import { ArrowLeft, ExternalLink, Eye, Calendar, Star } from 'lucide-react'
import { api } from '../lib/api'
import { ensureSession, getSessionId } from '../lib/session'
import type { Item } from '../lib/types'
import { categoryIcon } from '../lib/icons'
import { sourceMeta } from '../lib/source'
import { Markdown } from '../components/Markdown'
import { FavButton } from '../components/FavButton'

export function Detail({ slug }: { slug: string }) {
  const [item, setItem] = useState<Item | null>(null)
  const [related, setRelated] = useState<Item[]>([])
  const [loading, setLoading] = useState(true)
  const [fav, setFav] = useState(false)
  const sessionId = getSessionId()

  useEffect(() => {
    setLoading(true)
    setItem(null)
    ensureSession()
      .then((sid) => api.getItem(slug, sid))
      .then((it) => {
        setItem(it)
        setFav(it.is_favorited)
        if (it.category_slug) {
          api
            .listItems({ category: it.category_slug, page_size: 5, session_id: getSessionId() })
            .then((r) => setRelated(r.items.filter((x) => x.id !== it.id).slice(0, 4)))
        }
      })
      .finally(() => setLoading(false))
  }, [slug])

  if (loading) {
    return <div className="mx-auto max-w-4xl px-4 py-16 text-center text-muted">加载中…</div>
  }
  if (!item) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 text-center">
        <p className="text-muted">未找到该条目。</p>
        <a href="#/" className="btn-primary mt-4 inline-flex">
          返回首页
        </a>
      </div>
    )
  }

  const Icon = categoryIcon(item.category_slug)
  const sm = sourceMeta(item.source_type)

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 fade-in">
      <a href="#/" className="mb-6 inline-flex items-center gap-1.5 text-sm text-muted hover:text-accent">
        <ArrowLeft size={15} /> 返回列表
      </a>

      <div className="card">
        <div className="flex flex-wrap items-center gap-2">
          <span className="badge border-accent/30 bg-accent/10 text-accent">
            <Icon size={13} /> {item.category_name || '未分类'}
          </span>
          <span className={`badge ${sm.cls}`}>
            <sm.Icon size={13} /> {sm.label}
          </span>
          {item.status === 'trending' && (
            <span className="badge border-emerald-400/30 bg-emerald-400/10 text-emerald-400">趋势</span>
          )}
        </div>

        <h1 className="mt-4 text-2xl font-extrabold sm:text-3xl">{item.title}</h1>
        <p className="mt-2 text-muted">{item.summary}</p>

        <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-muted">
          {item.author_org && <span>机构：{item.author_org}</span>}
          {item.language && <span className="rounded bg-surface-2 px-2 py-0.5 font-mono">{item.language}</span>}
          {item.github_stars != null && (
            <span className="flex items-center gap-1 font-mono">
              <Star size={14} className="text-amber-400" /> {item.github_stars.toLocaleString()}
            </span>
          )}
          <span className="flex items-center gap-1">
            <Eye size={14} /> {item.views}
          </span>
          <span className="flex items-center gap-1">
            <Calendar size={14} /> {item.created_at?.slice(0, 10)}
          </span>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-3 border-t pt-4">
          {item.source_url && (
            <a href={item.source_url} target="_blank" rel="noreferrer" className="btn-primary">
              访问原始资源 <ExternalLink size={15} />
            </a>
          )}
          <FavButton itemId={item.id} active={fav} onChanged={setFav} />
          {fav && <span className="text-sm text-rose-400">已收藏</span>}
        </div>
      </div>

      {item.tags.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {item.tags.map((t) => (
            <a
              key={t}
              href={`#/?q=${encodeURIComponent(t)}`}
              className="badge border bg-surface text-muted hover:text-accent"
            >
              #{t}
            </a>
          ))}
        </div>
      )}

      <div className="card mt-4">
        <Markdown source={item.content} />
      </div>

      {related.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-bold">同分类推荐</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {related.map((r) => (
              <a key={r.id} href={`#/item/${r.slug}`} className="card card-hover">
                <p className="font-semibold text-fg">{r.title}</p>
                <p className="mt-1 line-clamp-2 text-sm text-muted">{r.summary}</p>
              </a>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
