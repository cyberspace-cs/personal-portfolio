// pages/index/index.js
const app = getApp();

Page({
  data: {
    streak: 0,
    totalQuestions: 0,
    doneToday: 0,
    wrongCount: 0,
    cats: [
      { key: '考研', name: '考研', emoji: '🎓', bg: '#eaf0ff', desc: '数学·英语·政治·专业课', count: 0 },
      { key: '考公', name: '考公', emoji: '🏛️', bg: '#e3faf3', desc: '行测·申论·常识判断', count: 0 },
      { key: '大厂', name: '大厂', emoji: '💻', bg: '#fff4e0', desc: '算法·系统·前端·后端', count: 0 }
    ]
  },

  onShow() {
    this.refresh();
  },

  onPullDownRefresh() {
    this.refresh().then(() => wx.stopPullDownRefresh());
  },

  async refresh() {
    const uid = await app.ensureUser();
    try {
      const [all, kaoyan, kaogong, dachang, streak, wrong] = await Promise.all([
        app.request('/api/questions'),
        app.request('/api/questions?cat=考研'),
        app.request('/api/questions?cat=考公'),
        app.request('/api/questions?cat=大厂'),
        app.request('/api/streak/' + uid),
        app.request('/api/wrong-book/' + uid)
      ]);
      const cats = this.data.cats.map(c => {
        const map = { '考研': kaoyan, '考公': kaogong, '大厂': dachang };
        return { ...c, count: (map[c.key] || []).length };
      });
      this.setData({
        totalQuestions: all.length,
        cats,
        streak: streak.streak || 0,
        wrongCount: wrong.length || 0
      });
      this.countToday();
    } catch (e) {
      wx.showToast({ title: '后端连接失败', icon: 'none' });
    }
  },

  // 统计今日已完成题数（基于本地缓存的答题流水）
  countToday() {
    const key = 'coach_done_' + this.formatDate(new Date());
    const n = wx.getStorageSync(key) || 0;
    this.setData({ doneToday: n });
  },

  formatDate(d) {
    const p = (x) => (x < 10 ? '0' + x : '' + x);
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  },

  startQuiz(e) {
    const cat = e.currentTarget.dataset.cat;
    wx.navigateTo({ url: '/pages/quiz/quiz?cat=' + cat });
  },

  openWeb() {
    wx.navigateTo({ url: '/pages/webview/webview?type=home' });
  },

  openChat() {
    wx.navigateTo({ url: '/pages/chat/chat' });
  },

  goMine() {
    wx.switchTab({ url: '/pages/mine/mine' });
  }
});
