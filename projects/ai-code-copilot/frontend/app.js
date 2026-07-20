/* AI Code Copilot · 前端逻辑（后端离线时降级为浏览器端启发式分析） */
const API = 'http://localhost:8003/api';
let state = { tab: 'explain', offline: false };
const $ = (id) => document.getElementById(id);
function toast(m) { const t = $('toast'); t.textContent = m; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 2000); }
function esc(s) { return String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c])); }

async function api(path, body) {
  const r = await fetch(API + path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}

const SAMPLE = `def fetch_users(ids):
    users = []
    for id in ids:
        if id == None:
            continue
        try:
            u = db.query(id)
            print(u)
            users.append(u)
        except:
            pass
    return users`;

function init() {
  document.querySelectorAll('#tabs button').forEach(b => b.onclick = () => {
    document.querySelectorAll('#tabs button').forEach(x => x.classList.remove('active'));
    b.classList.add('active'); state.tab = b.dataset.t;
    $('genBar').style.display = state.tab === 'generate' ? 'block' : 'none';
    $('runBtn').textContent = { explain: '解释代码', review: '审查代码', generate: '生成代码', complete: '智能补全' }[state.tab];
  });
  $('sampleBtn').onclick = () => { $('code').value = SAMPLE; toast('已填充示例'); };
  $('runBtn').onclick = run;
  fetch(API + '/health').catch(() => {
    state.offline = true;
    const b = document.querySelector('.badge-live');
    b.style.background = '#fff4e0'; b.style.borderColor = '#ffd8a8'; b.style.color = '#d97706';
    b.innerHTML = '<span class="dot" style="background:#d97706"></span> 演示模式（本地分析）';
  });
}

async function run() {
  const code = $('code').value, lang = $('lang').value;
  const tab = state.tab;
  if (tab !== 'generate' && !code.trim()) return toast('请输入代码');
  $('out').innerHTML = '<div class="empty">分析中…</div>';
  try {
    if (tab === 'explain') renderExplain(state.offline ? localExplain(code, lang) : await api('/explain', { code, lang }));
    else if (tab === 'review') renderReview(state.offline ? localReview(code, lang) : await api('/review', { code, lang }));
    else if (tab === 'generate') renderGenerate(state.offline ? localGenerate($('genPrompt').value, lang) : await api('/generate', { prompt: $('genPrompt').value, lang }));
    else renderComplete(state.offline ? localComplete(code, lang) : await api('/complete', { code, lang }));
  } catch { state.offline = true; run(); }
}

/* ---------------- 渲染 ---------------- */
function renderExplain(d) {
  if (!d.ok) return $('out').innerHTML = `<div class="issue high"><div class="top"><span class="sev">ERR</span>${esc(d.error)}</div></div>`;
  const s = d.structure;
  $('out').innerHTML = `
    <div class="stat-row">
      <div class="pill"><div class="n">${d.lines}</div><div class="l">代码行数</div></div>
      <div class="pill"><div class="n">${(s.functions || []).length}</div><div class="l">函数</div></div>
      <div class="pill"><div class="n">${d.cyclomatic_complexity}</div><div class="l">圈复杂度</div></div>
      <div class="pill"><div class="n" style="font-size:15px;padding-top:4px">${d.complexity_level}</div><div class="l">复杂度评估</div></div>
    </div>
    <div class="result-block"><h4>整体说明</h4><p style="font-size:14px;color:var(--ink-2)">${esc(d.summary)}</p></div>
    <div class="result-block"><h4>执行步骤</h4><div class="steps">${(d.steps || []).map(x => `<div class="step">${esc(x)}</div>`).join('')}</div></div>
    ${(s.functions || []).length ? `<div class="result-block"><h4>函数清单</h4>${s.functions.map(f => `<div class="issue low"><div class="top">${esc(f.name)}(${(f.args || []).join(', ')}) ${f.doc === false ? '<span class="ln">⚠ 无 docstring</span>' : ''}</div></div>`).join('')}</div>` : ''}`;
}

function renderReview(d) {
  const g = d.grade;
  $('out').innerHTML = `
    <div class="result-block" style="text-align:center;margin-bottom:20px">
      <span class="score-big" style="color:${d.score >= 75 ? 'var(--ok)' : d.score >= 60 ? 'var(--med)' : 'var(--high)'}">${d.score}</span>
      <span class="grade ${g}">${g}</span>
      <div style="font-size:12px;color:var(--ink-3);margin-top:4px">代码健康分</div>
    </div>
    <div class="stat-row">
      <div class="pill"><div class="n" style="color:var(--high)">${d.counts.high}</div><div class="l">严重</div></div>
      <div class="pill"><div class="n" style="color:var(--med)">${d.counts.medium}</div><div class="l">中等</div></div>
      <div class="pill"><div class="n" style="color:var(--low)">${d.counts.low}</div><div class="l">轻微</div></div>
    </div>
    <div class="result-block"><h4>问题清单（${d.issues.length}）</h4>
    ${d.issues.length ? d.issues.map(i => `
      <div class="issue ${i.severity}">
        <div class="top"><span class="sev">${{ high: '严重', medium: '中等', low: '轻微' }[i.severity]}</span>${esc(i.message)}<span class="ln">第 ${i.line} 行</span></div>
        <div class="fix">建议：${esc(i.suggestion)}</div>
        ${i.code ? `<div class="snip">${esc(i.code)}</div>` : ''}
      </div>`).join('') : '<div class="issue low"><div class="top">✓ 未发现明显问题，代码质量良好</div></div>'}
    </div>`;
}

function renderGenerate(d) {
  $('out').innerHTML = `<div class="result-block"><h4>${esc(d.note)}</h4><pre class="code">${esc(d.code)}</pre>
    <button class="btn btn-ghost" style="margin-top:12px" onclick="navigator.clipboard.writeText(${JSON.stringify(d.code)});window.__t&&window.__t('已复制')">复制代码</button></div>`;
  window.__t = toast;
}

function renderComplete(d) {
  $('out').innerHTML = `<div class="result-block"><h4>补全建议</h4>${d.completions.map(c => `<pre class="code">${esc(c)}</pre>`).join('')}</div>`;
}

/* ---------------- 本地降级分析 ---------------- */
function localExplain(code, lang) {
  const lines = code.split('\n');
  const funcs = [...code.matchAll(/def\s+(\w+)\s*\(([^)]*)\)|function\s+(\w+)/g)].map(m => ({ name: m[1] || m[3], args: (m[2] || '').split(',').map(s => s.trim()).filter(Boolean) }));
  const loops = (code.match(/\b(for|while)\b/g) || []).length;
  const branches = (code.match(/\b(if|elif|else|switch|catch|try)\b/g) || []).length;
  const complexity = 1 + loops + branches;
  const level = complexity <= 5 ? '简单' : complexity <= 10 ? '中等' : '偏高，建议拆分';
  return { ok: true, lines: lines.length, cyclomatic_complexity: complexity, complexity_level: level, structure: { functions: funcs, loops, branches }, summary: `这段代码包含 ${funcs.length} 个函数、${loops} 处循环、${branches} 处分支。`, steps: funcs.map(f => `定义函数 ${f.name}()`).concat(loops ? ['执行循环体'] : []).slice(0, 8) };
}
function localReview(code, lang) {
  const rules = lang === 'python'
    ? [[/except\s*:/, 'high', '捕获裸异常 except:', '指定具体异常类型'], [/==\s*None|!=\s*None/, 'medium', '与 None 用 == 比较', '改用 is None'], [/print\(/, 'low', '使用 print', '改用 logging'], [/\beval\(/, 'high', '使用 eval() 有安全风险', '改用安全解析']]
    : [[/\bvar\b/, 'medium', '使用 var 声明', '改用 let/const'], [/==(?!=)|!=(?!=)/, 'medium', '非严格相等', '改用 ===/!=='], [/console\.log/, 'low', 'console.log', '移除或统一日志']];
  const issues = [];
  code.split('\n').forEach((ln, i) => {
    rules.forEach(([p, s, m, f]) => { if (p.test(ln)) issues.push({ line: i + 1, severity: s, message: m, suggestion: f, code: ln.trim().slice(0, 70) }); });
    if (ln.length > 100) issues.push({ line: i + 1, severity: 'low', message: `行过长（${ln.length}）`, suggestion: '拆分为多行', code: ln.trim().slice(0, 50) + '…' });
  });
  const score = Math.max(0, 100 - issues.reduce((a, i) => a + ({ high: 15, medium: 8, low: 3 })[i.severity], 0));
  const counts = { high: 0, medium: 0, low: 0 }; issues.forEach(i => counts[i.severity]++);
  return { issues: issues.sort((a, b) => a.line - b.line), counts, score, grade: score >= 90 ? 'A' : score >= 75 ? 'B' : score >= 60 ? 'C' : 'D' };
}
function localGenerate(prompt, lang) {
  const p = (prompt || '').toLowerCase();
  if (/api|fastapi|接口|服务/.test(p)) return { note: '生成了一个 FastAPI 接口脚手架', code: 'from fastapi import FastAPI\n\napp = FastAPI()\n\n\n@app.get("/api/hello")\ndef hello(name: str = "world"):\n    return {"message": f"hello, {name}"}\n' };
  if (/排序|sort|快排/.test(p)) return { note: '生成了快速排序实现', code: 'def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr)//2]\n    return quicksort([x for x in arr if x<pivot]) + [x for x in arr if x==pivot] + quicksort([x for x in arr if x>pivot])\n' };
  if (/爬虫|爬取|抓取/.test(p)) return { note: '生成了网页抓取脚本', code: 'import requests\nfrom bs4 import BeautifulSoup\n\ndef fetch(url):\n    r = requests.get(url, timeout=10)\n    soup = BeautifulSoup(r.text, "html.parser")\n    return [h.get_text(strip=True) for h in soup.select("h1, h2")]\n' };
  const fn = (p.replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'solution').slice(0, 24);
  return { note: '根据描述生成了函数骨架', code: `def ${fn}(data):\n    """根据需求「${prompt}」实现。"""\n    # TODO: 实现核心逻辑\n    return None\n` };
}
function localComplete(code, lang) {
  const last = (code.trim().split('\n').pop() || '').trim();
  const sug = [];
  if (last.startsWith('def ') && last.endsWith(':')) sug.push('    """补全：函数说明。"""\n    pass');
  if (/for\s+\w+\s+in\s+.+:$/.test(last)) sug.push('    # 循环体');
  if (last.endsWith('try:')) sug.push('    pass\nexcept Exception as e:\n    logging.error(e)');
  if (!sug.length) sug.push('# 补全建议：为上一行补充实现或返回值');
  return { completions: sug };
}

$('code').value = SAMPLE;
init();
