/* ============================================================
   RAG Knowledge Hub · 前端逻辑（完全离线、自包含、file:// 可用）
   内置硬编码语料 + 混合检索（BM25 + 向量余弦），真实可检索。
   ============================================================ */
(function () {
  'use strict';

  /* ---------------- 内置语料（4 个知识库） ---------------- */
  const CORPUS = [
    {
      id: 'kb1', name: '产品手册', docs: 1, enabled: true,
      chunks: [
        'RAG Hub 支持 PDF、Word、Markdown、TXT 以及网页 HTML 等多种文档格式的导入与解析。',
        '系统默认采用混合检索策略，将 BM25 关键词检索与向量语义检索的分数加权融合，兼顾精确匹配与语义泛化。',
        '用户可以在控制台选择单一知识库或跨多个知识库联合检索，并指定召回数量 top_k 与相关性阈值。',
        '对每一份答案，系统都会自动附上来源文档与片段编号，实现逐句可溯源。'
      ]
    },
    {
      id: 'kb2', name: '合规文档', docs: 1, enabled: true,
      chunks: [
        '所有知识库均按部门与项目维度开启权限隔离，用户只能检索到被显式授权的文档范围。',
        '涉及个人敏感信息（PII）的文档在入库前会经过脱敏与分级处理，禁止在公开知识库中存储明文身份证或手机号。',
        '跨境或跨租户的数据检索请求会被强制路由到对应合规域，确保数据不出域、审计留痕可查。',
        '管理员可在合规后台一键导出全部检索与访问日志，满足等保与内部审计要求。'
      ]
    },
    {
      id: 'kb3', name: '研发知识库', docs: 1, enabled: true,
      chunks: [
        '检索链路由摄入服务、混合检索引擎、重排模型与引用生成器四个模块组成，各模块通过内部 gRPC 通信。',
        '系统支持增量索引，新文档入库后秒级刷新倒排表与向量索引，无需全量重建。',
        '向量检索基于 HNSW 近似最近邻，配合 BM25 倒排，单请求 p95 延迟稳定控制在 80 毫秒以内。',
        '生成阶段采用流式输出，首字延迟低于 200 毫秒，可在答案生成的同时逐步呈现引用来源。'
      ]
    },
    {
      id: 'kb4', name: '内部 Wiki', docs: 1, enabled: true,
      chunks: [
        'RAG Hub 默认通过 uvicorn 在 8002 端口提供 FastAPI 服务，路径 /api/query 接收问答请求。',
        '生产环境建议将向量库与关系型元数据库分离部署，并使用 Redis 缓存热门查询结果以降低延迟。',
        '团队可通过 docker-compose 一键拉起完整后端，包含摄入 worker、检索服务与 Web 控制台。',
        '监控面板实时展示召回文档数、平均相关性与首字延迟等核心指标，便于容量评估。'
      ]
    }
  ];

  const SAMPLES = [
    'RAG 系统支持哪些文档格式？',
    '如何进行混合检索？',
    '知识库如何保证权限隔离？',
    '检索延迟大概多少？'
  ];

  const THRESHOLD = 0.12;

  /* ---------------- 工具：分词 / 统计 ---------------- */
  function tokenize(text) {
    text = String(text).toLowerCase();
    const toks = [];
    (text.match(/[a-z0-9]+|[\u4e00-\u9fff]+/g) || []).forEach(seg => {
      if (/[a-z0-9]/.test(seg[0])) toks.push(seg);
      else {
        for (const ch of seg) toks.push(ch);
        for (let i = 0; i < seg.length - 1; i++) toks.push(seg.slice(i, i + 2));
      }
    });
    return toks;
  }
  function count(arr) { const m = {}; arr.forEach(t => { m[t] = (m[t] || 0) + 1; }); return m; }
  function idf(term, cs) {
    const n = cs.length || 1;
    const df = cs.filter(c => c.tf[term]).length;
    return Math.log(1 + (n - df + 0.5) / (df + 0.5));
  }

  function activeChunks() {
    const out = [];
    CORPUS.forEach(kb => {
      if (!kb.enabled) return;
      kb.chunks.forEach((txt, i) => out.push({ kb: kb.name, idx: i, text: txt, tf: count(tokenize(txt)) }));
    });
    return out;
  }
  function bestSentence(text, qterms) {
    const sents = text.split(/(?<=[。！？.!?])/).map(s => s.trim()).filter(Boolean);
    if (sents.length <= 1) return text;
    const set = new Set(qterms);
    return sents.reduce((a, b) => {
      const sa = new Set(tokenize(a)).size ? tokenize(a).filter(t => set.has(t)).length : 0;
      const sb = new Set(tokenize(b)).size ? tokenize(b).filter(t => set.has(t)).length : 0;
      return sb > sa ? b : a;
    }, sents[0]);
  }

  /* ---------------- 混合检索引擎 ---------------- */
  function retrieve(q) {
    const cs = activeChunks();
    if (!cs.length) return { empty: true };
    const qt = tokenize(q);
    if (!qt.length) return { noquery: true };
    const qtf = count(qt);
    const avgLen = cs.reduce((a, c) => a + Object.values(c.tf).reduce((x, y) => x + y, 0), 0) / cs.length;

    let bmMax = 1e-9;
    const scored = cs.map(c => {
      let dot = 0;
      Object.keys(qtf).forEach(t => { if (c.tf[t]) { const w = idf(t, cs); dot += (qtf[t] * w) * (c.tf[t] * w); } });
      const qn = Math.sqrt(Object.keys(qtf).reduce((a, t) => a + (qtf[t] * idf(t, cs)) ** 2, 0)) || 1e-9;
      const cn = Math.sqrt(Object.keys(c.tf).reduce((a, t) => a + (c.tf[t] * idf(t, cs)) ** 2, 0)) || 1e-9;
      const cos = dot / (qn * cn);
      const len = Object.values(c.tf).reduce((x, y) => x + y, 0);
      let bm = 0;
      [...new Set(qt)].forEach(t => {
        if (c.tf[t]) { const d = c.tf[t] + 1.5 * (1 - 0.75 + 0.75 * len / avgLen); bm += idf(t, cs) * (c.tf[t] * 2.5) / d; }
      });
      bmMax = Math.max(bmMax, bm);
      return { c, cos, bm };
    });

    const bmRank = scored.filter(r => r.bm > 0).sort((a, b) => b.bm - a.bm);
    const cosRank = scored.filter(r => r.cos > 0).sort((a, b) => b.cos - a.cos);
    const fused = scored.map(r => ({ ...r, score: 0.5 * r.cos + 0.5 * (r.bm / bmMax) }))
                        .sort((a, b) => b.score - a.score);
    const top = fused[0].score;
    const retrieved = fused.filter(r => r.score >= THRESHOLD).slice(0, 4);
    const relevant = top >= THRESHOLD;
    const avg = Math.round(fused.slice(0, 4).reduce((a, r) => a + r.score, 0) / Math.min(4, fused.length) * 100);
    const lat = 56 + (q.length % 18); // 模拟首字延迟 <80ms

    return { bmRank, cosRank, fused, retrieved, relevant, top, avg, lat, qterms: qt };
  }

  /* ---------------- 渲染：知识库列表 ---------------- */
  function renderKB() {
    const box = $('#kbList');
    box.innerHTML = CORPUS.map(kb => `
      <div class="wo ${kb.enabled ? '' : 'off'}" data-id="${kb.id}">
        <div class="top">
          <span class="nm">${esc(kb.name)}</span>
          <span class="toggle">${kb.enabled ? '已启用' : '已停用'}</span>
        </div>
        <div class="meta">${kb.docs} 文档 · ${kb.chunks.length} 段分块</div>
      </div>`).join('');
    $$('#kbList .wo').forEach(el => {
      el.onclick = () => {
        const kb = CORPUS.find(k => k.id === el.dataset.id);
        kb.enabled = !kb.enabled;
        renderKB();
      };
    });
  }

  /* ---------------- 渲染：问题样本 chips ---------------- */
  function renderSamples() {
    const box = $('#qChips');
    box.innerHTML = SAMPLES.map(q => `<span class="opt">${esc(q)}</span>`).join('');
    $$('#qChips .opt').forEach(el => {
      el.onclick = () => { $('#q').value = el.textContent; runQuery(); };
    });
  }

  function cut(s, n) { return s.length > n ? s.slice(0, n) + '…' : s; }
  function hl(text, terms) {
    let out = esc(text);
    terms.forEach(t => {
      const e = esc(t);
      if (!e) return;
      out = out.replace(new RegExp('(' + e.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi'), '<mark>$1</mark>');
    });
    return out;
  }

  /* ---------------- 运行查询 ---------------- */
  async function runQuery() {
    const q = $('#q').value.trim();
    if (!q) { toast('请输入问题'); return; }
    const term = $('#term');
    term.innerHTML = '';
    const data = retrieve(q);
    if (data.empty) { toast('所有知识库已停用，请至少启用一个'); return; }
    if (data.noquery) { toast('请输入有效的问题'); return; }

    termLine(term, '> query: ' + q, 'acc');
    await wait(220);
    termLine(term, '> BM25 倒排检索 · 扫描 ' + activeChunks().length + ' 个分块 ...', 'dim');
    await wait(160);
    data.bmRank.slice(0, 3).forEach(r =>
      termLine(term, '  ✓ ' + r.c.kb + ' · ' + cut(r.c.text, 24) + '   (bm25 ' + r.bm.toFixed(2) + ')', 'ok'));
    await wait(160);
    termLine(term, '> 向量语义检索 (HNSW ANN) ...', 'dim');
    await wait(160);
    data.cosRank.slice(0, 3).forEach(r =>
      termLine(term, '  ✓ ' + r.c.kb + ' · ' + cut(r.c.text, 24) + '   (cos ' + r.cos.toFixed(2) + ')', 'ok'));
    await wait(160);
    termLine(term, '> 融合重排 + 阈值门控 (α=0.5) ...', 'dim');
    await wait(160);
    termLine(term, '  召回 ' + data.retrieved.length + ' 段 · 平均相关性 ' + data.avg + '% · 首字 ' + data.lat + 'ms', 'acc');
    await wait(140);
    if (data.relevant) termLine(term, '> 生成带引用的答案 + 溯源 ...', 'ok');
    else termLine(term, '> 最高相关性 ' + data.top.toFixed(2) + ' < 阈值，拒绝硬答', 'warn');

    renderAnswer(q, data);

    countUp($('#recallStat'), data.retrieved.length);
    countUp($('#relStat'), data.avg, { suffix: '%' });
    countUp($('#latStat'), data.lat, { suffix: ' ms' });
  }

  function renderAnswer(q, data) {
    const ans = $('#answer');
    const wrap = $('#citeWrap');
    const list = $('#citeList');

    if (!data.relevant) {
      ans.innerHTML = '<span class="gate no">⚠ 相关性不足 · 已拒绝硬答</span>' +
        '<div class="lead">未检索到足够可靠的依据（最高相关度 ' + data.top.toFixed(2) +
        ' &lt; 阈值 ' + THRESHOLD + '）。为避免臆测，建议补充相关文档或换一种问法后再提问。</div>';
      wrap.style.display = 'none';
      return;
    }

    const lead = '<div class="lead">根据检索到的 ' + data.retrieved.length +
      ' 个文档片段，综合整理如下：</div>';
    const body = data.retrieved.map((r, i) =>
      esc(bestSentence(r.c.text, data.qterms)) + ' <span class="cite-mk">[' + (i + 1) + ']</span>'
    ).join('<br/>');
    ans.innerHTML = '<span class="gate ok">✓ 已召回 ' + data.retrieved.length +
      ' 段 · 平均相关性 ' + data.avg + '% · 首字 ' + data.lat + 'ms</span>' + lead +
      '<div style="margin-top:8px">' + body + '</div>';

    list.innerHTML = data.retrieved.map((r, i) => `
      <div class="cite-item">
        <span class="ci-num">[${i + 1}]</span>
        <div style="flex:1;min-width:0">
          <div class="ci-doc">${esc(r.c.kb)} · 第 ${r.c.idx + 1} 段 · score ${r.score.toFixed(3)}</div>
          <div class="ci-snippet">${hl(r.c.text, data.qterms)}</div>
        </div>
      </div>`).join('');
    wrap.style.display = 'block';
  }

  /* ---------------- 流水线演示 ---------------- */
  const PIPE_DESC = [
    '解析文档 / 语义切分 chunk',
    'BM25 ⊕ 向量余弦融合打分',
    'Cross-Encoder 重排 + 上下文压缩',
    '逐句引用 + 来源溯源'
  ];

  /* ---------------- 初始化 ---------------- */
  function init() {
    renderKB();
    renderSamples();
    $('#askBtn').onclick = runQuery;
    $('#q').addEventListener('keydown', e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) runQuery(); });
    $('#runPipe').onclick = () =>
      window.runPipeline(['s1', 's2', 's3', 's4'], {
        delay: 520,
        onStep: (i) => window.setStageDesc('s' + (i + 1), PIPE_DESC[i])
      });
    // 首屏预填并自动演示一次，让页面非空
    setTimeout(runQuery, 500);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  window.boot();
})();
