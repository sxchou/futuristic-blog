import apiClient from './client'
import type { Comment, CommentCreate, AdminComment, CommentAuditLog, CommentAuditRequest, BatchAuditRequest, PaginatedResponse } from '@/types'

export const commentApi = {
  getArticleComments: async (articleId: number): Promise<Comment[]> => {
    const response = await apiClient.get(`/comments/article/${articleId}`)
    return response.data
  },

  create: async (data: CommentCreate): Promise<Comment> => {
    const response = await apiClient.post('/comments', data)
    return response.data
  },

  delete: async (commentId: number): Promise<void> => {
    await apiClient.delete(`/comments/${commentId}`)
  },

  getAdminComments: async (params: {
    page?: number
    page_size?: number
    status?: 'pending' | 'approved' | 'rejected'
    article_id?: number
  }): Promise<PaginatedResponse<AdminComment>> => {
    const response = await apiClient.get('/comments/admin', { params })
    return response.data
  },

  auditComment: async (commentId: number, data: CommentAuditRequest): Promise<AdminComment> => {
    const response = await apiClient.put(`/comments/admin/${commentId}/audit`, data)
    return response.data
  },

  batchAudit: async (data: BatchAuditRequest): Promise<{ message: string; updated_count: number }> => {
    const response = await apiClient.post('/comments/admin/batch-audit', data)
    return response.data
  },

  getAuditLogs: async (commentId: number): Promise<CommentAuditLog[]> => {
    const response = await apiClient.get(`/comments/admin/${commentId}/logs`)
    return response.data
  },

  adminDelete: async (commentId: number, keepRecord: boolean = true): Promise<{ message: string; type: string }> => {
    const response = await apiClient.delete(`/comments/admin/${commentId}`, {
      params: { keep_record: keepRecord }
    })
    return response.data
  }
}
