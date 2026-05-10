import apiClient, { clearCacheByPattern } from './client'
import type { Article, ArticleListItem, PaginatedResponse } from '@/types'

export interface UniqueCheckResult {
  exists: boolean
  field: string
  value: string
}

export const articleApi = {
  checkUnique: async (field: 'slug' | 'title', value: string, excludeId?: number): Promise<UniqueCheckResult> => {
    const params: Record<string, string | number> = { field, value }
    if (excludeId) {
      params.exclude_id = excludeId
    }
    const response = await apiClient.get('/articles/check-unique', { params })
    return response.data
  },

  getArticles: async (params: {
    page?: number
    page_size?: number
    category_id?: number
    tag_id?: number
    is_featured?: boolean
    search?: string
  }): Promise<PaginatedResponse<ArticleListItem>> => {
    const response = await apiClient.get('/articles', { params })
    return response.data
  },

  getUserArticles: async (params: {
    page?: number
    page_size?: number
  }): Promise<PaginatedResponse<ArticleListItem>> => {
    const response = await apiClient.get('/articles/user/my-articles', { params })
    return response.data
  },

  getAdminArticles: async (params: {
    page?: number
    page_size?: number
    status?: 'draft' | 'published' | 'scheduled'
    title?: string
    category?: string
    author?: string
    start_date?: string
    end_date?: string
  }): Promise<PaginatedResponse<ArticleListItem>> => {
    const response = await apiClient.get('/articles/admin', { params })
    return response.data
  },

  getAdminArticle: async (slug: string): Promise<Article> => {
    const response = await apiClient.get(`/articles/admin/${slug}`)
    return response.data
  },

  getArticle: async (slug: string): Promise<Article> => {
    const response = await apiClient.get(`/articles/${slug}`)
    return response.data
  },

  createArticle: async (data: Partial<Article>): Promise<Article> => {
    const response = await apiClient.post('/articles', data)
    clearCacheByPattern('/articles')
    return response.data
  },

  updateArticle: async (id: number, data: Partial<Article>): Promise<Article> => {
    const cleanData = { ...data } as Record<string, unknown>
    if ('cover_image' in cleanData && cleanData.cover_image === undefined) {
      cleanData.cover_image = null
    }
    const response = await apiClient.put(`/articles/${id}`, cleanData)
    clearCacheByPattern('/articles')
    return response.data
  },

  deleteArticle: async (id: number): Promise<void> => {
    await apiClient.delete(`/articles/${id}`)
    clearCacheByPattern('/articles')
  }
}
