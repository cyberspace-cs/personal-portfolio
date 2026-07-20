/* ============================================================
   LLM Finetune Studio · 前端逻辑
   - 与后端 FastAPI 通信；后端离线时自动降级为本地模拟
   ============================================================ */
const API = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
  ? 'http://localhost:8001/api' : 'http://localhost:8001/api';

let state = { method: 'LoRA', currentJob: null, poll: null, offline: false };

const $ = (id) => document.getElementById(id);
function toast(msg) { const t = $('toast'); t.textContent = msg; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 2200); }

async function api(path, opts = {}) {
  const cfg = { headers: { 'Content-Type': 'application/json' }, ...opts };
  if (cfg.body && typeof cfg.body === 'object') cfg.body = JSON.stringify(cfg.body);
  const r = await fetch(API + path, cfg);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}

/* ---------------- 初始化 ---------------- */
async function init() {
  bindUI();
  try {
    const meta = await api('/meta');
    $('baseModel').innerHTML = meta.base_models.map(m =>
      `<option value="${m.id}">${m.name} · ${m.params} · ${m.vendor}</option>`).join('');
    $('methodChips').innerHTML = meta.methods.map((m, i) =>
      `<button class="chip ${i === 0 ? 'active' : ''}" data-m="${m}">${m}</button>`).join('');
    $('kvModels').textContent = meta.base_models.length;
    bindMethodChips();
    await refreshJobs();
    document.querySelector('.badge-live').style.display = '';
  } catch (e) {
    state.offline = true;
    setupOfflineMeta();
    const b = document.querySelector('.badge-live');
    b.style.background = '#fff4e0'; b.style.borderColor = '#ffd8a8'; b.style.color = '#d97706';
    b.innerHTML = '<span class="dot" style="background:#d97706"></span> 演示模式（后端离线）';
  }
}

function setupOfflineMeta() {
  const models = [
    { id: 'hunyuan-7b', name: 'Hunyuan-7B', params: '7B', vendor: '腾讯混元' },
    { id: 'qwen2.5-7b', name: 'Qwen2.5-7B', params: '7B', vendor: '阿里通义' },
    { id: 'llama3.1-8b', name: 'Llama-3.1-8B', params: '8B', vendor: 'Meta' },
    { id: 'glm4-9b', name: 'GLM-4-9B', params: '9B', vendor: '智谱' },
  ];
  $('baseModel').innerHTML = models.map(m => `<option value="${m.id}">${m.name} · ${m.params} · ${m.vendor}</option>`).join('');
  $('methodChips').innerHTML = ['LoRA', 'QLoRA', 'Full-Finetune', 'DoRA'].map((m, i) =>
    `<button class="chip ${i === 0 ? 'active' : ''}" data-m="${m}">${m}</button>`).join('');
  $('kvModels').textContent = 4;
  bindMethodChips();
}

function bindMethodChips() {
  document.querySelectorAll('#methodChips .chip').forEach(c => c.addEventListener('click', () => {
    document.querySelectorAll('#methodChips .chip').forEach(x => x.classList.remove('active'));
    c.classList.add('active'); state.method = c.dataset.m;
  }));
}

function bindUI() {
  $('loraRank').oninput = e => $('vRank').textContent = e.target.value;
  $('loraAlpha').oninput = e => $('vAlpha').textContent = e.target.value;
  $('epochs').oninput = e => $('vEp').textContent = e.target.value;
  $('sampleBtn').onclick = fillSample;
  $('validateBtn').onclick = validate;
  $('startBtn').onclick = startTraining;
  $('inferBtn').onclick = runInference;
  $('pauseBtn').onclick = () => jobAction('pause');
  $('resumeBtn').onclick = () => jobAction('resume');
}

/* ---------------- 数据集 ---------------- */
function fillSample() {
  const rows = [
    { instruction: '解释什么是 LoRA', input: '', output: 'LoRA 通过在冻结的预训练权重旁注入低秩矩阵，仅训练极少量参数即可适配下游任务。' },
    { instruction: '把下面这句翻译成英文', input: '模型微调很有趣', output: 'Model fine-tuning is fun.' },
    { instruction: '总结这段话的要点', input: '大模型训练成本高，参数高效微调可显著降低显存占用。', output: '要点：参数高效微调可降低训练成本与显存占用。' },
    { instruction: '判断情感', input: '这次实验结果太棒了！', output: '正向' },
    { bad: 'this line is invalid json' },
  ];
  $('dataset').value = rows.map(r => JSON.stringify(r)).join('\n');
}

async function validate() {
  const raw = $('dataset').value.trim();
  if (!raw) return toast('请先输入数据集');
  let data;
  try {
    data = state.offline ? offlineValidate(raw) : await api('/datasets/validate', { method: 'POST', body: { raw } });
  } catch { data = offlineValidate(raw); }
  const s = data.stats;
  $('dsStats').innerHTML = `
    <div class="stat-grid">
      <div class="stat"><div class="n">${s.total}</div><div class="l">总样本</div></div>
      <div class="stat"><div class="n ok">${s.valid}</div><div class="l">有效样本</div></div>
      <div class="stat"><div class="n rose">${s.invalid}</div><div class="l">异常样本</div></div>
      <div class="stat"><div class="n">${s.avg_tokens}</div><div class="l">平均 token</div></div>
      <div class="stat"><div class="n">${s.p95_tokens}</div><div class="l">P95 token</div></div>
      <div class="stat"><div class="n brand">${(s.estimated_train_tokens / 1000).toFixed(1)}K</div><div class="l">训练 token 估算</div></div>
    </div>`;
  $('dsErrors').innerHTML = (data.errors || []).map(e => `<div class="e">第 ${e.line} 行：${e.reason}</div>`).join('');
  $('sampleCount').value = s.valid || 500;
  toast(`校验完成：${s.valid}/${s.total} 有效`);
}

function offlineValidate(raw) {
  const lines = raw.split('\n').filter(l => l.trim());
  const ok = [], errors = [], lens = [];
  lines.forEach((ln, i) => {
    try {
      const o = JSON.parse(ln);
      if (!o.output) { errors.push({ line: i + 1, reason: '缺少 output 字段' }); return; }
      if (!o.instruction && !o.input) { errors.push({ line: i + 1, reason: '缺少 instruction/input' }); return; }
      ok.push(o); lens.push(Math.floor((`${o.instruction || ''}${o.input || ''}${o.output || ''}`).length / 2.2));
    } catch { errors.push({ line: i + 1, reason: 'JSON 解析失败' }); }
  });
  const avg = lens.length ? Math.floor(lens.reduce((a, b) => a + b, 0) / lens.length) : 0;
  const p95 = lens.length ? [...lens].sort((a, b) => a - b)[Math.floor(0.95 * (lens.length - 1))] : 0;
  return { stats: { total: lines.length, valid: ok.length, invalid: lines.length - ok.length, avg_tokens: avg, p95_tokens: p95, estimated_train_tokens: lens.reduce((a, b) => a + b, 0) }, errors };
}

/* ---------------- 训练 ---------------- */
async function startTraining() {
  const body = {
    base_model: $('baseModel').value,
    method: state.method,
    sample_count: parseInt($('sampleCount').value) || 500,
    hparams: {
      lora_rank: +$('loraRank').value, lora_alpha: +$('loraAlpha').value, lora_dropout: 0.05,
      learning_rate: parseFloat($('lr').value) || 2e-4, epochs: +$('epochs').value,
      batch_size: +$('batch').value, max_seq_len: 1024, warmup_ratio: 0.03,
    },
  };
  if (state.offline) return startOfflineTraining(body);
  try {
    const r = await api('/finetune/start', { method: 'POST', body });
    state.currentJob = r.job_id;
    toast('训练已启动 · ' + r.total_steps + ' steps');
    startPolling();
    refreshJobs();
  } catch { startOfflineTraining(body); }
}

function startPolling() {
  clearInterval(state.poll);
  state.poll = setInterval(async () => {
    if (!state.currentJob) return;
    try {
      const j = await api('/finetune/' + state.currentJob);
      renderJob(j);
      if (j.status === 'done' || j.status === 'failed') { clearInterval(state.poll); refreshJobs(); }
    } catch { clearInterval(state.poll); }
  }, 500);
}

async function jobAction(act) {
  if (!state.currentJob || state.offline) return;
  try { await api('/finetune/' + state.currentJob + '/' + act, { method: 'POST' }); } catch {}
}

async function refreshJobs() {
  let jobs = [];
  try { jobs = state.offline ? offlineJobs : (await api('/finetune/jobs')).jobs; } catch { jobs = offlineJobs; }
  $('kvJobs').textContent = jobs.length;
  if (!jobs.length) { $('jobList').innerHTML = '<div class="empty">暂无训练任务</div>'; return; }
  $('jobList').innerHTML = jobs.map(j => `
    <div class="job ${j.id === state.currentJob ? 'active' : ''}" data-id="${j.id}">
      <span class="st ${j.status}"></span>
      <div class="info"><div class="n">${j.base_model} · ${j.method}</div>
        <div class="m">step ${j.step}/${j.total_steps} · loss ${j.metrics && j.metrics.length ? j.metrics[j.metrics.length - 1].loss : '—'}</div></div>
      <div class="pct">${Math.round((j.progress || 0) * 100)}%</div>
    </div>`).join('');
  document.querySelectorAll('.job').forEach(el => el.onclick = async () => {
    state.currentJob = el.dataset.id;
    if (state.offline) { renderJob(offlineJobs.find(x => x.id === el.dataset.id)); }
    else { try { renderJob(await api('/finetune/' + el.dataset.id)); startPolling(); } catch {} }
    refreshJobs();
  });
}

function renderJob(j) {
  $('mStep').textContent = j.step + '/' + j.total_steps;
  const last = j.metrics && j.metrics.length ? j.metrics[j.metrics.length - 1] : null;
  $('mLoss').textContent = last ? last.loss : '—';
  const stMap = { running: '训练中', paused: '已暂停', done: '已完成', failed: '失败', pending: '排队中' };
  $('mStatus').textContent = stMap[j.status] || j.status;
  $('mProg').style.width = Math.round((j.progress || 0) * 100) + '%';
  $('pauseBtn').style.display = j.status === 'running' ? '' : 'none';
  $('resumeBtn').style.display = j.status === 'paused' ? '' : 'none';
  drawChart(j.metrics || []);
  if (j.log && j.log.length) {
    $('log').innerHTML = j.log.map(l => `<div><span class="t">${l.t}</span>${l.msg}</div>`).join('');
    $('log').scrollTop = $('log').scrollHeight;
  }
}

/* ---------------- Canvas loss 曲线（自绘，无依赖） ---------------- */
function drawChart(metrics) {
  const cv = $('lossChart');
  const dpr = window.devicePixelRatio || 1;
  const W = cv.clientWidth, H = 220;
  cv.width = W * dpr; cv.height = H * dpr;
  const ctx = cv.getContext('2d'); ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, W, H);
  if (!metrics.length) return;
  const pad = { l: 40, r: 16, t: 14, b: 24 };
  const losses = metrics.map(m => m.loss);
  const lrs = metrics.map(m => m.lr);
  const maxL = Math.max(...losses), minL = Math.min(...losses);
  const maxLr = Math.max(...lrs) || 1;
  const n = metrics.length;
  const x = i => pad.l + (W - pad.l - pad.r) * (i / Math.max(1, n - 1));
  const yL = v => pad.t + (H - pad.t - pad.b) * (1 - (v - minL) / Math.max(1e-6, maxL - minL));
  const yLr = v => pad.t + (H - pad.t - pad.b) * (1 - v / maxLr);
  // 网格 + Y 轴刻度
  ctx.strokeStyle = 'rgba(255,255,255,.08)'; ctx.fillStyle = '#8ea0d0'; ctx.font = '10px monospace';
  for (let g = 0; g <= 4; g++) {
    const yy = pad.t + (H - pad.t - pad.b) * g / 4;
    ctx.beginPath(); ctx.moveTo(pad.l, yy); ctx.lineTo(W - pad.r, yy); ctx.stroke();
    ctx.fillText((maxL - (maxL - minL) * g / 4).toFixed(2), 4, yy + 3);
  }
  // LR 线（scaled）
  ctx.strokeStyle = '#3ddc9a'; ctx.lineWidth = 1.5; ctx.beginPath();
  lrs.forEach((v, i) => { const px = x(i), py = yLr(v); i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }); ctx.stroke();
  // Loss 线 + 渐变填充
  const grad = ctx.createLinearGradient(0, pad.t, 0, H - pad.b);
  grad.addColorStop(0, 'rgba(122,162,255,.35)'); grad.addColorStop(1, 'rgba(122,162,255,0)');
  ctx.beginPath(); losses.forEach((v, i) => { const px = x(i), py = yL(v); i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); });
  ctx.lineTo(x(n - 1), H - pad.b); ctx.lineTo(x(0), H - pad.b); ctx.closePath(); ctx.fillStyle = grad; ctx.fill();
  ctx.strokeStyle = '#7aa2ff'; ctx.lineWidth = 2; ctx.beginPath();
  losses.forEach((v, i) => { const px = x(i), py = yL(v); i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }); ctx.stroke();
  // 末点
  ctx.fillStyle = '#7aa2ff'; ctx.beginPath(); ctx.arc(x(n - 1), yL(losses[n - 1]), 3.5, 0, 7); ctx.fill();
}

/* ---------------- 推理 ---------------- */
async function runInference() {
  const prompt = $('prompt').value.trim();
  if (!prompt) return toast('请输入 prompt');
  $('cmpBox').style.display = 'grid';
  $('baseOut').textContent = '生成中…'; $('tunedOut').textContent = '生成中…';
  let data;
  try {
    data = state.offline ? offlineInfer(prompt) : await api('/inference', { method: 'POST', body: { prompt, job_id: state.currentJob } });
  } catch { data = offlineInfer(prompt); }
  $('baseOut').textContent = data.base.text;
  $('baseFoot').innerHTML = `⏱ ${data.base.latency}s · ${data.base.tokens} tok · ${data.base.throughput} tok/s`;
  if (data.tuned) {
    $('tunedOut').textContent = data.tuned.text;
    $('tunedFoot').innerHTML = `⏱ ${data.tuned.latency}s · ${data.tuned.tokens} tok · ${data.tuned.throughput} tok/s`;
  } else {
    $('tunedOut').textContent = '（该任务尚未完成训练，先启动并完成一个微调任务后再对比）';
    $('tunedFoot').textContent = '';
  }
}

/* ---------------- 离线模拟（后端不可用时） ---------------- */
let offlineJobs = [];
function startOfflineTraining(body) {
  const steps = Math.ceil(body.sample_count / body.hparams.batch_size) * body.hparams.epochs;
  const job = { id: Math.random().toString(36).slice(2, 10), base_model: body.base_model, method: body.method, status: 'running', step: 0, total_steps: steps, progress: 0, metrics: [], log: [{ t: now(), msg: `初始化 ${body.method} 微调 · 总步数=${steps}` }] };
  offlineJobs.unshift(job); state.currentJob = job.id; refreshJobs();
  const floor = 0.62 + 0.18 * Math.exp(-body.hparams.lora_rank / 16);
  clearInterval(state.poll);
  state.poll = setInterval(() => {
    if (job.step >= steps) { job.status = 'done'; job.log.push({ t: now(), msg: `训练完成 · eval_loss=${job.metrics[job.metrics.length - 1].loss}` }); renderJob(job); clearInterval(state.poll); refreshJobs(); return; }
    job.step++;
    const warm = Math.max(1, steps * 0.03);
    const lr = job.step <= warm ? body.hparams.learning_rate * job.step / warm : body.hparams.learning_rate * 0.5 * (1 + Math.cos(Math.PI * (job.step - warm) / (steps - warm)));
    const loss = +(2.4 * Math.exp(-3.2 * job.step / steps) + floor + (Math.random() - 0.5) * 0.05).toFixed(4);
    job.metrics.push({ step: job.step, loss, lr }); job.progress = job.step / steps;
    if (job.step % Math.max(1, Math.floor(steps / 8)) === 0) job.log.push({ t: now(), msg: `step ${job.step}/${steps} · loss=${loss}` });
    renderJob(job);
  }, 90);
  toast('演示模式训练已启动');
}
function offlineInfer(prompt) {
  const done = offlineJobs.find(j => j.id === state.currentJob && j.status === 'done');
  const mk = (tuned) => ({ text: tuned ? `【微调风格】针对「${prompt.slice(0, 30)}」：结论先行 + 结构化拆解 + 严格遵循指令模板。` : `关于「${prompt.slice(0, 30)}」，给出通用回答，覆盖基础概念但未领域优化。`, latency: +(Math.random() * 0.6 + 0.4).toFixed(3), tokens: Math.floor(Math.random() * 100 + 120), throughput: 0 });
  const b = mk(false); b.throughput = +(b.tokens / b.latency).toFixed(1);
  let t = null; if (done) { t = mk(true); t.throughput = +(t.tokens / t.latency).toFixed(1); }
  return { base: b, tuned: t };
}
function now() { return new Date().toTimeString().slice(0, 8); }

init();
