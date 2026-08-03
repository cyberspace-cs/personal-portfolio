import { Shield } from 'lucide-react'
import { Link } from 'react-router-dom'

export function Navbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-bg-900/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3">
        <Link to="/" className="flex items-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand-primary/15 text-brand-primary">
            <Shield className="h-5 w-5" />
          </span>
          <div className="leading-tight">
            <div className="text-base font-semibold tracking-wide">AuditScope</div>
            <div className="text-[11px] text-slate-400">审查查 · 审计综合信息查询</div>
          </div>
        </Link>
        <nav className="ml-6 hidden gap-1 text-sm text-slate-300 md:flex">
          <Link to="/" className="rounded-lg px-3 py-1.5 hover:bg-bg-700/60 cursor-pointer">首页</Link>
          <span className="rounded-lg px-3 py-1.5 text-slate-500">查公司</span>
          <span className="rounded-lg px-3 py-1.5 text-slate-500">查老板</span>
          <span className="rounded-lg px-3 py-1.5 text-slate-500">查人员</span>
          <span className="rounded-lg px-3 py-1.5 text-slate-500">查流水</span>
          <span className="rounded-lg px-3 py-1.5 text-slate-500">查社保</span>
        </nav>
        <div className="ml-auto flex items-center gap-2 text-xs text-slate-400">
          <span className="hidden rounded-full border border-line px-2.5 py-1 sm:inline">Deepseek · Qwen 驱动</span>
        </div>
      </div>
    </header>
  )
}
