<script setup>
import { computed } from 'vue'
import { renderMarkdown } from '../lib/markdown'

const props = defineProps({ source: { type: String, default: '' } })
const html = computed(() => renderMarkdown(props.source))
</script>

<template>
  <div class="prose-cs text-sm" v-html="html"></div>
</template>
