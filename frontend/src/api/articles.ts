import apiClient, { clearCacheByPattern } from './client'
import type { Article, ArticleListItem, PaginatedResponse } from '@/types'

export interface UniqueCheckResult {
  exists: boolean
  field: string
  value: string
}

export interface ArticleListRequestOptions {
  /** 外部取消信号：切换筛选条件时取消未完成的请求 */
  signal?: AbortSignal
  /** 允许与进行中的同参数请求并存（预取场景使用，不中断用户请求） */
  allowDuplicate?: boolean
}

const ARTICLE_LIST_TIMEOUT = 15000

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
  }, options?: ArticleListRequestOptions): Promise<PaginatedResponse<ArticleListItem>> => {
    const response = await apiClient.get('/articles', {
      params,
      signal: options?.signal,
      // 列表请求使用更短的超时，避免用户长时间等待无反馈
      timeout: ARTICLE_LIST_TIMEOUT,
      headers: options?.allowDuplicate ? { 'X-Allow-Duplicate': 'true' } : undefined
    })
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
    date_type?: 'created' | 'published' | 'updated'
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
