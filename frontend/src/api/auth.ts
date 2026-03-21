import apiClient from './client'
import type { User, Token, SessionInfo } from '@/types'

export const authApi = {
  login: async (username: string, password: string): Promise<Token> => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    const response = await apiClient.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  register: async (data: { username: string; email: string; password: string }): Promise<User> => {
    const response = await apiClient.post('/auth/register', data)
    return response.data
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get('/auth/me')
    return response.data
  },

  refreshToken: async (refreshToken: string): Promise<Token> => {
    const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken })
    return response.data
  },

  logout: async (refreshToken: string): Promise<{ message: string }> => {
    const response = await apiClient.post('/auth/logout', { refresh_token: refreshToken })
    return response.data
  },

  logoutAll: async (): Promise<{ message: string }> => {
    const response = await apiClient.post('/auth/logout-all')
    return response.data
  },

  getSessions: async (): Promise<SessionInfo[]> => {
    const response = await apiClient.get('/auth/sessions')
    return response.data
  },

  revokeSession: async (sessionId: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/auth/sessions/${sessionId}`)
    return response.data
  },

  verifyEmail: async (token: string): Promise<{ message: string }> => {
    const response = await apiClient.post('/auth/verify-email', null, {
      params: { token }
    })
    return response.data
  },

  resendVerification: async (email: string): Promise<{ message: string }> => {
    const response = await apiClient.post('/auth/resend-verification', null, {
      params: { email }
    })
    return response.data
  },

  requestPasswordReset: async (email: string): Promise<{ message: string; expires_in: number }> => {
    const response = await apiClient.post('/auth/password-reset/request', { email })
    return response.data
  },

  verifyPasswordReset: async (data: {
    email: string
    code: string
    new_password: string
    confirm_password: string
  }): Promise<{ message: string }> => {
    const response = await apiClient.post('/auth/password-reset/verify', data)
    return response.data
  }
}
