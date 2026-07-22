<script setup>
import { computed } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({
  item: { type: Object, required: true },
  height: { type: String, default: '140px' },
})

function hashHue(str) {
  let h = 0
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) % 360
  return h
}

const monogram = computed(() => {
  const t = (props.item.title || '?').trim()
  return t ? t[0].toUpperCase() : '?'
})

// 将生成的「画像」渐变约束在蓝→青色相区间（190°~225°），贴合蓝白酷炫风
const grad = computed(() => {
  const base = 190 + (hashHue(props.item.slug || props.item.title || 'x') % 36)
  const h2 = base + 22
  return `linear-gradient(135deg, hsl(${base} 80% 46%), hsl(${h2} 85% 32%))`
})

const hasImg = computed(() => !!props.item.image_url)
</script>

<template>
  <div class="cover relative overflow-hidden rounded-xl border" :style="{ height }">
    <img
      v-if="hasImg"
      :src="item.image_url"
      :alt="item.title"
      loading="lazy"
      class="absolute inset-0 h-full w-full object-cover"
    />
    <!-- 无真实图片时生成的渐变「画像」 -->
    <div
      v-else
      class="absolute inset-0 flex items-center justify-center"
      :style="{ background: grad }"
    >
      <span class="font-mono text-5xl font-extrabold text-white/90 drop-shadow">{{ monogram }}</span>
    </div>

    <!-- 暗角与分类标识 -->
    <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/55 via-transparent to-transparent"></div>
    <div class="absolute left-2 top-2 flex items-center gap-1 rounded-full bg-black/35 px-2 py-0.5 text-[11px] font-medium text-white/90 backdrop-blur">
      <Icon :name="item.category_slug || 'sparkles'" :size="13" />
      <span>{{ item.category_name || '前沿' }}</span>
    </div>
  </div>
</template>
