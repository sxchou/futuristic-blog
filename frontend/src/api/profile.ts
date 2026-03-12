import apiClient from './client'
import type { Profile } from '@/types'

export const profileApi = {
  getProfile: async (): Promise<Profile> => {
    const response = await apiClient.get('/profile')
    return response.data
  },

  updateProfile: async (data: Partial<Profile>): Promise<Profile> => {
    const response = await apiClient.put('/profile', data)
    return response.data
  }
}
