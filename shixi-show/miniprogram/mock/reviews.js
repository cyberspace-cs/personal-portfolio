// 本地 mock：点评数据（status: 0审核中 / 1通过 / 2拒绝）
const reviews = [
  { id: 1, companyId: 1, companyName: '腾讯', dept: '微信', role: '后端开发',
    scores: { mentor: 5, growth: 4, 转正: 4, 薪资: 4, wlb: 3 },
    stamps: ['推荐'], content: '导师很负责，转正机会大，业务锻炼人。', status: 1, createdAt: '2026-07-20' },
  { id: 2, companyId: 2, companyName: '字节跳动', dept: '抖音', role: '前端',
    scores: { mentor: 4, growth: 5, 转正: 3, 薪资: 5, wlb: 2 },
    stamps: ['推荐'], content: '成长快但节奏非常快，薪资给得足。', status: 1, createdAt: '2026-07-18' },
  { id: 3, companyId: 5, companyName: '某创业公司', dept: '研发', role: '全栈',
    scores: { mentor: 2, growth: 3, 转正: 2, 薪资: 3, wlb: 1 },
    stamps: ['避雷'], content: '加班严重，转正画饼，谨慎。', status: 1, createdAt: '2026-07-15' },
  { id: 4, companyId: 3, companyName: '阿里', dept: '云', role: '算法',
    scores: { mentor: 4, growth: 4, 转正: 4, 薪资: 4, wlb: 3 },
    stamps: ['还想来'], content: '体系成熟，能学到规范。', status: 0, createdAt: '2026-07-21' }
]

module.exports = { reviews }
