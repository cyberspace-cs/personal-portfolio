import { useEffect, useState } from 'react'
import { Bookmark, Heart } from 'lucide-react'
import { api } from '../lib/api'
import { ensureSession } from '../lib/session'
import type { Item } from '../lib/types'
import { ItemCard } from '../components/ItemCard'

export function Favorites() {
  const [items, setItems] = useState<Item[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    ensureSession()
      .then((sid) => api.getFavorites(sid))
      .then(setItems)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="flex items-center gap-2 text-2xl font-extrabold">
        <Bookmark size={22} className="text-accent" /> 我的收藏
      </h1>
      <p className="mt-1 text-sm text-muted">收藏的前沿信息会保存在本机浏览器会话中。</p>

      <div className="mt-6">
        {loading ? (
          <div className="card py-16 text-center text-muted">加载中…</div>
        ) : items.length === 0 ? (
          <div className="card flex flex-col items-center gap-3 py-16 text-center text-muted">
            <Heart size={28} />
            <p>还没有收藏任何内容。点击卡片上的 ♥ 即可收藏。</p>
            <a href="#/" className="btn-primary mt-2">
              去发现前沿
            </a>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((i) => (
              <ItemCard key={i.id} item={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
