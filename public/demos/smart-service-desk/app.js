/* ============================================================
   Smart Service Desk · 智能客服 Agent 前端逻辑
   纯前端意图路由 + Skill 路由 + MCP 工具调用演示（与后端同构）
   依赖 ../_shared.js 提供的 window 全局助手
   ============================================================ */
(function () {
  'use strict';

  /* ---------------- 意图引擎（9 意图 / 4 技能 / 8 MCP 工具） ---------------- */
  // skill: faq_rag(知识库检索) / ticket_create(工单创建) / human_handoff(人工转接) / intent_router(意图路由)
  const NLU = {
    物流查询: {
      kw: ['物流', '快递', '发货', '到哪', '到货', '配送', '签收', '运单', '寄', '还没发', '没发货'],
      skill: 'faq_rag', tools: ['查订单系统(order_svc)', '物流轨迹查询(logistics_svc)'],
      reply: '已为您查询物流：订单已揽收，承运商【顺丰】，预计 2 天内送达。运单号 SF1009，可凭订单号实时追踪轨迹。'
    },
    退款退货: {
      kw: ['退款', '退货', '退钱', '怎么退', '不想要了', '退换'],
      skill: 'ticket_create', tools: ['查订单系统(order_svc)', '退款审批(refund_svc)'],
      reply: '已为您发起退款流程：订单状态校验通过，退款将原路退回，审核约 1-3 个工作日到账。已生成退款工单跟进。'
    },
    发票开具: {
      kw: ['发票', '开票', '开发票', '报销', '普票', '专票', '增值税'],
      skill: 'faq_rag', tools: ['发票系统(invoice_svc)', '订单核验(order_svc)'],
      reply: '已为您开具电子发票：订单核验通过，增值税普通电子发票已推送至您的注册邮箱，抬头默认为下单用户名。'
    },
    退货进度: {
      kw: ['退货进度', '退到哪', '退货到', '退回', '退款进度', '退货到哪一步'],
      skill: 'faq_rag', tools: ['查订单系统(order_svc)', '物流轨迹查询(logistics_svc)'],
      reply: '您的退货包裹已签收入库，退款将在 24 小时内原路退回，当前进度：退货签收 → 入库质检 → 退款中。'
    },
    订单问题: {
      kw: ['订单', '下单', '支付', '付款', '改地址', '取消订单', '修改地址', '催单'],
      skill: 'faq_rag', tools: ['查订单系统(order_svc)'],
      reply: '已调取您的订单：状态为【待发货】，可在「我的订单」修改收货地址或申请催单，已为您记录催单诉求。'
    },
    产品咨询: {
      kw: ['怎么用', '功能', '支持', '能不能', '规格', '介绍', '价格', '多少钱', '尺寸', '材质'],
      skill: 'faq_rag', tools: ['知识库检索(kb_svc)'],
      reply: '已从产品知识库为您检索：该商品支持 7 天无理由，含图文说明书与视频教程，详细参数见商品详情页「规格」区。'
    },
    投诉建议: {
      kw: ['投诉', '差评', '态度', '垃圾', '骗人', '举报', '失望', '不满'],
      skill: 'human_handoff', tools: ['工单系统(ticket_svc)', '升级专员(escalation_svc)'],
      escalate: true,
      reply: '非常抱歉给您带来不好的体验，已升级至人工专员并生成投诉工单优先处理，专员将在 15 分钟内主动联系您。'
    },
    人工客服: {
      kw: ['人工', '客服', '真人', '转接', '坐席', '转人工'],
      skill: 'human_handoff', tools: ['坐席分配(agent_svc)'],
      escalate: true,
      reply: '已为您转接人工坐席，正在分配空闲客服，上下文已同步，请稍候，坐席将尽快接入对话。'
    },
    其他: {
      kw: [], skill: 'intent_router', tools: ['知识库检索(kb_svc)'],
      reply: '我已记录您的问题，但暂未匹配到确定意图。您可补充订单号或具体问题类型，或回复「转人工」由专员为您处理。'
    }
  };

  const STAGES = ['p1', 'p2', 'p3', 'p4', 'p5'];
  let turnCount = 0;

  /* ---------------- 意图分类 ---------------- */
  function classify(msg) {
    const m = msg.toLowerCase();
    let best = '其他', hits = 0;
    Object.keys(NLU).forEach(k => {
      if (k === '其他') return;
      const h = NLU[k].kw.filter(w => m.includes(w.toLowerCase())).length;
      if (h > hits) { hits = h; best = k; }
    });
    const conf = best === '其他'
      ? Math.max(0.32, 0.4 - 0.02 * Math.max(0, 0))
      : Math.min(0.98, 0.55 + 0.13 * hits);
    return { intent: best, confidence: conf, hits, def: NLU[best] };
  }

  function extractOrder(msg) {
    const re = /(?:订单号|单号|order)\D{0,4}([A-Za-z0-9]{4,})/i;
    const mt = msg.match(re);
    if (mt) return mt[1].toUpperCase();
    const digits = msg.match(/[A-Za-z0-9]{6,}/);
    return digits ? digits[0].toUpperCase() : null;
  }

  /* ---------------- 编排流水线（每轮对话快速高亮） ---------------- */
  async function flashPipeline(descs) {
    STAGES.forEach(id => { const s = $('#' + id); if (s) s.classList.remove('on', 'done'); });
    for (let i = 0; i < STAGES.length; i++) {
      const s = $('#' + STAGES[i]);
      if (s) {
        s.classList.add('on');
        if (descs && descs[i]) setStageDesc(STAGES[i], descs[i]);
      }
      await wait(170);
      if (s) { s.classList.add('done'); s.classList.remove('on'); }
    }
  }

  /* ---------------- 更新右侧面板 ---------------- */
  function updateIntentCard(r) {
    $('#intentChip').textContent = r.intent;
    $('#intentConfTxt').textContent = (r.confidence * 100).toFixed(0) + '%';
    const bar = $('#intentConf');
    bar.style.width = (r.confidence * 100).toFixed(0) + '%';
    bar.style.background = r.confidence < 0.6
      ? 'linear-gradient(120deg,#fbbf24,#fb7185)'
      : 'linear-gradient(120deg,#fbbf24,#34d399)';
  }

  function logMcp(tools, order) {
    const term = $('#mcpTerm');
    term.innerHTML = '';
    termLine(term, '^dim 本轮 MCP 工具调用链 (#' + (++turnCount) + ')', 'dim');
    termLine(term, '^acc route → skill:' + tools.skill, 'acc');
    tools.tools.forEach(t => termLine(term, '  call_tool(' + t + ')  ✓', 'ok'));
    if (order) termLine(term, '  slot order_id = ' + order, 'dim');
    termLine(term, '^ok 工具调用完成，构造闭环回复', 'ok');
  }

  function updateContext(r, order) {
    $('#ctxOrder').textContent = order || '未提供';
    $('#ctxType').textContent = r.intent;
    const human = !!r.def.escalate;
    $('#ctxHuman').textContent = human ? '是' : '否';
    $('#ctxHuman').style.color = human ? 'var(--warn)' : '';
  }

  /* ---------------- 一轮对话 ---------------- */
  async function handleMessage(rawMsg) {
    const msg = (rawMsg || '').trim();
    if (!msg) return;
    chatAdd($('#chatBox'), 'user', esc(msg), '您');

    const r = classify(msg);
    const order = extractOrder(msg);

    // 编排流水线（不阻塞回复）
    const descs = [
      '命中 ' + r.intent + ' (' + (r.confidence * 100).toFixed(0) + '%)',
      r.def.escalate ? '转人工工单' : '复用模板',
      'RAG 检索命中',
      r.def.tools.join(' · '),
      r.def.escalate ? '转接 + 交接上下文' : '意图闭环回复'
    ];
    flashPipeline(descs);

    // 更新右侧面板
    updateIntentCard(r);
    logMcp({ skill: r.def.skill, tools: r.def.tools }, order);
    updateContext(r, order);

    // 机器人回复（typing 后输出）
    const typing = chatTyping($('#chatBox'));
    await wait(700);
    typing.remove();
    chatAdd($('#chatBox'), 'bot', md(r.def.reply), '智能客服 Agent');
  }

  /* ---------------- 完整编排演示 ---------------- */
  async function runDemo() {
    const sample = '我的订单还没发货，订单号 SO2024，能帮我催一下吗？';
    $('#msgInput').value = sample;
    toast('运行编排演示：' + sample);
    await runPipeline(STAGES, {
      delay: 480,
      onStep: (i) => {
        const desc = [
          '语义编码 → 9 意图向量',
          '命中 物流查询 · 路由模板',
          'FAQ / 知识库 RAG 检索',
          'call_tool(查订单系统) ✓ · call_tool(物流轨迹) ✓',
          '生成闭环回复并回写记忆'
        ][i];
        setStageDesc(STAGES[i], desc);
      }
    });
    await handleMessage(sample);
  }

  function resetPanels() {
    STAGES.forEach(id => { const s = $('#' + id); if (s) { s.classList.remove('on', 'done'); } });
    STAGES.forEach(id => setStageDesc(id, '—'));
    $('#intentChip').textContent = '等待输入';
    $('#intentConfTxt').textContent = '—';
    $('#intentConf').style.width = '0%';
    $('#mcpTerm').innerHTML = '<div class="empty">暂无工具调用…</div>';
    $('#ctxOrder').textContent = '未提供';
    $('#ctxType').textContent = '—';
    $('#ctxHuman').textContent = '否';
    $('#ctxHuman').style.color = '';
    turnCount = 0;
    toast('面板已重置');
  }

  /* ---------------- 绑定 ---------------- */
  function send() {
    const el = $('#msgInput');
    const v = el.value;
    el.value = '';
    handleMessage(v);
  }
  window.__send = send;

  function bootPage() {
    $('#sendBtn').onclick = send;
    $('#runPipe').onclick = runDemo;
    $('#resetBtn').onclick = resetPanels;
    $$('#intentChips .opt').forEach(c => {
      c.onclick = () => { $('#msgInput').value = c.dataset.q; send(); };
    });
    // 欢迎气泡
    chatAdd($('#chatBox'), 'bot',
      '您好，我是 <b>智能客服 Agent</b> 👋 我能识别 9 类服务意图，自动调用 MCP 工具并闭环回复。试试下方示例，或描述您的问题。',
      '智能客服 Agent');
    toast('对话已就绪，后端 :8005 在线');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootPage);
  } else {
    bootPage();
  }

  window.boot();
})();
