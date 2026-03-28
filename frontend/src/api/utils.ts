import apiClient from './client'

export const utilsApi = {
  generateSlug: async (text: string, entityType?: string, excludeId?: number): Promise<{
    slug: string
    is_unique: boolean
    base_slug?: string
  }> => {
    const params = new URLSearchParams()
    params.append('text', text)
    if (entityType) params.append('entity_type', entityType)
    if (excludeId) params.append('exclude_id', excludeId.toString())
    
    const response = await apiClient.post(`/utils/generate-slug?${params.toString()}`)
    return response.data
  },

  checkSlugUniqueness: async (slug: string, entityType: string, excludeId?: number): Promise<{
    slug: string
    is_unique: boolean
    exists: boolean
  }> => {
    const params = new URLSearchParams()
    params.append('slug', slug)
    params.append('entity_type', entityType)
    if (excludeId) params.append('exclude_id', excludeId.toString())
    
    const response = await apiClient.get(`/utils/check-slug?${params.toString()}`)
    return response.data
  }
}
