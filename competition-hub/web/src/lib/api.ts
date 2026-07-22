import type {
  Category,
  Competition,
  CompetitionInput,
  CompetitionListResp,
  Stats,
  User,
} from './types'

const API = '/api'

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((opts.headers as Record<string, string>) || {}),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${API}${path}`, { ...opts, headers })
  if (!res.ok) {
    let detail = `请求失败 (${res.status})`
    try {
      const err = await res.json()
      detail = err.detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  // 分类
  getCategories: () => request<Category[]>('/categories'),
  // 统计
  getStats: () => request<Stats>('/stats'),
  // 竞赛列表
  listCompetitions: (params: Record<string, any> = {}) => {
    const qs = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') qs.append(k, String(v))
    })
    return request<CompetitionListResp>(`/competitions?${qs.toString()}`)
  },
  getCompetition: (id: number) => request<Competition>(`/competitions/${id}`),
  // 认证
  register: (username: string, password: string, email = '') =>
    request<{ token: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, email }),
    }),
  login: (username: string, password: string) =>
    request<{ token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  logout: () => request<{ ok: true }>('/auth/logout', { method: 'POST' }),
  // 收藏
  getFavorites: () => request<Competition[]>('/favorites'),
  addFavorite: (competitionId: number) =>
    request<{ ok: true; favorited: boolean }>('/favorites', {
      method: 'POST',
      body: JSON.stringify({ competition_id: competitionId }),
    }),
  removeFavorite: (competitionId: number) =>
    request<{ ok: true; favorited: boolean }>(`/favorites/${competitionId}`, { method: 'DELETE' }),
  checkFavorite: (competitionId: number) =>
    request<{ favorited: boolean }>(`/favorites/check/${competitionId}`),
  // 竞赛增删改（需登录）
  createCompetition: (payload: CompetitionInput) =>
    request<Competition>('/competitions', { method: 'POST', body: JSON.stringify(payload) }),
  updateCompetition: (id: number, payload: CompetitionInput) =>
    request<Competition>(`/competitions/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteCompetition: (id: number) =>
    request<{ ok: true; deleted: number }>(`/competitions/${id}`, { method: 'DELETE' }),
  // 自动聚合
  getCollectSources: () => request<{ name: string; homepage: string }[]>('/collect/sources'),
  collect: () =>
    request<{
      ok: true
      created: number
      updated: number
      failed: number
      total: number
      sources: { name: string; fetched: number; error?: string }[]
    }>('/collect', { method: 'POST' }),
  // 补全官网图片（og:image 横幅）
  enrichImages: () =>
    request<{ ok: true; total: number; updated: number; failed: number }>(
      '/admin/enrich-images',
      { method: 'POST' },
    ),
}
