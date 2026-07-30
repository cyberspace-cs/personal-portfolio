<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import api from '../lib/api'
import Icon from '../components/Icon.vue'
import TechArchitecture from '../components/TechArchitecture.vue'
import CategoryNav from '../components/CategoryNav.vue'
import ItemCard from '../components/ItemCard.vue'

const categories = ref([])
const stats = ref(null)
const items = ref([])
const total = ref(0)
const totalPages = ref(1)
const page = ref(1)
const loading = ref(false)

const q = ref('')
const selectedCategory = ref('')
const selectedSource = ref('')
const hoverSrc = ref('')
const sort = ref('latest')

const gridRef = ref(null)
const crawling = ref(false)
const crawlMsg = ref('')

const SORTS = [
  { v: 'latest', label: '最新' },
  { v: 'views', label: '最热' },
  { v: 'stars', label: '星标' },
  { v: 'title', label: '名称' },
]

const SOURCES = [
  { v: '', label: '全部', icon: 'sparkles' },
  { v: 'repo', label: '仓库', icon: 'github' },
  { v: 'paper', label: '论文', icon: 'file-text' },
  { v: 'blog', label: '博客', icon: 'book-open' },
  { v: 'news', label: '资讯', icon: 'newspaper' },
  { v: 'product', label: '产品', icon: 'box' },
]

async function loadCategories() {
  categories.value = await api.categories()
}
async function loadStats() {
  stats.value = await api.stats()
}
async function loadItems() {
  loading.value = true
  try {
    const r = await api.items({
      q: q.value, category: selectedCategory.value, source_type: selectedSource.value,
      sort: sort.value, page: page.value, page_size: 12,
    })
    items.value = r.items
    total.value = r.total
    totalPages.value = r.total_pages
  } finally {
    loading.value = false
  }
}

async function search() {
  page.value = 1
  await loadItems()
}

function onSelectCategory(slug) {
  selectedCategory.value = slug
  page.value = 1
  nextTick(() => gridRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
}

async function crawl() {
  if (crawling.value) return
  crawling.value = true
  crawlMsg.value = '正在从 GitHub / Gitee / HuggingFace / arXiv / CSDN / AI 资讯 抓取最新前沿信息…'
  try {
    const r = await api.runCrawler(
      ['github', 'gitee', 'hf', 'arxiv', 'csdn', 'news', 'semantic'], 20)
    const parts = Object.entries(r.by_source || {})
      .map(([k, v]) => `${k} +${v.added}`).join('，')
    crawlMsg.value = `抓取完成：新增 ${r.added} 条（${parts}）。其中 ${r.with_images} 条带真实封面图。`
    await Promise.all([loadCategories(), loadStats(), loadItems()])
  } catch (e) {
    crawlMsg.value = '抓取失败：' + (e.message || e)
  } finally {
    crawling.value = false
  }
}

watch(selectedCategory, () => loadItems())
watch(selectedSource, () => { page.value = 1; loadItems() })
watch(sort, () => loadItems())

onMounted(async () => {
  await ensureSessionSafe()
  await Promise.all([loadCategories(), loadStats()])
  await loadItems()
})

async function ensureSessionSafe() {
  try { await api.createSession() } catch (e) { /* ignore */ }
}
</script>

<template>
  <main class="mx-auto max-w-6xl px-4 pb-10">
    <!-- Hero -->
    <section class="hero-glow relative pt-12 pb-8 text-center">
      <div class="mb-3 flex justify-center">
        <span class="kicker">FRONTIER_INTELLIGENCE_HUB</span>
      </div>
      <div class="float-y mb-4 inline-flex items-center gap-2 rounded-full border bg-surface-2 px-3 py-1 text-xs text-muted">
        <Icon name="sparkles" :size="14" class="text-accent" />
        聚合 GitHub · Gitee · 论文 · 博客 · AI 资讯 等全网前沿
      </div>
      <h1 class="text-3xl font-extrabold tracking-tight sm:text-5xl">
        CS 前沿<span class="gradient-text">知识地图</span>
      </h1>
      <p class="mx-auto mt-3 max-w-2xl text-sm text-muted sm:text-base">
        一个动态的技术架构视图 + 实时聚合的前沿信息库。点击下方架构图中的任意节点，即可按方向筛选开源项目、论文、博客与资讯。
      </p>

      <!-- 搜索 -->
      <form class="mx-auto mt-6 flex max-w-xl items-center gap-2" @submit.prevent="search">
        <div class="relative flex-1">
          <Icon name="search" :size="18" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            v-model="q" class="input !pl-10" type="text"
            placeholder="搜索项目 / 论文 / 技术，如 vLLM、Agent、量化…"
            @keyup.enter="search"
          />
        </div>
        <button class="btn btn-primary" type="submit">
          <Icon name="search" :size="16" /> 搜索
        </button>
      </form>

      <!-- 实时统计 -->
      <div v-if="stats" class="mt-6 flex flex-wrap items-center justify-center gap-3 text-sm">
        <span class="badge border-accent/30 text-accent">
          <Icon name="boxes" :size="13" /> {{ stats.total }} 条前沿信息
        </span>
        <span class="badge border-accent-2/30 text-accent-2">
          <Icon name="layers" :size="13" /> {{ stats.categories }} 个方向
        </span>
        <span class="badge border-emerald-400/30 text-emerald-500">
          <Icon name="star" :size="13" /> {{ stats.featured }} 精选
        </span>
        <button class="badge border-amber-400/30 text-amber-500 transition hover:brightness-110" @click="crawl" :disabled="crawling">
          <Icon name="rocket" :size="13" /> {{ crawling ? '抓取中…' : '抓取最新前沿' }}
        </button>
      </div>
      <p v-if="crawlMsg" class="mt-2 text-xs text-muted">{{ crawlMsg }}</p>
    </section>

    <!-- 动态技术架构图 -->
    <section class="card mt-2 overflow-hidden p-5">
      <div class="mb-3 flex items-center justify-between">
        <h2 class="flex items-center gap-2 text-lg font-bold">
          <Icon name="network" :size="18" class="text-accent" /> 动态技术架构地图
        </h2>
        <span class="text-xs text-muted">点击节点按方向筛选 ↓</span>
      </div>
      <TechArchitecture :categories="categories" @select="onSelectCategory" />
    </section>

      <!-- 筛选 + 列表 -->
    <section ref="gridRef" class="mt-8 scroll-mt-24">
      <div class="mb-4 flex flex-col gap-3">
        <!-- 来源筛选 -->
        <div class="flex flex-wrap items-center gap-2">
          <button
            v-for="s in SOURCES" :key="s.v"
            class="chip src-chip" :class="{ 'chip-active': selectedSource === s.v }"
            @click="selectedSource = s.v"
            @mouseenter="hoverSrc = s.v" @mouseleave="hoverSrc = ''"
          >
            <Icon :name="s.icon" :size="14" class="src-icon" :class="{ 'src-icon-on': selectedSource === s.v, 'src-icon-hover': hoverSrc === s.v }" />
            <span>{{ s.label }}</span>
          </button>
        </div>
        <CategoryNav :categories="categories" :active="selectedCategory" @select="onSelectCategory" />
        <div class="flex items-center justify-between">
          <p class="text-sm text-muted">
            共 <span class="font-semibold text-fg">{{ total }}</span> 条
            <span v-if="selectedCategory">· 已筛选「{{ categories.find(c => c.slug === selectedCategory)?.name }}」</span>
          </p>
          <label class="flex items-center gap-2 text-sm text-muted">
            排序
            <select v-model="sort" class="input !w-auto !py-1">
              <option v-for="s in SORTS" :key="s.v" :value="s.v">{{ s.label }}</option>
            </select>
          </label>
        </div>
      </div>

      <div v-if="loading" class="grid place-items-center py-20 text-muted">
        <Icon name="cpu" :size="28" class="float-y" />
      </div>

      <div v-else-if="items.length" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <ItemCard v-for="it in items" :key="it.id" :item="it" />
      </div>
      <div v-else class="card place-items-center py-16 text-center text-muted">
        <Icon name="search" :size="26" />
        <p class="mt-2">没有找到匹配的前沿信息，换个关键词或方向试试。</p>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="mt-6 flex items-center justify-center gap-3">
        <button class="btn btn-ghost" :disabled="page <= 1" @click="page--; loadItems()">
          <Icon name="arrow-right" :size="15" class="rotate-180" /> 上一页
        </button>
        <span class="text-sm text-muted">{{ page }} / {{ totalPages }}</span>
        <button class="btn btn-ghost" :disabled="page >= totalPages" @click="page++; loadItems()">
          下一页 <Icon name="arrow-right" :size="15" />
        </button>
      </div>
    </section>
  </main>
</template>
