import { Link } from 'react-router-dom'
import { Radar } from 'lucide-react'

export function NotFound() {
  return (
    <div className="mx-auto grid max-w-md place-items-center px-4 py-28 text-center">
      <span className="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-neon-cyan to-neon-blue text-ink-950">
        <Radar size={24} />
      </span>
      <h1 className="mt-4 text-3xl font-bold text-white">404</h1>
      <p className="mt-2 text-sm text-slate-400">页面走丢了，去竞赛列表看看吧。</p>
      <Link to="/" className="btn-primary mt-5">
        返回首页
      </Link>
    </div>
  )
}
