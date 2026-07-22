import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Radar, Compass, Heart, PlusCircle, LogOut, User as UserIcon, RefreshCw, Loader2 } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { useUI } from '../lib/ui'
import { api } from '../lib/api'

export function Navbar() {
  const { user, logout } = useAuth()
  const { openLogin, toast } = useUI()
  const navigate = useNavigate()
  const [collecting, setCollecting] = useState(false)

  async function handleCollect() {
    if (collecting) return
    setCollecting(true)
    try {
      const r = await api.collect()
      toast(`聚合完成：新增 ${r.created} · 更新 ${r.updated} · 共 ${r.total} 条`, 'ok')
    } catch (e: any) {
      toast(e?.message || '聚合失败', 'err')
    } finally {
      setCollecting(false)
    }
  }

  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-ink-950/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-4 px-4">
        <Link to="/" className="flex items-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-neon-cyan to-neon-blue text-ink-950 shadow-glow">
            <Radar size={20} />
          </span>
          <span className="text-lg font-bold tracking-tight text-white neon-text">竞赛雷达</span>
        </Link>

        <nav className="ml-2 hidden items-center gap-1 text-sm text-slate-300 md:flex">
          <Link to="/" className="rounded-lg px-3 py-2 hover:bg-white/5 hover:text-white">
            全部竞赛
          </Link>
          <Link to="/favorites" className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 hover:bg-white/5 hover:text-white">
            <Heart size={15} /> 我的收藏
          </Link>
          <Link to="/submit" className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 hover:bg-white/5 hover:text-white">
            <PlusCircle size={15} /> 发布赛事
          </Link>
        </nav>

        <div className="ml-auto flex items-center gap-2">
          {user?.role === 'admin' && (
            <button
              className="btn-ghost inline-flex items-center gap-1.5"
              onClick={handleCollect}
              disabled={collecting}
              title="从已配置的数据源自动聚合最新赛事"
            >
              {collecting ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              {collecting ? '聚合中…' : '一键聚合'}
            </button>
          )}
          {user ? (
            <div className="flex items-center gap-2">
              <span className="hidden items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-slate-200 sm:inline-flex">
                <UserIcon size={14} /> {user.username}
              </span>
              <button
                className="btn-ghost"
                onClick={() => {
                  logout()
                  navigate('/')
                }}
                title="退出登录"
              >
                <LogOut size={15} />
              </button>
            </div>
          ) : (
            <button className="btn-primary" onClick={openLogin}>
              <Compass size={15} /> 登录 / 注册
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
