import apiClient from './client'
import type { User } from '@/types'

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ChangePasswordData {
  current_password: string
  new_password: string
  confirm_password: string
}

export const userApi = {
  getUsers: async (page: number = 1, pageSize: number = 10): Promise<PaginatedResponse<User>> => {
    const response = await apiClient.get(`/users?page=${page}&page_size=${pageSize}`)
    return response.data
  },

  getUser: async (userId: number): Promise<User> => {
    const response = await apiClient.get(`/users/${userId}`)
    return response.data
  },

  updateUser: async (userId: number, data: Partial<User>): Promise<User> => {
    const response = await apiClient.put(`/users/${userId}`, data)
    return response.data
  },

  deleteUser: async (userId: number): Promise<void> => {
    await apiClient.delete(`/users/${userId}`)
  },

  resetPassword: async (userId: number, newPassword: string): Promise<void> => {
    await apiClient.post(`/users/${userId}/reset-password?new_password=${encodeURIComponent(newPassword)}`)
  },

  changePassword: async (data: ChangePasswordData): Promise<{ message: string }> => {
    const response = await apiClient.post('/users/change-password', data)
    return response.data
  }
}
