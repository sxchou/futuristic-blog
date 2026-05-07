import apiClient, { clearCacheByPattern } from './client'
import type { Category } from '@/types'

export interface UniqueCheckResult {
  exists: boolean
  field: string
  value: string
}

export const categoryApi = {
  checkUnique: async (field: 'name' | 'slug', value: string, excludeId?: number): Promise<UniqueCheckResult> => {
    const params: Record<string, string | number> = { field, value }
    if (excludeId) {
      params.exclude_id = excludeId
    }
    const response = await apiClient.get('/categories/check-unique', { params })
    return response.data
  },

  getCategories: async (): Promise<Category[]> => {
    const response = await apiClient.get('/categories')
    return response.data
  },

  getCategory: async (id: number): Promise<Category> => {
    const response = await apiClient.get(`/categories/${id}`)
    return response.data
  },

  createCategory: async (data: Partial<Category>): Promise<Category> => {
    const response = await apiClient.post('/categories', data)
    clearCacheByPattern('/categories')
    return response.data
  },

  updateCategory: async (id: number, data: Partial<Category>): Promise<Category> => {
    const response = await apiClient.put(`/categories/${id}`, data)
    clearCacheByPattern('/categories')
    return response.data
  },

  deleteCategory: async (id: number): Promise<void> => {
    await apiClient.delete(`/categories/${id}`)
    clearCacheByPattern('/categories')
  }
}
