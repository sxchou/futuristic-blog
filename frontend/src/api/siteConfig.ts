import apiClient, { clearCacheByPattern } from './client'
import type { SiteConfig } from '@/types'

export interface GitHubStats {
  enabled: boolean
  stars: number
  forks: number
  watchers: number
  open_issues: number
  full_name?: string
  html_url?: string
}

export const siteConfigApi = {
  async getAll(): Promise<SiteConfig[]> {
    const response = await apiClient.get('/site-config')
    return response.data
  },

  async get(key: string): Promise<SiteConfig> {
    const response = await apiClient.get(`/site-config/${key}`)
    return response.data
  },

  async update(key: string, value: string, description?: string): Promise<SiteConfig> {
    const response = await apiClient.put(`/site-config/${key}`, {
      key,
      value,
      description
    })
    clearCacheByPattern('/site-config')
    return response.data
  },

  async create(data: { key: string; value?: string; description?: string }): Promise<SiteConfig> {
    const response = await apiClient.post('/site-config', data)
    clearCacheByPattern('/site-config')
    return response.data
  },

  async delete(key: string): Promise<void> {
    await apiClient.delete(`/site-config/${key}`)
    clearCacheByPattern('/site-config')
  },

  async uploadLogo(formData: FormData): Promise<SiteConfig> {
    const response = await apiClient.post('/site-config/upload-logo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    clearCacheByPattern('/site-config')
    return response.data
  },

  async resetLogo(): Promise<SiteConfig> {
    const response = await apiClient.post('/site-config/reset-logo')
    clearCacheByPattern('/site-config')
    return response.data
  },

  async getGitHubStats(): Promise<GitHubStats> {
    const response = await apiClient.get('/site-config/github-stats')
    return response.data
  }
}
