import apiClient, { clearCacheByPattern } from './client'
import type { Resource } from '@/types'

export const resourceApi = {
  getResources: async (): Promise<Resource[]> => {
    const response = await apiClient.get('/resources')
    return response.data
  },

  getAdminResources: async (): Promise<Resource[]> => {
    const response = await apiClient.get('/resources/admin')
    return response.data
  },

  createResource: async (data: Partial<Resource>): Promise<Resource> => {
    const response = await apiClient.post('/resources', data)
    clearCacheByPattern('/resources')
    return response.data
  },

  updateResource: async (id: number, data: Partial<Resource>): Promise<Resource> => {
    const response = await apiClient.put(`/resources/${id}`, data)
    clearCacheByPattern('/resources')
    return response.data
  },

  deleteResource: async (id: number): Promise<void> => {
    await apiClient.delete(`/resources/${id}`)
    clearCacheByPattern('/resources')
  }
}
