import apiClient from './client'

export interface ResourceCategory {
  id: number
  name: string
  slug: string
  description?: string
  icon?: string
  order: number
  is_active: boolean
  created_at?: string
}

export interface ResourceCategoryCreate {
  name: string
  slug: string
  description?: string
  icon?: string
  order?: number
  is_active?: boolean
}

export interface ResourceCategoryUpdate {
  name?: string
  slug?: string
  description?: string
  icon?: string
  order?: number
  is_active?: boolean
}

export const resourceCategoryApi = {
  getCategories: async (): Promise<ResourceCategory[]> => {
    const response = await apiClient.get('/resource-categories')
    return response.data
  },

  createCategory: async (data: ResourceCategoryCreate): Promise<ResourceCategory> => {
    const response = await apiClient.post('/resource-categories', data)
    return response.data
  },

  updateCategory: async (id: number, data: ResourceCategoryUpdate): Promise<ResourceCategory> => {
    const response = await apiClient.put(`/resource-categories/${id}`, data)
    return response.data
  },

  deleteCategory: async (id: number): Promise<void> => {
    await apiClient.delete(`/resource-categories/${id}`)
  },

  reorderCategories: async (orderData: Array<{ id: number; order: number }>): Promise<void> => {
    await apiClient.post('/resource-categories/reorder', orderData)
  }
}
