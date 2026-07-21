import type { Category } from '../lib/types'

const STATUS_OPTS = [
  { v: '', label: '全部状态' },
  { v: 'upcoming', label: '即将开始' },
  { v: 'ongoing', label: '进行中' },
  { v: 'ended', label: '已结束' },
]
const MODE_OPTS = [
  { v: '', label: '全部形式' },
  { v: 'online', label: '线上' },
  { v: 'offline', label: '线下' },
  { v: 'hybrid', label: '线上+线下' },
]
const SORT_OPTS = [
  { v: 'latest', label: '最新发布' },
  { v: 'prize', label: '奖金最高' },
  { v: 'deadline', label: '即将截止' },
  { v: 'views', label: '最热门' },
]

export function FilterBar({
  categories,
  activeCategory,
  onCategory,
  status,
  onStatus,
  mode,
  onMode,
  sort,
  onSort,
}: {
  categories: Category[]
  activeCategory: string
  onCategory: (slug: string) => void
  status: string
  onStatus: (v: string) => void
  mode: string
  onMode: (v: string) => void
  sort: string
  onSort: (v: string) => void
}) {
  return (
    <div className="glass mb-6 p-4">
      <div className="flex flex-wrap gap-2">
        <button className={`chip ${activeCategory === '' ? 'chip-active' : ''}`} onClick={() => onCategory('')}>
          全部
        </button>
        {categories.map((c) => (
          <button
            key={c.slug}
            className={`chip ${activeCategory === c.slug ? 'chip-active' : ''}`}
            onClick={() => onCategory(c.slug)}
          >
            <span>{c.icon}</span>
            {c.name}
            <span className="ml-1 text-[10px] text-slate-500">{c.count}</span>
          </button>
        ))}
      </div>

      <div className="mt-3 flex flex-col gap-3 border-t border-white/5 pt-3 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500">状态</span>
          {STATUS_OPTS.map((o) => (
            <button
              key={o.v}
              onClick={() => onStatus(o.v)}
              className={`chip !px-2.5 !py-1 text-[11px] ${status === o.v ? 'chip-active' : ''}`}
            >
              {o.label}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500">形式</span>
          {MODE_OPTS.map((o) => (
            <button
              key={o.v}
              onClick={() => onMode(o.v)}
              className={`chip !px-2.5 !py-1 text-[11px] ${mode === o.v ? 'chip-active' : ''}`}
            >
              {o.label}
            </button>
          ))}
          <select
            className="input !w-auto !py-1.5 text-[11px]"
            value={sort}
            onChange={(e) => onSort(e.target.value)}
          >
            {SORT_OPTS.map((o) => (
              <option key={o.v} value={o.v}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}
