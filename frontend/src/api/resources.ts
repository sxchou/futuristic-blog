import apiClient, { clearCacheByPattern } from './client'
import type { Resource } from '@/types'

export interface ResourceCategory {
  id: number
  name: string
  slug: string
  icon?: string
}

export interface UniqueCheckResult {
  exists: boolean
  field: string
  value: string
}

export const resourceApi = {
  getCategories: async (): Promise<ResourceCategory[]> => {
    const response = await apiClient.get('/resources/categories')
    return response.data
  },

  checkUnique: async (field: 'title' | 'url', value: string, excludeId?: number): Promise<UniqueCheckResult> => {
    const params: Record<string, string | number> = { field, value }
    if (excludeId) {
      params.exclude_id = excludeId
    }
    const response = await apiClient.get('/resources/check-unique', { params })
    return response.data
  },

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
