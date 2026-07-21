Page({
  data: { q: '', results: [] },
  onInput(e) { this.setData({ q: e.detail.value }) },
  onSearch() {
    const q = this.data.q.trim()
    if (!q) return
    const { companies } = require('../../mock/companies.js')
    const results = companies.filter(c => c.name.includes(q) || (c.industry || '').includes(q))
    this.setData({ results })
  },
  goCompany(e) {
    wx.navigateTo({ url: '/pages/company/company?id=' + e.currentTarget.dataset.id })
  }
})
