import apiClient from './client'
import type { 
  SiteConfig, Category, Tag, ArticleListItem, PaginatedResponse
} from '@/types'
import type { Announcement } from './announcements'
import type { UserProfile } from './userProfile'

export interface GitHubStats {
  enabled: boolean
  stars: number
  forks: number
  watchers: number
  open_issues: number
}

export interface InitResponse {
  site_config: SiteConfig[]
  categories: Category[]
  tags: Tag[]
  announcements: Announcement[]
  articles: PaginatedResponse<ArticleListItem>
  featured_articles: PaginatedResponse<ArticleListItem>
  github_stats: GitHubStats | null
  user_profile: UserProfile | null
  liked_article_ids: number[] | null
  bookmarked_article_ids: number[] | null
}

export const initApi = {
  getInitData: async (params?: {
    page?: number
    page_size?: number
    featured_page_size?: number
  }): Promise<InitResponse> => {
    const response = await apiClient.get('/init', { params })
    return response.data
  }
}
