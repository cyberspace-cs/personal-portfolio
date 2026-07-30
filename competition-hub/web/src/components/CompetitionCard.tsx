import { Link } from 'react-router-dom'
import { Heart, MapPin, Trophy, CalendarDays, Eye, Radio } from 'lucide-react'
import type { Competition } from '../lib/types'
import { STATUS_META, MODE_META, fmtDate, sourceTagClass } from '../lib/format'

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
  const isLive = /实时|heikesong|Biendata|赛氪/.test(c.source || '')
  return (
    <div
      className="group glass relative flex flex-col overflow-hidden transition duration-300 hover:-translate-y-1 hover:border-neon-blue/50 hover:shadow-glow-blue card-enter"
      style={{ ['--i' as any]: index ?? 0 }}
    >
      <div className="tech-line h-0.5 w-full opacity-40 transition group-hover:opacity-100" />
      {/* 左侧蓝色光带（未来科技感） */}
      <span className="pointer-events-none absolute left-0 top-0 h-full w-1 bg-gradient-to-b from-neon-blue/70 via-neon-azure/50 to-transparent opacity-60 transition group-hover:opacity-100" />
      <div className="flex flex-1 flex-col p-4 pl-5">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-[11px] font-medium text-slate-300">
              {c.category_name || '综合'}
            </span>
            <StatusBadge status={c.status} />
          </div>
          {c.featured && (
            <span className="rounded bg-neon-blue/80 px-2 py-0.5 text-[11px] font-semibold text-white">
              精选
            </span>
          )}
        </div>

        <Link to={`/competition/${c.id}`} className="mt-2 block">
          <h3 className="line-clamp-2 min-h-[2.5rem] gradient-text text-[15px] font-bold leading-snug transition group-hover:brightness-125">
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
          {c.source ? (
            <div className="inline-flex min-w-0 items-center gap-1.5 text-[11px] text-slate-500">
              <Radio size={10} className="shrink-0" />
              <span className="shrink-0">聚合自</span>
              <span
                className={`shrink-0 rounded-md border px-1.5 py-0.5 font-semibold ${sourceTagClass(c.source)}`}
              >
                {c.source}
              </span>
              {isLive && (
                <span className="inline-flex shrink-0 items-center gap-0.5 text-neon-green">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-neon-green" />
                  实时
                </span>
              )}
            </div>
          ) : (
            <span />
          )}
          <div className="flex shrink-0 items-center gap-2">
            <span className="hidden text-[11px] text-slate-500 sm:inline">主办方：{c.organizer || '—'}</span>
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
    </div>
  )
}
