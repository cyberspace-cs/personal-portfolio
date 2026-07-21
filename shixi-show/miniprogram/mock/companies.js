// 本地 mock：热门公司排行（先跑通界面，后续替换为服务端接口）
const companies = [
  { id: 1, name: '腾讯', industry: '互联网', logo: '', avgScore: 4.6, reviewCount: 1280, tags: ['转正友好', '导师负责'], stamp: '推荐', hot: true },
  { id: 2, name: '字节跳动', industry: '互联网', logo: '', avgScore: 4.4, reviewCount: 1560, tags: ['成长快', '节奏快'], stamp: '推荐', hot: true },
  { id: 3, name: '阿里', industry: '互联网', logo: '', avgScore: 4.2, reviewCount: 980, tags: ['体系成熟'], stamp: '还想来', hot: false },
  { id: 4, name: '某国企研究院', industry: '科研', logo: '', avgScore: 3.6, reviewCount: 120, tags: ['稳定', 'wlb好'], stamp: '一般', hot: false },
  { id: 5, name: '某创业公司', industry: '互联网', logo: '', avgScore: 2.8, reviewCount: 64, tags: ['加班多'], stamp: '避雷', hot: false },
  { id: 6, name: '美团', industry: '互联网', logo: '', avgScore: 4.1, reviewCount: 730, tags: ['业务多'], stamp: '推荐', hot: false }
]

module.exports = { companies }
