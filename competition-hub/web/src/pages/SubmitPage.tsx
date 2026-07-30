import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { PlusCircle, Lock, ArrowLeft } from 'lucide-react'
import { api } from '../lib/api'
import type { Category, Competition, CompetitionInput } from '../lib/types'
import { useAuth } from '../lib/auth'
import { useUI } from '../lib/ui'
import { Loader2 } from 'lucide-react'

function slugify(title: string, fallback: string) {
  const s = title
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return s || fallback
}

export function SubmitPage() {
  const { user } = useAuth()
  const { openLogin, toast } = useUI()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const editId = params.get('id')
  const isEdit = Boolean(editId)

  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(false)
  const [loaded, setLoaded] = useState(false)

  const [form, setForm] = useState({
    title: '',
    slug: '',
    summary: '',
    description: '',
    category_id: '' as number | '',
    organizer: '',
    location: '',
    mode: 'offline',
    prize: '',
    prize_amount: '',
    status: 'upcoming',
    start_date: '',
    end_date: '',
    reg_deadline: '',
    tags: '',
    source_url: '',
    featured: false,
  })

  useEffect(() => {
    window.scrollTo(0, 0)
    api.getCategories().then(setCategories).catch(() => {})
  }, [])

  useEffect(() => {
    if (!editId) {
      setLoaded(true)
      return
    }
    api
      .getCompetition(Number(editId))
      .then((c: Competition) => {
        setForm({
          title: c.title,
          slug: c.slug,
          summary: c.summary,
          description: c.description,
          category_id: c.category_id ?? '',
          organizer: c.organizer,
          location: c.location,
          mode: c.mode,
          prize: c.prize,
          prize_amount: String(c.prize_amount || ''),
          status: c.status,
          start_date: c.start_date || '',
          end_date: c.end_date || '',
          reg_deadline: c.reg_deadline || '',
          tags: c.tags.join(', '),
          source_url: c.source_url,
          featured: c.featured,
        })
      })
      .catch(() => toast('加载竞赛失败', 'err'))
      .finally(() => setLoaded(true))
  }, [editId])

  function set<K extends keyof typeof form>(k: K, v: (typeof form)[K]) {
    setForm((f) => ({ ...f, [k]: v }))
  }

  async function submit() {
    if (!form.title.trim()) return toast('请填写竞赛名称', 'err')
    const slug = form.slug.trim() || slugify(form.title, 'event-' + Date.now())
    const payload: CompetitionInput = {
      title: form.title.trim(),
      slug,
      summary: form.summary.trim(),
      description: form.description,
      category_id: form.category_id === '' ? null : Number(form.category_id),
      organizer: form.organizer.trim(),
      location: form.location.trim(),
      mode: form.mode as CompetitionInput['mode'],
      prize: form.prize.trim(),
      prize_amount: Number(form.prize_amount) || 0,
      status: form.status as CompetitionInput['status'],
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      reg_deadline: form.reg_deadline || null,
      tags: form.tags
        .split(/[,，]/)
        .map((t) => t.trim())
        .filter(Boolean),
      cover: '',
      source_url: form.source_url.trim(),
      featured: form.featured,
    }
    setLoading(true)
    try {
      const res = isEdit
        ? await api.updateCompetition(Number(editId), payload)
        : await api.createCompetition(payload)
      toast(isEdit ? '已更新竞赛' : '发布成功', 'ok')
      navigate(`/competition/${res.id}`)
    } catch (e: any) {
      toast(e?.message || '提交失败', 'err')
    } finally {
      setLoading(false)
    }
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-md px-4 py-24 text-center">
        <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-white/5 text-neon-cyan">
          <Lock size={24} />
        </div>
        <h1 className="text-xl font-semibold text-white">登录后可发布赛事</h1>
        <p className="mt-2 text-sm text-slate-400">把你知道的黑客松、比赛信息分享给更多开发者。</p>
        <button className="btn-primary mt-5" onClick={openLogin}>
          登录 / 注册
        </button>
        <Link to="/" className="btn-ghost mt-3 w-full">
          返回首页
        </Link>
      </div>
    )
  }

  if (!loaded) {
    return (
      <div className="grid place-items-center py-32 text-neon-cyan">
        <Loader2 className="animate-spin" size={28} />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <Link to="/" className="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-neon-cyan">
        <ArrowLeft size={15} /> 返回列表
      </Link>
      <h1 className="mb-6 flex items-center gap-2 text-2xl font-bold text-white">
        <PlusCircle size={22} className="text-neon-cyan" /> {isEdit ? '编辑赛事' : '发布新赛事'}
      </h1>

      <div className="glass space-y-4 p-6">
        <Field label="竞赛名称 *">
          <input className="input" value={form.title} onChange={(e) => set('title', e.target.value)} placeholder="例如：2026 XX 黑客松" />
        </Field>
        <Field label="Slug（留空自动生成）">
          <input className="input" value={form.slug} onChange={(e) => set('slug', e.target.value)} placeholder="xx-hackathon-2026" />
        </Field>
        <Field label="一句话简介">
          <input className="input" value={form.summary} onChange={(e) => set('summary', e.target.value)} placeholder="简短描述，展示在卡片上" />
        </Field>
        <Field label="详细介绍">
          <textarea className="input min-h-[120px]" value={form.description} onChange={(e) => set('description', e.target.value)} placeholder="支持多段，用换行分隔" />
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="分类">
            <select className="input" value={form.category_id} onChange={(e) => set('category_id', e.target.value === '' ? '' : Number(e.target.value))}>
              <option value="">未分类</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.icon} {c.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="状态">
            <select className="input" value={form.status} onChange={(e) => set('status', e.target.value)}>
              <option value="upcoming">即将开始</option>
              <option value="ongoing">进行中</option>
              <option value="ended">已结束</option>
            </select>
          </Field>
          <Field label="形式">
            <select className="input" value={form.mode} onChange={(e) => set('mode', e.target.value)}>
              <option value="online">线上</option>
              <option value="offline">线下</option>
              <option value="hybrid">线上+线下</option>
            </select>
          </Field>
          <Field label="主办方">
            <input className="input" value={form.organizer} onChange={(e) => set('organizer', e.target.value)} />
          </Field>
          <Field label="地点">
            <input className="input" value={form.location} onChange={(e) => set('location', e.target.value)} placeholder="城市或「线上」" />
          </Field>
          <Field label="奖金">
            <input className="input" value={form.prize} onChange={(e) => set('prize', e.target.value)} placeholder="例如：¥ 100,000" />
          </Field>
          <Field label="奖金数额（数字，用于排序）">
            <input className="input" type="number" value={form.prize_amount} onChange={(e) => set('prize_amount', e.target.value)} placeholder="100000" />
          </Field>
          <Field label="开始日期">
            <input className="input" type="date" value={form.start_date} onChange={(e) => set('start_date', e.target.value)} />
          </Field>
          <Field label="结束日期">
            <input className="input" type="date" value={form.end_date} onChange={(e) => set('end_date', e.target.value)} />
          </Field>
          <Field label="报名截止">
            <input className="input" type="date" value={form.reg_deadline} onChange={(e) => set('reg_deadline', e.target.value)} />
          </Field>
          <Field label="官网 / 报名链接">
            <input className="input" value={form.source_url} onChange={(e) => set('source_url', e.target.value)} placeholder="https://" />
          </Field>
        </div>

        <Field label="标签（逗号分隔）">
          <input className="input" value={form.tags} onChange={(e) => set('tags', e.target.value)} placeholder="AI, 黑客松, 青年" />
        </Field>

        <label className="flex items-center gap-2 text-sm text-slate-300">
          <input type="checkbox" checked={form.featured} onChange={(e) => set('featured', e.target.checked)} />
          设为精选（首页高亮）
        </label>

        <div className="flex gap-3 pt-2">
          <button className="btn-primary" onClick={submit} disabled={loading}>
            {loading ? <Loader2 className="animate-spin" size={16} /> : isEdit ? '保存修改' : '发布赛事'}
          </button>
          <Link to="/" className="btn-ghost">
            取消
          </Link>
        </div>
      </div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-slate-400">{label}</span>
      {children}
    </label>
  )
}
