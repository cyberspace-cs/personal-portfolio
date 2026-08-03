import { searchAll, type SearchHit } from '../mock/data'

// 对接后端网关 /api/v1。后端未就绪时自动降级到本地 mock，保证界面始终可演示。
const API = '/api/v1'

export async function search(q: string): Promise<SearchHit[]> {
  try {
    const r = await fetch(`${API}/search?q=${encodeURIComponent(q)}`, { headers: { Accept: 'application/json' } })
    if (!r.ok) throw new Error('bad')
    const data = await r.json()
    return data.hits as SearchHit[]
  } catch {
    // 降级：本地 mock
    return searchAll(q)
  }
}

export async function ask(q: string): Promise<{ answer: string; refs: string[] }> {
  try {
    const r = await fetch(`${API}/rag/ask`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q }),
    })
    if (!r.ok) throw new Error('bad')
    return await r.json()
  } catch {
    return {
      answer:
        '（演示模式，RAG 后端未连接）审计建议：对「公转私」「关联方未披露资金往来」等异常流水应追加银行函证与合同穿透，' +
        '对社保缴费缺口较大的人员重点核实劳动关系与薪酬真实性。',
      refs: ['星河智能-2025-11 资金流水', '云栖数据-社保缴费记录'],
    }
  }
}
