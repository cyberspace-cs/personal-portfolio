import { Heart } from 'lucide-react'
import { api } from '../lib/api'
import { ensureSession } from '../lib/session'

export function FavButton({
  itemId,
  active,
  onChanged,
}: {
  itemId: number
  active: boolean
  onChanged?: (next: boolean) => void
}) {
  const handle = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    try {
      const sid = await ensureSession()
      const r = await api.toggleFavorite(sid, itemId)
      onChanged?.(r.favorited)
    } catch (err) {
      alert('收藏失败：' + (err as Error).message)
    }
  }
  return (
    <button
      onClick={handle}
      aria-label="收藏"
      className={`btn-ghost h-8 w-8 !px-0 ${active ? 'text-rose-400 border-rose-400/40' : 'text-muted'}`}
    >
      <Heart size={16} className={active ? 'fill-rose-400' : ''} />
    </button>
  )
}
