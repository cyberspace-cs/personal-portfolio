import { useState } from 'react'
import { Eye, ExternalLink } from 'lucide-react'
import type { Item } from '../lib/types'
import { categoryIcon } from '../lib/icons'
import { sourceMeta, StarCount } from '../lib/source'
import { FavButton } from './FavButton'

export function ItemCard({ item }: { item: Item }) {
  const [fav, setFav] = useState(item.is_favorited)
  const Icon = categoryIcon(item.category_slug)
  const sm = sourceMeta(item.source_type)

  return (
    <a href={`#/item/${item.slug}`} className="card card-hover group flex flex-col gap-3 fade-in">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 text-xs">
          <span className="badge border-accent/30 bg-accent/10 text-accent">
            <Icon size={13} /> {item.category_name || '未分类'}
          </span>
          <span className={`badge ${sm.cls}`}>
            <sm.Icon size={13} /> {sm.label}
          </span>
        </div>
        <FavButton itemId={item.id} active={fav} onChanged={setFav} />
      </div>

      <div>
        <h3 className="flex items-center gap-1.5 font-bold leading-snug text-fg">
          {item.title}
          {item.featured && (
            <span className="rounded bg-amber-400/15 px-1.5 text-[10px] font-semibold text-amber-400">
              精选
            </span>
          )}
        </h3>
        <p className="mt-1 line-clamp-2 text-sm text-muted">{item.summary}</p>
      </div>

      {item.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {item.tags.slice(0, 4).map((t) => (
            <span key={t} className="rounded-md bg-surface-2 px-2 py-0.5 text-[11px] text-muted">
              #{t}
            </span>
          ))}
        </div>
      )}

      <div className="mt-auto flex items-center justify-between border-t pt-3 text-xs text-muted">
        <div className="flex items-center gap-3">
          {item.author_org && <span>{item.author_org}</span>}
          {item.language && <span className="rounded bg-surface-2 px-1.5 py-0.5 font-mono">{item.language}</span>}
          <StarCount stars={item.github_stars} />
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <Eye size={13} /> {item.views}
          </span>
          {item.source_url && (
            <span className="flex items-center gap-0.5 text-accent">
              <ExternalLink size={13} />
            </span>
          )}
        </div>
      </div>
    </a>
  )
}
