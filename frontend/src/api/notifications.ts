import apiClient from './client'

export interface NotificationSettings {
  id: number
  notify_on_register: boolean
  notify_on_comment: boolean
  notify_on_like: boolean
  notify_on_reply: boolean
  require_comment_audit: boolean
  created_at: string
  updated_at: string
}

export interface NotificationSettingsUpdate {
  notify_on_register?: boolean
  notify_on_comment?: boolean
  notify_on_like?: boolean
  notify_on_reply?: boolean
  require_comment_audit?: boolean
}

export const notificationApi = {
  getSettings: async (): Promise<NotificationSettings> => {
    const response = await apiClient.get('/notifications/settings')
    return response.data
  },

  updateSettings: async (data: NotificationSettingsUpdate): Promise<NotificationSettings> => {
    const response = await apiClient.put('/notifications/settings', data)
    return response.data
  }
}
