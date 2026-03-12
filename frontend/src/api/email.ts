import apiClient from './client'

export interface EmailConfig {
  id: number
  provider: 'qq' | 'gmail'
  smtp_host: string | null
  smtp_port: number
  smtp_user: string | null
  from_email: string | null
  from_name: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface EmailLog {
  id: number
  email_type: string
  recipient_email: string
  recipient_name: string | null
  subject: string | null
  status: 'pending' | 'sent' | 'failed'
  error_message: string | null
  verification_token: string | null
  is_verified: boolean
  verified_at: string | null
  user_id: number | null
  sent_at: string | null
  created_at: string
}

export interface EmailStats {
  total_sent: number
  total_failed: number
  total_verified: number
  total_pending: number
  verification_rate: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface EmailProvider {
  id: string
  name: string
  host: string
  port: number
  description: string
}

export const emailApi = {
  getProviders: async (): Promise<{ providers: EmailProvider[] }> => {
    const response = await apiClient.get('/email/providers')
    return response.data
  },

  getConfigs: async (): Promise<EmailConfig[]> => {
    const response = await apiClient.get('/email/configs')
    return response.data
  },

  getActiveConfig: async (): Promise<EmailConfig | null> => {
    const response = await apiClient.get('/email/config')
    return response.data
  },

  createConfig: async (data: {
    provider: 'qq' | 'gmail'
    smtp_user: string
    smtp_password: string
    from_email: string
    from_name: string
  }): Promise<EmailConfig> => {
    const response = await apiClient.post('/email/config', data)
    return response.data
  },

  updateConfig: async (id: number, data: Partial<{
    provider: 'qq' | 'gmail'
    smtp_user: string
    smtp_password: string
    from_email: string
    from_name: string
    is_active: boolean
  }>): Promise<EmailConfig> => {
    const response = await apiClient.put(`/email/config/${id}`, data)
    return response.data
  },

  activateConfig: async (id: number): Promise<{ message: string; config: EmailConfig }> => {
    const response = await apiClient.post(`/email/config/${id}/activate`)
    return response.data
  },

  deleteConfig: async (id: number): Promise<{ message: string; was_active: boolean }> => {
    const response = await apiClient.delete(`/email/config/${id}`)
    return response.data
  },

  testEmail: async (recipientEmail: string): Promise<{ message: string }> => {
    const response = await apiClient.post('/email/test', { recipient_email: recipientEmail })
    return response.data
  },

  getLogs: async (params: {
    page?: number
    page_size?: number
    email_type?: string
    status?: string
  }): Promise<PaginatedResponse<EmailLog>> => {
    const response = await apiClient.get('/email/logs', { params })
    return response.data
  },

  getStats: async (): Promise<EmailStats> => {
    const response = await apiClient.get('/email/stats')
    return response.data
  },

  markVerified: async (logId: number): Promise<{ message: string }> => {
    const response = await apiClient.post(`/email/logs/${logId}/verify`)
    return response.data
  }
}
