<script setup>
import { computed } from 'vue'
import {
  Boxes, Gauge, Server, Bot, Workflow, Users, Plug, Database, Zap, Split,
  Layers, SlidersHorizontal, Brain, ClipboardCheck, Image as ImageIcon, Cloud,
  Terminal, GraduationCap, Sparkles, Github, FileText, BookOpen, Wrench, Blocks,
  Box, Cpu, Network, Rocket, Star, Heart, Search, Menu, X, ArrowRight, ExternalLink,
  Newspaper, Code2, Flame, Globe, Radio,
} from 'lucide-vue-next'

const props = defineProps({
  name: { type: String, default: 'sparkles' },
  size: { type: [Number, String], default: 18 },
})

const catMap = {
  'llm-arch': Boxes, 'inference-opt': Gauge, 'inference-engine': Server,
  'agent-arch': Bot, 'agent-framework': Workflow, 'multi-agent': Users,
  'mcp': Plug, 'rag': Database, 'gpu-triton': Zap, 'context-parallel': Split,
  'pretrain': Layers, 'finetune': SlidersHorizontal, 'rl-agentic': Brain,
  'agent-eval': ClipboardCheck, 'multimodal': ImageIcon, 'ai-infra': Cloud,
  'data': Database, 'systems': Terminal, 'conference': GraduationCap,
  'frontier-model': Sparkles,
}
const srcMap = {
  repo: Github, paper: FileText, blog: BookOpen, news: Newspaper, tool: Wrench,
  framework: Blocks, product: Box, conference: GraduationCap, course: BookOpen,
}
const extra = {
  cpu: Cpu, network: Network, rocket: Rocket, star: Star, heart: Heart,
  search: Search, menu: Menu, x: X, 'arrow-right': ArrowRight, external: ExternalLink,
  code: Code2, flame: Flame, globe: Globe, radio: Radio,
}

const all = {
  Boxes, Gauge, Server, Bot, Workflow, Users, Plug, Database, Zap, Split, Layers,
  SlidersHorizontal, Brain, ClipboardCheck, Image: ImageIcon, Cloud, Terminal,
  GraduationCap, Sparkles, Github, FileText, BookOpen, Wrench, Blocks, Box, Cpu,
  Network, Rocket, Star, Heart, Search, Menu, X, ArrowRight, ExternalLink, Newspaper,
  Code2, Flame, Globe, Radio,
}

const comp = computed(() => {
  if (all[props.name]) return all[props.name]
  if (catMap[props.name]) return catMap[props.name]
  if (srcMap[props.name]) return srcMap[props.name]
  if (extra[props.name]) return extra[props.name]
  return Sparkles
})
</script>

<template>
  <component :is="comp" :size="size" :stroke-width="2" />
</template>
