import { ChevronLeft, ChevronRight } from 'lucide-react'

export function Pagination({
  page,
  totalPages,
  onChange,
}: {
  page: number
  totalPages: number
  onChange: (p: number) => void
}) {
  if (totalPages <= 1) return null
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1).filter(
    (p) => p === 1 || p === totalPages || Math.abs(p - page) <= 1,
  )
  const items: (number | '...')[] = []
  pages.forEach((p, i) => {
    if (i > 0 && p - pages[i - 1] > 1) items.push('...')
    items.push(p)
  })

  return (
    <div className="mt-8 flex items-center justify-center gap-1.5">
      <button
        className="btn-ghost !px-2.5"
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
      >
        <ChevronLeft size={16} />
      </button>
      {items.map((it, idx) =>
        it === '...' ? (
          <span key={`e${idx}`} className="px-2 text-slate-500">
            …
          </span>
        ) : (
          <button
            key={it}
            onClick={() => onChange(it)}
            className={`h-9 w-9 rounded-lg text-sm transition ${
              it === page
                ? 'bg-neon-cyan/20 text-neon-cyan ring-1 ring-neon-cyan/50'
                : 'border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
            }`}
          >
            {it}
          </button>
        ),
      )}
      <button
        className="btn-ghost !px-2.5"
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
      >
        <ChevronRight size={16} />
      </button>
    </div>
  )
}
