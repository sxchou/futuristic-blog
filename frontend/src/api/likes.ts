import apiClient from './client'
import type { LikeResponse, ArticleListItem, PaginatedResponse } from '@/types'

export const likeApi = {
  toggle: async (articleId: number): Promise<LikeResponse> => {
    const response = await apiClient.post(`/likes/${articleId}`)
    return response.data
  },

  getStatus: async (articleId: number): Promise<LikeResponse> => {
    const response = await apiClient.get(`/likes/${articleId}`)
    return response.data
  },

  getUserLikedArticles: async (page: number = 1, pageSize: number = 10): Promise<PaginatedResponse<ArticleListItem>> => {
    const response = await apiClient.get('/likes/user/liked', {
      params: { page, page_size: pageSize }
    })
    return response.data
  }
}
