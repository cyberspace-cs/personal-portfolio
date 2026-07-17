// pages/webview/webview.js
// C 方案：web-view 承载现有 coach.html（需部署到公网 HTTPS 域名）
const app = getApp();

Page({
  data: { url: '' },

  onLoad(opt) {
    const type = opt.type || 'home';
    // H5 部署地址：部署后把 baseUrl 指向 coach.html 的公网地址
    const h5 = (app.globalData.baseUrl || '').replace(/\/api\/?$/, '') + '/coach.html';
    // 用 hash 路由跳到对应模块（H5 支持 #智能 / #数据 等锚点）
    const anchor = type === 'wrong' ? '#数据' : (type === 'home' ? '#智能' : '');
    wx.setNavigationBarTitle({ title: type === 'wrong' ? '数据看板' : 'AI 深度版' });
    this.setData({ url: h5 + anchor });
  }
});
