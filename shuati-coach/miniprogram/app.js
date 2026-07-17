// app.js · 全局状态与后端地址
App({
  globalData: {
    // 后端地址：本地试水默认走本机（Windows 开发者工具勾「不校验合法域名」即可）
    // 部署后替换为公网 HTTPS 域名（微信小程序要求 request 域名必须备案且为 https）
    // 若后端跑在另一台机器，改成该机局域网 IP，如 'http://192.168.1.100:8000'
    baseUrl: 'http://127.0.0.1:8000',
    userId: null,
    userInfo: null
  },

  onLaunch() {
    // 从本地缓存恢复登录态（简单演示，生产建议用 openid + token）
    const uid = wx.getStorageSync('coach_uid');
    if (uid) this.globalData.userId = uid;
  },

  // 统一请求封装
  request(path, method = 'GET', data = {}) {
    const base = this.globalData.baseUrl;
    return new Promise((resolve, reject) => {
      wx.request({
        url: base + path,
        method,
        data,
        header: { 'Content-Type': 'application/json' },
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data);
          else reject(res.data || new Error('HTTP ' + res.statusCode));
        },
        fail: (err) => reject(err)
      });
    });
  },

  // 确保有用户身份（演示：无则自动注册一个本地用户）
  async ensureUser() {
    if (this.globalData.userId) return this.globalData.userId;
    const uid = wx.getStorageSync('coach_uid');
    if (uid) { this.globalData.userId = uid; return uid; }
    try {
      const uname = 'wx_' + Date.now().toString(36);
      const r = await this.request('/api/register', 'POST', { username: uname, password: 'coach123' });
      this.globalData.userId = r.id;
      wx.setStorageSync('coach_uid', r.id);
      return r.id;
    } catch (e) {
      // 后端不可用时降级为本地临时 id
      const tid = -Date.now();
      this.globalData.userId = tid;
      return tid;
    }
  },

  getUserId() {
    return this.globalData.userId;
  }
});
