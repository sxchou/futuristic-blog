import apiClient from './client'

export interface UserProfile {
  id: number
  user_id: number
  username: string
  avatar_type: 'default' | 'custom'
  avatar_url: string | null
  default_avatar_gradient: string[] | null
  created_at: string | null
  updated_at: string | null
}

export interface UploadResponse {
  success: boolean
  message: string
  profile: UserProfile
}

export const userProfileApi = {
  getProfile: () => apiClient.get<UserProfile>('/user-profile').then(res => res.data),
  
  getProfileByUserId: (userId: number) => 
    apiClient.get<UserProfile>(`/user-profile/${userId}`).then(res => res.data),
  
  uploadAvatar: (formData: FormData) => 
    apiClient.post<UserProfile>('/user-profile/upload-avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }).then(res => res.data),
  
  resetAvatar: () => 
    apiClient.post<UserProfile>('/user-profile/reset-avatar').then(res => res.data)
}
