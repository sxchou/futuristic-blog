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

export interface EmailChangeRequestData {
  new_email: string
  password?: string
  verification_type: 'password' | 'old_email'
  old_email_code?: string
}

export interface EmailChangeVerifyData {
  new_email: string
  code: string
  password?: string
  verification_type?: string
}

export interface SendCodeToOldEmailData {
  message: string
  expires_in: number
}

export interface ChangeUsernameData {
  new_username: string
  password: string
}

export interface CreateUserInput {
  username: string
  email: string
  password: string
  role_ids: number[]
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

  createUser: async (data: CreateUserInput): Promise<User> => {
    const response = await apiClient.post('/users', data)
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
  },

  requestSetPassword: async (): Promise<{ message: string; expires_in: number }> => {
    const response = await apiClient.post('/users/set-password/request')
    return response.data
  },

  verifySetPassword: async (data: { code: string; new_password: string; confirm_password: string }): Promise<{ message: string }> => {
    const response = await apiClient.post('/users/set-password/verify', data)
    return response.data
  },

  sendCodeToOldEmail: async (): Promise<SendCodeToOldEmailData> => {
    const response = await apiClient.post('/users/email-change/send-to-old')
    return response.data
  },

  requestEmailChange: async (data: EmailChangeRequestData): Promise<{ message: string; expires_in: number }> => {
    const response = await apiClient.post('/users/email-change/request', data)
    return response.data
  },

  verifyEmailChange: async (data: EmailChangeVerifyData): Promise<{ message: string }> => {
    const response = await apiClient.post('/users/email-change/verify', data)
    return response.data
  },

  changeUsername: async (data: ChangeUsernameData): Promise<{ message: string; new_username: string }> => {
    const response = await apiClient.post('/users/change-username', data)
    return response.data
  }
}
