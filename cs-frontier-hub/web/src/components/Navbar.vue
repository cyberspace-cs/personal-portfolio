<script setup>
import { RouterLink } from 'vue-router'
import Icon from './Icon.vue'
import ThemeToggle from './ThemeToggle.vue'
</script>

<template>
  <header class="sticky top-0 z-30 glass border-b">
    <nav class="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3">
      <RouterLink to="/" class="flex items-center gap-2 font-extrabold tracking-tight">
        <span class="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-accent to-accent-2 text-white shadow-glow">
          <Icon name="network" :size="20" />
        </span>
        <span class="hidden sm:block text-lg">CS 前沿<span class="neon">地图</span></span>
      </RouterLink>

      <div class="ml-auto flex items-center gap-1.5">
        <RouterLink to="/" class="chip" active-class="chip-active">
          <Icon name="rocket" :size="16" /><span class="hidden sm:inline">首页</span>
        </RouterLink>
        <RouterLink to="/favorites" class="chip" active-class="chip-active">
          <Icon name="heart" :size="16" /><span class="hidden sm:inline">收藏</span>
        </RouterLink>
        <RouterLink to="/admin" class="chip" active-class="chip-active">
          <Icon name="cpu" :size="16" /><span class="hidden sm:inline">管理</span>
        </RouterLink>
        <ThemeToggle />
      </div>
    </nav>
  </header>
</template>
