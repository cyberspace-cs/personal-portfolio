<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../lib/api'
import Icon from '../components/Icon.vue'
import ItemCard from '../components/ItemCard.vue'

const items = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    items.value = await api.favorites()
  } catch (e) {
    items.value = []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <main class="mx-auto max-w-6xl px-4 pb-10">
    <h1 class="mt-8 flex items-center gap-2 text-2xl font-extrabold">
      <Icon name="heart" :size="22" class="text-rose-500" /> 我的收藏
    </h1>
    <p class="mt-1 text-sm text-muted">收藏基于本机匿名会话，清空浏览器数据会丢失。</p>

    <div v-if="loading" class="grid place-items-center py-20 text-muted">
      <Icon name="cpu" :size="28" class="float-y" />
    </div>
    <div v-else-if="items.length" class="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <ItemCard v-for="it in items" :key="it.id" :item="it" />
    </div>
    <div v-else class="card mt-6 place-items-center py-16 text-center text-muted">
      <Icon name="heart" :size="26" />
      <p class="mt-2">还没有收藏。去列表里点 ♥ 收藏感兴趣的前沿信息吧。</p>
      <RouterLink to="/" class="btn btn-primary mt-3"><Icon name="rocket" :size="15" /> 去逛逛</RouterLink>
    </div>
  </main>
</template>
