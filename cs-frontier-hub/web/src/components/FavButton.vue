<script setup>
import { ref } from 'vue'
import Icon from './Icon.vue'
import { api } from '../lib/api'

const props = defineProps({
  itemId: { type: Number, required: true },
  favorited: { type: Boolean, default: false },
})
const emit = defineEmits(['update'])

const active = ref(props.favorited)
const busy = ref(false)

async function toggle() {
  if (busy.value) return
  busy.value = true
  try {
    const r = await api.toggleFav(props.itemId)
    active.value = r.favorited
    emit('update', active.value)
  } catch (e) {
    console.error(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <button
    class="btn !px-2.5 !py-2 transition-colors"
    :class="active ? 'text-rose-500' : 'btn-ghost text-muted hover:text-rose-500'"
    :title="active ? '取消收藏' : '收藏'"
    @click.stop="toggle"
  >
    <Icon :name="'heart'" :size="18" :fill="active ? 'currentColor' : 'none'" />
  </button>
</template>
