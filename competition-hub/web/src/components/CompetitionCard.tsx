import { Link } from 'react-router-dom'
import { Heart, MapPin, Trophy, CalendarDays, Eye, Radio, ExternalLink } from 'lucide-react'
import type { Competition } from '../lib/types'
import { STATUS_META, MODE_META, fmtDate, coverGradient } from '../lib/format'

export function StatusBadge({ status }: { status: string }) {
  const meta = STATUS_META[status] ?? STATUS_META.ended
  return (
    <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${meta.cls}`}>
      {meta.label}
    </span>
  )
}

export function FavoriteHeart({
  active,
  onClick,
  size = 18,
}: {
  active: boolean
  onClick?: (e: React.MouseEvent) => void
  size?: number
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={active ? '取消收藏' : '收藏'}
      className={`grid place-items-center rounded-full border p-2 transition ${
        active
          ? 'border-neon-pink/50 bg-neon-pink/15 text-neon-pink'
          : 'border-white/10 bg-white/5 text-slate-300 hover:text-neon-pink'
      }`}
    >
      <Heart size={size} fill={active ? 'currentColor' : 'none'} />
    </button>
  )
}

export function CompetitionCard({
  c,
  index,
  onToggleFavorite,
  favLoading,
}: {
  c: Competition
  index?: number
  onToggleFavorite?: (c: Competition) => void
  favLoading?: boolean
}) {
  const gradient = c.cover || coverGradient(c.title)
  const isLive = /实时|heikesong|Biendata|赛氪/.test(c.source || '')
  return (
    <div
      className="group glass relative flex flex-col overflow-hidden transition duration-300 hover:-translate-y-1 hover:border-neon-blue/50 hover:shadow-glow-blue card-enter"
      style={{ ['--i' as any]: index ?? 0 }}
    >
      <div className="tech-line h-0.5 w-full opacity-40 transition group-hover:opacity-100" />
      <Link to={`/competition/${c.id}`} className="block">
        <div className="relative h-32 w-full overflow-hidden" style={{ background: gradient }}>
          <div className="absolute inset-0 cyber-grid opacity-40" />
          <div className="absolute inset-0 bg-gradient-to-t from-ink-950/40 to-transparent" />
          <div className="absolute left-3 top-3 flex items-center gap-2">
            <span className="rounded-md bg-black/40 px-2 py-1 text-xs font-medium text-white backdrop-blur">
              {c.category_name || '综合'}
            </span>
          </div>
          <div className="absolute right-3 top-3">
            <StatusBadge status={c.status} />
          </div>
          {c.source && c.source_url && (
            <a
              href={c.source_url}
              target="_blank"
              rel="noreferrer"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
              }}
              className="absolute bottom-3 left-3 inline-flex items-center gap-1 rounded bg-black/45 px-2 py-0.5 text-[10px] font-medium text-neon-cyan backdrop-blur transition hover:bg-black/65"
            >
              <Radio size={10} /> 聚合自 {c.source}
              {isLive && (
                <span className="ml-1 inline-flex items-center gap-0.5 text-neon-green">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-neon-green" />
                  实时
                </span>
              )}
            </a>
          )}
          {c.featured && (
            <span className="absolute bottom-3 right-3 rounded bg-neon-blue/80 px-2 py-0.5 text-[11px] font-semibold text-white">
              精选
            </span>
          )}
        </div>
      </Link>

      <div className="flex flex-1 flex-col p-4">
        <Link to={`/competition/${c.id}`} className="block">
          <h3 className="line-clamp-2 min-h-[2.5rem] text-[15px] font-semibold leading-snug text-white transition group-hover:text-neon-cyan">
            {c.title}
          </h3>
        </Link>
        <p className="mt-1.5 line-clamp-2 text-xs text-slate-300">{c.summary || '—'}</p>

        {c.tags?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {c.tags.slice(0, 3).map((t) => (
              <span key={t} className="tag-chip">
                {t}
              </span>
            ))}
          </div>
        )}

        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-400">
          <span className="inline-flex items-center gap-1">
            <MapPin size={12} /> {c.location || '待定'}
          </span>
          <span className="inline-flex items-center gap-1">
            <CalendarDays size={12} /> {fmtDate(c.start_date)}
          </span>
          <span className="inline-flex items-center gap-1 text-slate-500">
            <Eye size={12} /> {c.views || 0}
          </span>
        </div>

        <div className="mt-3 flex items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1 rounded-lg bg-neon-amber/10 px-2 py-1 text-xs font-semibold text-neon-amber">
            <Trophy size={13} /> {c.prize || '荣誉证书'}
          </span>
          <span className="text-[11px] text-slate-500">{MODE_META[c.mode]?.label ?? c.mode}</span>
        </div>

        <div className="mt-3 flex items-center justify-between gap-2 border-t border-white/5 pt-3">
          <div className="flex min-w-0 items-center gap-2">
            {c.source_url && (
              <a
                href={c.source_url}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                }}
                className="inline-flex shrink-0 items-center gap-1 rounded text-[11px] font-medium text-neon-cyan transition hover:underline"
              >
                <ExternalLink size={12} /> 官网
              </a>
            )}
            <span className="truncate text-[11px] text-slate-500">主办方：{c.organizer || '—'}</span>
          </div>
          {onToggleFavorite && (
            <FavoriteHeart
              active={c.is_favorited}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                !favLoading && onToggleFavorite(c)
              }}
            />
          )}
        </div>
      </div>
    </div>
  )
}
