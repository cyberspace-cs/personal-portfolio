import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, BorderStyle, WidthType, Footer } from "docx";
import { writeFileSync, mkdirSync } from "fs";
import { contact, engineer, pm } from "./data.js";
import { companies } from "./companies.js";

const OUT = "output";
mkdirSync(OUT, { recursive: true });

const DEFAULT_PHASE_ORDER = ["A", "B", "C", "D", "E", "F", "G", "H"];
const PM_BASE_SKILLS = ["Agent 产品定义", "竞品分析", "指标设计(A/B/四率)", "低代码/生态", "RAG 可解释", "多 Agent 陪练", "PRD", "技术同频"];

// ---------- 样式辅助 ----------
const FONT = "Microsoft YaHei";
const sectionBorder = { bottom: { color: "999999", space: 1, style: BorderStyle.SINGLE, size: 6 } };

function heading(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 160, after: 60 },
    border: sectionBorder,
    children: [new TextRun({ text, bold: true, size: 26, font: FONT, color: "1F4E79" })],
  });
}

function para(runs, opts = {}) {
  return new Paragraph({ spacing: { after: 40 }, children: runs, ...opts });
}

function bullet(text, opts = {}) {
  return new Paragraph({
    bullet: { level: 0 },
    spacing: { after: 30 },
    children: [new TextRun({ text, size: 21, font: FONT, ...opts })],
  });
}

function run(text, opts = {}) {
  return new TextRun({ text, size: 21, font: FONT, ...opts });
}

function reorder(arr, order) {
  const set = new Set(order);
  const pri = arr.filter((x) => set.has(x));
  const rest = arr.filter((x) => !set.has(x));
  return [...pri, ...rest];
}

// 页脚：招聘入口 + 复核提示
function makeFooter(c) {
  return {
    default: new Footer({
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { color: "CCCCCC", space: 2, style: BorderStyle.SINGLE, size: 4 } },
          children: [
            new TextRun({ text: `招聘入口：${c.url}`, size: 16, font: FONT, color: "888888" }),
            new TextRun({ text: `　|　投递前请用对应分厂适配简历并以官网最新 JD 复核`, size: 16, font: FONT, color: "888888" }),
          ],
        }),
      ],
    }),
  };
}

// ---------- 按方向构建文档 ----------
function buildEngineerDoc(c) {
  const techOrder = c.techOrder || Object.keys(engineer.techStack);
  const cats = reorder(Object.keys(engineer.techStack), techOrder);

  const children = [];
  // 头部
  children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 20 }, children: [new TextRun({ text: contact.name, bold: true, size: 36, font: FONT })] }));
  children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 20 }, children: [run(`${contact.phone}  |  ${contact.email}  |  ${contact.base}`)] }));
  children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [run(contact.links, { size: 18, color: "555555" })] }));

  // 求职意向
  children.push(para([run("求职意向：", { bold: true }), run(c.objective)], { spacing: { after: 80 } }));

  // 个人总结
  children.push(heading("个人总结"));
  children.push(para([run((c.summaryHook || "") + engineer.summary)]));

  // 技术栈
  children.push(heading("技术栈"));
  cats.forEach((cat) => {
    children.push(
      para([
        run(cat + "：", { bold: true }),
        run(engineer.techStack[cat].join(" · ")),
      ])
    );
  });

  // 核心能力 / 方法论
  children.push(heading("核心能力与方法论"));
  engineer.方法论.forEach((t) => children.push(bullet(t)));

  // 项目经历
  children.push(heading("项目经历"));
  children.push(para([run(engineer.project.title, { bold: true }), run("    " + engineer.project.meta, { size: 18, color: "666666" })]));
  const phases = reorder(DEFAULT_PHASE_ORDER, c.phaseOrder || DEFAULT_PHASE_ORDER);
  phases.forEach((k) => {
    const p = engineer.project.phases[k];
    if (!p) return;
    children.push(para([run(`Phase ${k}：${p.title}`, { bold: true, color: "1F4E79" })], { spacing: { before: 60, after: 20 } }));
    p.bullets.forEach((b) => children.push(bullet(b)));
  });

  // 量化验证
  children.push(heading("量化验证"));
  engineer.project.quant.forEach((t) => children.push(bullet(t)));

  // 工程实践
  children.push(heading("工程实践"));
  engineer.工程实践.forEach((t) => children.push(bullet(t)));

  // 作品集
  children.push(heading("个人作品集网站"));
  children.push(para([run(engineer.web.title, { bold: true }), run("    " + engineer.web.meta, { size: 18, color: "666666" })]));
  engineer.web.bullets.forEach((b) => children.push(bullet(b)));

  // 岗位匹配关键词
  if (c.keywords && c.keywords.length) {
    children.push(para([run("岗位匹配关键词：", { bold: true, color: "C00000" }), run(c.keywords.join(" · "), { color: "C00000" })]));
  }

  return new Document({
    creator: contact.name,
    title: `${contact.name} - ${c.objective}`,
    sections: [{ properties: { page: { margin: { top: 800, bottom: 800, left: 900, right: 900 } } }, footers: makeFooter(c), children }],
  });
}

function buildPmDoc(c) {
  const children = [];
  children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 20 }, children: [new TextRun({ text: contact.name, bold: true, size: 36, font: FONT })] }));
  children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 20 }, children: [run(`${contact.phone}  |  ${contact.email}  |  ${contact.base}`)] }));
  children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [run(contact.links, { size: 18, color: "555555" })] }));

  children.push(para([run("求职意向：", { bold: true }), run(c.objective)], { spacing: { after: 80 } }));

  children.push(heading("个人总结"));
  children.push(para([run((c.summaryHook || "") + pm.summary)]));

  children.push(heading("核心能力"));
  pm.核心能力.forEach((t) => children.push(bullet(t)));

  children.push(heading("项目经历（产品视角）"));
  children.push(para([run(pm.project.title, { bold: true }), run("    " + pm.project.meta, { size: 18, color: "666666" })]));
  const phases = reorder(DEFAULT_PHASE_ORDER, c.phaseOrder || DEFAULT_PHASE_ORDER);
  phases.forEach((k) => {
    const p = pm.project.phases[k];
    if (!p) return;
    children.push(para([run(`Phase ${k}：${p.title}`, { bold: true, color: "1F4E79" })], { spacing: { before: 60, after: 20 } }));
    p.bullets.forEach((b) => children.push(bullet(b)));
  });

  children.push(heading("量化验证"));
  pm.project.quant.forEach((t) => children.push(bullet(t)));

  children.push(heading("个人作品集网站"));
  children.push(para([run(pm.web.title, { bold: true }), run("    " + pm.web.meta, { size: 18, color: "666666" })]));
  pm.web.bullets.forEach((b) => children.push(bullet(b)));

  children.push(heading("行业洞察"));
  pm.行业洞察.forEach((t) => children.push(bullet(t)));

  const skills = [...(c.keywords || []), ...PM_BASE_SKILLS];
  children.push(para([run("岗位匹配技能：", { bold: true, color: "C00000" }), run(skills.join(" · "), { color: "C00000" })]));

  return new Document({
    creator: contact.name,
    title: `${contact.name} - ${c.objective}`,
    sections: [{ properties: { page: { margin: { top: 800, bottom: 800, left: 900, right: 900 } } }, footers: makeFooter(c), children }],
  });
}

// ---------- 批量生成 ----------
const files = [];
for (const c of companies) {
  const doc = c.direction === "pm" ? buildPmDoc(c) : buildEngineerDoc(c);
  const fname = `${OUT}/${c.name}-${c.direction === "pm" ? "产品经理" : "Agent应用开发"}.docx`;
  const buf = await Packer.toBuffer(doc);
  writeFileSync(fname, buf);
  files.push(fname);
  console.log("✓", fname);
}
console.log(`\n生成完成：${files.length} 份`);
