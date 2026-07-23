import { Github } from 'lucide-react'
import { ThemeToggle } from './ThemeToggle'

function NavLink({ href, label, active }: { href: string; label: string; active: boolean }) {
  return (
    <a
      href={href}
      className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
        active ? 'bg-surface-2 text-accent' : 'text-muted hover:text-fg'
      }`}
    >
      {label}
    </a>
  )
}

export function Navbar({ route }: { route: string }) {
  return (
    <header className="sticky top-0 z-30 glass border-b">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4">
        <a href="#/" className="flex items-center gap-2 font-extrabold tracking-tight">
          <img src="/favicon.svg" alt="" className="h-7 w-7" />
          <span>
            CS<span className="neon">前沿</span>
          </span>
        </a>
        <nav className="ml-2 hidden items-center gap-1 sm:flex">
          <NavLink href="#/" label="首页" active={route === ''} />
          <NavLink href="#/favorites" label="收藏" active={route === 'favorites'} />
          <NavLink href="#/admin" label="管理" active={route === 'admin'} />
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <a
            href="https://github.com/lvy010/lvynote"
            target="_blank"
            rel="noreferrer"
            className="btn-ghost hidden h-9 w-9 !px-0 sm:inline-flex"
            title="参考前沿笔记 lvynote"
          >
            <Github size={17} />
          </a>
          <ThemeToggle />
        </div>
      </div>
      {/* 移动端导航 */}
      <nav className="flex items-center gap-1 px-4 pb-2 sm:hidden">
        <NavLink href="#/" label="首页" active={route === ''} />
        <NavLink href="#/favorites" label="收藏" active={route === 'favorites'} />
        <NavLink href="#/admin" label="管理" active={route === 'admin'} />
      </nav>
    </header>
  )
}
