<script setup>
import { ref, onMounted } from 'vue'
import Icon from './Icon.vue'

const isDark = ref(true)

function apply() {
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('csf_theme', isDark.value ? 'dark' : 'light')
}

function toggle() {
  isDark.value = !isDark.value
  apply()
}

onMounted(() => {
  const saved = localStorage.getItem('csf_theme')
  isDark.value = saved ? saved === 'dark' : true
  apply()
})
</script>

<template>
  <button class="btn btn-ghost !px-2.5 !py-2" :title="isDark ? '切换到亮色' : '切换到暗色'" @click="toggle">
    <Icon :name="isDark ? 'star' : 'sparkles'" :size="18" />
  </button>
</template>
