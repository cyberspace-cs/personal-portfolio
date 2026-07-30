import { Radar, Github, Radar as RadarIcon } from 'lucide-react'

export function Footer() {
  return (
    <footer className="mt-16 border-t border-white/10 bg-ink-950/60">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex flex-col items-start justify-between gap-6 md:flex-row">
          <div>
            <div className="flex items-center gap-2">
              <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-neon-cyan to-neon-blue text-ink-950">
                <Radar size={16} />
              </span>
              <span className="font-bold text-white">竞赛雷达</span>
            </div>
            <p className="mt-2 max-w-sm text-xs leading-relaxed text-slate-500">
              聚合全球黑客松、Kaggle、算法、CTF、AI 大模型、创新创业等技术竞赛信息，
              帮助开发者与创作者不错过每一个舞台。
            </p>
          </div>
          <div className="grid grid-cols-2 gap-x-10 gap-y-2 text-sm text-slate-400">
            <a className="hover:text-neon-cyan" href="#">
              关于平台
            </a>
            <a className="hover:text-neon-cyan" href="#">
              提交赛事
            </a>
            <a className="hover:text-neon-cyan" href="#">
              API 文档
            </a>
            <a
              className="inline-flex items-center gap-1.5 hover:text-neon-cyan"
              href="https://github.com/cyberspace-cs/personal-portfolio"
              target="_blank"
              rel="noreferrer"
            >
              <Github size={14} /> 开源仓库
            </a>
          </div>
        </div>
        <div className="mt-6 border-t border-white/5 pt-4 text-center text-[11px] text-slate-600">
          © {new Date().getFullYear()} 竞赛雷达 · 个人作品集项目 · Built with FastAPI + React
        </div>
      </div>
    </footer>
  )
}
