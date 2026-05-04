import apiClient from './client'

export interface Announcement {
  id: number
  title: string
  content: string
  type: 'info' | 'warning' | 'success' | 'error'
  is_active: boolean
  order: number
  created_at: string
  updated_at: string
}

export interface AnnouncementCreate {
  title: string
  content: string
  type?: 'info' | 'warning' | 'success' | 'error'
  is_active?: boolean
  order?: number
}

export interface AnnouncementUpdate {
  title?: string
  content?: string
  type?: 'info' | 'warning' | 'success' | 'error'
  is_active?: boolean
  order?: number
}

export const announcementApi = {
  getAnnouncements: async (activeOnly: boolean = false): Promise<Announcement[]> => {
    const response = await apiClient.get('/announcements', {
      params: { active_only: activeOnly }
    })
    return response.data
  },

  getAnnouncement: async (id: number): Promise<Announcement> => {
    const response = await apiClient.get(`/announcements/${id}`)
    return response.data
  },

  createAnnouncement: async (data: AnnouncementCreate): Promise<Announcement> => {
    const response = await apiClient.post('/announcements', data)
    return response.data
  },

  updateAnnouncement: async (id: number, data: AnnouncementUpdate): Promise<Announcement> => {
    const response = await apiClient.put(`/announcements/${id}`, data)
    return response.data
  },

  deleteAnnouncement: async (id: number): Promise<void> => {
    await apiClient.delete(`/announcements/${id}`)
  }
}
