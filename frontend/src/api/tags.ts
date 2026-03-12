import apiClient from './client'
import type { Tag } from '@/types'

export const tagApi = {
  getTags: async (): Promise<Tag[]> => {
    const response = await apiClient.get('/tags')
    return response.data
  },

  getTag: async (id: number): Promise<Tag> => {
    const response = await apiClient.get(`/tags/${id}`)
    return response.data
  },

  createTag: async (data: Partial<Tag>): Promise<Tag> => {
    const response = await apiClient.post('/tags', data)
    return response.data
  },

  updateTag: async (id: number, data: Partial<Tag>): Promise<Tag> => {
    const response = await apiClient.put(`/tags/${id}`, data)
    return response.data
  },

  deleteTag: async (id: number): Promise<void> => {
    await apiClient.delete(`/tags/${id}`)
  }
}
