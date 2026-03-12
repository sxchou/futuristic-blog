import apiClient from './client'
import type { Category } from '@/types'

export const categoryApi = {
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
    return response.data
  },

  updateCategory: async (id: number, data: Partial<Category>): Promise<Category> => {
    const response = await apiClient.put(`/categories/${id}`, data)
    return response.data
  },

  deleteCategory: async (id: number): Promise<void> => {
    await apiClient.delete(`/categories/${id}`)
  }
}
