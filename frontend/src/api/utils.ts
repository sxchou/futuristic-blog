import apiClient from './client'

export interface SlugGenerationResult {
  slug: string
  is_unique: boolean
  base_slug?: string
  source?: 'exact_match' | 'similar_match' | 'generated' | 'default'
  similarity_score?: number
  matched_slug?: string | null
}

export interface SimilarSlugResult {
  input_slug: string
  matched_slug: string | null
  similarity_score: number
  found: boolean
  existing_count?: number
}

export const utilsApi = {
  generateSlug: async (
    text: string, 
    entityType?: string, 
    excludeId?: number,
    enableSimilarity: boolean = false,
    similarityThreshold: number = 0.6
  ): Promise<SlugGenerationResult> => {
    const params = new URLSearchParams()
    params.append('text', text)
    if (entityType) params.append('entity_type', entityType)
    if (excludeId) params.append('exclude_id', excludeId.toString())
    params.append('enable_similarity', enableSimilarity.toString())
    params.append('similarity_threshold', similarityThreshold.toString())
    
    const response = await apiClient.post(`/utils/generate-slug?${params.toString()}`)
    return response.data
  },

  findSimilarSlug: async (
    text: string,
    entityType: string,
    threshold: number = 0.6,
    excludeId?: number
  ): Promise<SimilarSlugResult> => {
    const params = new URLSearchParams()
    params.append('text', text)
    params.append('entity_type', entityType)
    params.append('threshold', threshold.toString())
    if (excludeId) params.append('exclude_id', excludeId.toString())
    
    const response = await apiClient.get(`/utils/find-similar-slug?${params.toString()}`)
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
