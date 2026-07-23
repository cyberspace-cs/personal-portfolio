<script setup>
import { computed } from 'vue'

const props = defineProps({
  categories: { type: Array, default: () => [] },
})
const emit = defineEmits(['select'])

// 技术栈分层（底 -> 顶），每层映射到分类 slug；配色统一为蓝→青霓虹族
const LAYERS = [
  { key: 'sys', label: '系统与底层', color: '#64748b', cats: ['systems', 'data'] },
  { key: 'infra', label: 'AI Infra · 混元', color: '#3b82f6', cats: ['ai-infra'] },
  { key: 'train', label: '训练 / 后训练', color: '#0ea5e9', cats: ['pretrain', 'finetune', 'rl-agentic'] },
  { key: 'infer', label: '推理优化 / 引擎', color: '#06b6d4', cats: ['inference-opt', 'inference-engine', 'gpu-triton', 'context-parallel'] },
  { key: 'model', label: '模型 / 多模态', color: '#22d3ee', cats: ['llm-arch', 'multimodal'] },
  { key: 'agent', label: 'Agent / 编排', color: '#38bdf8', cats: ['agent-arch', 'agent-framework', 'multi-agent', 'mcp', 'rag', 'agent-eval'] },
  { key: 'app', label: '前沿模型与产品', color: '#60a5fa', cats: ['frontier-model'] },
]

const SHORT = {
  systems: '系统/底层', data: '数据工程', ai: 'AI Infra', aiinfra: 'AI Infra',
  pretrain: '预训练', finetune: '微调/后训练', rlagentic: '强化学习',
  inferenceopt: '推理优化', inferenceengine: '推理引擎', gputriton: 'GPU/Triton',
  contextparallel: '上下文并行', llmarch: 'LLM 架构', multimodal: '多模态',
  agentarch: 'Agent 架构', agentframework: 'Agent 框架', multiagent: '多智能体',
  mcp: 'MCP', rag: 'RAG', agenteval: 'Agent 评估', frontier: '前沿模型',
}

const W = 980
const marginX = 24
const bandX = marginX
const bandW = W - 2 * marginX
const labelW = 150
const nodeAreaX = bandX + labelW + 16
const nodeAreaW = W - bandX - labelW - 16 - 16
const layerH = 64
const gapY = 52
const top = 28
const nodeH = 40

const counts = computed(() => {
  const m = {}
  for (const c of props.categories) m[c.slug] = c
  return m
})

function shortName(slug) {
  const s = slug.replace(/[-]/g, '').toLowerCase()
  if (SHORT[s]) return SHORT[s]
  if (SHORT[slug]) return SHORT[slug]
  return counts.value[slug]?.name || slug
}

const layout = computed(() => {
  const layers = LAYERS.map((L, i) => {
    const nodes = L.cats
      .map((slug) => counts.value[slug])
      .filter(Boolean)
      .map((c) => ({ slug: c.slug, name: shortName(c.slug), count: c.count }))
    const n = Math.max(nodes.length, 1)
    const gap = 12
    const nodeW = Math.min(190, (nodeAreaW - gap * (n - 1)) / n)
    const startX = nodeAreaX + (nodeAreaW - (n * nodeW + gap * (n - 1))) / 2
    const y = top + i * (layerH + gapY)
    nodes.forEach((nd, k) => {
      nd.x = startX + k * (nodeW + gap)
      nd.w = nodeW
      nd.y = y + (layerH - nodeH) / 2
    })
    return { ...L, y, nodes, hasNodes: nodes.length > 0 }
  })
  const lastY = top + (LAYERS.length - 1) * (layerH + gapY) + layerH
  const spineX = bandX + 14
  return { layers, spineX, y1: top, y2: lastY, totalH: lastY + top }
})

function onClick(slug) {
  emit('select', slug)
}
</script>

<template>
  <div class="w-full overflow-x-auto">
    <svg
      :viewBox="`0 0 ${W} ${layout.totalH}`"
      class="w-full min-w-[720px]"
      role="img"
      aria-label="CS 前沿技术架构地图"
    >
      <defs>
        <linearGradient id="spineGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#3b82f6" />
          <stop offset="1" stop-color="#22d3ee" />
        </linearGradient>
      </defs>

      <!-- 中央数据流动脊柱 -->
      <line
        :x1="layout.spineX" :y1="layout.y1" :x2="layout.spineX" :y2="layout.y2"
        stroke="url(#spineGrad)" stroke-width="3" class="arch-flow"
      />
      <!-- 流动光点 -->
      <circle :cx="layout.spineX" r="4" fill="#3b82f6" class="arch-pulse">
        <animate attributeName="cy" :from="layout.y1" :to="layout.y2" dur="3.2s" repeatCount="indefinite" />
      </circle>
      <circle :cx="layout.spineX" r="3" fill="#22d3ee" class="arch-pulse">
        <animate attributeName="cy" :from="layout.y2" :to="layout.y1" dur="4.1s" repeatCount="indefinite" />
      </circle>

      <!-- 每层 -->
      <g v-for="(L, i) in layout.layers" :key="L.key">
        <!-- 连接支线 -->
        <line :x1="layout.spineX" :y1="L.y + layerH/2" :x2="nodeAreaX" :y2="L.y + layerH/2"
              :stroke="L.color" stroke-width="1.5" stroke-opacity="0.5" />

        <!-- 层标签 -->
        <text :x="bandX + 12" :y="L.y + layerH/2 - 6" style="fill: var(--muted)" font-size="13" font-weight="700">
          {{ L.label.split(' ')[0] }}
        </text>
        <text :x="bandX + 12" :y="L.y + layerH/2 + 12" :fill="L.color" font-size="11" font-weight="600" opacity="0.9">
          {{ L.label.split(' ').slice(1).join(' ') }}
        </text>

        <!-- 节点 -->
        <g
          v-for="nd in L.nodes"
          :key="nd.slug"
          class="arch-node"
          @click="onClick(nd.slug)"
        >
          <rect
            :x="nd.x" :y="nd.y" :width="nd.w" :height="nodeH" rx="11"
            :fill="L.color" :fill-opacity="0.10" :stroke="L.color" :stroke-opacity="0.55" stroke-width="1.5"
          />
          <text
            :x="nd.x + nd.w/2" :y="nd.y + nodeH/2 - 1" text-anchor="middle"
            style="fill: var(--fg)" font-size="12.5" font-weight="600"
          >{{ nd.name }}</text>
          <text
            :x="nd.x + nd.w/2" :y="nd.y + nodeH/2 + 14" text-anchor="middle"
            style="fill: var(--muted)" font-size="10"
          >{{ nd.count }} 条</text>
        </g>

        <!-- 无节点占位 -->
        <text v-if="!L.hasNodes" :x="nodeAreaX + nodeAreaW/2" :y="L.y + layerH/2 + 4"
              text-anchor="middle" style="fill: var(--muted)" font-size="12" opacity="0.6">—</text>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.arch-node {
  cursor: pointer;
  transition: transform 0.15s ease;
}
.arch-node:hover rect {
  fill-opacity: 0.28 !important;
  stroke-opacity: 1 !important;
  filter: drop-shadow(0 0 6px currentColor);
}
.arch-node:hover {
  transform: translateY(-2px);
}
text {
  font-family: Inter, system-ui, sans-serif;
  pointer-events: none;
}
</style>
