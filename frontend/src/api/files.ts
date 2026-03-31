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
  order: number
  created_at: string
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

  async deleteFile(fileId: number): Promise<void> {
    await apiClient.delete(`/files/${fileId}`)
  },

  async updateFileOrder(orders: { id: number; order: number }[]): Promise<void> {
    await apiClient.put('/files/order', { orders })
  }
}
