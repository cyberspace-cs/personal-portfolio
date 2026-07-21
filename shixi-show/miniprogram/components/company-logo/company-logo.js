// 公司 Logo 组件：有图用图，无图/加载失败用「文字 Logo」（取首字 + 稳定底色）
Component({
  properties: {
    name: { type: String, value: '' },
    logo: { type: String, value: '' },
    size: { type: Number, value: 80 }
  },
  data: {
    showImg: true,
    initialChar: '?',
    bgColor: '#6C5CE7'
  },
  observers: {
    'name': function (name) {
      const palette = ['#6C5CE7', '#00B894', '#0984E3', '#E17055', '#FD79A8', '#636E72']
      const s = name || '?'
      let h = 0
      for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0
      this.setData({
        initialChar: s.charAt(0),
        bgColor: palette[h % palette.length]
      })
    },
    'logo': function () {
      // logo 变化（含清空）时重置为尝试显示图片
      this.setData({ showImg: true })
    }
  },
  methods: {
    onErr() {
      this.setData({ showImg: false })
    }
  }
})
