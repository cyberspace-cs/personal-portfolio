import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Heart, Lock } from 'lucide-react'
import { api } from '../lib/api'
import type { Competition } from '../lib/types'
import { CompetitionCard } from '../components/CompetitionCard'
import { useAuth } from '../lib/auth'
import { useUI } from '../lib/ui'
import { Loader2 } from 'lucide-react'

export function FavoritesPage() {
  const { user } = useAuth()
  const { openLogin, toast } = useUI()
  const [items, setItems] = useState<Competition[]>([])
  const [loading, setLoading] = useState(true)
  const [favLoading, setFavLoading] = useState(false)

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }
    api
      .getFavorites()
      .then(setItems)
      .catch((e) => toast(e?.message || '加载失败', 'err'))
      .finally(() => setLoading(false))
  }, [user])

  async function toggle(c: Competition) {
    setFavLoading(true)
    try {
      if (c.is_favorited) await api.removeFavorite(c.id)
      else await api.addFavorite(c.id)
      setItems((arr) => arr.filter((x) => x.id !== c.id))
    } catch (e: any) {
      toast(e?.message || '操作失败', 'err')
    } finally {
      setFavLoading(false)
    }
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-md px-4 py-24 text-center">
        <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-white/5 text-neon-pink">
          <Lock size={24} />
        </div>
        <h1 className="text-xl font-semibold text-white">登录后查看收藏</h1>
        <p className="mt-2 text-sm text-slate-400">收藏你感兴趣的竞赛，随时回来查看，不再错过报名。</p>
        <button className="btn-primary mt-5" onClick={openLogin}>
          登录 / 注册
        </button>
        <Link to="/" className="btn-ghost mt-3 w-full">
          返回首页
        </Link>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-6 flex items-center gap-2">
        <Heart size={20} className="text-neon-pink" />
        <h1 className="text-xl font-bold text-white">我的收藏</h1>
        <span className="text-sm text-slate-500">({items.length})</span>
      </div>

      {loading ? (
        <div className="grid place-items-center py-24 text-neon-cyan">
          <Loader2 className="animate-spin" />
        </div>
      ) : items.length === 0 ? (
        <div className="grid place-items-center py-24 text-center text-slate-500">
          <Heart size={40} className="mb-3 opacity-60" />
          <p>还没有收藏任何竞赛。</p>
          <Link to="/" className="btn-ghost mt-4">
            去发现竞赛
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((c) => (
            <CompetitionCard key={c.id} c={c} onToggleFavorite={toggle} favLoading={favLoading} />
          ))}
        </div>
      )}
    </div>
  )
}
