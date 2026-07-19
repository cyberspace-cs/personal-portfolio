// 每厂面试适配包配置：侧重类目(focus) + 优先话术(starTags) + 厂内专属题(extra)
// focus 顺序即题库在 MD 中的呈现顺序；starTags 需在 skillbank.starScripts 的 tag 中存在。

import { companies } from "./companies.js";

const EMBODIED_FOCUS = ["EMBODIED", "AGENT", "INFER", "ENGINEER"];
const EMBODIED_STAR = ["多Agent", "工程落地", "推理优化", "职业规划"];

// 厂内专属题（补充到通用题库之外）
const deepseekExtra = [
  { q: "什么是 MoE？DeepSeekMoE 的 Share/Router 专家各起什么作用？", a: "混合专家，路由专家按 token 动态激活、共享专家捕获通用知识；负载均衡避免少数专家过载。" },
  { q: "什么是 MLA(多头潜在注意力)？相对 MHA 改进？", a: "多头潜在注意力，低秩压缩 K/V 显存，显著降低推理时的 KV Cache 占用、提升吞吐。" },
  { q: "什么是 MTP(多令牌预测)？作用？", a: "一次预测多个 token，提升训练数据效率与推理吞吐，配合投机解码加速。" },
  { q: "DeepSeek 为何用 GRPO、为何放弃 Critic？", a: "GRPO 用组内相对优势估计，去掉价值网络(Critic)，省显存更稳定，适合可验证奖励场景。" },
  { q: "DeepSeek-V3 推理快的原因？", a: "MLA 压缩 KV + MoE 稀疏激活 + MTP 多 token 预测，三者共同降低单 token 成本。" },
];

export const packs = {
  "bytedance-seed": { focus: ["AGENT", "RAG", "TOOL", "TRAIN", "ENGINEER", "PROMPT"], starTags: ["多Agent", "评测体系", "技术挑战", "工程落地", "职业规划"] },
  "tencent-hunyuan": { focus: ["RAG", "AGENT", "TRAIN", "INFER", "PROMPT"], starTags: ["技术挑战", "多Agent", "评测体系", "职业规划"] },
  "zhipu": { focus: ["AGENT", "TOOL", "INFER", "RAG", "TRAIN"], starTags: ["多Agent", "工具调用", "评测体系", "职业规划"] },
  "kimi": { focus: ["INFER", "TOOL", "ENGINEER", "TRAIN", "AGENT"], starTags: ["推理优化", "工程落地", "评测体系", "职业规划"] },
  "deepseek": { focus: ["TRAIN", "INFER", "ENGINEER", "AGENT", "TOOL"], starTags: ["推理优化", "工程落地", "多Agent", "职业规划"], extra: deepseekExtra },
  "deepseek-pm": { focus: ["PM", "AGENT", "RAG", "TRAIN"], starTags: ["产品思维", "评测体系", "职业规划"] },
  "jd": { focus: ["PM", "RAG", "AGENT"], starTags: ["产品思维", "职业规划"] },
  "kuaishou": { focus: ["RAG", "AGENT", "TOOL", "ENGINEER", "PROMPT"], starTags: ["工程落地", "技术挑战", "多Agent", "职业规划"] },
  "kuaishou-pm": { focus: ["PM", "AGENT", "RAG"], starTags: ["产品思维", "评测体系", "职业规划"] },
  "stepfun": { focus: ["RAG", "INFER", "AGENT", "TRAIN"], starTags: ["推理优化", "技术挑战", "多Agent", "职业规划"] },
  "yushu": { focus: EMBODIED_FOCUS, starTags: EMBODIED_STAR },
  "zhiyuan": { focus: EMBODIED_FOCUS, starTags: EMBODIED_STAR },
  "galaxy": { focus: EMBODIED_FOCUS, starTags: EMBODIED_STAR },
  "alibaba-tongyi": { focus: ["RAG", "AGENT", "ENGINEER", "TOOL"], starTags: ["技术挑战", "多Agent", "评测体系", "职业规划"] },
  "baidu": { focus: ["RAG", "AGENT", "ENGINEER", "TOOL"], starTags: ["技术挑战", "多Agent", "工程落地", "职业规划"] },
  "minimax": { focus: ["AGENT", "RAG", "PROMPT", "TOOL"], starTags: ["多Agent", "技术挑战", "职业规划"] },
  "baichuan": { focus: ["RAG", "AGENT", "TRAIN"], starTags: ["技术挑战", "多Agent", "职业规划"] },
  "sensetime": { focus: ["RAG", "INFER", "AGENT", "TRAIN"], starTags: ["技术挑战", "推理优化", "多Agent", "职业规划"] },
  "meituan": { focus: ["ENGINEER", "RAG", "AGENT", "INFER"], starTags: ["工程落地", "多Agent", "评测体系", "职业规划"] },
  "xinghai": { focus: EMBODIED_FOCUS, starTags: EMBODIED_STAR },
  "xingdong": { focus: EMBODIED_FOCUS, starTags: EMBODIED_STAR },
  "lingchu": { focus: EMBODIED_FOCUS, starTags: EMBODIED_STAR },
};

// 校验：packs 必须覆盖全部 companies
for (const c of companies) {
  if (!packs[c.id]) throw new Error("缺少 company-pack 配置: " + c.id);
}
