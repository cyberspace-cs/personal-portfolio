// pages/mine/mine.js
const app = getApp();

Page({
  data: {
    uid: '-',
    streak: 0,
    checkedToday: false,
    week: [],
    totalDone: 0,
    wrongCount: 0,
    quizRounds: 0
  },

  async onShow() {
    const uid = await app.ensureUser();
    this.setData({ uid });
    await this.refresh();
  },

  async refresh() {
    const uid = app.getUserId();
    try {
      const [streak, wrong, history] = await Promise.all([
        app.request('/api/streak/' + uid),
        app.request('/api/wrong-book/' + uid),
        app.request('/api/quiz/history/' + uid)
      ]);
      const dates = streak.dates || [];
      const today = this.fmt(new Date());
      const checkedToday = dates.includes(today);
      this.setData({
        streak: streak.streak || 0,
        checkedToday,
        wrongCount: wrong.length || 0,
        quizRounds: history.length || 0,
        week: this.buildWeek(dates),
        totalDone: this.countTotalDone()
      });
    } catch (e) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  buildWeek(dates) {
    const labels = ['日', '一', '二', '三', '四', '五', '六'];
    const arr = [];
    const now = new Date();
    for (let i = 6; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(now.getDate() - i);
      arr.push({ label: labels[d.getDay()], on: dates.includes(this.fmt(d)) });
    }
    return arr;
  },

  fmt(d) {
    const p = (x) => (x < 10 ? '0' + x : '' + x);
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  },

  countTotalDone() {
    let total = 0;
    const now = new Date();
    // 累计最近 30 天本地刷题计数
    for (let i = 0; i < 30; i++) {
      const d = new Date(now);
      d.setDate(now.getDate() - i);
      total += wx.getStorageSync('coach_done_' + this.fmt(d)) || 0;
    }
    return total;
  },

  async checkIn() {
    const uid = app.getUserId();
    try {
      await app.request('/api/checkin/' + uid, 'POST');
      wx.showToast({ title: '打卡成功', icon: 'success' });
      this.refresh();
    } catch (e) {
      wx.showToast({ title: '打卡失败', icon: 'none' });
    }
  },

  openWeb(e) {
    const type = e.currentTarget.dataset.type || 'home';
    wx.navigateTo({ url: '/pages/webview/webview?type=' + type });
  },

  goWrong() {
    wx.switchTab({ url: '/pages/wrong/wrong' });
  }
});
