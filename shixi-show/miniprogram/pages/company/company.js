Page({
  data: { company: null, reviews: [] },
  onLoad(opt) {
    const id = Number(opt.id)
    const { companies } = require('../../mock/companies.js')
    const { reviews } = require('../../mock/reviews.js')
    const company = companies.find(c => c.id === id)
    const list = reviews.filter(r => r.companyId === id)
    this.setData({ company, reviews: list })
  },
  goReview() {
    wx.switchTab({ url: '/pages/review/review' })
  }
})
