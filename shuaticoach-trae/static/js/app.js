/* ============================================
   专属刷题教练 - 主应用脚本
   TRAE AI 创造力大赛 · 学习工作赛道
   ============================================ */

// ========== STATE ==========
const state = {
    user: null,
    stats: { totalAnswered: 0, correctCount: 0, streak: 0, lastDate: '', wrongBook: {}, answered: {} },
    answered: {},
    currentFilter: 'all',
    currentQuestionIndex: 0,
    selectedAnswer: null,
    multiSelectValues: [],
    questions: []
};

// ========== QUESTION BANK ==========
const DEFAULT_QUESTIONS = [
    { id:1, source:'LeetCode', type:'单选', difficulty:'简单', question:'两数之和问题中，使用哈希表可以将时间复杂度优化到多少？', options:['O(n)','O(n²)','O(log n)','O(n log n)'], answer:0, explanation:'使用哈希表存储已遍历元素，一次遍历即可找到目标对，时间复杂度 O(n)。', knowledge:'哈希表' },
    { id:2, source:'LeetCode', type:'单选', difficulty:'简单', question:'在链表反转问题中，需要几个指针来完成原地反转？', options:['1个','2个','3个','4个'], answer:2, explanation:'需要三个指针：prev、curr、next。', knowledge:'链表' },
    { id:3, source:'牛客网', type:'单选', difficulty:'中等', question:'以下哪种排序算法是稳定的？', options:['快速排序','堆排序','归并排序','选择排序'], answer:2, explanation:'归并排序在合并过程中保持相等元素的相对顺序。', knowledge:'排序' },
    { id:4, source:'牛客网', type:'判断', difficulty:'简单', question:'二叉搜索树的中序遍历结果是有序的。', options:['正确','错误'], answer:0, explanation:'二叉搜索树的性质：左<根<右，中序遍历得递增序列。', knowledge:'树' },
    { id:5, source:'AcWing', type:'单选', difficulty:'中等', question:'动态规划的两个核心要素是什么？', options:['递归和回溯','贪心和分治','最优子结构和重叠子问题','枚举和剪枝'], answer:2, explanation:'动态规划的核心是最优子结构和重叠子问题。', knowledge:'动态规划' },
    { id:6, source:'AcWing', type:'多选', difficulty:'简单', question:'以下哪些属于算法设计中的常用技巧？', options:['双指针','滑动窗口','前缀和','迪杰斯特拉'], answer:0, explanation:'双指针、滑动窗口、前缀和都是常用算法技巧。', knowledge:'算法技巧' },
    { id:7, source:'洛谷', type:'单选', difficulty:'简单', question:'vector 的 push_back 操作均摊时间复杂度是多少？', options:['O(1)','O(n)','O(log n)','O(n²)'], answer:0, explanation:'vector 的 push_back 均摊 O(1)。', knowledge:'数据结构' },
    { id:8, source:'洛谷', type:'判断', difficulty:'中等', question:'DFS 总是能找到无权图中的最短路径。', options:['正确','错误'], answer:1, explanation:'DFS 不保证最短路径，应使用 BFS。', knowledge:'图论' },
    { id:9, source:'Codeforces', type:'单选', difficulty:'中等', question:'KMP 字符串匹配算法的时间复杂度是多少？', options:['O(n)','O(n*m)','O(n²)','O(log n)'], answer:0, explanation:'KMP 算法 O(n) 线性时间匹配。', knowledge:'字符串' },
    { id:10, source:'Codeforces', type:'多选', difficulty:'中等', question:'以下哪些数据结构可以用来实现优先队列？', options:['二叉堆','斐波那契堆','平衡树','普通队列'], answer:0, explanation:'二叉堆和斐波那契堆都可以实现优先队列。', knowledge:'数据结构' },
    { id:11, source:'考研', type:'单选', difficulty:'简单', question:'Cache 的映射方式不包括以下哪种？', options:['直接映射','全相联映射','组相联映射','链式映射'], answer:3, explanation:'三种映射：直接映射、全相联映射、组相联映射。', knowledge:'计算机组成' },
    { id:12, source:'考研', type:'判断', difficulty:'简单', question:'死锁的四个必要条件是：互斥、持有并等待、不可抢占、循环等待。', options:['正确','错误'], answer:0, explanation:'正确。死锁四个必要条件。', knowledge:'操作系统' },
    { id:13, source:'考研', type:'单选', difficulty:'中等', question:'TCP 三次握手中，第二次握手包含的标志位是？', options:['SYN','ACK','SYN+ACK','FIN'], answer:2, explanation:'第二次握手 SYN+ACK。', knowledge:'计算机网络' },
    { id:14, source:'考公', type:'单选', difficulty:'简单', question:'行测：某商品原价200元，先涨价20%再打八折，最终价格？', options:['192元','200元','208元','180元'], answer:0, explanation:'200 × 1.2 × 0.8 = 192。', knowledge:'数量关系' },
    { id:15, source:'考公', type:'判断', difficulty:'简单', question:'申论大作文字数要求一般为800-1000字。', options:['正确','错误'], answer:0, explanation:'正确。国考申论800-1000字。', knowledge:'申论' },
    { id:16, source:'考公', type:'单选', difficulty:'简单', question:'我国现行宪法是哪一年通过的？', options:['1954年','1975年','1978年','1982年'], answer:3, explanation:'1982年12月4日通过。', knowledge:'常识判断' },
    { id:17, source:'大厂', type:'单选', difficulty:'简单', question:'React 中哪个 Hook 用于处理副作用？', options:['useState','useEffect','useContext','useReducer'], answer:1, explanation:'useEffect 处理副作用。', knowledge:'React' },
    { id:18, source:'大厂', type:'多选', difficulty:'简单', question:'以下哪些是 HTTP 常见状态码？', options:['200 OK','301 永久重定向','404 未找到','502 网关错误'], answer:0, explanation:'以上都是常见状态码。', knowledge:'网络' },
    { id:19, source:'大厂', type:'单选', difficulty:'中等', question:'MySQL InnoDB 默认隔离级别？', options:['READ UNCOMMITTED','READ COMMITTED','REPEATABLE READ','SERIALIZABLE'], answer:2, explanation:'默认 REPEATABLE READ。', knowledge:'数据库' },
    { id:20, source:'LeetCode', type:'单选', difficulty:'简单', question:'二分查找算法的时间复杂度是？', options:['O(1)','O(n)','O(log n)','O(n log n)'], answer:2, explanation:'每次减半，O(log n)。', knowledge:'算法' },
    { id:21, source:'牛客网', type:'填空', difficulty:'简单', question:'Java 中实现多线程的接口名称是 ____。', options:['Runnable'], answer:0, explanation:'实现 Runnable 接口或继承 Thread 类。', knowledge:'Java' }
];

// ========== API ==========
async function api(path, opts = {}) {
    try {
        const res = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...opts });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || res.statusText);
        }
        return await res.json();
    } catch (e) {
        throw e;
    }
}

// ========== AUTH ==========
async function loadUser() {
    try {
        const data = await api('/api/auth/me');
        state.user = data;
        state.stats = data.stats || state.stats;
        state.answered = data.stats?.answered || {};
        showApp();
    } catch (e) {
        showAuth();
    }
}

function showAuth() {
    document.getElementById('authPage').classList.add('active');
    document.getElementById('mainApp').classList.remove('active');
}

function showApp() {
    document.getElementById('authPage').classList.remove('active');
    document.getElementById('mainApp').classList.add('active');
    updateUserUI();
    state.questions = DEFAULT_QUESTIONS;
    renderQuestion();
    updateAllUI();
    initCharts();
}

async function handleLogin() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errEl = document.getElementById('loginError');
    if (!username || !password) { errEl.textContent = '请填写用户名和密码'; errEl.style.display = 'block'; return; }
    try {
        await api('/api/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) });
        await loadUser();
    } catch (e) {
        errEl.textContent = e.message; errEl.style.display = 'block';
    }
}

async function handleRegister() {
    const username = document.getElementById('regUsername').value.trim();
    const password = document.getElementById('regPassword').value;
    const email = document.getElementById('regEmail').value.trim();
    const errEl = document.getElementById('regError');
    if (!username || !password) { errEl.textContent = '请填写用户名和密码'; errEl.style.display = 'block'; return; }
    if (password.length < 4) { errEl.textContent = '密码至少4位'; errEl.style.display = 'block'; return; }
    try {
        await api('/api/auth/register', { method: 'POST', body: JSON.stringify({ username, password, email }) });
        await loadUser();
    } catch (e) {
        errEl.textContent = e.message; errEl.style.display = 'block';
    }
}

async function handleLogout() {
    await api('/api/auth/logout', { method: 'POST' });
    state.user = null;
    state.stats = { totalAnswered: 0, correctCount: 0, streak: 0, lastDate: '', wrongBook: {}, answered: {} };
    state.answered = {};
    showAuth();
}

function updateUserUI() {
    if (!state.user) return;
    document.getElementById('userName').textContent = state.user.username;
}

function switchAuthTab(tab) {
    document.getElementById('loginForm').style.display = tab === 'login' ? 'block' : 'none';
    document.getElementById('regForm').style.display = tab === 'register' ? 'block' : 'none';
    document.getElementById('loginError').style.display = 'none';
    document.getElementById('regError').style.display = 'none';
}

// ========== DATA PERSIST ==========
async function saveData() {
    state.stats.answered = state.answered;
    try {
        await api('/api/data', { method: 'POST', body: JSON.stringify({ stats: state.stats, answered: state.answered }) });
    } catch (e) { /* silent fail */ }
}

// ========== QUIZ ==========
function getFilteredQuestions() {
    if (state.currentFilter === 'all') return state.questions;
    return state.questions.filter(q => q.source === state.currentFilter);
}

function renderQuestion() {
    const questions = getFilteredQuestions();
    if (questions.length === 0) { state.currentQuestionIndex = 0; return; }
    if (state.currentQuestionIndex >= questions.length) state.currentQuestionIndex = questions.length - 1;
    const q = questions[state.currentQuestionIndex];
    state.selectedAnswer = state.answered[q.id] !== undefined ? state.answered[q.id] : null;
    const qAnswered = state.answered[q.id] !== undefined;
    const isCorrect = qAnswered && state.answered[q.id] === q.answer;

    document.getElementById('qSource').textContent = q.source;
    document.getElementById('qType').textContent = q.type;
    document.getElementById('qDiff').textContent = q.difficulty || '';
    document.getElementById('qNumber').textContent = `第 ${state.currentQuestionIndex + 1}/${questions.length} 题`;
    document.getElementById('qText').textContent = q.question;

    const optsDiv = document.getElementById('qOptions');
    optsDiv.innerHTML = q.options.map((opt, i) => {
        let cls = 'option';
        if (qAnswered) {
            if (i === q.answer) cls += ' correct';
            else if (state.answered[q.id] !== q.answer && state.answered[q.id] === i) cls += ' wrong';
        } else if (state.selectedAnswer === i) {
            cls += ' selected';
        }
        return `<div class="${cls}" onclick="selectOption(${i})" data-idx="${i}">
            <div class="option-letter">${String.fromCharCode(65 + i)}</div>
            <div class="option-text">${opt}</div>
        </div>`;
    }).join('');

    const explDiv = document.getElementById('qExplanation');
    const explText = document.getElementById('qExplanationText');
    if (qAnswered) { explDiv.classList.add('show'); explText.textContent = q.explanation; }
    else { explDiv.classList.remove('show'); }

    document.getElementById('btnSubmit').style.display = qAnswered ? 'none' : 'inline-flex';
    renderAnswerGrid();
}

function selectOption(idx) {
    const questions = getFilteredQuestions();
    if (questions.length === 0) return;
    const q = questions[state.currentQuestionIndex];
    if (state.answered[q.id] !== undefined) return;
    if (q.type === '多选') {
        const i = state.multiSelectValues.indexOf(idx);
        if (i >= 0) state.multiSelectValues.splice(i, 1);
        else state.multiSelectValues.push(idx);
        state.selectedAnswer = state.multiSelectValues.length > 0 ? state.multiSelectValues[0] : null;
        renderQuestion();
        return;
    }
    state.selectedAnswer = idx;
    state.multiSelectValues = [];
    renderQuestion();
}

function submitAnswer() {
    const questions = getFilteredQuestions();
    if (questions.length === 0) return;
    const q = questions[state.currentQuestionIndex];
    if (state.answered[q.id] !== undefined) return;
    let finalAnswer;
    if (q.type === '多选') {
        if (state.multiSelectValues.length === 0) { showToast('请至少选择一个选项', 'error'); return; }
        finalAnswer = state.multiSelectValues[0];
    } else {
        if (state.selectedAnswer === null) { showToast('请先选择一个选项', 'error'); return; }
        finalAnswer = state.selectedAnswer;
    }
    state.answered[q.id] = finalAnswer;
    state.stats.totalAnswered = (state.stats.totalAnswered || 0) + 1;
    const isCorrect = finalAnswer === q.answer;
    if (isCorrect) state.stats.correctCount = (state.stats.correctCount || 0) + 1;
    else {
        const key = q.knowledge || q.id;
        if (!state.stats.wrongBook) state.stats.wrongBook = {};
        state.stats.wrongBook[key] = (state.stats.wrongBook[key] || 0) + 1;
    }
    updateStreak();
    saveData();
    renderQuestion();
    updateAllUI();
    showToast(isCorrect ? '回答正确！继续加油！' : '回答错误，已加入错题本', isCorrect ? 'success' : 'error');
}

function updateStreak() {
    const today = new Date().toISOString().slice(0, 10);
    if (state.stats.lastDate === today) return;
    const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    if (state.stats.lastDate === yesterday) state.stats.streak = (state.stats.streak || 0) + 1;
    else if (state.stats.lastDate !== today) state.stats.streak = 1;
    state.stats.lastDate = today;
}

function prevQuestion() {
    if (state.currentQuestionIndex > 0) { state.currentQuestionIndex--; state.multiSelectValues = []; renderQuestion(); }
}
function nextQuestion() {
    const questions = getFilteredQuestions();
    if (state.currentQuestionIndex < questions.length - 1) { state.currentQuestionIndex++; state.multiSelectValues = []; renderQuestion(); }
}

function renderAnswerGrid() {
    const questions = getFilteredQuestions();
    const grid = document.getElementById('answerGrid');
    if (!grid) return;
    grid.innerHTML = questions.map((q, i) => {
        let cls = 'answer-dot';
        if (i === state.currentQuestionIndex) cls += ' current';
        if (state.answered[q.id] !== undefined) {
            cls += state.answered[q.id] === q.answer ? ' dot-correct' : ' dot-wrong';
        }
        return `<div class="${cls}" onclick="goToQuestion(${i})">${i + 1}</div>`;
    }).join('');
    const answered = questions.filter(q => state.answered[q.id] !== undefined).length;
    const pct = questions.length > 0 ? Math.round((answered / questions.length) * 100) : 0;
    document.getElementById('quizProgress').style.width = pct + '%';
    document.getElementById('quizProgressText').textContent = `${answered}/${questions.length} 已答`;
    const correct = questions.filter(q => state.answered[q.id] === q.answer).length;
    document.getElementById('quizCorrectText').textContent = `正确 ${correct}`;
}

function goToQuestion(idx) {
    state.currentQuestionIndex = idx;
    state.multiSelectValues = [];
    const q = getFilteredQuestions()[idx];
    state.selectedAnswer = q && state.answered[q.id] !== undefined ? state.answered[q.id] : null;
    renderQuestion();
}

// ========== UI UPDATES ==========
function updateAllUI() {
    const total = state.stats.totalAnswered || 0;
    const correct = state.stats.correctCount || 0;
    const rate = total > 0 ? Math.round((correct / total) * 100) : 0;
    document.getElementById('totalQuestions').textContent = total;
    document.getElementById('accuracyRate').textContent = rate + '%';
    document.getElementById('streakCount').textContent = state.stats.streak || 0;
    document.getElementById('wrongCount').textContent = total - correct;
    document.getElementById('heroTotal').textContent = total;
    document.getElementById('heroStreak').textContent = state.stats.streak || 0;
    document.getElementById('heroRate').textContent = total > 0 ? rate + '%' : '--';
    renderWrongBook();
    renderRecList();
    renderAnswerGrid();
    updateChartsData();
}

function renderWrongBook() {
    const wb = state.stats.wrongBook || {};
    const entries = Object.entries(wb).sort((a, b) => b[1] - a[1]);
    const container = document.getElementById('wrongList');
    const empty = document.getElementById('wrongEmpty');
    if (!container) return;
    container.querySelectorAll('.wrong-item').forEach(el => el.remove());
    if (entries.length === 0) {
        if (empty) empty.style.display = 'block';
        return;
    }
    if (empty) empty.style.display = 'none';
    entries.forEach(([key, count]) => {
        const q = state.questions.find(q => (q.knowledge || q.id) === key);
        const div = document.createElement('div');
        div.className = 'wrong-item';
        div.innerHTML = `<div class="wrong-count">${count}次</div>
            <div class="wrong-content"><div class="wrong-title">${q ? q.question : key}</div>
            <div class="wrong-meta"><span class="tag">${q ? q.knowledge : ''}</span><span class="tag">${q ? q.source : ''}</span></div></div>`;
        container.appendChild(div);
    });
}

function renderRecList() {
    const wb = state.stats.wrongBook || {};
    const weakPoints = Object.entries(wb).sort((a, b) => b[1] - a[1]).slice(0, 5).map(e => e[0]);
    const recs = state.questions.filter(q => weakPoints.includes(q.knowledge || q.id) && state.answered[q.id] === undefined);
    const container = document.getElementById('recList');
    const empty = document.getElementById('recEmpty');
    if (!container) return;
    container.querySelectorAll('.rec-item').forEach(el => el.remove());
    if (recs.length === 0) {
        if (empty) empty.style.display = 'block';
        return;
    }
    if (empty) empty.style.display = 'none';
    recs.slice(0, 5).forEach(q => {
        const div = document.createElement('div');
        div.className = 'rec-item';
        div.onclick = () => {
            document.getElementById('quiz').scrollIntoView({ behavior: 'smooth' });
            state.currentFilter = 'all';
            state.currentQuestionIndex = state.questions.indexOf(q);
            renderQuestion();
        };
        div.innerHTML = `<div class="rec-icon">🎯</div>
            <div class="rec-content"><div class="rec-title">${q.question}</div>
            <div class="rec-meta"><span class="tag">${q.knowledge}</span><span class="tag">${q.source}</span></div></div>`;
        container.appendChild(div);
    });
}

// ========== CHARTS ==========
let charts = {};
const knowledgePoints = ['哈希表', '链表', '排序', '树', '动态规划', '算法技巧', '数据结构', '图论', '字符串', '计算机网络', '操作系统', '数据库'];
const knowledgeMastery = [75, 60, 55, 45, 30, 80, 70, 50, 65, 40, 35, 45];
const platformLabels = ['LeetCode', '牛客', 'AcWing', '洛谷', 'Codeforces', '考研', '考公', '大厂'];
const platformCounts = [4, 3, 2, 2, 2, 3, 3, 3];

function initCharts() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#e8ecf4' : '#0f172a';
    const gridColor = isDark ? 'rgba(255,255,255,.08)' : 'rgba(15,23,42,.08)';

    const trendCtx = document.getElementById('trendChart');
    if (trendCtx) {
        charts.trend = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: getLast7Days(),
                datasets: [
                    { label: '刷题数', data: getLast7DaysData(), borderColor: isDark ? '#a78bfa' : '#722ED1', backgroundColor: isDark ? 'rgba(167,139,250,.1)' : 'rgba(114,46,209,.1)', fill: true, tension: .4, pointRadius: 4, pointBackgroundColor: isDark ? '#a78bfa' : '#722ED1' },
                    { label: '正确数', data: getLast7DaysCorrect(), borderColor: isDark ? '#38bdf8' : '#165DFF', backgroundColor: isDark ? 'rgba(56,189,248,.1)' : 'rgba(22,93,255,.1)', fill: true, tension: .4, pointRadius: 4, pointBackgroundColor: isDark ? '#38bdf8' : '#165DFF' }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: textColor } } }, scales: { x: { ticks: { color: textColor }, grid: { color: gridColor } }, y: { ticks: { color: textColor }, grid: { color: gridColor } } } }
        });
    }

    const radarCtx = document.getElementById('radarChart');
    if (radarCtx) {
        charts.radar = new Chart(radarCtx, {
            type: 'radar',
            data: { labels: knowledgePoints, datasets: [{ label: '掌握度', data: knowledgeMastery, borderColor: isDark ? '#a78bfa' : '#722ED1', backgroundColor: isDark ? 'rgba(167,139,250,.2)' : 'rgba(114,46,209,.2)', pointBackgroundColor: isDark ? '#a78bfa' : '#722ED1' }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: textColor } } }, scales: { r: { angleLines: { color: gridColor }, grid: { color: gridColor }, pointLabels: { color: textColor }, ticks: { color: textColor, backdropColor: 'transparent' }, suggestedMin: 0, suggestedMax: 100 } } }
        });
    }

    const pieCtx = document.getElementById('pieChart');
    if (pieCtx) {
        charts.pie = new Chart(pieCtx, {
            type: 'doughnut',
            data: { labels: platformLabels, datasets: [{ data: platformCounts, backgroundColor: ['#a78bfa','#38bdf8','#818cf8','#2dd4bf','#f472b6','#fb923c','#fbbf24','#34d399'], borderColor: isDark ? '#060913' : '#f0f4fc', borderWidth: 2 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: textColor }, position: 'bottom' } } }
        });
    }
}

function updateChartsData() {
    if (charts.trend) { charts.trend.data.labels = getLast7Days(); charts.trend.data.datasets[0].data = getLast7DaysData(); charts.trend.data.datasets[1].data = getLast7DaysCorrect(); charts.trend.update(); }
    if (charts.radar) charts.radar.update();
    if (charts.pie) charts.pie.update();
}

function getLast7Days() {
    const days = [];
    for (let i = 6; i >= 0; i--) { const d = new Date(); d.setDate(d.getDate() - i); days.push((d.getMonth() + 1) + '/' + d.getDate()); }
    return days;
}
function getLast7DaysData() { return [5, 8, 3, 12, 7, 10, state.stats.totalAnswered || 0]; }
function getLast7DaysCorrect() { return [3, 6, 2, 9, 5, 8, state.stats.correctCount || 0]; }

// ========== AI PANEL ==========
function openAiPanel() { document.getElementById('aiPanel').classList.add('open'); }
function closeAiPanel() { document.getElementById('aiPanel').classList.remove('open'); }
function quickAsk(q) { document.getElementById('aiInput').value = q; sendAiMsg(); }

async function sendAiMsg() {
    const input = document.getElementById('aiInput');
    const msg = input.value.trim();
    if (!msg) return;
    const messages = document.getElementById('aiMessages');
    const userMsg = document.createElement('div'); userMsg.className = 'ai-message user'; userMsg.textContent = msg;
    messages.appendChild(userMsg); input.value = ''; messages.scrollTop = messages.scrollHeight;

    const typing = document.createElement('div'); typing.className = 'ai-message bot typing'; typing.innerHTML = '<span></span><span></span><span></span>';
    messages.appendChild(typing); messages.scrollTop = messages.scrollHeight;

    try {
        const data = await api('/api/agent/chat', { method: 'POST', body: JSON.stringify({ message: msg }) });
        typing.remove();
        const botMsg = document.createElement('div'); botMsg.className = 'ai-message bot'; botMsg.textContent = data.reply;
        messages.appendChild(botMsg); messages.scrollTop = messages.scrollHeight;
    } catch (e) {
        typing.remove();
        const botMsg = document.createElement('div'); botMsg.className = 'ai-message bot'; botMsg.textContent = '抱歉，AI 服务暂时不可用，请稍后再试。';
        messages.appendChild(botMsg); messages.scrollTop = messages.scrollHeight;
    }
}

// ========== SETTINGS ==========
function openSettingsModal() { document.getElementById('settingsModal').classList.add('active'); }
function closeSettingsModal() { document.getElementById('settingsModal').classList.remove('active'); }
function updateTempDisplay() { document.getElementById('tempValue').textContent = document.getElementById('tempRange').value; }
function saveSettings() {
    const model = document.querySelector('.model-card.selected')?.dataset?.model || 'doubao';
    const agent = document.querySelector('.agent-card-sel.selected')?.dataset?.agent || 'auto';
    const temp = document.getElementById('tempRange').value;
    localStorage.setItem('aiSettings', JSON.stringify({ model, agent, temperature: parseFloat(temp) }));
    closeSettingsModal(); showToast('AI 设置已保存', 'success');
}

// ========== THEME ==========
function initThemeToggle() {
    document.getElementById('themeToggle').addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        updateChartsTheme();
    });
}

function updateChartsTheme() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#e8ecf4' : '#0f172a';
    const gridColor = isDark ? 'rgba(255,255,255,.08)' : 'rgba(15,23,42,.08)';
    const trendColor = isDark ? '#a78bfa' : '#722ED1';
    const trendColor2 = isDark ? '#38bdf8' : '#165DFF';
    const radarColor = isDark ? '#a78bfa' : '#722ED1';
    const radarBg = isDark ? 'rgba(167,139,250,.2)' : 'rgba(114,46,209,.2)';
    const pieBorder = isDark ? '#060913' : '#f0f4fc';

    Object.values(charts).forEach(chart => {
        if (chart.config.type === 'line') {
            chart.data.datasets[0].borderColor = trendColor; chart.data.datasets[0].pointBackgroundColor = trendColor;
            chart.data.datasets[1].borderColor = trendColor2; chart.data.datasets[1].pointBackgroundColor = trendColor2;
        }
        if (chart.config.type === 'radar') { chart.data.datasets[0].borderColor = radarColor; chart.data.datasets[0].backgroundColor = radarBg; chart.data.datasets[0].pointBackgroundColor = radarColor; }
        if (chart.config.type === 'doughnut') chart.data.datasets[0].borderColor = pieBorder;
        chart.options.plugins.legend.labels.color = textColor;
        if (chart.options.scales) Object.values(chart.options.scales).forEach(s => { if (s.ticks) s.ticks.color = textColor; if (s.grid) s.grid.color = gridColor; });
        if (chart.options.scales?.r) { chart.options.scales.r.angleLines.color = gridColor; chart.options.scales.r.grid.color = gridColor; chart.options.scales.r.pointLabels.color = textColor; chart.options.scales.r.ticks.color = textColor; }
        chart.update();
    });
}

// ========== PARTICLES ==========
function initParticles() {
    const canvas = document.getElementById('particles-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let particles = [];
    function resize() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
    resize(); window.addEventListener('resize', resize);
    for (let i = 0; i < 30; i++) {
        particles.push({ x: Math.random() * canvas.width, y: Math.random() * canvas.height, vx: (Math.random() - .5) * .25, vy: (Math.random() - .5) * .25, r: Math.random() * 2 + .8, alpha: Math.random() * .5 + .2 });
    }
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        particles.forEach((p, i) => {
            p.x += p.vx; p.y += p.vy;
            if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
            const color = isDark ? `rgba(56,189,248,${p.alpha * .4})` : `rgba(22,93,255,${p.alpha * .25})`;
            ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fillStyle = color; ctx.fill();
            particles.slice(i + 1).forEach(p2 => {
                const dx = p.x - p2.x, dy = p.y - p2.y, dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) { ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p2.x, p2.y); ctx.strokeStyle = isDark ? `rgba(167,139,250,${.08 * (1 - dist / 120)})` : `rgba(114,46,209,${.06 * (1 - dist / 120)})`; ctx.lineWidth = .6; ctx.stroke(); }
            });
        });
        requestAnimationFrame(animate);
    }
    animate();
}

// ========== REVEAL ==========
function initReveal() {
    const observer = new IntersectionObserver((entries) => { entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('in'); }); }, { threshold: .1 });
    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

// ========== CURSOR GLOW ==========
function initCursorGlow() {
    const glow = document.getElementById('cursor-glow');
    if (!glow) return;
    document.addEventListener('mousemove', e => { glow.style.left = e.clientX + 'px'; glow.style.top = e.clientY + 'px'; });
}

// ========== TOAST ==========
function showToast(msg, type) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.className = 'toast ' + (type || '');
    toast.textContent = msg;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300); }, 2500);
}

// ========== INIT ==========
document.addEventListener('DOMContentLoaded', () => {
    // Restore theme
    const theme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', theme);

    initThemeToggle();
    initParticles();
    initReveal();
    initCursorGlow();

    // Filter chips
    document.querySelectorAll('#filterChips .opt').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('#filterChips .opt').forEach(c => c.classList.remove('on'));
            chip.classList.add('on');
            state.currentFilter = chip.dataset.filter;
            state.currentQuestionIndex = 0;
            state.multiSelectValues = [];
            renderQuestion();
        });
    });

    // Model cards
    document.querySelectorAll('.model-card').forEach(card => {
        card.addEventListener('click', () => { document.querySelectorAll('.model-card').forEach(c => c.classList.remove('selected')); card.classList.add('selected'); });
    });

    // Agent cards
    document.querySelectorAll('.agent-card-sel').forEach(card => {
        card.addEventListener('click', () => { document.querySelectorAll('.agent-card-sel').forEach(c => c.classList.remove('selected')); card.classList.add('selected'); });
    });

    // Smooth scroll
    document.querySelectorAll('.top-links a').forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) target.scrollIntoView({ behavior: 'smooth' });
        });
    });

    // Enter key for login/register
    document.getElementById('loginPassword')?.addEventListener('keydown', e => { if (e.key === 'Enter') handleLogin(); });
    document.getElementById('regPassword')?.addEventListener('keydown', e => { if (e.key === 'Enter') handleRegister(); });

    // Load user
    loadUser();
});