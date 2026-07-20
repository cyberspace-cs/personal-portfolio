/* ============================================================
   Shared JS helpers for Agent Demo pages (plain global script —
   safe for both http:// and file://). Helpers are attached to
   window so each demo's app.js can use them directly.
   ============================================================ */
(function(){
  const $  = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => Array.prototype.slice.call(r.querySelectorAll(s));
  window.$ = $; window.$$ = $$;

  /* reveal on scroll */
  let _revObs;
  if('IntersectionObserver' in window){
    _revObs = new IntersectionObserver((es)=>{
      es.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add('in'); _revObs.unobserve(e.target);} });
    },{threshold:.12});
  }
  window.observeReveal = function(root){
    root = root||document;
    $$('.reveal', root).forEach(el=>{ if(_revObs) _revObs.observe(el); else el.classList.add('in'); });
  };

  /* animated count-up */
  window.countUp = function(el, to, opts){
    opts=opts||{}; const dur=opts.dur||1100, suffix=opts.suffix||'', prefix=opts.prefix||'';
    const start=performance.now(); const from=0;
    function tick(now){
      const p=Math.min(1,(now-start)/dur);
      const e=1-Math.pow(1-p,3);
      el.textContent = prefix + Math.round(from+(to-from)*e) + suffix;
      if(p<1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  };

  /* toast */
  let _toastTimer;
  window.toast = function(msg){
    let t=$('#toast');
    if(!t){ t=document.createElement('div'); t.id='toast'; t.className='toast'; document.body.appendChild(t); }
    t.textContent=msg; t.classList.add('show');
    clearTimeout(_toastTimer); _toastTimer=setTimeout(()=>t.classList.remove('show'),2400);
  };

  window.wait = ms => new Promise(r=>setTimeout(r,ms));

  /* pipeline runner */
  window.runPipeline = async function(stages, opt){
    opt=opt||{}; const delay=opt.delay||480;
    stages.forEach(id=>{ const s=$('#'+id); if(s) s.classList.remove('on','done'); });
    for(let i=0;i<stages.length;i++){
      const s=$('#'+stages[i]); if(!s) continue;
      s.classList.add('on');
      if(opt.onStep) opt.onStep(i, s);
      await wait(delay);
      s.classList.add('done'); s.classList.remove('on');
    }
  };
  window.setStageDesc = function(id, txt){ const d=$('#'+id+'d'); if(d) d.textContent=txt; };

  /* typewriter terminal */
  window.typeLines = async function(el, lines, opt){
    opt=opt||{}; const speed=opt.speed||14, pause=opt.pause||110;
    el.innerHTML='';
    for(let li=0; li<lines.length; li++){
      const raw=lines[li];
      const ln=document.createElement('div'); ln.className='ln'; el.appendChild(ln);
      const m=raw.match(/^(\^acc|\^ok|\^warn|\^dim)\s([\s\S]*)$/);
      const cls = m ? m[1].slice(1) : '';
      const text = m ? m[2] : raw;
      if(cls) ln.classList.add('c-'+cls);
      for(let i=0;i<text.length;i++){ ln.textContent+=text[i]; if(i%3===0) await wait(speed); }
      el.scrollTop=el.scrollHeight; await wait(pause);
    }
  };
  window.termLine = function(el, text, cls){
    const ln=document.createElement('div'); ln.className='ln'+(cls?' c-'+cls:''); ln.textContent=text;
    el.appendChild(ln); el.scrollTop=el.scrollHeight; return ln;
  };

  window.esc = function(s){ return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); };
  window.md = function(s){ return window.esc(s)
    .replace(/\*\*(.+?)\*\*/g,'<b>$1</b>')
    .replace(/`(.+?)`/g,'<code style="font-family:var(--mono);color:var(--accent)">$1</code>')
    .replace(/\n/g,'<br/>'); };

  window.chatAdd = function(chatEl, role, html, who){
    const m=document.createElement('div'); m.className='msg '+role;
    m.innerHTML='<div class="av">'+(role==='user'?'你':'AI')+'</div><div><div class="who">'+(who||(role==='user'?'You':'Assistant'))+'</div><div class="bubble">'+html+'</div></div>';
    chatEl.appendChild(m); chatEl.scrollTop=chatEl.scrollHeight; return m.querySelector('.bubble');
  };
  window.chatTyping = function(chatEl){
    const m=document.createElement('div'); m.className='msg bot';
    m.innerHTML='<div class="av">AI</div><div><div class="who">Assistant</div><div class="bubble"><span class="typing"><i></i><i></i><i></i></span></div></div>';
    chatEl.appendChild(m); chatEl.scrollTop=chatEl.scrollHeight; return m;
  };

  window.boot = function(){
    const y=$('#year'); if(y) y.textContent=new Date().getFullYear();
    window.observeReveal();
  };
})();
