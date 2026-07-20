/* Multimodal Chat Hub — interactive demo logic (plain IIFE, file:// safe) */
(function(){
  const $ = window.$;

  /* ---------------- 8 维情绪模型 ---------------- */
  const EMO = {
    joy:        { label:'喜悦', kw:['喜欢','开心','棒','赞','满意','优秀','爱','惊喜','完美','厉害','感谢','太好了','不错','高兴','哈哈','美好','好'] },
    trust:      { label:'信任', kw:['相信','可靠','放心','靠谱','值得','安全','稳定','信任'] },
    anticipation:{ label:'期待', kw:['期待','希望','想要','想看','等着','盼','准备','计划','期待'] },
    surprise:   { label:'惊讶', kw:['哇','竟然','居然','没想到','天哪','吃惊','不敢相信','意外'] },
    sadness:    { label:'悲伤', kw:['难过','伤心','哭','失望','遗憾','失落','想哭','孤独','难受'] },
    fear:       { label:'恐惧', kw:['害怕','担心','恐惧','慌','紧张','怕','焦虑','恐惧'] },
    anger:      { label:'愤怒', kw:['讨厌','生气','垃圾','烦','崩溃','气死','可恶','差劲','愤怒'] },
    disgust:    { label:'厌恶', kw:['恶心','反感','无聊','敷衍','厌恶','不想'] },
  };
  const EMO_CLASS = { joy:'ok', trust:'ok', anticipation:'ok', surprise:'brand', sadness:'warn', fear:'warn', anger:'warn', disgust:'warn' };

  function detectEmotion(t){
    let best='neutral', bestN=0;
    for(const k in EMO){
      let n=0;
      EMO[k].kw.forEach(w=>{ if(t.includes(w)){ const neg = t.includes('不'+w) || t.includes('没'+w) || t.includes('不太'+w); n += neg?-1:1; } });
      if(n>bestN){ bestN=n; best=k; }
    }
    if(best==='neutral') return { label:'中性', conf:50 };
    const conf = Math.min(0.98, 0.34 + bestN*0.18);
    return { label:EMO[best].label, key:best, conf:Math.round(conf*100) };
  }

  /* ---------------- 意图识别 ---------------- */
  function detectIntent(t){
    if(/[?？]|什么|怎么|为什么|如何|吗$|呢$/.test(t)) return '提问';
    if(/帮我|请|能不能|可以|我想|我要|能否/.test(t)) return '请求';
    if(/你好|hi|hello|在吗|您好|嗨/i.test(t)) return '问候';
    if(/谢谢|感谢|多谢|thanks|thank/i.test(t)) return '致谢';
    if(/烦|差|糟|讨厌|垃圾|崩溃|气|失望|难受|恶心/.test(t)) return '抱怨';
    return '陈述';
  }

  /* ---------------- 实体抽取（轻量词典） ---------------- */
  const ENT = ['订单','物流','快递','发货','退款','退货','付款','支付','价格','收费','发票','天气','气温','音乐','歌曲','播放','翻译','英文','会议','日程','提醒','文件','图片','视频','股票','新闻','地址','电话','邮箱','账号'];
  function extractEntities(t){
    const out=[];
    ENT.forEach(e=>{ if(t.includes(e)) out.push(e); });
    return out.slice(0,5);
  }

  /* ---------------- 主题回应映射 ---------------- */
  const TOPICS = {
    '订单物流': ['订单','下单','物流','快递','发货','收货','到哪'],
    '退款':     ['退款','退货','退钱'],
    '支付':     ['付款','支付','价格','多少钱','收费','发票'],
    '天气':     ['天气','气温','下雨','温度'],
    '音乐':     ['音乐','歌曲','播放','歌','听'],
    '翻译':     ['翻译','translate','英文','英语'],
    '日程':     ['会议','日程','提醒','闹钟','时间'],
    '查询':     ['搜索','查一下','查找','查询','查'],
  };
  const TOPIC_REPLY = {
    '订单物流': e => '已为你定位**订单/物流**上下文'+(e.length?'（关注：'+e.join('、')+'）':'')+'：当前在途包裹预计 24h 内更新节点，需要我订阅到货提醒吗？',
    '退款':     e => '关于**退款**：我已在上下文中标记售后意图'+(e.length?'，关联 '+e.join('、'):'')+'，可协助发起退货并跟踪退款进度。',
    '支付':     e => '**支付**相关已记录'+(e.length?'，涉及 '+e.join('、'):'')+'。当前账单状态正常，如需开票我可以调用账单工具。',
    '天气':     e => '结合上下文，**天气**方面：今日多云转晴、气温 18–26℃，适合出门；需要我把行程建议写进记忆吗？',
    '音乐':     e => '收到**音乐**请求，已在 Context Harness 调用播放工具，为你续播轻松歌单 🎵。',
    '翻译':     e => '**翻译**已处理：原文已转为目标语言并回写上下文，后续可基于译文继续多轮问答。',
    '日程':     e => '已把**日程/提醒**写入记忆'+(e.length?'（'+e.join('、')+'）':'')+'，到点前我会主动提示你。',
    '查询':     e => '正在基于上下文对「'+(e[0]||'你提到的内容')+'」做检索，结果会带入下一轮，保持连续。',
  };
  function matchTopic(t){
    for(const k in TOPICS){ if(TOPICS[k].some(w=>t.toLowerCase().includes(w))) return k; }
    return null;
  }

  /* ---------------- 状态 ---------------- */
  let turn = 0, ctxLen = 0, modality = 'text';

  /* ---------------- 回复生成 ---------------- */
  function genReply(text, emo, intent, entities, mod){
    if(mod==='image'){
      return '**已理解图像内容**：图中以渐变主色调呈现，前景含山峦轮廓与高光圆形（疑似光源/主体），判定为**场景/风景类**图像。已写入视觉记忆，可继续基于它提问。';
    }
    const topic = matchTopic(text);
    let base;
    if(intent==='问候') base='你好呀～ 我是多模态对话机器人，能理解文字、图片和语音。有什么可以帮你的？';
    else if(intent==='致谢') base='不客气，很高兴能帮到你 🙂 随时找我。';
    else if(intent==='抱怨') base='听得出你有些不满，我理解你的感受。能多说一点具体情况吗？我会尽力协助解决。';
    else if(topic) base = TOPIC_REPLY[topic](entities);
    else if(intent==='提问') base='这是个好问题。结合当前上下文，我倾向于从「'+(entities[0]||'你提到的内容')+'」切入分析，并给出可执行的下一步。';
    else if(intent==='请求') base='收到你的请求，我会在 Context Harness 中记录意图「'+intent+'」并调用相应能力来处理。';
    else base='我已记录这条消息到上下文。'+(entities.length?'本次关注：'+entities.join('、')+'。':'')+'需要我进一步分析或采取行动吗？';

    if(emo.label==='喜悦') base += ' 看到你心情不错，继续保持～';
    else if(['悲伤','恐惧','愤怒','厌恶'].includes(emo.label)) base += ' 我注意到你情绪偏向'+emo.label+'，先照顾好自己，我在这里听你说。';
    return base;
  }

  /* ---------------- 上下文面板 / 统计 ---------------- */
  function pushContext(intent, emo, entities, mod){
    const term = $('#ctxTerm');
    if(term.querySelector('.empty')) term.innerHTML='';
    window.termLine(term, '^acc [turn '+turn+'] mod='+mod+' intent='+intent+' emotion='+emo.label, 'acc');
    window.termLine(term, '^dim   entities: '+(entities.length?entities.join(', '):'—'), 'dim');
  }
  function updateStats(emo, intent, entities, mod){
    const em = $('#stEmo');
    em.textContent = emo.label;
    em.className = 'n ' + (EMO_CLASS[emo.key]||'');
    $('#stConf').textContent = emo.conf + '%';
    ctxLen += 18 + entities.length*6;
    $('#stCtx').textContent = ctxLen;
  }

  /* ---------------- 图像占位 ---------------- */
  function placeholderImg(seed){
    const pal=[['#e879f9','#8b5cf6'],['#38bdf8','#22d3ee'],['#fb7185','#f59e0b'],['#34d399','#22d3ee']];
    const [c1,c2]=pal[seed%pal.length];
    const svg="<svg xmlns='http://www.w3.org/2000/svg' width='240' height='150'>"+
      "<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='"+c1+"'/><stop offset='1' stop-color='"+c2+"'/></linearGradient></defs>"+
      "<rect width='240' height='150' fill='url(#g)'/>"+
      "<circle cx='190' cy='40' r='22' fill='rgba(255,255,255,.75)'/>"+
      "<path d='M0 120 L70 70 L120 110 L170 65 L240 115 V150 H0 Z' fill='rgba(0,0,0,.22)'/>"+
      "<text x='12' y='142' fill='rgba(255,255,255,.9)' font-size='11' font-family='sans-serif'>captured-frame-"+seed+"</text></svg>";
    return 'data:image/svg+xml;utf8,'+encodeURIComponent(svg);
  }

  const VOICE_POOL = [
    '我想查一下我的订单到哪了',
    '今天天气怎么样，适合出门吗',
    '帮我播放一首轻松的音乐',
    '把这句话翻译成英文：今天的会议取消了',
  ];

  /* ---------------- 发送 ---------------- */
  const chat = () => $('#chatBox');

  async function respondTo(text, mod){
    const emo = detectEmotion(text);
    const intent = mod==='image' ? '视觉理解' : detectIntent(text);
    const entities = mod==='image' ? ['图像'] : extractEntities(text);
    turn++;
    pushContext(intent, emo, entities, mod);
    updateStats(emo, intent, entities, mod);

    const typing = window.chatTyping(chat());
    await window.wait(560 + Math.random()*260);
    typing.remove();
    window.chatAdd(chat(), 'bot', window.md(genReply(text, emo, intent, entities, mod)), 'Assistant');
  }

  async function send(){
    const input = $('#msgInput');
    const text = input.value.trim();
    if(modality==='text'){
      if(!text){ window.toast('请输入文本内容'); return; }
      window.chatAdd(chat(), 'user', window.md(window.esc(text)), 'You');
      input.value='';
      await respondTo(text, 'text');
    } else if(modality==='image'){
      const seed = turn + 1;
      window.chatAdd(chat(), 'user', '<img src="'+placeholderImg(seed)+'" style="max-width:210px;border-radius:10px;border:1px solid var(--border)">', 'You');
      await respondTo('', 'image');
    } else if(modality==='voice'){
      const transcript = text || VOICE_POOL[Math.floor(Math.random()*VOICE_POOL.length)];
      window.chatAdd(chat(), 'user', window.md('🎙️ '+window.esc(transcript)), 'You');
      input.value='';
      await respondTo(transcript, 'voice');
    }
  }

  /* ---------------- 模态切换 ---------------- */
  $$('#modChips .opt').forEach(o=>o.onclick=()=>{
    $$('#modChips .opt').forEach(x=>x.classList.remove('on'));
    o.classList.add('on'); modality=o.dataset.mod;
    const ph = { text:'输入消息，回车发送…', image:'（图像模式）点击发送即可上传示例图', voice:'（语音模式）点击发送开始转录，或输入文本' };
    $('#msgInput').placeholder = ph[modality];
    window.toast('已切换模态：'+o.textContent);
  });

  $('#sendBtn').onclick = send;
  $('#msgInput').addEventListener('keydown', e=>{ if(e.key==='Enter') send(); });

  /* ---------------- 流水线演示 ---------------- */
  const STAGES = ['p1','p2','p3','p4'];
  const DESC = ['文本/图/音接入', '情感·语义解析', '编排与记忆', '多模态合成'];
  $('#runPipe').onclick = async ()=>{
    $('#runPipe').disabled = true;
    const term = $('#ctxTerm');
    if(term.querySelector('.empty')) term.innerHTML='';
    window.termLine(term, '^ok pipeline.run() → 4 stages', 'ok');
    await window.runPipeline(STAGES, { delay:520, onStep:(i)=>window.setStageDesc(STAGES[i], DESC[i]) });
    window.termLine(term, '^acc loop 完成，上下文已更新', 'acc');
    $('#runPipe').disabled = false;
  };
  $('#clearCtx').onclick = ()=>{
    $('#ctxTerm').innerHTML = '<div class="empty">上下文已清空，等待新一轮对话…</div>';
    turn=0; ctxLen=0;
    $('#stEmo').textContent='中性'; $('#stEmo').className='n brand';
    $('#stConf').textContent='34%'; $('#stCtx').textContent='0';
    window.toast('上下文已重置');
  };

  /* ---------------- 种子欢迎语 ---------------- */
  window.chatAdd(chat(), 'bot',
    window.md('你好，我是 **多模态对话机器人**。我可以感知文本情感、理解图像、转录语音，并把它们统一编排在 **Context Harness Loop** 中。试试切换下方的「图像 / 语音」模式，或直接发送文字。'),
    'Assistant');

  window.boot();
})();
