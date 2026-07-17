// pages/wrong/wrong.js
const app = getApp();

Page({
  data: { list: [] },

  onShow() { this.refresh(); },

  onPullDownRefresh() {
    this.refresh().then(() => wx.stopPullDownRefresh());
  },

  async refresh() {
    const uid = await app.ensureUser();
    try {
      const list = await app.request('/api/wrong-book/' + uid);
      this.setData({ list });
    } catch (e) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  }
});
