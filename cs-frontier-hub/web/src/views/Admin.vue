<script setup>
import { ref, onMounted } from 'vue'
import api from '../lib/api'
import Icon from '../components/Icon.vue'

const adminKey = ref(localStorage.getItem('csf_admin_key') || '')
const msg = ref('')
const busy = ref(false)

const categories = ref([])
const items = ref([])

// 分类表单
const catForm = ref({ name: '', slug: '', icon: 'sparkles', description: '', sort_order: 0 })
// 条目表单
const editingId = ref(null)
const itemForm = ref({
  title: '', slug: '', summary: '', content: '', category_id: '', source_type: 'repo',
  source_url: '', author_org: '', language: '', status: 'active', featured: false, image_url: '', tags: '',
})

function setMsg(m, ok = true) { msg.value = (ok ? '✅ ' : '⚠️ ') + m }

function persistKey() { localStorage.setItem('csf_admin_key', adminKey.value) }

async function loadAll() {
  categories.value = await api.categories()
  const r = await api.items({ page_size: 60 })
  items.value = r.items
}

onMounted(loadAll)

async function saveCategory() {
  if (!catForm.value.name) return setMsg('请填写分类名称', false)
  busy.value = true
  try {
    await api.createCategory({ ...catForm.value, sort_order: Number(catForm.value.sort_order) }, adminKey.value)
    persistKey()
    catForm.value = { name: '', slug: '', icon: 'sparkles', description: '', sort_order: 0 }
    await loadAll()
    setMsg('分类已创建')
  } catch (e) { setMsg(e.message, false) } finally { busy.value = false }
}

async function delCategory(id) {
  if (!confirm('确认删除该分类？')) return
  try { await api.deleteCategory(id, adminKey.value); await loadAll(); setMsg('分类已删除') }
  catch (e) { setMsg(e.message, false) }
}

function loadItem(it) {
  editingId.value = it.id
  itemForm.value = {
    title: it.title, slug: it.slug, summary: it.summary, content: it.content,
    category_id: it.category_id || '', source_type: it.source_type, source_url: it.source_url,
    author_org: it.author_org, language: it.language, status: it.status,
    featured: it.featured, image_url: it.image_url || '', tags: (it.tags || []).join(', '),
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function saveItem() {
  if (!itemForm.value.title) return setMsg('请填写标题', false)
  const payload = {
    ...itemForm.value,
    category_id: itemForm.value.category_id ? Number(itemForm.value.category_id) : null,
    tags: itemForm.value.tags.split(',').map((s) => s.trim()).filter(Boolean),
  }
  busy.value = true
  try {
    if (editingId.value) {
      await api.updateItem(editingId.value, payload, adminKey.value)
      setMsg('条目已更新')
    } else {
      await api.createItem(payload, adminKey.value)
      setMsg('条目已创建')
    }
    persistKey()
    editingId.value = null
    itemForm.value = {
      title: '', slug: '', summary: '', content: '', category_id: '', source_type: 'repo',
      source_url: '', author_org: '', language: '', status: 'active', featured: false, image_url: '', tags: '',
    }
    await loadAll()
  } catch (e) { setMsg(e.message, false) } finally { busy.value = false }
}

async function delItem(id) {
  if (!confirm('确认删除该条目？')) return
  try { await api.deleteItem(id, adminKey.value); await loadAll(); setMsg('条目已删除') }
  catch (e) { setMsg(e.message, false) }
}
</script>

<template>
  <main class="mx-auto max-w-4xl px-4 pb-10">
    <h1 class="mt-8 flex items-center gap-2 text-2xl font-extrabold">
      <Icon name="cpu" :size="22" class="text-accent" /> 管理后台
    </h1>
    <p class="mt-1 text-sm text-muted">
      若服务端设置了 <code>ADMIN_KEY</code> 环境变量，请填入密钥；未设置则留空即可。
    </p>

    <div class="mt-4 flex items-center gap-2">
      <input v-model="adminKey" class="input max-w-xs" type="password" placeholder="X-Admin-Key（可选）" />
      <button class="btn btn-ghost" @click="persistKey">保存密钥</button>
    </div>

    <p v-if="msg" class="mt-2 text-sm">{{ msg }}</p>

    <!-- 条目表单 -->
    <section class="card mt-6">
      <h2 class="mb-3 font-bold">{{ editingId ? '编辑条目 #' + editingId : '新建条目' }}</h2>
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <input v-model="itemForm.title" class="input" placeholder="标题 *" />
        <input v-model="itemForm.slug" class="input" placeholder="slug（留空自动生成）" />
        <input v-model="itemForm.summary" class="input" placeholder="一句话摘要" />
        <input v-model="itemForm.source_url" class="input" placeholder="来源链接" />
        <select v-model="itemForm.category_id" class="input">
          <option value="">选择分类</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <select v-model="itemForm.source_type" class="input">
          <option value="repo">开源仓库</option>
          <option value="paper">论文</option>
          <option value="blog">文章</option>
          <option value="tool">工具</option>
          <option value="framework">框架</option>
          <option value="product">产品</option>
          <option value="conference">会议</option>
          <option value="course">课程</option>
        </select>
        <input v-model="itemForm.author_org" class="input" placeholder="机构 / 作者" />
        <input v-model="itemForm.language" class="input" placeholder="语言" />
        <input v-model="itemForm.image_url" class="input" placeholder="封面图 URL（可选）" />
        <input v-model="itemForm.tags" class="input" placeholder="标签，逗号分隔" />
        <select v-model="itemForm.status" class="input">
          <option value="active">active</option>
          <option value="trending">trending</option>
          <option value="archived">archived</option>
        </select>
        <label class="flex items-center gap-2 text-sm text-muted">
          <input v-model="itemForm.featured" type="checkbox" /> 设为精选
        </label>
      </div>
      <textarea v-model="itemForm.content" class="input mt-3 h-28" placeholder="详情（支持 Markdown）"></textarea>
      <div class="mt-3 flex gap-2">
        <button class="btn btn-primary" :disabled="busy" @click="saveItem">
          <Icon name="star" :size="15" /> {{ editingId ? '保存修改' : '创建条目' }}
        </button>
        <button v-if="editingId" class="btn btn-ghost" @click="editingId = null; itemForm.title=''">取消</button>
      </div>
    </section>

    <!-- 分类管理 -->
    <section class="card mt-6">
      <h2 class="mb-3 font-bold">分类管理</h2>
      <div class="grid grid-cols-2 gap-2 sm:grid-cols-5">
        <input v-model="catForm.name" class="input" placeholder="名称" />
        <input v-model="catForm.slug" class="input" placeholder="slug" />
        <input v-model="catForm.icon" class="input" placeholder="图标" />
        <input v-model="catForm.sort_order" type="number" class="input" placeholder="排序" />
        <button class="btn btn-primary" :disabled="busy" @click="saveCategory"><Icon name="layers" :size="15" /> 添加</button>
      </div>
      <input v-model="catForm.description" class="input mt-2" placeholder="描述" />
    </section>

    <!-- 条目列表 -->
    <section class="mt-6">
      <h2 class="mb-3 font-bold">条目列表（{{ items.length }}）</h2>
      <div class="space-y-2">
        <div v-for="it in items" :key="it.id" class="card flex items-center gap-3 py-3">
          <div class="min-w-0 flex-1">
            <p class="truncate font-semibold">{{ it.title }}</p>
            <p class="truncate text-xs text-muted">{{ it.category_name }} · {{ it.source_type }}</p>
          </div>
          <button class="btn btn-ghost !py-1.5" @click="loadItem(it)"><Icon name="sparkles" :size="14" /> 编辑</button>
          <button class="btn !py-1.5 text-rose-500" @click="delItem(it.id)"><Icon name="x" :size="14" /> 删</button>
        </div>
      </div>
    </section>
  </main>
</template>
