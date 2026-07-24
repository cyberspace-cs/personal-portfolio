<script setup>
import { RouterLink } from 'vue-router'
import Icon from './Icon.vue'
import Cover from './Cover.vue'
import FavButton from './FavButton.vue'

defineProps({
  item: { type: Object, required: true },
})

const srcLabel = {
  repo: '开源仓库', paper: '论文', blog: '博客', news: '资讯', tool: '工具',
  framework: '框架', product: '产品', conference: '会议', course: '课程',
}
</script>

<template>
  <RouterLink
    :to="`/item/${item.slug}`"
    class="card card-hover group flex flex-col gap-3 fade-in"
  >
    <Cover :item="item" />

    <div class="flex items-start justify-between gap-2">
      <div class="min-w-0">
        <h3 class="truncate text-base font-bold text-fg group-hover:text-accent">{{ item.title }}</h3>
        <div class="mt-1 flex items-center gap-1.5 text-xs text-muted">
          <Icon :name="item.source_type" :size="13" />
          <span>{{ srcLabel[item.source_type] || item.source_type }}</span>
          <span v-if="item.author_org">· {{ item.author_org }}</span>
        </div>
      </div>
      <FavButton :item-id="item.id" :favorited="item.is_favorited" @update="item.is_favorited = $event" />
    </div>

    <p class="line-clamp-2 text-sm text-muted">{{ item.summary }}</p>

    <div class="mt-auto flex flex-wrap items-center gap-1.5">
      <span
        v-for="t in (item.tags || []).slice(0, 3)"
        :key="t"
        class="badge border-accent/30 text-accent"
      >{{ t }}</span>
      <span v-if="item.featured" class="badge border-amber-400/40 text-amber-500">
        <Icon name="star" :size="12" /> 精选
      </span>
      <span v-if="item.status === 'trending'" class="badge border-emerald-400/40 text-emerald-500">🔥 热门</span>
    </div>
  </RouterLink>
</template>
