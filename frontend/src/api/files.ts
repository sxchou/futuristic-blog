import apiClient from './client'
import type { AxiosProgressEvent } from 'axios'

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
  preview_count: number
  order: number
  created_at: string
}

export interface StorageFileInfo {
  name: string
  display_name: string
  path: string
  size: number
  size_formatted: string
  modified: string
  is_avatar: boolean
}

export interface StorageDirectoryInfo {
  size: number
  size_formatted: string
  file_count: number
  files: StorageFileInfo[]
  is_protected: boolean
}

export interface StorageInfo {
  upload_dir: string
  total_size: number
  total_size_formatted: string
  total_files: number
  directories: Record<string, StorageDirectoryInfo>
  orphan_files: StorageFileInfo[]
  orphan_count: number
  db_files_count: number
}

export interface ArchiveEntry {
  name: string
  path: string
  is_dir: boolean
  size: number
  compressed_size: number
  modified?: string
}

export interface ArchiveContent {
  format: string
  total_files: number
  total_dirs: number
  total_size: number
  compressed_size: number
  entries: ArchiveEntry[]
  tree: Record<string, any>
}

export interface UploadProgressEvent {
  loaded: number
  total: number
  progress: number
}

export interface UploadError {
  type: 'network' | 'timeout' | 'size_limit' | 'server' | 'unknown'
  message: string
  suggestion: string
}

const MAX_FILE_SIZE = 100 * 1024 * 1024

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export const parseUploadError = (error: any): UploadError => {
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    return {
      type: 'timeout',
      message: '上传超时',
      suggestion: '网络连接较慢，请检查网络后重试，或尝试上传较小的文件'
    }
  }
  
  if (error.code === 'ERR_NETWORK' || error.message === 'Network Error' || !error.response) {
    return {
      type: 'network',
      message: '网络连接失败',
      suggestion: '请检查网络连接是否正常，然后重试'
    }
  }
  
  if (error.response?.status === 413 || error.response?.data?.detail?.includes('大小超过限制')) {
    return {
      type: 'size_limit',
      message: '文件大小超过限制',
      suggestion: `单个文件大小不能超过 ${formatFileSize(MAX_FILE_SIZE)}，请压缩后重试`
    }
  }
  
  if (error.response?.status >= 500) {
    return {
      type: 'server',
      message: '服务器错误',
      suggestion: '服务器暂时无法处理请求，请稍后重试'
    }
  }
  
  return {
    type: 'unknown',
    message: error.response?.data?.detail || error.message || '上传失败',
    suggestion: '请稍后重试，如问题持续请联系管理员'
  }
}

export const fileApi = {
  async uploadFile(
    file: File, 
    articleId?: number, 
    onProgress?: (event: UploadProgressEvent) => void,
    signal?: AbortSignal
  ): Promise<FileUploadResponse> {
    if (file.size > MAX_FILE_SIZE) {
      throw {
        type: 'size_limit',
        message: '文件大小超过限制',
        suggestion: `单个文件大小不能超过 ${formatFileSize(MAX_FILE_SIZE)}，请压缩后重试`
      }
    }
    
    const formData = new FormData()
    formData.append('file', file)
    if (articleId) {
      formData.append('article_id', articleId.toString())
    }
    
    const response = await apiClient.post<FileUploadResponse>('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 300000,
      maxContentLength: Infinity,
      maxBodyLength: Infinity,
      signal,
      onUploadProgress: (progressEvent: AxiosProgressEvent) => {
        if (onProgress && progressEvent.total) {
          onProgress({
            loaded: progressEvent.loaded,
            total: progressEvent.total,
            progress: Math.round((progressEvent.loaded * 100) / progressEvent.total)
          })
        }
      }
    })
    return response.data
  },

  async uploadImage(
    file: File, 
    onProgress?: (event: UploadProgressEvent) => void,
    signal?: AbortSignal,
    articleId?: number
  ): Promise<FileUploadResponse> {
    if (file.size > MAX_FILE_SIZE) {
      throw {
        type: 'size_limit',
        message: '文件大小超过限制',
        suggestion: `单个文件大小不能超过 ${formatFileSize(MAX_FILE_SIZE)}，请压缩后重试`
      }
    }
    
    const formData = new FormData()
    formData.append('file', file)
    if (articleId) {
      formData.append('article_id', articleId.toString())
    }
    
    const response = await apiClient.post<FileUploadResponse>('/files/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 300000,
      maxContentLength: Infinity,
      maxBodyLength: Infinity,
      signal,
      onUploadProgress: (progressEvent: AxiosProgressEvent) => {
        if (onProgress && progressEvent.total) {
          onProgress({
            loaded: progressEvent.loaded,
            total: progressEvent.total,
            progress: Math.round((progressEvent.loaded * 100) / progressEvent.total)
          })
        }
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

  getContentUrl(fileId: number): string {
    return `${apiClient.defaults.baseURL}/files/${fileId}/content`
  },

  async downloadFile(fileId: number): Promise<{ data: Blob }> {
    const response = await apiClient.get(`/files/${fileId}/download`, {
      responseType: 'blob'
    })
    return response
  },

  async deleteFile(fileId: number): Promise<void> {
    await apiClient.delete(`/files/${fileId}`)
  },

  async updateFileOrder(orders: { id: number; order: number }[]): Promise<void> {
    await apiClient.put('/files/order', { orders })
  },

  async getStorageInfo(): Promise<StorageInfo> {
    const response = await apiClient.get<StorageInfo>('/files/admin/storage-info')
    return response.data
  },

  async deleteOrphanFiles(): Promise<{ deleted_count: number; deleted_size_formatted: string; errors: { path: string; error: string }[] }> {
    const response = await apiClient.delete('/files/admin/orphan-files')
    return response.data
  },

  async getArchiveContent(fileId: number): Promise<ArchiveContent> {
    const response = await apiClient.get<ArchiveContent>(`/files/${fileId}/archive-content`)
    return response.data
  },

  async previewFile(fileId: number): Promise<{ preview_count: number; file_id: number }> {
    const response = await apiClient.post<{ preview_count: number; file_id: number }>(`/files/${fileId}/preview`)
    return response.data
  }
}
