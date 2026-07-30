import { categoryIcon } from '../lib/icons'
import type { Category } from '../lib/types'
import { sourceMeta } from '../lib/source'

const SOURCE_TYPES = ['repo', 'paper', 'blog', 'tool', 'conference', 'framework', 'product', 'course']

export function Sidebar({
  categories,
  activeCategory,
  onSelectCategory,
  sourceType,
  onSelectSource,
}: {
  categories: Category[]
  activeCategory: string
  onSelectCategory: (slug: string) => void
  sourceType: string
  onSelectSource: (t: string) => void
}) {
  return (
    <aside className="flex flex-col gap-6">
      <div className="card">
        <h2 className="mb-3 text-sm font-bold text-fg">前沿分类</h2>
        <ul className="space-y-1">
          <li>
            <button
              onClick={() => onSelectCategory('')}
              className={`flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-sm transition-colors ${
                activeCategory === '' ? 'bg-accent/15 text-accent' : 'text-muted hover:bg-surface-2 hover:text-fg'
              }`}
            >
              <span className="flex items-center gap-2">🌐 全部方向</span>
            </button>
          </li>
          {categories.map((c) => {
            const Icon = categoryIcon(c.slug)
            const active = activeCategory === c.slug
            return (
              <li key={c.id}>
                <button
                  onClick={() => onSelectCategory(c.slug)}
                  className={`flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-sm transition-colors ${
                    active ? 'bg-accent/15 text-accent' : 'text-muted hover:bg-surface-2 hover:text-fg'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <Icon size={15} /> {c.name}
                  </span>
                  <span className="rounded-full bg-surface-2 px-2 text-xs text-muted">{c.count}</span>
                </button>
              </li>
            )
          })}
        </ul>
      </div>

      <div className="card">
        <h2 className="mb-3 text-sm font-bold text-fg">类型筛选</h2>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onSelectSource('')}
            className={`chip ${sourceType === '' ? 'chip-active' : ''}`}
          >
            全部
          </button>
          {SOURCE_TYPES.map((t) => {
            const sm = sourceMeta(t)
            return (
              <button
                key={t}
                onClick={() => onSelectSource(t)}
                className={`chip ${sourceType === t ? 'chip-active' : ''}`}
              >
                <sm.Icon size={13} /> {sm.label}
              </button>
            )
          })}
        </div>
      </div>
    </aside>
  )
}
