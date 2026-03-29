import apiClient from './client'

export interface FileUploadResponse {
  id: number
  filename: string
  original_filename: string
  file_path: string
  file_size: number
  file_type: string
  mime_type: string
  is_image: boolean
  article_id: number | null
  download_count: number
  view_count: number
  order: number
  created_at: string
}

export interface FilePreviewResponse {
  type: 'text' | 'pdf' | 'image'
  content?: string
  filename: string
}

export const fileApi = {
  async uploadFile(file: File, articleId?: number): Promise<FileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (articleId) {
      formData.append('article_id', articleId.toString())
    }
    
    const response = await apiClient.post<FileUploadResponse>('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  async uploadImage(file: File): Promise<FileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await apiClient.post<FileUploadResponse>('/files/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  async getFiles(articleId?: number, fileType?: string): Promise<FileUploadResponse[]> {
    const params: Record<string, string | number> = {}
    if (articleId) params.article_id = articleId
    if (fileType) params.file_type = fileType
    
    const response = await apiClient.get<FileUploadResponse[]>('/files', { params })
    return response.data
  },

  async getFileInfo(fileId: number): Promise<FileUploadResponse> {
    const response = await apiClient.get<FileUploadResponse>(`/files/${fileId}`)
    return response.data
  },

  getDownloadUrl(fileId: number): string {
    return `${apiClient.defaults.baseURL}/files/${fileId}/download`
  },

  getPreviewUrl(fileId: number): string {
    return `${apiClient.defaults.baseURL}/files/${fileId}/preview`
  },

  async previewFile(fileId: number): Promise<FilePreviewResponse> {
    const response = await apiClient.get<FilePreviewResponse>(`/files/${fileId}/preview`)
    return response.data
  },

  async deleteFile(fileId: number): Promise<void> {
    await apiClient.delete(`/files/${fileId}`)
  },

  async updateFileOrder(fileId: number, order: number): Promise<FileUploadResponse> {
    const response = await apiClient.patch<FileUploadResponse>(`/files/${fileId}`, { order })
    return response.data
  },

  async batchUpdateOrder(orders: Array<{ id: number; order: number }>): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/files/batch-order', orders)
    return response.data
  }
}

export const FILE_ICONS: Record<string, string> = {
  'application/pdf': '📕',
  'application/msword': '📘',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '📘',
  'application/vnd.ms-excel': '📗',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '📗',
  'application/vnd.ms-powerpoint': '📙',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': '📙',
  'application/zip': '📦',
  'application/x-rar-compressed': '📦',
  'application/x-7z-compressed': '📦',
  'text/plain': '📄',
  'text/markdown': '📄',
  'image/jpeg': '🖼️',
  'image/png': '🖼️',
  'image/gif': '🖼️',
  'image/webp': '🖼️',
  'image/svg+xml': '🖼️',
}

export const getFileIcon = (fileType: string, mimeType: string): string => {
  if (mimeType && FILE_ICONS[mimeType]) {
    return FILE_ICONS[mimeType]
  }
  
  if (fileType === 'image') return '🖼️'
  if (fileType === 'document') return '📁'
  
  return '📁'
}

export const isPreviewable = (_mimeType: string): boolean => {
  return true
}

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + units[i]
}

export const formatDateTime = (dateStr: string): string => {
  if (!dateStr) return ''
  
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}
