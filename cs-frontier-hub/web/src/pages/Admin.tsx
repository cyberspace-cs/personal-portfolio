import { useEffect, useState } from 'react'
import { Plus, Pencil, Trash2, Save, X, Settings2, Boxes, AlertTriangle } from 'lucide-react'
import { api } from '../lib/api'
import type { Category, Item, ItemInput } from '../lib/types'
import { sourceMeta } from '../lib/source'
import { categoryIcon } from '../lib/icons'

const EMPTY_ITEM: ItemInput & { tags_str?: string; id?: number } = {
  title: '', slug: '', summary: '', content: '', category_id: null,
  source_type: 'repo', source_url: '', github_stars: null, author_org: '',
  language: '', status: 'active', featured: false, tags: [], tags_str: '',
}
const EMPTY_CAT = { name: '', slug: '', icon: 'sparkles', description: '', sort_order: 0 }

export function Admin() {
  const [tab, setTab] = useState<'items' | 'cats'>('items')
  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="flex items-center gap-2 text-2xl font-extrabold">
        <Settings2 size={22} className="text-accent" /> 内容管理
      </h1>
      <p className="mt-1 text-sm text-muted">
        前沿信息的增删改查与分类管理。生产环境建议设置后端 ADMIN_KEY 以保护写接口。
      </p>

      <div className="mt-5 flex gap-2">
        <button className={`chip ${tab === 'items' ? 'chip-active' : ''}`} onClick={() => setTab('items')}>
          <Boxes size={14} /> 前沿条目
        </button>
        <button className={`chip ${tab === 'cats' ? 'chip-active' : ''}`} onClick={() => setTab('cats')}>
          <Boxes size={14} /> 分类管理
        </button>
      </div>

      <div className="mt-5">{tab === 'items' ? <ItemsManager /> : <CategoryManager />}</div>
    </div>
  )
}

function ItemsManager() {
  const [items, setItems] = useState<Item[]>([])
  const [cats, setCats] = useState<Category[]>([])
  const [editing, setEditing] = useState<Item | null>(null)
  const [form, setForm] = useState<any>(EMPTY_ITEM)
  const [showForm, setShowForm] = useState(false)

  const reload = () => {
    api.listItems({ page_size: 200 }).then((r) => setItems(r.items))
    api.getCategories().then(setCats)
  }
  useEffect(reload, [])

  const openCreate = () => {
    setEditing(null)
    setForm({ ...EMPTY_ITEM })
    setShowForm(true)
  }
  const openEdit = (it: Item) => {
    setEditing(it)
    setForm({
      ...EMPTY_ITEM, ...it, tags_str: (it.tags || []).join(', '),
    })
    setShowForm(true)
  }
  const close = () => { setShowForm(false); setEditing(null) }

  const submit = async () => {
    if (!form.title?.trim()) { alert('请填写标题'); return }
    const payload: ItemInput = {
      title: form.title,
      slug: form.slug || undefined,
      summary: form.summary,
      content: form.content,
      category_id: form.category_id ? Number(form.category_id) : null,
      source_type: form.source_type,
      source_url: form.source_url,
      github_stars: form.github_stars === '' || form.github_stars == null ? null : Number(form.github_stars),
      author_org: form.author_org,
      language: form.language,
      status: form.status,
      featured: !!form.featured,
      tags: (form.tags_str || '').split(',').map((s: string) => s.trim()).filter(Boolean),
    }
    try {
      if (editing) await api.updateItem(editing.id, payload)
      else await api.createItem(payload)
      close()
      reload()
    } catch (e) { alert('保存失败：' + (e as Error).message) }
  }

  const remove = async (it: Item) => {
    if (!confirm(`确认删除「${it.title}」？`)) return
    try { await api.deleteItem(it.id); reload() }
    catch (e) { alert('删除失败：' + (e as Error).message) }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
      <div className="card p-0">
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="font-bold">条目列表（{items.length}）</h2>
          <button className="btn-primary" onClick={openCreate}>
            <Plus size={15} /> 新建
          </button>
        </div>
        <div className="divide-y">
          {items.map((it) => (
            <div key={it.id} className="flex items-center gap-3 p-3 hover:bg-surface-2">
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-fg">{it.title}</p>
                <p className="truncate text-xs text-muted">
                  {it.category_name} · {sourceMeta(it.source_type).label}
                  {it.github_stars != null ? ` · ★${it.github_stars}` : ''}
                </p>
              </div>
              <button className="btn-ghost h-8 w-8 !px-0" onClick={() => openEdit(it)} title="编辑">
                <Pencil size={15} />
              </button>
              <button className="btn-ghost h-8 w-8 !px-0 text-rose-400" onClick={() => remove(it)} title="删除">
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {showForm && (
        <div className="card h-fit lg:sticky lg:top-20">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-bold">{editing ? '编辑条目' : '新建条目'}</h2>
            <button className="btn-ghost h-8 w-8 !px-0" onClick={close}>
              <X size={15} />
            </button>
          </div>
          <div className="space-y-3 text-sm">
            <Field label="标题 *">
              <input className="input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Slug（可选）">
                <input className="input" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} />
              </Field>
              <Field label="分类">
                <select className="input" value={form.category_id ?? ''} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
                  <option value="">未分类</option>
                  {cats.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </Field>
            </div>
            <Field label="简介">
              <input className="input" value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} />
            </Field>
            <Field label="正文（Markdown）">
              <textarea className="input min-h-[120px] font-mono" value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="类型">
                <select className="input" value={form.source_type} onChange={(e) => setForm({ ...form, source_type: e.target.value })}>
                  {['repo', 'paper', 'blog', 'tool', 'conference', 'framework', 'product', 'course'].map((t) => (
                    <option key={t} value={t}>{sourceMeta(t).label}</option>
                  ))}
                </select>
              </Field>
              <Field label="状态">
                <select className="input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                  {['active', 'trending', 'archived'].map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </Field>
            </div>
            <Field label="原始链接">
              <input className="input" value={form.source_url} onChange={(e) => setForm({ ...form, source_url: e.target.value })} />
            </Field>
            <div className="grid grid-cols-3 gap-3">
              <Field label="机构">
                <input className="input" value={form.author_org} onChange={(e) => setForm({ ...form, author_org: e.target.value })} />
              </Field>
              <Field label="语言">
                <input className="input" value={form.language} onChange={(e) => setForm({ ...form, language: e.target.value })} />
              </Field>
              <Field label="Stars">
                <input type="number" className="input" value={form.github_stars ?? ''} onChange={(e) => setForm({ ...form, github_stars: e.target.value })} />
              </Field>
            </div>
            <Field label="标签（逗号分隔）">
              <input className="input" value={form.tags_str} onChange={(e) => setForm({ ...form, tags_str: e.target.value })} />
            </Field>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={!!form.featured} onChange={(e) => setForm({ ...form, featured: e.target.checked })} />
              设为精选
            </label>
            <button className="btn-primary w-full" onClick={submit}>
              <Save size={15} /> 保存
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function CategoryManager() {
  const [cats, setCats] = useState<Category[]>([])
  const [editing, setEditing] = useState<Category | null>(null)
  const [form, setForm] = useState<any>(EMPTY_CAT)
  const [showForm, setShowForm] = useState(false)

  const reload = () => api.getCategories().then(setCats)
  useEffect(reload, [])

  const openCreate = () => { setEditing(null); setForm({ ...EMPTY_CAT }); setShowForm(true) }
  const openEdit = (c: Category) => { setEditing(c); setForm({ ...c }); setShowForm(true) }
  const close = () => { setShowForm(false); setEditing(null) }

  const submit = async () => {
    if (!form.name?.trim()) { alert('请填写分类名称'); return }
    try {
      if (editing) await api.updateCategory(editing.id, form)
      else await api.createCategory(form)
      close(); reload()
    } catch (e) { alert('保存失败：' + (e as Error).message) }
  }
  const remove = async (c: Category) => {
    if (!confirm(`确认删除分类「${c.name}」？（其下条目将变为未分类）`)) return
    try { await api.deleteCategory(c.id); reload() } catch (e) { alert('删除失败：' + (e as Error).message) }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
      <div className="card p-0">
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="font-bold">分类列表（{cats.length}）</h2>
          <button className="btn-primary" onClick={openCreate}><Plus size={15} /> 新建</button>
        </div>
        <div className="divide-y">
          {cats.map((c) => {
            const Icon = categoryIcon(c.slug)
            return (
              <div key={c.id} className="flex items-center gap-3 p-3 hover:bg-surface-2">
                <Icon size={18} className="text-accent" />
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-fg">{c.name}</p>
                  <p className="truncate text-xs text-muted">{c.description || c.slug}</p>
                </div>
                <span className="rounded-full bg-surface-2 px-2 text-xs text-muted">{c.count}</span>
                <button className="btn-ghost h-8 w-8 !px-0" onClick={() => openEdit(c)}><Pencil size={15} /></button>
                <button className="btn-ghost h-8 w-8 !px-0 text-rose-400" onClick={() => remove(c)}><Trash2 size={15} /></button>
              </div>
            )
          })}
        </div>
      </div>

      {showForm && (
        <div className="card h-fit lg:sticky lg:top-20">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-bold">{editing ? '编辑分类' : '新建分类'}</h2>
            <button className="btn-ghost h-8 w-8 !px-0" onClick={close}><X size={15} /></button>
          </div>
          <div className="space-y-3 text-sm">
            <Field label="名称 *"><input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
            <Field label="Slug"><input className="input" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} /></Field>
            <Field label="图标（lucide 名，如 boxes / server）"><input className="input" value={form.icon} onChange={(e) => setForm({ ...form, icon: e.target.value })} /></Field>
            <Field label="描述"><input className="input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Field>
            <Field label="排序"><input type="number" className="input" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })} /></Field>
            <button className="btn-primary w-full" onClick={submit}><Save size={15} /> 保存</button>
          </div>
        </div>
      )}
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-muted">{label}</span>
      {children}
    </label>
  )
}
