// wx.request 封装：自动拼 baseUrl、注入登录态
function request(path, method = 'GET', data = {}) {
  const app = getApp()
  const base = (app && app.globalData && app.globalData.baseUrl) || 'http://localhost:5000/api'
  return new Promise((resolve, reject) => {
    wx.request({
      url: base + path,
      method,
      data,
      header: {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + (wx.getStorageSync('token') || '')
      },
      success: res => {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data)
        else reject(res.data)
      },
      fail: reject
    })
  })
}

// 热点公司排行（后续替换为 request('/companies/rank')）
function getRankedCompanies(page = 1, size = 20) {
  return request(`/companies/rank?page=${page}&size=${size}`)
}

module.exports = { request, getRankedCompanies }
