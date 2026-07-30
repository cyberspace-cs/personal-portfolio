<script setup>
import Icon from './Icon.vue'

defineProps({
  categories: { type: Array, default: () => [] },
  active: { type: String, default: '' },
})
const emit = defineEmits(['select'])
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <button
      class="chip"
      :class="{ 'chip-active': active === '' }"
      @click="emit('select', '')"
    >
      <Icon name="sparkles" :size="15" /> 全部
    </button>
    <button
      v-for="c in categories"
      :key="c.slug"
      class="chip"
      :class="{ 'chip-active': active === c.slug }"
      @click="emit('select', c.slug)"
    >
      <Icon :name="c.slug" :size="15" />
      <span>{{ c.name }}</span>
      <span class="ml-0.5 rounded-full bg-black/10 px-1.5 text-[11px] tabular-nums">{{ c.count }}</span>
    </button>
  </div>
</template>
