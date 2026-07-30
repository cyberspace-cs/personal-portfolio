<script setup>
import Icon from './Icon.vue'
</script>

<template>
  <footer class="mt-16 border-t">
    <div class="mx-auto max-w-6xl px-4 py-8 text-sm text-muted">
      <div class="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
        <div class="flex items-center gap-2">
          <Icon name="network" :size="16" />
          <span>CS 前沿知识聚合平台 · FastAPI + Vue 3</span>
        </div>
        <div class="flex items-center gap-3">
          <span>聚合 GPU 算子 · 推理优化 · Agent · 多模态 · 顶会 等前沿方向</span>
        </div>
      </div>
      <p class="mt-3 text-xs opacity-70">
        数据来源于公开资料与爬虫（HuggingFace Papers / arXiv），仅供学习研究。封面图版权归原作者所有。
      </p>
    </div>
  </footer>
</template>
