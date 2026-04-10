import apiClient from './client'
import type { SiteConfig } from '@/types'

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
    return response.data
  },

  async create(data: { key: string; value?: string; description?: string }): Promise<SiteConfig> {
    const response = await apiClient.post('/site-config', data)
    return response.data
  },

  async delete(key: string): Promise<void> {
    await apiClient.delete(`/site-config/${key}`)
  },

  async uploadLogo(formData: FormData): Promise<SiteConfig> {
    const response = await apiClient.post('/site-config/upload-logo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  async resetLogo(): Promise<SiteConfig> {
    const response = await apiClient.post('/site-config/reset-logo')
    return response.data
  }
}
