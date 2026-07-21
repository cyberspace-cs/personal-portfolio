App({
  globalData: {
    // 后端地址，开发时改成你的服务地址；本地先走 mock
    baseUrl: 'http://localhost:5000/api',
    token: null,
    userInfo: null
  },
  onLaunch() {
    const token = wx.getStorageSync('token')
    if (token) this.globalData.token = token
  }
})
