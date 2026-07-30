export interface Category {
  id: number
  name: string
  slug: string
  icon: string
  description: string
  sort_order: number
  count: number
}

export interface Competition {
  id: number
  title: string
  slug: string
  summary: string
  description: string
  category_id: number | null
  category_name: string
  organizer: string
  location: string
  mode: 'online' | 'offline' | 'hybrid'
  prize: string
  prize_amount: number
  status: 'upcoming' | 'ongoing' | 'ended'
  start_date: string | null
  end_date: string | null
  reg_deadline: string | null
  tags: string[]
  cover: string
  source_url: string
  source: string
  image: string
  featured: boolean
  views: number
  created_at: string
  updated_at: string
  is_favorited: boolean
}

export interface CompetitionListResp {
  items: Competition[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface User {
  id: number
  username: string
  email: string
  avatar: string
  role: string
  created_at: string
}

export interface Stats {
  total: number
  ongoing: number
  upcoming: number
  ended: number
  categories: number
  users: number
  top_viewed: { id: number; title: string; views: number }[]
}

export type CompetitionInput = Omit<
  Competition,
  'id' | 'slug' | 'category_name' | 'views' | 'created_at' | 'updated_at' | 'is_favorited'
> & { slug?: string }
