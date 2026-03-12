import apiClient from './client'
import type { Resource } from '@/types'

export const resourceApi = {
  getResources: async (): Promise<Resource[]> => {
    const response = await apiClient.get('/resources')
    return response.data
  },

  createResource: async (data: Partial<Resource>): Promise<Resource> => {
    const response = await apiClient.post('/resources', data)
    return response.data
  },

  updateResource: async (id: number, data: Partial<Resource>): Promise<Resource> => {
    const response = await apiClient.put(`/resources/${id}`, data)
    return response.data
  },

  deleteResource: async (id: number): Promise<void> => {
    await apiClient.delete(`/resources/${id}`)
  }
}
