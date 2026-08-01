// 北大风格简历批量生成器（22 份分厂适配包）
// 复用 companies.js / data.js 的内容，仅将版式与字体改为「北京大学」风格：
//  - 正文宋体、标题微软雅黑
//  - 蓝色细分割线章节标题
//  - 「·」项目符号
//  - 页脚招聘入口 + 复核提示
// 联系方式使用真实信息（与 master 简历一致）。
import { Document, Packer, Paragraph, TextRun, AlignmentType, BorderStyle, Footer } from "docx";
import { writeFileSync, mkdirSync } from "fs";
import { companies } from "./companies.js";
import { engineer, pm } from "./data.js";

// —— 真实联系方式（覆盖 data.js 中的占位符）——
const contact = {
  name: "【姓名】",
  phone: "【电话】",
  email: "【邮箱】",
  base: "北京 · 北京大学软件工程硕士",
  links: "GitHub: github.com/cyberspace-cs · 作品集: 见个人网站",
};

const OUT = "output-peking";
mkdirSync(OUT, { recursive: true });

const DEFAULT_PHASE_ORDER = ["A", "B", "C", "D", "E", "F", "G", "H"];
const PM_BASE_SKILLS = ["Agent 产品定义", "竞品分析", "指标设计(A/B/四率)", "低代码/生态", "RAG 可解释", "多 Agent 陪练", "PRD", "技术同频"];

// —— 北大风格字体 / 颜色 ——
const BODY = { ascii: "SimSun", eastAsia: "宋体" };            // 宋体正文
const HEAD = { ascii: "Microsoft YaHei", eastAsia: "微软雅黑" }; // 微软雅黑标题
const BLUE = "1E3A8A";
const GRAY = "595959";

function run(text, opts = {}) {
  return new TextRun({
    text,
    font: opts.head ? HEAD : BODY,
    size: opts.size ?? 21,      // 默认 10.5pt（半磅）
    bold: opts.bold ?? false,
    color: opts.color ?? "000000",
    italics: opts.italic ?? false,
  });
}

function heading(text) {
  return new Paragraph({
    spacing: { before: 220, after: 60 },
    border: { bottom: { color: BLUE, space: 1, style: BorderStyle.SINGLE, size: 6 } },
    children: [run(text, { head: true, size: 24, bold: true, color: BLUE })],
  });
}

function bullet(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 20, after: 20 },
    indent: { left: 320, hanging: 200 },
    children: [run("· ", { bold: true, color: BLUE }), run(text, opts)],
  });
}

function para(text, opts = {}) {
  return new Paragraph({ spacing: { before: 40, after: 40 }, children: [run(text, opts)] });
}

function entryTitle(text) {
  return new Paragraph({
    spacing: { before: 60, after: 20 },
    children: [run(text, { head: true, size: 22, bold: true, color: "1F2937" })],
  });
}

function makeFooter(c) {
  return new Footer({
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 40 },
        border: { top: { color: "BFBFBF", space: 4, style: BorderStyle.SINGLE, size: 4 } },
        children: [run(`招聘入口：${c.url}　|　投递前请以对应分厂官网最新 JD 复核本简历`, { size: 15, color: GRAY })],
      }),
    ],
  });
}

function reorder(arr, order) {
  const set = new Set(order);
  return [...arr.filter((x) => set.has(x)), ...arr.filter((x) => !set.has(x))];
}

// —— 工程师版式 ——
function buildEngineer(c) {
  const e = engineer;
  const techOrder = c.techOrder || Object.keys(e.techStack);
  const cats = reorder(Object.keys(e.techStack), techOrder);
  const phases = reorder(DEFAULT_PHASE_ORDER, c.phaseOrder || DEFAULT_PHASE_ORDER);
  const children = [];

  // 头部
  children.push(new Paragraph({ spacing: { after: 20 }, children: [run(contact.name, { head: true, size: 44, bold: true, color: BLUE })] }));
  children.push(new Paragraph({ spacing: { after: 20 }, children: [run(`求职意向：${c.objective}`, { size: 22, bold: true })] }));
  children.push(new Paragraph({ spacing: { after: 120 }, children: [run(`${contact.base}　|　${contact.phone}　|　${contact.email}　|　${contact.links}`, { size: 19, color: GRAY })] }));

  // 个人总结
  children.push(heading("个人总结"));
  children.push(para((c.summaryHook || "") + e.summary));

  // 技术栈
  children.push(heading("技术栈"));
  for (const cat of cats) {
    children.push(new Paragraph({
      spacing: { before: 30, after: 30 },
      children: [run(`${cat}：`, { bold: true }), run(e.techStack[cat].join("、"))],
    }));
  }

  // 核心能力与方法论
  children.push(heading("核心能力与方法论"));
  for (const m of e.方法论) children.push(bullet(m));

  // 项目经历
  children.push(heading("项目经历"));
  children.push(new Paragraph({
    spacing: { before: 40, after: 40 },
    children: [run(e.project.title, { bold: true }), run("    " + e.project.meta, { size: 18, color: "666666" })],
  }));
  for (const k of phases) {
    const p = e.project.phases[k];
    if (!p) continue;
    children.push(new Paragraph({
      spacing: { before: 60, after: 20 },
      children: [run(`阶段 ${k}：${p.title}`, { head: true, size: 22, bold: true, color: BLUE })],
    }));
    for (const b of p.bullets) children.push(bullet(b));
  }

  // 量化验证
  children.push(heading("量化验证"));
  for (const q of e.project.quant) children.push(bullet(q));

  // 工程实践
  children.push(heading("工程实践"));
  for (const g of e.工程实践) children.push(bullet(g));

  // 个人作品集
  children.push(heading("个人作品集网站"));
  children.push(new Paragraph({
    spacing: { before: 40, after: 40 },
    children: [run(e.web.title, { bold: true }), run("    " + e.web.meta, { size: 18, color: "666666" })],
  }));
  for (const b of e.web.bullets) children.push(bullet(b));

  // 岗位匹配关键词
  if (c.keywords && c.keywords.length) {
    children.push(new Paragraph({
      spacing: { before: 120, after: 40 },
      children: [run("岗位匹配关键词：", { bold: true, color: "C0392B" }), run(c.keywords.join(" / "), { color: "C0392B" })],
    }));
  }

  return new Document({
    creator: contact.name,
    title: `${contact.name}-${c.name}-北大风格`,
    sections: [{
      properties: { page: { margin: { top: 800, bottom: 800, left: 900, right: 900 } } },
      footers: { default: makeFooter(c) },
      children,
    }],
  });
}

// —— 产品/PM 版式 ——
function buildPm(c) {
  const p = pm;
  const phases = reorder(DEFAULT_PHASE_ORDER, c.phaseOrder || DEFAULT_PHASE_ORDER);
  const children = [];

  children.push(new Paragraph({ spacing: { after: 20 }, children: [run(contact.name, { head: true, size: 44, bold: true, color: BLUE })] }));
  children.push(new Paragraph({ spacing: { after: 20 }, children: [run(`求职意向：${c.objective}`, { size: 22, bold: true })] }));
  children.push(new Paragraph({ spacing: { after: 120 }, children: [run(`${contact.base}　|　${contact.phone}　|　${contact.email}　|　${contact.links}`, { size: 19, color: GRAY })] }));

  children.push(heading("个人总结"));
  children.push(para((c.summaryHook || "") + p.summary));

  children.push(heading("核心能力"));
  for (const m of p.核心能力) children.push(bullet(m));

  children.push(heading("项目经历（产品视角）"));
  children.push(new Paragraph({
    spacing: { before: 40, after: 40 },
    children: [run(p.project.title, { bold: true }), run("    " + p.project.meta, { size: 18, color: "666666" })],
  }));
  for (const k of phases) {
    const ph = p.project.phases[k];
    if (!ph) continue;
    children.push(new Paragraph({
      spacing: { before: 60, after: 20 },
      children: [run(`阶段 ${k}：${ph.title}`, { head: true, size: 22, bold: true, color: BLUE })],
    }));
    for (const b of ph.bullets) children.push(bullet(b));
  }

  children.push(heading("量化验证"));
  for (const q of p.project.quant) children.push(bullet(q));

  children.push(heading("个人作品集网站"));
  children.push(new Paragraph({
    spacing: { before: 40, after: 40 },
    children: [run(p.web.title, { bold: true }), run("    " + p.web.meta, { size: 18, color: "666666" })],
  }));
  for (const b of p.web.bullets) children.push(bullet(b));

  children.push(heading("行业洞察"));
  for (const m of p.行业洞察) children.push(bullet(m));

  const skills = [...(c.keywords || []), ...PM_BASE_SKILLS];
  children.push(new Paragraph({
    spacing: { before: 120, after: 40 },
    children: [run("岗位匹配技能：", { bold: true, color: "C0392B" }), run(skills.join(" / "), { color: "C0392B" })],
  }));

  return new Document({
    creator: contact.name,
    title: `${contact.name}-${c.name}-北大风格`,
    sections: [{
      properties: { page: { margin: { top: 800, bottom: 800, left: 900, right: 900 } } },
      footers: { default: makeFooter(c) },
      children,
    }],
  });
}

async function main() {
  let n = 0;
  for (const c of companies) {
    const doc = c.direction === "pm" ? buildPm(c) : buildEngineer(c);
    const file = `${OUT}/${c.name}-${c.direction === "pm" ? "产品经理" : "Agent应用开发"}-北大风格.docx`;
    const buf = await Packer.toBuffer(doc);
    writeFileSync(file, buf);
    console.log("生成:", file);
    n++;
  }
  console.log(`\n完成：共生成 ${n} 份北大风格分厂简历 -> ${OUT}/`);
}

main().catch((e) => { console.error(e); process.exit(1); });
