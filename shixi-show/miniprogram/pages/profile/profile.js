Page({
  data: { reviews: [] },
  onShow() {
    const { reviews } = require('../../mock/reviews.js')
    // mock：假设当前用户提交了第 4 条（审核中）
    const statusText = r => r.status === 1 ? '已通过' : (r.status === 2 ? '已拒绝' : '审核中')
    this.setData({
      reviews: reviews.filter(r => r.companyId === 3).map(r => ({ ...r, statusText: statusText(r) }))
    })
  }
})
