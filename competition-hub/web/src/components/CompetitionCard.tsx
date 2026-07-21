import { Link } from 'react-router-dom'
import { Heart, MapPin, Trophy, CalendarDays, ExternalLink } from 'lucide-react'
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
  onToggleFavorite,
  favLoading,
}: {
  c: Competition
  onToggleFavorite?: (c: Competition) => void
  favLoading?: boolean
}) {
  const gradient = c.cover || coverGradient(c.title)
  return (
    <div className="group glass relative flex flex-col overflow-hidden transition duration-300 hover:-translate-y-1 hover:border-neon-cyan/40 hover:shadow-glow">
      <Link to={`/competition/${c.id}`} className="block">
        <div className="relative h-32 w-full overflow-hidden" style={{ background: gradient }}>
          <div className="absolute inset-0 cyber-grid opacity-40" />
          <div className="absolute left-3 top-3 flex items-center gap-2">
            <span className="rounded-md bg-black/40 px-2 py-1 text-xs font-medium text-white backdrop-blur">
              {c.category_name || '综合'}
            </span>
          </div>
          <div className="absolute right-3 top-3">
            <StatusBadge status={c.status} />
          </div>
          {c.featured && (
            <span className="absolute bottom-3 left-3 rounded bg-neon-violet/80 px-2 py-0.5 text-[11px] font-semibold text-white">
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
        <p className="mt-1.5 line-clamp-2 text-xs text-slate-400">{c.summary || '—'}</p>

        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-400">
          <span className="inline-flex items-center gap-1">
            <MapPin size={12} /> {c.location || '待定'}
          </span>
          <span className="inline-flex items-center gap-1">
            <CalendarDays size={12} /> {fmtDate(c.start_date)}
          </span>
        </div>

        <div className="mt-3 flex items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1 rounded-lg bg-neon-amber/10 px-2 py-1 text-xs font-semibold text-neon-amber">
            <Trophy size={13} /> {c.prize || '荣誉证书'}
          </span>
          <span className="text-[11px] text-slate-500">{MODE_META[c.mode]?.label ?? c.mode}</span>
        </div>

        <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-3">
          <span className="truncate text-[11px] text-slate-500">主办方：{c.organizer || '—'}</span>
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
