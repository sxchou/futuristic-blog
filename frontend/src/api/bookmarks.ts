import apiClient from './client'
import type { BookmarkResponse, ArticleListItem, PaginatedResponse } from '@/types'

export const bookmarkApi = {
  toggle: async (articleId: number): Promise<BookmarkResponse> => {
    const response = await apiClient.post(`/bookmarks/${articleId}`)
    return response.data
  },

  getStatus: async (articleId: number): Promise<BookmarkResponse> => {
    const response = await apiClient.get(`/bookmarks/${articleId}`)
    return response.data
  },

  getUserBookmarks: async (page: number = 1, pageSize: number = 10): Promise<PaginatedResponse<ArticleListItem>> => {
    const response = await apiClient.get('/bookmarks/', {
      params: { page, page_size: pageSize }
    })
    return response.data
  },

  getBookmarkedIds: async (): Promise<number[]> => {
    const response = await apiClient.get('/bookmarks/ids')
    return response.data
  }
}
