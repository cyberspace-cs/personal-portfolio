<script setup>
import { ref, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../lib/api'
import Icon from '../components/Icon.vue'
import Cover from '../components/Cover.vue'
import FavButton from '../components/FavButton.vue'
import Markdown from '../components/Markdown.vue'

const props = defineProps({ slug: { type: String, required: true } })
const item = ref(null)
const related = ref([])
const notFound = ref(false)

const srcLabel = {
  repo: '开源仓库', paper: '论文', blog: '文章', tool: '工具',
  framework: '框架', product: '产品', conference: '会议', course: '课程',
}

async function load() {
  notFound.value = false
  try {
    item.value = await api.item(props.slug)
  } catch (e) {
    notFound.value = true
    return
  }
  // 同方向推荐
  try {
    const r = await api.items({ category: item.value.category_slug, page_size: 4 })
    related.value = r.items.filter((i) => i.id !== item.value.id).slice(0, 3)
  } catch (e) { related.value = [] }
}

onMounted(load)
watch(() => props.slug, load)
</script>

<template>
  <main class="mx-auto max-w-3xl px-4 pb-10">
    <RouterLink to="/" class="btn btn-ghost mt-6">
      <Icon name="arrow-right" :size="15" class="rotate-180" /> 返回列表
    </RouterLink>

    <div v-if="notFound" class="card mt-6 place-items-center py-16 text-center text-muted">
      <Icon name="search" :size="28" />
      <p class="mt-2">未找到该条目。</p>
    </div>

    <article v-if="item" class="mt-4 fade-in">
      <Cover :item="item" height="220px" />

      <div class="mt-4 flex items-start justify-between gap-3">
        <div>
          <div class="flex items-center gap-2 text-xs text-muted">
            <RouterLink :to="`/?c=${item.category_slug}`" class="badge border-accent/30 text-accent hover:brightness-110">
              <Icon :name="item.category_slug" :size="13" /> {{ item.category_name }}
            </RouterLink>
            <span class="badge border-border">{{ srcLabel[item.source_type] || item.source_type }}</span>
          </div>
          <h1 class="mt-2 text-2xl font-extrabold">{{ item.title }}</h1>
        </div>
        <FavButton :item-id="item.id" :favorited="item.is_favorited" @update="item.is_favorited = $event" />
      </div>

      <p class="mt-3 text-muted">{{ item.summary }}</p>

      <div class="mt-4 flex flex-wrap items-center gap-3 text-sm text-muted">
        <span v-if="item.author_org" class="flex items-center gap-1.5"><Icon name="cpu" :size="15" /> {{ item.author_org }}</span>
        <span v-if="item.language" class="flex items-center gap-1.5"><Icon name="terminal" :size="15" /> {{ item.language }}</span>
        <span v-if="item.github_stars != null" class="flex items-center gap-1.5 text-amber-500"><Icon name="star" :size="15" /> {{ item.github_stars.toLocaleString() }}</span>
        <span class="flex items-center gap-1.5"><Icon name="sparkles" :size="15" /> {{ item.views }} 浏览</span>
        <a v-if="item.source_url" :href="item.source_url" target="_blank" rel="noopener" class="btn btn-primary !py-1.5 !text-xs ml-auto">
          <Icon name="external" :size="14" /> 阅读原文
        </a>
      </div>

      <div v-if="item.tags?.length" class="mt-3 flex flex-wrap gap-1.5">
        <span v-for="t in item.tags" :key="t" class="badge border-accent/30 text-accent">{{ t }}</span>
      </div>

      <div class="card mt-6">
        <Markdown :source="item.content" />
      </div>

      <section v-if="related.length" class="mt-8">
        <h2 class="mb-3 flex items-center gap-2 text-lg font-bold">
          <Icon name="layers" :size="18" class="text-accent" /> 同方向推荐
        </h2>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <RouterLink
            v-for="r in related" :key="r.id" :to="`/item/${r.slug}`"
            class="card card-hover flex flex-col gap-2"
          >
            <Cover :item="r" height="96px" />
            <h3 class="truncate text-sm font-semibold">{{ r.title }}</h3>
          </RouterLink>
        </div>
      </section>
    </article>
  </main>
</template>
