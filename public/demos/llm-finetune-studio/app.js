/* LLM Finetune Studio — interactive demo logic */
(function(){
  const $ = window.$;

  /* ---------- pipeline demo ---------- */
  const STAGES = ['p1','p2','p3','p4','p5'];
  const STAGE_DESC = [
    'JSONL 校验通过',
    'LoRA r=8 α=16',
    '反向传播中',
    'loss 流式回传',
    '基座 vs 微调'
  ];
  async function runPipe(){
    $('#runPipe').disabled = true;
    await window.runPipeline(STAGES, { delay:520, onStep:(i)=>window.setStageDesc(STAGES[i], STAGE_DESC[i]) });
    $('#runPipe').disabled = false;
  }
  $('#runPipe').onclick = runPipe;
  $('#sampleFlow').onclick = ()=>{
    $('#dataset').value = JSON.stringify({instruction:"解释什么是LoRA",input:"",output:"LoRA 是一种参数高效微调方法，仅训练低秩适配矩阵即可接近全量微调效果。"}) + "\n" +
      JSON.stringify({instruction:"什么是QLoRA",input:"",output:"QLoRA = 量化 + LoRA，先 4-bit 量化基座再训 LoRA，单卡可微调超大模型。"}) + "\n" +
      JSON.stringify({instruction:"DoRA 与 LoRA 区别",input:"",output:"DoRA 将权重更新分解为幅度和方向分别学习，通常更稳定。"}) + "\n" +
      JSON.stringify({instruction:"Adapter 微调原理",input:"",output:"Adapter 在 Transformer 子层间插入小巧的前馈瓶颈层，仅训练这些适配器。"});
    window.toast('已填充 4 条示例样本');
  };

  /* ---------- config ---------- */
  let method = 'LoRA';
  $$('#methodChips .opt').forEach(o=>o.onclick=()=>{
    $$('#methodChips .opt').forEach(x=>x.classList.remove('on'));
    o.classList.add('on'); method=o.dataset.m;
  });
  const bind = (id, vid)=>{ const el=$(id); if(el) el.oninput=()=>{ if(vid) $(vid).textContent=el.value; }; };
  bind('#loraRank','#vRank'); bind('#loraAlpha','#vAlpha'); bind('#epochs','#vEp');

  /* ---------- dataset validate ---------- */
  const SAMPLE_DS = [
    {instruction:"解释什么是LoRA",input:"",output:"LoRA 是一种参数高效微调方法，仅训练低秩适配矩阵即可接近全量微调效果。"},
    {instruction:"什么是QLoRA",input:"",output:"QLoRA = 量化 + LoRA，先 4-bit 量化基座再训 LoRA，单卡可微调超大模型。"},
    {instruction:"DoRA 与 LoRA 区别",input:"",output:"DoRA 将权重更新分解为幅度和方向分别学习。"},
    {instruction:"Adapter 微调原理",input:"",output:"Adapter 在 Transformer 子层间插入小巧的前馈瓶颈层。"},
    {instruction:"full fine-tuning 缺点",input:"",output:"全量微调显存与存储开销大，小样本易过拟合。"}
  ];
  $('#sampleBtn').onclick = ()=>{ $('#dataset').value = SAMPLE_DS.map(o=>JSON.stringify(o)).join("\n"); window.toast('已填充示例数据集'); };
  $('#validateBtn').onclick = ()=>{
    const raw = $('#dataset').value.trim();
    const lines = raw.split(/\n+/).filter(Boolean);
    const stats = $('#dsStats'), errs = $('#dsErrors');
    if(!lines.length){ stats.innerHTML=''; errs.innerHTML='<div class="wo" style="border-color:#fb7185">未检测到样本</div>'; return; }
    let ok=0, bad=0; const errList=[]; let toks=0;
    lines.forEach((ln,i)=>{
      try{ const o=JSON.parse(ln);
        if(!o.output||!o.instruction){ errList.push({i,msg:'缺少 instruction / output 字段'}); bad++; }
        else { ok++; toks += (o.instruction+o.output).length; }
      }catch(e){ errList.push({i,msg:'JSON 解析失败'}); bad++; }
    });
    stats.innerHTML =
      '<div class="stat-grid">'+
      '<div class="stat"><div class="n ok">'+ok+'</div><div class="l">合法样本</div></div>'+
      '<div class="stat"><div class="n warn">'+bad+'</div><div class="l">异常样本</div></div>'+
      '<div class="stat"><div class="n brand">'+(toks?Math.round(toks/ok):0)+'</div><div class="l">平均 token</div></div>'+
      '</div>';
    errs.innerHTML = errList.length
      ? '<div style="margin-top:10px">'+errList.map(e=>'<div class="wo" style="border-color:#fb7185"><div class="top"><span class="nm">Line '+(e.i+1)+'</span></div><div class="meta">'+window.esc(e.msg)+'</div></div>').join('')+'</div>'
      : '<div class="wo" style="border-color:#34d399;margin-top:10px"><div class="top"><span class="nm">✓ 数据集校验通过</span></div><div class="meta">可进入训练流水线</div></div>';
  };

  /* ---------- training sim + chart ---------- */
  const canvas = $('#lossChart'); const ctx = canvas.getContext('2d');
  let lossData=[], lrData=[], running=false, paused=false, step=0, timer=null;
  function fitCanvas(){ const r=canvas.getBoundingClientRect(); canvas.width=r.width*devicePixelRatio; canvas.height=220*devicePixelRatio; ctx.scale(devicePixelRatio,devicePixelRatio); }
  function drawChart(){
    const W=canvas.width/devicePixelRatio, H=220;
    ctx.clearRect(0,0,W,H);
    ctx.strokeStyle='rgba(148,163,184,.12)'; ctx.lineWidth=1;
    for(let i=0;i<=4;i++){ const y=18+i*(H-40)/4; ctx.beginPath(); ctx.moveTo(36,y); ctx.lineTo(W-10,y); ctx.stroke(); }
    if(lossData.length<2) return;
    const maxL=Math.max(...lossData)*1.1, minL=0;
    const px=i=>36+(W-46)*i/(lossData.length-1);
    const py=v=>18+(H-40)*(1-(v-minL)/(maxL-minL||1));
    // loss
    ctx.beginPath(); ctx.strokeStyle='#22d3ee'; ctx.lineWidth=2.4;
    lossData.forEach((v,i)=>{ const x=px(i),y=py(v); i?ctx.lineTo(x,y):ctx.moveTo(x,y); }); ctx.stroke();
    // lr (scaled)
    ctx.beginPath(); ctx.strokeStyle='#34d399'; ctx.lineWidth=1.6; ctx.setLineDash([4,4]);
    lrData.forEach((v,i)=>{ const x=px(i),y=py(v*maxL); i?ctx.lineTo(x,y):ctx.moveTo(x,y); }); ctx.stroke(); ctx.setLineDash([]);
  }
  function logLine(t, c){ const log=$('#log'); if(log.querySelector('.empty')) log.innerHTML=''; window.termLine(log, t, c); }
  function tick(){
    if(!running||paused) return;
    step++;
    const base=2.4, decay=base*Math.exp(-step/22);
    const loss=decay + 0.12 + Math.random()*0.06;
    const lr=parseFloat($('#lr').value||'2e-4');
    lossData.push(loss); lrData.push(lr);
    $('#mStep').textContent=step;
    $('#mLoss').textContent=loss.toFixed(3);
    const total=Math.max(1, parseInt($('#sampleCount').value||'500')/ (parseInt($('#batch').value||'8')) );
    $('#mProg').style.width=Math.min(100, step/ (total>40?40:total) *100)+'%';
    drawChart();
    if(step%4===0) logLine('^acc step '+step+' | loss '+loss.toFixed(3)+' | lr '+lr.toExponential(2)+' | grad_norm '+(0.8+Math.random()*0.4).toFixed(2), '');
    if(step>=40){ running=false; $('#mStatus').textContent='已完成'; $('#mStatus').className='n ok'; logLine('^ok 训练完成 → 导出 adapter/ 并注册到 vLLM', 'ok'); pushJob(); return; }
    timer=setTimeout(tick, 420);
  }
  function pushJob(){
    const list=$('#jobList'); if(list.querySelector('.empty')) list.innerHTML='';
    const id='FT-'+String(step).padStart(3,'0');
    const card=document.createElement('div'); card.className='wo';
    card.innerHTML='<div class="top"><span class="nm">'+id+' · '+$('#baseModel').value+'</span><span class="chip">'+method+'</span></div>'+
      '<div class="meta">r='+$('#loraRank').value+' α='+$('#loraAlpha').value+' · epochs='+$('#epochs').value+' · min_loss='+Math.min(...lossData).toFixed(3)+'</div>';
    list.prepend(card);
    const n=parseInt($('#kvJobs').textContent||'0')+1; $('#kvJobs').textContent=n;
  }
  $('#startBtn').onclick=()=>{
    if(running){ window.toast('已有任务在运行'); return; }
    lossData=[]; lrData=[]; step=0; running=true; paused=false;
    $('#mStatus').textContent='训练中'; $('#mStatus').className='n warn';
    $('#pauseBtn').style.display=''; $('#resumeBtn').style.display='none';
    $('#log').innerHTML=''; logLine('^dim 初始化 '+method+' 适配器 → '+$('#baseModel').value, 'dim');
    fitCanvas(); drawChart(); tick();
  };
  $('#pauseBtn').onclick=()=>{ paused=true; $('#pauseBtn').style.display='none'; $('#resumeBtn').style.display=''; $('#mStatus').textContent='已暂停'; logLine('^warn 用户暂停训练', 'warn'); };
  $('#resumeBtn').onclick=()=>{ paused=false; $('#resumeBtn').style.display='none'; $('#pauseBtn').style.display=''; $('#mStatus').textContent='训练中'; logLine('^acc 续训…', ''); tick(); };
  window.addEventListener('resize', ()=>{ if(lossData.length){ fitCanvas(); drawChart(); } });

  /* ---------- comparison inference ---------- */
  $('#inferBtn').onclick=async ()=>{
    const p=$('#prompt').value.trim(); if(!p){ window.toast('请输入 prompt'); return; }
    const box=$('#cmpBox'); box.style.display='grid';
    $('#baseOut').textContent='思考中…'; $('#tunedOut').textContent='思考中…';
    await window.wait(500);
    $('#baseOut').textContent = '【基座】'+p+'：LoRA 是一种微调技术，通过在权重旁增加低秩矩阵来减少训练参数。（回答偏泛化、缺少领域细节）';
    $('#tunedOut').textContent = '【微调后】'+p+'：QLoRA = 4-bit 量化基座 + LoRA 适配器，显存从 >24GB 降到 ~6GB，单张消费级显卡即可微调 13B 模型，训练时仅更新低秩矩阵、基座权重冻结。';
    $('#baseFoot').textContent='tokens ~ 38 · 无领域适配';
    $('#tunedFoot').textContent='tokens ~ 71 · 领域增益明显';
    window.toast('对比完成');
  };

  window.boot();
})();
