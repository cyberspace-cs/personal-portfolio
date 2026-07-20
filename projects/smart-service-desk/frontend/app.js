/* Smart Service Desk · 前端逻辑（后端离线时降级为本地引擎） */
const API = 'http://localhost:8005/api';
const THRESHOLD = 0.16;
const SID = 'web-' + Math.random().toString(36).slice(2, 8);
let state = { offline: false };
const $ = (id) => document.getElementById(id);
function toast(m) { const t = $('toast'); t.textContent = m; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 2000); }
function esc(s) { return String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c])); }

async function api(path, body) {
  const opt = body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {};
  const r = await fetch(API + path, opt);
  if (!r.ok) throw new Error('HTTP');
  return r.json();
}

async function init() {
  $('sendBtn').onclick = send; window.__send = send;
  document.querySelectorAll('#quickChips .chip').forEach(c => c.onclick = () => { $('msgInput').value = c.textContent; send(); });
  try {
    await api('/health');
    let f = await api('/faqs');
    if (!f.faqs.length) { await api('/seed', {}); f = await api('/faqs'); }
    renderFaqs(f.faqs); refreshStats(); refreshTickets();
  } catch {
    state.offline = true; LOCAL.seed();
    const b = document.querySelector('.badge-live');
    b.style.background = '#fff4e0'; b.style.borderColor = '#ffd8a8'; b.style.color = '#d97706';
    b.innerHTML = '<span class="dot" style="background:#d97706"></span> 演示模式（本地引擎）';
    renderFaqs(LOCAL.faqs); refreshStats(); refreshTickets();
  }
}

async function send() {
  const msg = $('msgInput').value.trim(); if (!msg) return;
  addMsg('u', esc(msg)); $('msgInput').value = '';
  let d;
  try { d = state.offline ? LOCAL.chat(msg) : await api('/chat', { message: msg, session_id: SID }); }
  catch { state.offline = true; LOCAL.seed(); d = LOCAL.chat(msg); }
  renderBot(d); refreshStats();
}

function renderBot(d) {
  const route = d.escalate
    ? `<div class="route esc">⚠ 转人工 · 意图 ${d.intent}</div>`
    : `<div class="route">✓ ${d.intent}${d.matched_faq ? ' · FAQ命中 ' + d.matched_faq.score : ''}</div>`;
  const actions = (d.suggested_actions || []).map(a => `<button class="qa">${esc(a)}</button>`).join('');
  const el = document.createElement('div'); el.className = 'msg a';
  const rateHtml = !d.escalate ? `<div class="rate">${[1, 2, 3, 4, 5].map(i => `<span data-s="${i}">★</span>`).join('')}</div>` : '';
  const ticketBtn = d.escalate ? `<div class="actions-inline"><button class="qa" id="mkTicket">创建工单跟进</button></div>` : '';
  el.innerHTML = `<div class="bubble">${route}${esc(d.reply)}<div class="actions-inline">${actions}</div>${ticketBtn}${rateHtml}</div>`;
  $('chat').appendChild(el); $('chat').scrollTop = $('chat').scrollHeight;
  el.querySelectorAll('.qa').forEach(b => { if (b.id !== 'mkTicket') b.onclick = () => { $('msgInput').value = b.textContent; send(); }; });
  const mk = el.querySelector('#mkTicket'); if (mk) mk.onclick = () => makeTicket(d.intent);
  el.querySelectorAll('.rate span').forEach(s => s.onclick = async () => {
    el.querySelectorAll('.rate span').forEach((x, i) => x.classList.toggle('on', i < +s.dataset.s));
    if (state.offline) LOCAL.rate(+s.dataset.s); else { try { await api('/rate', { score: +s.dataset.s }); } catch {} }
    refreshStats(); toast('感谢您的评价！');
  });
}

async function makeTicket(category) {
  const content = prompt('请简要描述您的问题（将创建工单）：', '');
  if (!content) return;
  let t;
  if (state.offline) t = LOCAL.ticket(category, content);
  else { try { t = (await api('/ticket', { session_id: SID, category, content })).ticket; } catch { t = LOCAL.ticket(category, content); } }
  addMsg('a', `已为您创建工单 <b>${t.id}</b>（${esc(t.category)}），我们会尽快跟进处理。`);
  refreshTickets(); refreshStats(); toast('工单已创建：' + t.id);
}

function addMsg(role, html) {
  const d = document.createElement('div'); d.className = 'msg ' + role;
  d.innerHTML = `<div class="bubble">${html}</div>`;
  $('chat').appendChild(d); $('chat').scrollTop = $('chat').scrollHeight;
}

function renderFaqs(faqs) {
  $('faqList').innerHTML = faqs.map(f => `<div class="faq" data-q="${esc(f.q)}"><span class="cat">${esc(f.cat)}</span><div class="q">${esc(f.q)}</div></div>`).join('') || '<div class="empty">暂无 FAQ</div>';
  document.querySelectorAll('.faq').forEach(el => el.onclick = () => { $('msgInput').value = el.dataset.q; send(); });
}

async function refreshStats() {
  let s;
  try { s = state.offline ? LOCAL.stats() : await api('/stats'); } catch { s = LOCAL.stats(); }
  $('sTotal').textContent = s.total;
  $('sResolve').textContent = (s.resolve_rate * 100).toFixed(0) + '%';
  $('sEsc').textContent = s.escalated;
  $('sTicket').textContent = s.tickets;
  $('sSat').textContent = s.satisfaction ? s.satisfaction.toFixed(1) : '—';
}
async function refreshTickets() {
  let list;
  try { list = state.offline ? LOCAL.tickets : (await api('/tickets')).tickets; } catch { list = LOCAL.tickets; }
  $('ticketList').innerHTML = list.length ? list.map(t => `<div class="ticket"><span class="st">${t.status}</span><span class="id">${t.id}</span><div class="c">${esc(t.content)}</div><div class="t">${t.category} · ${t.created_at}</div></div>`).join('') : '<div class="empty">暂无工单</div>';
}

/* ---------------- 本地引擎（离线降级，与后端同构） ---------------- */
const LOCAL = {
  faqs: [], tickets: [], m: { total: 0, auto: 0, esc: 0, tk: 0, satSum: 0, satCnt: 0 },
  INTENT: {
    物流查询: ['物流', '快递', '发货', '到哪', '什么时候到', '配送', '签收'],
    退款退货: ['退款', '退货', '退钱', '怎么退', '不想要了'],
    订单问题: ['订单', '下单', '支付', '付款', '改地址', '取消订单'],
    投诉建议: ['投诉', '差评', '态度', '垃圾', '骗人', '举报'],
    产品咨询: ['怎么用', '功能', '支持', '能不能', '规格', '介绍', '价格', '多少钱'],
    转人工: ['人工', '客服', '真人', '转接'],
  },
  QA: { 物流查询: ['查看物流轨迹', '催发货'], 退款退货: ['申请退款', '退货流程说明'], 订单问题: ['查看我的订单', '取消订单'], 投诉建议: ['提交投诉工单', '转接主管'], 产品咨询: ['查看产品文档'], 转人工: ['转接人工客服'], 其他: ['浏览常见问题', '转人工客服'] },
  seed() {
    if (this.faqs.length) return;
    [['怎么查看物流信息？', '进入「我的订单」找到对应订单，点击「查看物流」即可看到实时配送轨迹。', '物流查询'],
    ['多久发货？', '现货商品通常 24 小时内发货，预售商品以商品页标注时间为准。', '物流查询'],
    ['如何申请退款？', '在「我的订单」选择订单点击「申请退款」，填写原因提交，审核通过 1-3 个工作日原路退回。', '退款退货'],
    ['退货运费谁承担？', '质量问题退货运费由商家承担；七天无理由退货运费由买家承担。', '退款退货'],
    ['可以修改收货地址吗？', '订单未发货前可在「我的订单」修改地址；已发货需联系客服拦截。', '订单问题'],
    ['支持哪些支付方式？', '支持微信支付、支付宝、银行卡及花呗分期等多种方式。', '订单问题'],
    ['产品怎么使用？', '每件产品附带图文说明，也可在「帮助中心-产品文档」查看教程。', '产品咨询'],
    ['有优惠活动吗？', '关注店铺可第一时间获取满减、优惠券与限时秒杀信息。', '产品咨询']]
      .forEach(([q, a, c], i) => this.faqs.push({ id: 'f' + i, q, a, cat: c, tf: count(tok(q + a)) }));
  },
  idf(t) { const n = this.faqs.length || 1; const df = this.faqs.filter(f => f.tf[t]).length; return Math.log(1 + (n - df + 0.5) / (df + 0.5)); },
  intent(msg) { let best = '其他', bh = 0; Object.entries(this.INTENT).forEach(([k, kw]) => { const h = kw.filter(x => msg.includes(x)).length; if (h > bh) { bh = h; best = k; } }); return [best, Math.min(1, bh / 2)]; },
  match(msg) {
    const q = count(tok(msg)); let best = null, bs = 0;
    this.faqs.forEach(f => {
      let dot = 0; Object.keys(q).forEach(t => { if (f.tf[t]) dot += (q[t] * this.idf(t)) * (f.tf[t] * this.idf(t)); });
      const qn = Math.sqrt(Object.keys(q).reduce((a, t) => a + (q[t] * this.idf(t)) ** 2, 0)) || 1e-9;
      const cn = Math.sqrt(Object.keys(f.tf).reduce((a, t) => a + (f.tf[t] * this.idf(t)) ** 2, 0)) || 1e-9;
      const s = dot / (qn * cn); if (s > bs) { bs = s; best = f; }
    });
    return [best, bs];
  },
  chat(msg) {
    this.m.total++;
    const [intent] = this.intent(msg); const [faq, score] = this.match(msg);
    let escalate = false, reply, matched = null;
    if (intent === '转人工' || intent === '投诉建议') { escalate = true; reply = intent === '转人工' ? '已为您转接人工客服，坐席将尽快接入。' : '非常抱歉给您带来不好的体验，已升级到人工专员处理并记录本次反馈。'; }
    else if (faq && score >= THRESHOLD) { reply = faq.a; matched = { q: faq.q, score: +score.toFixed(4) }; this.m.auto++; }
    else { escalate = true; reply = `我理解您想咨询「${intent}」相关问题，但暂未匹配到足够确定的答案（置信度 ${score.toFixed(3)} < 阈值 ${THRESHOLD}）。要不要转接人工，或创建工单跟进？`; }
    if (escalate) this.m.esc++;
    return { reply, intent, matched_faq: matched, faq_score: +score.toFixed(4), threshold: THRESHOLD, escalate, suggested_actions: this.QA[intent] || this.QA['其他'] };
  },
  ticket(cat, content) { const t = { id: 'TK' + Math.random().toString(36).slice(2, 10).toUpperCase(), category: cat, content, status: '待处理', created_at: new Date().toLocaleString() }; this.tickets.unshift(t); this.m.tk++; return t; },
  rate(s) { this.m.satSum += s; this.m.satCnt++; },
  stats() { const tot = this.m.total || 1; return { total: this.m.total, auto_resolved: this.m.auto, escalated: this.m.esc, tickets: this.m.tk, resolve_rate: this.m.auto / tot, satisfaction: this.m.satCnt ? this.m.satSum / this.m.satCnt : 0 }; },
};
function tok(text) { text = text.toLowerCase(); const t = []; (text.match(/[a-z0-9]+|[\u4e00-\u9fff]+/g) || []).forEach(seg => { if (/[a-z0-9]/.test(seg[0])) t.push(seg); else { for (const c of seg) t.push(c); for (let i = 0; i < seg.length - 1; i++) t.push(seg.slice(i, i + 2)); } }); return t; }
function count(a) { const m = {}; a.forEach(x => m[x] = (m[x] || 0) + 1); return m; }

init();
