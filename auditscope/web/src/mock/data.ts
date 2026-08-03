// 演示数据：审计综合信息查询（公司 / 老板 / 人员 / 流水 / 社保）
// 后端未启动时，前端用这些 mock 渲染界面；后端就绪后由 /api/v1 覆盖。

export type RiskLevel = 'normal' | 'watch' | 'high'

export interface Company {
  id: string
  name: string
  creditCode: string
  legalPerson: string
  regCapital: string
  established: string
  industry: string
  status: string
  risk: RiskLevel
  score: number
  tags: string[]
  address: string
}

export interface Boss {
  id: string
  name: string
  idCardMask: string
  heldCount: number
  totalCapital: string
  risk: RiskLevel
  companies: { name: string; role: string; ratio: string }[]
}

export interface Person {
  id: string
  name: string
  title: string
  company: string
 任职: string[]
  socialConnected: boolean
  risk: RiskLevel
}

export interface Flow {
  id: string
  date: string
  counterparty: string
  bank: string
  amount: number
  direction: 'in' | 'out'
  abnormal: boolean
  note: string
}

export interface Social {
  id: string
  name: string
  company: string
  base: number
  months: number
  paid: boolean
  gapMonths: number
  risk: RiskLevel
}

export const companies: Company[] = [
  { id: 'C1001', name: '星河智能科技有限公司', creditCode: '91110108MA01A1B2X3', legalPerson: '陈嘉禾', regCapital: '5000万人民币', established: '2016-03-12', industry: '人工智能/软件', status: '存续', risk: 'normal', score: 86, tags: ['高新企业', '瞪羚企业', '无失信'], address: '北京市海淀区中关村南大街5号' },
  { id: 'C1002', name: '通汇供应链管理有限公司', creditCode: '91310115MA1K35Y7T9', legalPerson: '王立军', regCapital: '2000万人民币', established: '2013-07-21', industry: '物流/供应链', status: '存续', risk: 'watch', score: 62, tags: ['涉诉2起', '股权质押'], address: '上海市浦东新区张江路88号' },
  { id: 'C1003', name: '云栖数据服务股份有限公司', creditCode: '91440300MA5DA2B4K6', legalPerson: '李文博', regCapital: '12000万人民币', established: '2011-09-02', industry: '云计算/大数据', status: '存续', risk: 'high', score: 38, tags: ['失信被执行人', '限制高消费', '税务异常'], address: '深圳市南山区科技中一路9号' },
]

export const bosses: Boss[] = [
  { id: 'B2001', name: '陈嘉禾', idCardMask: '110108**********3015', heldCount: 7, totalCapital: '3.2亿人民币', risk: 'normal', companies: [
    { name: '星河智能科技有限公司', role: '法定代表人/实控人', ratio: '41.2%' },
    { name: '星河投资管理(有限合伙)', role: '执行事务合伙人', ratio: 'GP' },
  ]},
  { id: 'B2002', name: '李文博', idCardMask: '440301**********1027', heldCount: 11, totalCapital: '5.8亿人民币', risk: 'high', companies: [
    { name: '云栖数据服务股份有限公司', role: '董事长', ratio: '28.5%' },
    { name: '云栖(海南)控股有限公司', role: '法定代表人', ratio: '90%' },
  ]},
]

export const persons: Person[] = [
  { id: 'P3001', name: '赵敏', title: '财务总监', company: '星河智能科技有限公司', 任职: ['星河智能-财务总监', '星河投资-监事'], socialConnected: true, risk: 'normal' },
  { id: 'P3002', name: '孙浩', title: '资金经理', company: '通汇供应链管理有限公司', 任职: ['通汇供应链-资金经理'], socialConnected: false, risk: 'watch' },
  { id: 'P3003', name: '周倩', title: '前出纳', company: '云栖数据服务股份有限公司', 任职: ['云栖数据-出纳(已离职)'], socialConnected: true, risk: 'high' },
]

export const flows: Flow[] = [
  { id: 'F4001', date: '2025-11-03', counterparty: '陈嘉禾(个人账户)', bank: '招商银行 6214****8831', amount: 4800000, direction: 'out', abnormal: true, note: '大额公转私，无合同支撑' },
  { id: 'F4002', date: '2025-11-08', counterparty: '北京某广告有限公司', bank: '工商银行 6222****1190', amount: 1200000, direction: 'out', abnormal: false, note: '广告服务费' },
  { id: 'F4003', date: '2025-11-15', counterparty: '客户回款-深圳市XX科技', bank: '招商银行 6214****8831', amount: 9300000, direction: 'in', abnormal: false, note: '货款回款' },
  { id: 'F4004', date: '2025-11-22', counterparty: '云栖(海南)控股有限公司', bank: '建设银行 6217****5520', amount: 6600000, direction: 'out', abnormal: true, note: '关联方资金往来，未披露' },
]

export const socials: Social[] = [
  { id: 'S5001', name: '赵敏', company: '星河智能科技有限公司', base: 32000, months: 36, paid: true, gapMonths: 0, risk: 'normal' },
  { id: 'S5002', name: '孙浩', company: '通汇供应链管理有限公司', base: 18000, months: 28, paid: true, gapMonths: 2, risk: 'watch' },
  { id: 'S5003', name: '周倩', company: '云栖数据服务股份有限公司', base: 24000, months: 12, paid: false, gapMonths: 9, risk: 'high' },
]

// 统一搜索：把五类数据拍平为结果条目
export interface SearchHit {
  kind: 'company' | 'boss' | 'person' | 'flow' | 'social'
  id: string
  title: string
  sub: string
  risk: RiskLevel
  detail: Record<string, unknown>
}

export function searchAll(q: string): SearchHit[] {
  const t = q.trim().toLowerCase()
  const hits: SearchHit[] = []
  if (!t) {
    companies.forEach(c => hits.push({ kind: 'company', id: c.id, title: c.name, sub: c.industry, risk: c.risk, detail: c as any }))
    bosses.forEach(b => hits.push({ kind: 'boss', id: b.id, title: b.name, sub: `控股 ${b.heldCount} 家`, risk: b.risk, detail: b as any }))
    persons.forEach(p => hits.push({ kind: 'person', id: p.id, title: p.name, sub: p.title, risk: p.risk, detail: p as any }))
    return hits
  }
  companies.forEach(c => {
    if (c.name.toLowerCase().includes(t) || c.legalPerson.toLowerCase().includes(t) || c.industry.toLowerCase().includes(t))
      hits.push({ kind: 'company', id: c.id, title: c.name, sub: c.industry, risk: c.risk, detail: c as any })
  })
  bosses.forEach(b => {
    if (b.name.toLowerCase().includes(t))
      hits.push({ kind: 'boss', id: b.id, title: b.name, sub: `控股 ${b.heldCount} 家`, risk: b.risk, detail: b as any })
  })
  persons.forEach(p => {
    if (p.name.toLowerCase().includes(t) || p.company.toLowerCase().includes(t))
      hits.push({ kind: 'person', id: p.id, title: p.name, sub: p.title, risk: p.risk, detail: p as any })
  })
  flows.forEach(f => {
    if (f.counterparty.toLowerCase().includes(t) || f.note.toLowerCase().includes(t))
      hits.push({ kind: 'flow', id: f.id, title: f.counterparty, sub: `${f.date} · ${f.direction === 'in' ? '流入' : '流出'}`, risk: f.abnormal ? 'high' : 'normal', detail: f as any })
  })
  socials.forEach(s => {
    if (s.name.toLowerCase().includes(t) || s.company.toLowerCase().includes(t))
      hits.push({ kind: 'social', id: s.id, title: s.name, sub: s.company, risk: s.risk, detail: s as any })
  })
  return hits
}
