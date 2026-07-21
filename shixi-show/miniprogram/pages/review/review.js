Page({
  data: {
    companyId: null,
    companyName: '', dept: '', role: '',
    dims: [
      { key: 'mentor', label: '导师质量', val: 5 },
      { key: 'growth', label: '成长空间', val: 5 },
      { key: '转正', label: '转正机会', val: 5 },
      { key: '薪资', label: '薪资待遇', val: 5 },
      { key: 'wlb', label: '工作生活平衡', val: 5 }
    ],
    stamps: ['推荐', '还想来', '一般', '拉', '避雷'],
    picked: [],
    content: ''
  },
  onLoad(opt) {
    if (opt && opt.id) this.setData({ companyId: Number(opt.id) })
  },
  setScore(e) {
    const i = e.currentTarget.dataset.i
    const v = Number(e.currentTarget.dataset.v)
    const dims = this.data.dims
    dims[i].val = v
    this.setData({ dims })
  },
  toggleStamp(e) {
    const s = e.currentTarget.dataset.s
    const picked = this.data.picked
    this.setData({
      picked: picked.includes(s) ? picked.filter(x => x !== s) : [...picked, s]
    })
  },
  onContent(e) { this.setData({ content: e.detail.value }) },
  onCompany(e) { this.setData({ companyName: e.detail.value }) },
  onDept(e) { this.setData({ dept: e.detail.value }) },
  onRole(e) { this.setData({ role: e.detail.value }) },
  submit() {
    // 业务规则：正面章 与 负面章 互斥
    const hasGood = this.data.picked.includes('推荐') || this.data.picked.includes('还想来')
    const hasBad = this.data.picked.includes('拉') || this.data.picked.includes('避雷')
    if (hasGood && hasBad) {
      wx.showToast({ title: '盖章矛盾，请检查', icon: 'none' })
      return
    }
    if (!this.data.companyName) {
      wx.showToast({ title: '请填写公司名', icon: 'none' })
      return
    }
    // 后续调用 api 提交；此处先本地模拟
    wx.showToast({ title: '已提交，审核中', icon: 'success' })
    setTimeout(() => {
      wx.showModal({ title: '小彩蛋', content: '感谢分享！记得把实习 Show 推荐给同学 🎁', showCancel: false })
    }, 800)
  }
})
