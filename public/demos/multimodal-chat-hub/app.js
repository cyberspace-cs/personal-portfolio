/* Multimodal Chat Hub · 前端逻辑
   - 文本→后端情感/意图；图片→Canvas 提取视觉特征→后端理解；语音→Web Speech API */
const API = 'http://localhost:8004/api';
let state = { offline: false, pendingImage: null };
const $ = (id) => document.getElementById(id);
function toast(m) { const t = $('toast'); t.textContent = m; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 2000); }
function esc(s) { return String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c])); }

async function api(path, body) {
  const r = await fetch(API + path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error('HTTP');
  return r.json();
}

function init() {
  $('sendBtn').onclick = send; window.__send = send;
  $('imgBtn').onclick = () => $('fileInput').click();
  $('fileInput').onchange = onImage;
  $('rmImg').onclick = () => { state.pendingImage = null; $('preview').style.display = 'none'; };
  $('micBtn').onclick = toggleMic;
  fetch(API + '/health').catch(() => {
    state.offline = true;
    const b = document.querySelector('.badge-live');
    b.style.background = '#fff4e0'; b.style.borderColor = '#ffd8a8'; b.style.color = '#d97706';
    b.innerHTML = '<span class="dot" style="background:#d97706"></span> 演示模式（本地推理）';
  });
}

/* ---------------- 图片：Canvas 视觉特征提取 ---------------- */
function onImage(e) {
  const file = e.target.files[0]; if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    const img = new Image();
    img.onload = () => {
      const feat = extractFeatures(img);
      state.pendingImage = { dataUrl: ev.target.result, features: feat };
      $('previewImg').src = ev.target.result; $('preview').style.display = 'block';
      toast('图片已解析，主色：' + '#' + feat.dominant.map(c => c.toString(16).padStart(2, '0')).join(''));
    };
    img.src = ev.target.result;
  };
  reader.readAsDataURL(file);
  e.target.value = '';
}

function extractFeatures(img) {
  const cv = $('cv'); const W = 64, H = Math.max(1, Math.round(64 * img.height / img.width));
  cv.width = W; cv.height = H;
  const ctx = cv.getContext('2d'); ctx.drawImage(img, 0, 0, W, H);
  const data = ctx.getImageData(0, 0, W, H).data;
  let r = 0, g = 0, b = 0, lum = 0; const n = W * H;
  const gray = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const R = data[i * 4], G = data[i * 4 + 1], B = data[i * 4 + 2];
    r += R; g += G; b += B;
    const y = 0.299 * R + 0.587 * G + 0.114 * B; gray[i] = y; lum += y;
  }
  // 边缘密度：相邻像素梯度均值（Sobel 简化）
  let edge = 0, cnt = 0;
  for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) {
    const i = y * W + x;
    const gx = Math.abs(gray[i - 1] - gray[i + 1]);
    const gy = Math.abs(gray[i - W] - gray[i + W]);
    edge += (gx + gy); cnt++;
  }
  return {
    dominant: [Math.round(r / n), Math.round(g / n), Math.round(b / n)],
    brightness: +(lum / n / 255).toFixed(3),
    edge_density: +Math.min(1, (edge / cnt) / 120).toFixed(3),
    aspect: +(img.width / img.height).toFixed(2),
    width: img.width, height: img.height,
  };
}

/* ---------------- 发送 ---------------- */
async function send() {
  const text = $('textInput').value.trim();
  const img = state.pendingImage;
  if (!text && !img) return;
  addUserMsg(text, img);
  $('textInput').value = '';
  state.pendingImage = null; $('preview').style.display = 'none';

  const body = { text, image_features: img ? img.features : null };
  let data;
  try { data = state.offline ? localChat(body) : await api('/chat', body); }
  catch { state.offline = true; data = localChat(body); }
  addBotMsg(data);
  renderAnalysis(data, img);
}

function addUserMsg(text, img) {
  const d = document.createElement('div'); d.className = 'msg u';
  d.innerHTML = (img ? `<img class="thumb" src="${img.dataUrl}">` : '') + (text ? `<div class="bubble">${esc(text)}</div>` : '');
  $('chat').appendChild(d); scroll();
}
function addBotMsg(data) {
  const d = document.createElement('div'); d.className = 'msg a';
  const tags = `<div class="meta-tags"><span class="tag">意图·${data.intent}</span><span class="tag senti-${data.sentiment.label}">情感·${data.sentiment.label}</span>${data.vision ? '<span class="tag">视觉·' + esc(data.vision.dominant_name) + '</span>' : ''}</div>`;
  d.innerHTML = `<div class="bubble">${esc(data.reply)}</div>${tags}<span class="speak" data-say="${esc(data.reply)}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5 6 9H2v6h4l5 4V5Z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/></svg>朗读</span>`;
  $('chat').appendChild(d); scroll();
  d.querySelector('.speak').onclick = () => speak(data.reply);
}
function scroll() { $('chat').scrollTop = $('chat').scrollHeight; }

function renderAnalysis(data, img) {
  const s = data.sentiment;
  let html = `
    <div class="feat-row">
      <div class="feat"><div class="n">${data.intent}</div><div class="l">意图</div></div>
      <div class="feat"><div class="n" style="color:${s.label === '积极' ? 'var(--ok)' : s.label === '消极' ? 'var(--rose)' : 'var(--ink-3)'}">${s.label}</div><div class="l">情感</div></div>
      <div class="feat"><div class="n">${(s.confidence * 100).toFixed(0)}%</div><div class="l">置信度</div></div>
    </div>`;
  if (s.hits && s.hits.length) html += `<div style="font-size:12px;color:var(--ink-3);margin-bottom:12px">命中情感词：${s.hits.map(h => `<span class="tag senti-${h.polarity === 'pos' ? '积极' : '消极'}">${esc(h.word)}</span>`).join(' ')}</div>`;
  if (data.vision && img) {
    const f = img.features;
    html += `
      <div class="swatch" style="background:rgb(${f.dominant.join(',')})"></div>
      <div class="feat-row">
        <div class="feat"><div class="n">${(f.brightness * 100).toFixed(0)}%</div><div class="l">亮度</div></div>
        <div class="feat"><div class="n">${(f.edge_density * 100).toFixed(0)}%</div><div class="l">边缘密度</div></div>
        <div class="feat"><div class="n">${f.aspect}</div><div class="l">宽高比</div></div>
      </div>
      <div style="font-size:13px;color:var(--ink-2)">${esc(data.vision.caption)}</div>
      <div class="meta-tags" style="margin-top:10px">${data.vision.labels.map(l => `<span class="tag">${esc(l)}</span>`).join('')}</div>`;
  }
  $('analysis').innerHTML = html;
}

/* ---------------- 语音：Web Speech API ---------------- */
function speak(text) {
  if (!('speechSynthesis' in window)) return toast('当前浏览器不支持语音合成');
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text); u.lang = 'zh-CN'; u.rate = 1.05;
  speechSynthesis.speak(u);
}
let recog = null, recording = false;
function toggleMic() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return toast('当前浏览器不支持语音识别（建议 Chrome）');
  if (recording) { recog && recog.stop(); return; }
  recog = new SR(); recog.lang = 'zh-CN'; recog.interimResults = false;
  recog.onstart = () => { recording = true; $('micBtn').classList.add('rec'); toast('请说话…'); };
  recog.onresult = e => { $('textInput').value = e.results[0][0].transcript; };
  recog.onerror = () => toast('语音识别出错');
  recog.onend = () => { recording = false; $('micBtn').classList.remove('rec'); };
  recog.start();
}

/* ---------------- 本地降级推理 ---------------- */
const POS = ['喜欢', '开心', '棒', '好', '赞', '满意', '优秀', '爱', '惊喜', '完美', '厉害', '感谢', '太好了', '不错'];
const NEG = ['讨厌', '难过', '差', '糟', '失望', '生气', '垃圾', '烦', '崩溃', '累', '痛苦', '不好', '问题'];
function localSentiment(t) {
  let score = 0; const hits = [];
  POS.forEach(w => { if (t.includes(w)) { const neg = t.includes('不' + w) || t.includes('没' + w); score += neg ? -1 : 1; hits.push({ word: w, polarity: neg ? 'neg' : 'pos' }); } });
  NEG.forEach(w => { if (t.includes(w)) { score -= 1; hits.push({ word: w, polarity: 'neg' }); } });
  const label = score > 0 ? '积极' : score < 0 ? '消极' : '中性';
  return { label, score, confidence: Math.min(1, Math.abs(score) / 3 + 0.34), hits: hits.slice(0, 8) };
}
function localIntent(t) {
  if (/[?？]|什么|怎么|为什么|如何/.test(t)) return '提问';
  if (/帮我|请|能不能|可以/.test(t)) return '请求';
  if (/你好|hi|hello|在吗/i.test(t)) return '问候';
  if (/谢谢|感谢|thanks/i.test(t)) return '致谢';
  return '陈述';
}
const COLORS = [[[220, 40, 40], '红色'], [[240, 140, 30], '橙色'], [[240, 210, 40], '黄色'], [[60, 180, 75], '绿色'], [[40, 120, 220], '蓝色'], [[130, 70, 200], '紫色'], [[240, 240, 240], '白/浅色'], [[30, 30, 30], '黑/深色'], [[150, 150, 150], '灰色']];
function nameColor(rgb) { let best = '未知', bd = 1e9; COLORS.forEach(([c, n]) => { const d = (rgb[0] - c[0]) ** 2 + (rgb[1] - c[1]) ** 2 + (rgb[2] - c[2]) ** 2; if (d < bd) { bd = d; best = n; } }); return best; }
function localVision(f) {
  const color = nameColor(f.dominant);
  const tone = f.brightness > 0.62 ? '明亮' : f.brightness < 0.38 ? '昏暗' : '适中亮度';
  const cx = f.edge_density > 0.45 ? '细节丰富、纹理复杂' : f.edge_density < 0.2 ? '画面简洁、色块平整' : '细节适中';
  const shape = f.aspect > 1.3 ? '横向构图' : f.aspect < 0.77 ? '纵向构图' : '接近方形构图';
  const labels = [color, tone, cx.split('、')[0]]; if (f.edge_density > 0.5) labels.push('高细节');
  return { caption: `这是一张以${color}为主色调的图片，整体${tone}，${cx}，${shape}。分辨率约 ${f.width}×${f.height}。`, labels, dominant_name: color };
}
function localChat(body) {
  const text = body.text || '', f = body.image_features;
  const senti = text ? localSentiment(text) : { label: '中性', score: 0, confidence: 0.34, hits: [] };
  const intent = text ? localIntent(text) : '陈述';
  const vision = f ? localVision(f) : null;
  const parts = [];
  if (vision) parts.push('我看了你发的图片：' + vision.caption);
  if (text) {
    parts.push({ 问候: '你好呀！很高兴和你聊天～', 致谢: '不客气，随时为你服务！', 提问: `关于「${text.slice(0, 30)}」，这是个好问题，可以从多角度展开。`, 请求: `收到你的请求「${text.slice(0, 30)}」，我来帮你。`, 陈述: `我注意到你说：「${text.slice(0, 40)}」。` }[intent]);
    if (senti.label === '积极') parts.push('能感受到你心情不错，继续保持！');
    else if (senti.label === '消极') parts.push('听起来你有些情绪，我在这里听你说。');
  }
  return { reply: parts.join(' ') || '给我发文字或图片，我会结合多模态理解并回应。', intent, sentiment: senti, vision };
}

init();
