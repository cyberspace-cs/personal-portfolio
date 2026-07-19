// 生成：分厂面试适配包(MD) + 题库总库 + README 索引
import { companies } from "./companies.js";
import { packs } from "./company-packs.js";
import { bank, CAT_TITLE, starScripts, reverseQuestions } from "./skillbank.js";
import { writeFileSync, mkdirSync } from "fs";
import path from "path";

const ROOT = "分厂适配包";
mkdirSync(ROOT, { recursive: true });

const docxFname = (c) => `${c.name}-${c.direction === "pm" ? "产品经理" : "Agent应用开发"}.docx`;
const packFname = (c) => `${c.name}-${c.direction === "pm" ? "产品经理" : "Agent应用开发"}.md`;

function buildCompanyMD(c) {
  const p = packs[c.id];
  const L = [];
  L.push(`# ${c.name} · ${c.objective} —— 面试适配包`);
  L.push("");
  L.push(`> 投递前：使用对应分厂 docx 简历（\`output/${docxFname(c)}\`）并以官网最新 JD 复核；本文件含「招聘网址 + 简历匹配 + 面试题库 + 话术」。`);
  L.push("");

  // 1. 招聘网址
  L.push(`## 1. 官方招聘网址`);
  L.push(`- 官网 / 招聘入口：**${c.url}**`);
  if (c.urlDetail) L.push(`- 岗位示例直链：${c.urlDetail}`);
  L.push(`- Boss 直聘可搜索「${c.name} ${c.objective}」同岗位（详情页有反爬，以官网为准）。`);
  L.push("");

  // 2. 简历匹配要点
  L.push(`## 2. 简历匹配要点（投递前核对）`);
  L.push(`- **求职意向**：${c.objective}`);
  L.push(`- **定向总结**：${c.summaryHook}`);
  L.push(`- **重点强调**：${c.note}`);
  L.push(`- **岗位匹配关键词**：${c.keywords.join(" / ")}`);
  L.push(`- **项目 Phase 重排**：${c.phaseOrder.join(" → ")}（其余按默认序）`);
  L.push(`- **对应简历文件**：\`output/${docxFname(c)}\``);
  L.push("");

  // 3. 面试题库
  L.push(`## 3. 面试题库（按本岗侧重挑选）`);
  L.push(`> 来源：2026 公开经验帖（字节 Agent 四面 21 题、小林 coding Agent16/RAG20/工具调用16/工程22、具身 Gank 面经、DeepSeek 模型专项）。完整总库见 \`面试题库总库.md\`。`);
  L.push("");
  for (const cat of p.focus) {
    const qs = bank[cat] || [];
    if (!qs.length) continue;
    L.push(`### ${CAT_TITLE[cat]}（${qs.length} 题）`);
    qs.forEach((it, i) => {
      L.push(`${i + 1}. **Q**：${it.q}`);
      L.push(`   **A**：${it.a}`);
    });
    L.push("");
  }
  if (p.extra && p.extra.length) {
    L.push(`### 厂内专项（${p.extra.length} 题）`);
    p.extra.forEach((it, i) => {
      L.push(`${i + 1}. **Q**：${it.q}`);
      L.push(`   **A**：${it.a}`);
    });
    L.push("");
  }

  // 4. 话术
  L.push(`## 4. 话术（STAR 模板 + 本项目定制）`);
  L.push(`> 以下话术基于本项目「刷题教练 → 定制化备考 Agent v3.1.0-agent-mem」设计，请按你的真实经历微调数据与措辞。`);
  L.push("");
  const picked = starScripts.filter((s) => p.starTags.includes(s.tag));
  // 确保「职业规划」始终给出
  if (!picked.find((s) => s.tag === "职业规划")) {
    const cr = starScripts.find((s) => s.tag === "职业规划");
    if (cr) picked.push(cr);
  }
  picked.forEach((s) => {
    L.push(`### ${s.tag}`);
    L.push(`- **面试官可能问**：${s.ask}`);
    L.push(`- **话术（STAR）**：${s.star.replace(/\n/g, " ")}`);
    L.push("");
  });

  // 5. 反问清单
  L.push(`## 5. 反问清单（面试官问「你有什么想问的」）`);
  reverseQuestions.forEach((q) => L.push(`- ${q}`));
  L.push("");

  // 6. 投递前核对清单
  L.push(`## 6. 投递前 CheckList`);
  L.push(`- [ ] 用 \`output/${docxFname(c)}\` 而非通用简历`);
  L.push(`- [ ] 以 ${c.url} 最新 JD 复核「求职意向 / 关键词 / Phase 重排」`);
  L.push(`- [ ] 本适配包第 3 节题库过一遍，第 4 节话术能脱稿讲`);
  L.push(`- [ ] 准备 1-2 个反问（第 5 节）`);
  L.push("");

  return L.join("\n");
}

// 生成各厂 MD
const indexRows = [];
for (const c of companies) {
  const md = buildCompanyMD(c);
  const f = path.join(ROOT, packFname(c));
  writeFileSync(f, md);
  indexRows.push({ c, pack: packFname(c) });
  console.log("✓", f);
}

// 题库总库
const allL = [];
allL.push(`# 面试题库总库（2026 大模型 Agent / AI 产品方向）`);
allL.push("");
allL.push(`> 综合公开经验帖整理：字节 Agent 四面 21 题、小林 coding Agent16/RAG20/工具调用16/工程22、具身 Gank 面经、DeepSeek 模型专项。分厂适配包按岗位侧重抽取子集。`);
allL.push("");
for (const cat of Object.keys(CAT_TITLE)) {
  const qs = bank[cat];
  allL.push(`## ${CAT_TITLE[cat]}（${qs.length} 题）`);
  qs.forEach((it, i) => {
    allL.push(`${i + 1}. **Q**：${it.q}`);
    allL.push(`   **A**：${it.a}`);
  });
  allL.push("");
}
allL.push(`## STAR 话术总库（结合本项目）`);
starScripts.forEach((s) => {
  allL.push(`### ${s.tag}`);
  allL.push(`- 面试官可能问：${s.ask}`);
  allL.push(`- 话术（STAR）：${s.star}`);
  allL.push("");
});
allL.push(`## 反问清单`);
reverseQuestions.forEach((q) => allL.push(`- ${q}`));
allL.push("");
writeFileSync(path.join(ROOT, "面试题库总库.md"), allL.join("\n"));
console.log("✓", path.join(ROOT, "面试题库总库.md"));

// README 索引
const rL = [];
rL.push(`# 分厂面试适配包总索引`);
rL.push("");
rL.push(`> 每个岗位 = 招聘网址 + 匹配简历(docx) + 面试题库 + 话术，一键可达。投递前请用对应分厂 docx 简历并以官网最新 JD 复核。`);
rL.push("");
rL.push(`## 第一梯队：五大模型厂`);
rL.push("");
rL.push(`| 公司 | 岗位 | 招聘网址 | 简历(docx) | 适配包(MD) |`);
rL.push(`|---|---|---|---|---|`);
for (const c of companies.filter((x) => ["bytedance-seed","tencent-hunyuan","zhipu","kimi","deepseek","deepseek-pm"].includes(x.id))) {
  rL.push(`| ${c.name} | ${c.objective} | ${c.url} | output/${docxFname(c)} | 分厂适配包/${packFname(c)} |`); 
}
rL.push("");
rL.push(`## 第二梯队：典型中小厂（≤20）`);
rL.push("");
rL.push(`| 公司 | 岗位 | 招聘网址 | 简历(docx) | 适配包(MD) |`);
rL.push(`|---|---|---|---|---|`);
for (const c of companies.filter((x) => !["bytedance-seed","tencent-hunyuan","zhipu","kimi","deepseek","deepseek-pm"].includes(x.id))) {
  rL.push(`| ${c.name} | ${c.objective} | ${c.url} | output/${docxFname(c)} | 分厂适配包/${packFname(c)} |`); 
}
rL.push("");
rL.push(`## 通用资料`);
rL.push(`- 题库总库：\`分厂适配包/面试题库总库.md\``);
rL.push(`- 招聘调研与适配策略：\`../招聘调研与适配策略.md\``);
rL.push(`- 提升效果与用户场景说明：\`../提升效果与用户场景说明.md\``);
rL.push(`- 生成器（改配置秒出全厂）：\`generate.js\`（简历）、\`gen-packs.js\`（适配包）`);
rL.push("");
writeFileSync(path.join(ROOT, "README.md"), rL.join("\n"));
console.log("✓", path.join(ROOT, "README.md"));
console.log(`\n适配包生成完成：${companies.length} 份 MD + 总库 + 索引`);
