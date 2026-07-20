/* ============================================================
   RAG Knowledge Hub · 前端逻辑（后端离线时降级为本地检索）
   ============================================================ */
const API = 'http://localhost:8002/api';
const THRESHOLD = 0.12;
let state = { offline: false, docs: [], chunks: [] };
const $ = (id) => document.getElementById(id);
function toast(m) { const t = $('toast'); t.textContent = m; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 2200); }

async function api(path, opts = {}) {
  const cfg = { headers: { 'Content-Type': 'application/json' }, ...opts };
  if (cfg.body && typeof cfg.body === 'object') cfg.body = JSON.stringify(cfg.body);
  const r = await fetch(API + path, cfg);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}

async function init() {
  $('ingestBtn').onclick = ingest;
  $('seedBtn').onclick = seed;
  $('askBtn').onclick = ask;
  window.__ask = ask;
  try { await refreshDocs(); }
  catch {
    state.offline = true;
    const b = document.querySelector('.badge-live');
    b.style.background = '#fff4e0'; b.style.borderColor = '#ffd8a8'; b.style.color = '#d97706';
    b.innerHTML = '<span class="dot" style="background:#d97706"></span> 演示模式（本地检索）';
  }
}

/* ---------------- 文档 ---------------- */
async function ingest() {
  const title = $('docTitle').value.trim() || '未命名文档';
  const text = $('docText').value.trim();
  if (!text) return toast('请输入文档内容');
  if (state.offline) { localIngest(title, text); }
  else { try { await api('/docs/ingest', { method: 'POST', body: { title, text } }); await refreshDocs(); } catch { state.offline = true; localIngest(title, text); } }
  $('docTitle').value = ''; $('docText').value = '';
  toast('入库成功');
}

async function seed() {
  if (!state.offline) { try { await api('/seed', { method: 'POST' }); await refreshDocs(); return toast('示例已灌入'); } catch { state.offline = true; } }
  SAMPLES.forEach(s => localIngest(s[0], s[1])); toast('示例已灌入');
}

async function refreshDocs() {
  const d = await api('/docs');
  state.docs = d.docs; renderDocs(d.docs, d.total_chunks);
}

function renderDocs(docs, totalChunks) {
  $('kvDocs').textContent = docs.length;
  $('kvChunks').textContent = totalChunks;
  $('chunkInfo').textContent = '共 ' + totalChunks + ' 个分块';
  if (!docs.length) { $('docList').innerHTML = '<div class="empty">知识库为空，先入库或灌入示例</div>'; return; }
  $('docList').innerHTML = docs.map(x => `
    <div class="doc">
      <span class="di"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/></svg></span>
      <div class="info"><div class="n">${esc(x.title)}</div><div class="m">${x.chunks} 分块 · ${x.chars} 字</div></div>
      <button class="del" data-id="${x.id}">删除</button>
    </div>`).join('');
  document.querySelectorAll('.doc .del').forEach(b => b.onclick = async () => {
    if (state.offline) { state.chunks = state.chunks.filter(c => c.doc_id !== b.dataset.id); state.docs = state.docs.filter(d => d.id !== b.dataset.id); renderDocs(state.docs, state.chunks.length); }
    else { try { await api('/docs/' + b.dataset.id, { method: 'DELETE' }); await refreshDocs(); } catch {} }
    toast('已删除');
  });
}

/* ---------------- 问答 ---------------- */
async function ask() {
  const q = $('qInput').value.trim();
  if (!q) return;
  addMsg('u', q); $('qInput').value = '';
  const loading = addMsg('a', '检索中…');
  let data;
  try { data = state.offline ? localQuery(q) : await api('/query', { method: 'POST', body: { question: q, top_k: 4 } }); }
  catch { state.offline = true; data = localQuery(q); }
  loading.remove();
  renderAnswer(q, data);
}

function renderAnswer(q, data) {
  const gate = data.relevant
    ? `<div class="gate ok">✓ 相关度 ${data.top_score} ≥ 阈值 ${data.threshold} · 置信 ${(data.confidence * 100).toFixed(0)}%</div>`
    : `<div class="gate no">⚠ 相关度 ${data.top_score} < 阈值 ${data.threshold} · 已拒绝硬答</div>`;
  const cites = (data.citations || []).filter(c => data.relevant).map((c, i) => `
    <div class="cite">
      <div class="ch"><span>[${i + 1}] ${esc(c.doc_title)} · 第 ${c.chunk_idx + 1} 块</span><span>score ${c.score}</span></div>
      <div class="cb">${highlight(c.text, q)}</div>
      <div class="score"><span>混合分 <b>${c.score}</b></span><span>余弦 ${c.cosine}</span><span>BM25 ${c.bm25}</span></div>
    </div>`).join('');
  const wrap = document.createElement('div');
  wrap.className = 'msg a';
  wrap.innerHTML = `<div class="bubble">${gate}${esc(data.answer)}${cites}</div>`;
  $('chat').appendChild(wrap); $('chat').scrollTop = $('chat').scrollHeight;
}

function addMsg(role, text) {
  const d = document.createElement('div');
  d.className = 'msg ' + role;
  d.innerHTML = `<div class="bubble">${esc(text)}</div>`;
  $('chat').appendChild(d); $('chat').scrollTop = $('chat').scrollHeight;
  return d;
}

function highlight(text, q) {
  const terms = [...new Set(tokenize(q))].filter(t => t.length >= 2).sort((a, b) => b.length - a.length).slice(0, 8);
  let out = esc(text);
  terms.forEach(t => { out = out.replace(new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi'), '<mark>$1</mark>'); });
  return out;
}
function esc(s) { return String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c])); }

/* ---------------- 本地检索引擎（离线降级，与后端同构） ---------------- */
function tokenize(text) {
  text = text.toLowerCase(); const toks = [];
  (text.match(/[a-z0-9]+|[\u4e00-\u9fff]+/g) || []).forEach(seg => {
    if (/[a-z0-9]/.test(seg[0])) toks.push(seg);
    else { for (const ch of seg) toks.push(ch); for (let i = 0; i < seg.length - 1; i++) toks.push(seg.slice(i, i + 2)); }
  });
  return toks;
}
function localIngest(title, text) {
  const id = Math.random().toString(36).slice(2, 10);
  const sents = text.split(/(?<=[。！？\.\!\?\n])/).map(s => s.trim()).filter(Boolean);
  const chunks = []; let cur = '';
  sents.forEach(s => { if ((cur + s).length <= 220) cur += s; else { if (cur) chunks.push(cur); cur = s; } });
  if (cur) chunks.push(cur);
  (chunks.length ? chunks : [text]).forEach((ct, i) => state.chunks.push({ doc_id: id, doc_title: title, idx: i, text: ct, tf: count(tokenize(ct)) }));
  state.docs.push({ id, title, chunks: chunks.length || 1, chars: text.length });
  renderDocs(state.docs, state.chunks.length);
}
function count(arr) { const m = {}; arr.forEach(t => m[t] = (m[t] || 0) + 1); return m; }
function idf(term) { const n = state.chunks.length || 1; const df = state.chunks.filter(c => c.tf[term]).length; return Math.log(1 + (n - df + 0.5) / (df + 0.5)); }
function localQuery(q) {
  if (!state.chunks.length) return { answer: '知识库为空，请先入库文档。', relevant: false, top_score: 0, threshold: THRESHOLD, confidence: 0, citations: [] };
  const qt = tokenize(q); const qtf = count(qt);
  const avgLen = state.chunks.reduce((a, c) => a + Object.values(c.tf).reduce((x, y) => x + y, 0), 0) / state.chunks.length;
  let bmMax = 1e-9; const raw = state.chunks.map(c => {
    let dot = 0; Object.keys(qtf).forEach(t => { if (c.tf[t]) { const w = idf(t); dot += (qtf[t] * w) * (c.tf[t] * w); } });
    const qn = Math.sqrt(Object.keys(qtf).reduce((a, t) => a + (qtf[t] * idf(t)) ** 2, 0)) || 1e-9;
    const cn = Math.sqrt(Object.keys(c.tf).reduce((a, t) => a + (c.tf[t] * idf(t)) ** 2, 0)) || 1e-9;
    const cos = dot / (qn * cn);
    const len = Object.values(c.tf).reduce((x, y) => x + y, 0);
    let bm = 0; [...new Set(qt)].forEach(t => { if (c.tf[t]) { const d = c.tf[t] + 1.5 * (1 - 0.75 + 0.75 * len / avgLen); bm += idf(t) * (c.tf[t] * 2.5) / d; } });
    bmMax = Math.max(bmMax, bm); return { c, cos, bm };
  });
  const scored = raw.map(r => ({ ...r, score: 0.6 * r.cos + 0.4 * (r.bm / bmMax) })).sort((a, b) => b.score - a.score).slice(0, 4);
  const top = scored[0].score; const relevant = top >= THRESHOLD;
  const citations = scored.map(s => ({ doc_title: s.c.doc_title, chunk_idx: s.c.idx, text: s.c.text, score: +s.score.toFixed(4), cosine: +s.cos.toFixed(4), bm25: +s.bm.toFixed(4) }));
  let answer;
  if (relevant) {
    const sents = scored[0].c.text.split(/(?<=[。！？\.\!\?])/); const qs = new Set(qt);
    const best = sents.reduce((a, b) => (new Set(tokenize(b)).size && [...new Set(tokenize(b))].filter(t => qs.has(t)).length > [...new Set(tokenize(a))].filter(t => qs.has(t)).length ? b : a), sents[0] || scored[0].c.text);
    answer = '根据知识库检索结果：\n' + best.trim();
  } else answer = `未检索到足够可靠的依据（最高相关度 ${top.toFixed(4)} < 阈值 ${THRESHOLD}）。为避免臆测，建议补充相关文档后再提问。`;
  return { answer, relevant, top_score: +top.toFixed(4), threshold: THRESHOLD, confidence: Math.min(1, top / (THRESHOLD * 3)), citations };
}

const SAMPLES = [
  ['RAG 检索增强生成简介', 'RAG（Retrieval-Augmented Generation，检索增强生成）是一种将信息检索与大语言模型生成结合的架构。它先从外部知识库中检索与问题相关的文档片段，再把这些片段作为上下文交给大模型生成答案。RAG 的核心优势是缓解大模型幻觉、支持知识实时更新、并可提供答案的引用来源，实现可溯源问答。典型链路包括：文档分块、向量化、相似度检索、重排序、以及带上下文的生成。'],
  ['向量检索与混合检索', '向量检索通过将文本编码为稠密向量，用余弦相似度衡量语义相关性，擅长捕捉同义与语义匹配。关键词检索（如 BM25）基于词频与逆文档频率，擅长精确术语匹配。混合检索（Hybrid Search）将向量分数与关键词分数加权融合，兼顾语义泛化与精确匹配，是企业级 RAG 的主流方案。检索后通常再接一个重排序模型进一步提升 Top-K 的精度。'],
  ['如何降低大模型幻觉', '降低幻觉的常见手段包括：引入 RAG 提供事实依据、设置相关度阈值门控拒绝硬答、要求模型引用来源、使用反思机制二次校验答案、以及对关键结论做事实核查。当检索到的证据相关度低于阈值时，系统应主动回答暂无可靠依据，而非编造答案。'],
];

init();
