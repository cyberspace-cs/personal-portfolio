import { Navbar } from '../components/Navbar'
import { GlobalSearch } from '../components/GlobalSearch'
import { KIND_META } from '../components/Kinds'
import { BarChart3, Network, FileSearch, Sparkles } from 'lucide-react'
import type { SearchHit } from '../mock/data'

const FEATURES = [
  { icon: BarChart3, title: '企业全景评分', desc: '工商、股权、诉讼、税务多维度风险评分' },
  { icon: Network, title: '人物关系图谱', desc: '老板—人员—公司任职与控股穿透' },
  { icon: FileSearch, title: '流水异常挖掘', desc: '公转私、关联方往来、无合同大额' },
  { icon: Sparkles, title: 'RAG 证据问答', desc: 'Deepseek+Qwen 基于检索证据智能作答' },
]

export function Home() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-5xl px-4">
        <section className="py-16 text-center md:py-24">
          <div className="mx-auto mb-5 inline-flex items-center gap-2 rounded-full border border-line bg-bg-800/60 px-3 py-1 text-xs text-slate-300">
            <Sparkles className="h-3.5 w-3.5 text-brand-accent" /> 审计 / 尽调 / 合规一站式查证
          </div>
          <h1 className="text-3xl font-semibold leading-tight md:text-5xl">
            审计综合信息查询
            <span className="bg-gradient-to-r from-brand-primary to-brand-accent bg-clip-text text-transparent"> 审查查</span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-slate-400">
            一个搜索框，查老板、查人员、查公司、查流水、查社保。融合 LLM 查询理解与向量检索，
            把分散的证据链收敛成可审计的结论。
          </p>
          <div className="mx-auto mt-9 max-w-3xl">
            <GlobalSearch />
          </div>
          <div className="mx-auto mt-6 grid max-w-3xl grid-cols-2 gap-2 sm:grid-cols-5">
            {(Object.keys(KIND_META) as SearchHit['kind'][]).map(k => {
              const m = KIND_META[k]
              const Icon = m.icon
              return (
                <div key={k} className="flex items-center gap-2 rounded-xl border border-line bg-bg-800/50 px-3 py-2.5">
                  <span className={`grid h-8 w-8 place-items-center rounded-lg ${m.tint}`}><Icon className="h-4 w-4" /></span>
                  <span className="text-sm text-slate-200">{m.label}</span>
                </div>
              )
            })}
          </div>
        </section>

        <section className="grid gap-4 pb-20 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map(f => {
            const Icon = f.icon
            return (
              <div key={f.title} className="rounded-xl border border-line bg-bg-800/60 p-5 transition-colors hover:border-brand-primary/40">
                <span className="grid h-10 w-10 place-items-center rounded-lg bg-brand-primary/10 text-brand-primary"><Icon className="h-5 w-5" /></span>
                <h3 className="mt-3 text-base font-medium text-slate-100">{f.title}</h3>
                <p className="mt-1 text-sm text-slate-400">{f.desc}</p>
              </div>
            )
          })}
        </section>
      </main>
    </div>
  )
}
