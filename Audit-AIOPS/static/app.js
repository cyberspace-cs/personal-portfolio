// 审计智能一体化运维平台 · 前端交互（对接 FastAPI）
const API = "";
let sessionId = null;

async function api(path, opts) {
  const res = await fetch(API + path, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2200);
}

// ---------- 服务目录 + 高频服务网格 ----------
async function loadCatalog() {
  try {
    const data = await api("/api/catalog");
    document.getElementById("catalogTotal").textContent = data.total + "项";
    const groups = {};
    data.items.forEach((it) => { (groups[it.group] = groups[it.group] || []).push(it); });

    const host = document.getElementById("catalogList");
    host.innerHTML = "";
    Object.entries(groups).forEach(([g, items]) => {
      const wrap = document.createElement("div");
      wrap.className = "cat-group";
      wrap.innerHTML = `<div class="cat-title">${g}</div>`;
      items.forEach((it) => {
        const el = document.createElement("div");
        el.className = "cat-item";
        el.innerHTML = `<div class="ic">${it.icon}</div><div><div>${it.name}</div><div class="meta">${it.desc}</div></div>`;
        el.onclick = () => {
          document.getElementById("chatInput").value = "我要办理：" + it.name;
          document.getElementById("chatInput").focus();
        };
        wrap.appendChild(el);
      });
      host.appendChild(wrap);
    });

    const grid = document.getElementById("svcGrid");
    grid.innerHTML = "";
    data.items.slice(0, 8).forEach((it) => {
      const el = document.createElement("div");
      el.className = "svc";
      el.innerHTML = `<span class="badge">${it.automated ? "自动化" : "审批"}</span><div class="ic">${it.icon}</div><h4>${it.name}</h4><p>${it.desc}</p>`;
      el.onclick = () => {
        document.getElementById("chatInput").value = "我要办理：" + it.name;
        sendChat();
      };
      grid.appendChild(el);
    });
  } catch (e) { console.error(e); }
}

// ---------- 工单进度卡片 ----------
function renderProgress(wo) {
  if (!wo) return;
  document.getElementById("progressStatus").textContent = wo.status === "completed" ? "已完成" : "处理中";
  const sh = document.getElementById("stepperHost");
  sh.innerHTML = wo.steps.map((s, i) => {
    const mark = s.status === "done" ? "✓" : String(i + 1);
    return `<div class="step ${s.status}">
      <div class="node">${mark}</div>
      <div class="name">${s.name}</div>
      <div class="time">${s.time || ""}</div>
      ${s.owner ? `<div class="owner">${s.owner}</div>` : ""}
    </div>`;
  }).join("");
  const cur = wo.steps.find((s) => s.status === "doing");
  document.getElementById("orderMetaHost").innerHTML = `
    <div>工单号 <b>${wo.id}</b></div>
    <div>类型 <b>${wo.title}</b></div>
    <div>当前节点 <b>${cur ? cur.name : "已完成"}</b></div>
    <a class="quick-link">一键联系责任人 →</a>`;
}

async function loadWorkorders() {
  try {
    const wos = await api("/api/workorders");
    if (wos.length) renderProgress(wos[wos.length - 1]);
  } catch (e) { console.error(e); }
}

// ---------- 待我审批 ----------
async function loadTodos() {
  try {
    const wos = await api("/api/workorders");
    const list = document.getElementById("todoList");
    list.innerHTML = "";
    let n = 0;
    wos.forEach((wo) => {
      const cur = wo.steps.find((s) => s.status === "doing");
      if (!cur || !cur.name.startsWith("审批")) return;
      n++;
      const li = document.createElement("li");
      li.innerHTML = `<span class="st y"></span><div class="body">${wo.title}<small>${wo.id} · ${cur.name} · ${cur.owner || ""}</small></div><button class="btn-approve">审批</button>`;
      li.querySelector(".btn-approve").onclick = async () => {
        await api(`/api/workorders/${wo.id}/approve`, { method: "POST" });
        toast("已审批：" + cur.name);
        await loadWorkorders();
        await loadTodos();
      };
      list.appendChild(li);
    });
    if (!n) list.innerHTML = `<li style="padding:14px 16px;color:var(--muted);font-size:13px">暂无待审批事项</li>`;
  } catch (e) { console.error(e); }
}

// ---------- 智能监控 ----------
async function loadMonitor() {
  try {
    const m = await api("/api/monitor");
    document.getElementById("kAnom").textContent = m.anomalies_today;
    document.getElementById("kDev").textContent = m.online_devices;
    document.getElementById("kAuto").textContent = m.auto_rate;
    document.getElementById("kDur").textContent = m.avg_duration_h;
  } catch (e) { console.error(e); }
}

// ---------- 对话直达服务单 ----------
function addBubble(role, content, isHtml) {
  const log = document.getElementById("chatLog");
  const b = document.createElement("div");
  b.className = "bubble " + role;
  if (isHtml) b.innerHTML = content; else b.textContent = content;
  log.appendChild(b);
  log.scrollTop = log.scrollHeight;
}

function quickSug(s) {
  document.getElementById("chatInput").value = s;
  document.getElementById("chatInput").focus();
}

async function sendChat() {
  const input = document.getElementById("chatInput");
  const msg = input.value.trim();
  if (!msg) return;
  addBubble("user", msg);
  input.value = "";
  try {
    const data = await api("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, session_id: sessionId }),
    });
    sessionId = data.session_id || sessionId;
    let html = escapeHtml(data.reply);
    if (data.suggestions && data.suggestions.length) {
      html += `<div>${data.suggestions
        .map((s) => `<span class="sug" onclick="quickSug('${s.replace(/'/g, "\\'")}')">${escapeHtml(s)}</span>`)
        .join("")}</div>`;
    }
    addBubble("bot", html, true);
    if (data.work_order) {
      renderProgress(data.work_order);
      toast("已生成工单 " + data.work_order.id);
      await loadWorkorders();
      await loadTodos();
    }
  } catch (e) {
    addBubble("bot", "服务异常：" + e.message, false);
  }
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// ---------- 事件绑定 ----------
document.getElementById("chatSend").onclick = sendChat;
document.getElementById("chatInput").addEventListener("keydown", (e) => { if (e.key === "Enter") sendChat(); });
document.getElementById("chips").addEventListener("click", (e) => {
  const t = e.target.closest(".chip");
  if (!t) return;
  const txt = t.textContent;
  if (txt.includes("工单到哪")) {
    document.getElementById("chatInput").value = "我的工单进度到哪了";
    sendChat();
  } else {
    const name = txt.replace(/^[＋?？\s]+/, "").trim();
    document.getElementById("chatInput").value = "我要办理：" + name;
    sendChat();
  }
});

// ---------- 知识库问答（RAG） ----------
async function askKB() {
  const input = document.getElementById("kbInput");
  const q = input.value.trim();
  if (!q) return;
  const host = document.getElementById("kbAnswer");
  const src = document.getElementById("kbSources");
  host.textContent = "检索中…";
  src.innerHTML = "";
  try {
    const data = await api("/api/knowledge/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q }),
    });
    host.textContent = data.answer;
    if (data.retrieved && data.retrieved.length) {
      src.innerHTML =
        '<div style="font-size:11px;color:var(--muted);margin-bottom:5px">参考来源</div>' +
        data.retrieved
          .map(
            (r) =>
              `<div style="padding:7px 9px;border:1px solid var(--line);border-radius:9px;margin-bottom:6px;background:var(--surface-2)">
                <div style="font-size:12px;font-weight:600;color:var(--c-primary)">${escapeHtml(r.title)} <span style="color:var(--muted);font-weight:400">· 相似度 ${r.score}</span></div>
                <div style="font-size:11.5px;color:var(--muted);margin-top:2px">${escapeHtml(r.snippet)}…</div>
              </div>`
          )
          .join("");
    }
  } catch (e) {
    host.textContent = "服务异常：" + e.message;
  }
}
document.getElementById("kbAsk").onclick = askKB;
document.getElementById("kbInput").addEventListener("keydown", (e) => { if (e.key === "Enter") askKB(); });

// ---------- 初始化 ----------
loadCatalog();
loadMonitor();
loadWorkorders();
loadTodos();
