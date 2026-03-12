import apiClient from './client'
import type { LikeResponse } from '@/types'

export const likeApi = {
  toggle: async (articleId: number): Promise<LikeResponse> => {
    const response = await apiClient.post(`/likes/${articleId}`)
    return response.data
  },

  getStatus: async (articleId: number): Promise<LikeResponse> => {
    const response = await apiClient.get(`/likes/${articleId}`)
    return response.data
  }
}
