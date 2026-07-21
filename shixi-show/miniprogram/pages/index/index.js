const { companies } = require('../../mock/companies.js')

Page({
  data: { list: [] },
  onLoad() {
    // 先读本地 mock；后续替换为 getRankedCompanies(1, 20)
    const list = companies.map((c, i) => ({ ...c, rank: i + 1 }))
    this.setData({ list })
  },
  goCompany(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: '/pages/company/company?id=' + id })
  }
})
