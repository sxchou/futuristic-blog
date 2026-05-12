import apiClient from './client'

export interface PublicStats {
  total_articles: number
  total_views: number
  total_likes: number
  total_comments: number
}

export interface OverviewStats {
  total_articles: number
  published_articles: number
  total_views: number
  total_likes: number
  total_comments: number
  total_users: number
  new_users_today: number
  new_articles_today: number
}

export interface TrendData {
  date: string
  value: number
}

export interface CategoryStats {
  name: string
  value: number
  color: string
}

export interface TagStats {
  name: string
  value: number
  color: string
}

export interface ArticleViewsRank {
  id: number
  title: string
  views: number
  likes: number
  comments: number
}

export interface UserActivity {
  date: string
  logins: number
  registrations: number
  comments: number
}

export interface AccessTrend {
  date: string
  page_views: number
  unique_visitors: number
  avg_response_time: number
}

export interface AllTrendsResponse {
  views_trend: TrendData[]
  articles_trend: TrendData[]
  comment_trend: TrendData[]
  access_trend: AccessTrend[]
}

export interface DashboardInitData {
  overview: OverviewStats
  category_stats: CategoryStats[]
  tag_stats: TagStats[]
  article_rank: ArticleViewsRank[]
  trends: AllTrendsResponse
}

export interface TrendsParams {
  trend_days?: number
  access_days?: number
}

export interface DashboardInitParams {
  trend_days?: number
  access_days?: number
  tag_limit?: number
  rank_limit?: number
  rank_sort_by?: 'views' | 'likes' | 'comments'
}

export const dashboardApi = {
  getPublicStats: () => 
    apiClient.get<PublicStats>('/dashboard/public-stats'),
  
  getOverview: () => 
    apiClient.get<OverviewStats>('/dashboard/overview'),
  
  getViewsTrend: (days: number = 30) => 
    apiClient.get<TrendData[]>('/dashboard/views-trend', { params: { days } }),
  
  getArticlesTrend: (days: number = 30) => 
    apiClient.get<TrendData[]>('/dashboard/articles-trend', { params: { days } }),
  
  getCategoryStats: () => 
    apiClient.get<CategoryStats[]>('/dashboard/category-stats'),
  
  getTagStats: (limit: number = 10) => 
    apiClient.get<TagStats[]>('/dashboard/tag-stats', { params: { limit } }),
  
  getArticleRank: (limit: number = 10, sortBy: 'views' | 'likes' | 'comments' = 'views') => 
    apiClient.get<ArticleViewsRank[]>('/dashboard/article-rank', { params: { limit, sort_by: sortBy } }),
  
  getUserActivity: (days: number = 30) => 
    apiClient.get<UserActivity[]>('/dashboard/user-activity', { params: { days } }),
  
  getAccessTrend: (days: number = 7) => 
    apiClient.get<AccessTrend[]>('/dashboard/access-trend', { params: { days } }),
  
  getCommentTrend: (days: number = 30) => 
    apiClient.get<TrendData[]>('/dashboard/comment-trend', { params: { days } }),
  
  getTrends: (params: TrendsParams = {}) => 
    apiClient.get<AllTrendsResponse>('/dashboard/trends', { params }),
  
  getInitData: (params: DashboardInitParams = {}) => 
    apiClient.get<DashboardInitData>('/dashboard/init', { params }),
  
  clearCache: () => 
    apiClient.post<{ success: boolean; message: string }>('/dashboard/clear-cache')
}
