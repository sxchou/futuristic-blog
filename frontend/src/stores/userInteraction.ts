import { defineStore } from 'pinia'
import { ref } from 'vue'
import { likeApi, bookmarkApi } from '@/api'
import { useAuthStore } from './auth'

export const useUserInteractionStore = defineStore('userInteraction', () => {
  const likedArticleIds = ref<Set<number>>(new Set())
  const bookmarkedArticleIds = ref<Set<number>>(new Set())
  const isInitialized = ref(false)

  const initialize = async () => {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) {
      likedArticleIds.value = new Set()
      bookmarkedArticleIds.value = new Set()
      isInitialized.value = false
      return
    }

    if (isInitialized.value) return

    try {
      const [likedResponse, bookmarkedIds] = await Promise.all([
        likeApi.getUserLikedArticles(1, 1000),
        bookmarkApi.getBookmarkedIds()
      ])
      
      likedArticleIds.value = new Set(likedResponse.items.map((a: any) => a.id))
      bookmarkedArticleIds.value = new Set(bookmarkedIds)
      isInitialized.value = true
    } catch (error) {
      console.error('Failed to initialize user interaction store:', error)
    }
  }

  const refreshFromAuth = async () => {
    const authStore = useAuthStore()
    if (authStore.isAuthenticated) {
      isInitialized.value = false
      await initialize()
    } else {
      likedArticleIds.value = new Set()
      bookmarkedArticleIds.value = new Set()
      isInitialized.value = false
    }
  }

  const isLiked = (articleId: number): boolean => {
    return likedArticleIds.value.has(articleId)
  }

  const isBookmarked = (articleId: number): boolean => {
    return bookmarkedArticleIds.value.has(articleId)
  }

  const setLiked = (articleId: number, liked: boolean) => {
    if (liked) {
      likedArticleIds.value.add(articleId)
    } else {
      likedArticleIds.value.delete(articleId)
    }
  }

  const setBookmarked = (articleId: number, bookmarked: boolean) => {
    if (bookmarked) {
      bookmarkedArticleIds.value.add(articleId)
    } else {
      bookmarkedArticleIds.value.delete(articleId)
    }
  }

  const setLikedIds = (ids: number[]) => {
    likedArticleIds.value = new Set(ids)
  }

  const setBookmarkedIds = (ids: number[]) => {
    bookmarkedArticleIds.value = new Set(ids)
  }

  const markInitialized = () => {
    isInitialized.value = true
  }

  const toggleLike = async (articleId: number): Promise<{ is_liked: boolean; like_count: number } | null> => {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) return null

    const wasLiked = likedArticleIds.value.has(articleId)
    setLiked(articleId, !wasLiked)

    try {
      const result = await likeApi.toggle(articleId)
      setLiked(articleId, result.is_liked)
      return result
    } catch (error) {
      console.error('Failed to toggle like:', error)
      setLiked(articleId, wasLiked)
      return null
    }
  }

  const toggleBookmark = async (articleId: number): Promise<{ is_bookmarked: boolean; bookmark_count: number } | null> => {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) return null

    const wasBookmarked = bookmarkedArticleIds.value.has(articleId)
    setBookmarked(articleId, !wasBookmarked)

    try {
      const result = await bookmarkApi.toggle(articleId)
      setBookmarked(articleId, result.is_bookmarked)
      return {
        is_bookmarked: result.is_bookmarked,
        bookmark_count: result.bookmark_count ?? 0
      }
    } catch (error) {
      console.error('Failed to toggle bookmark:', error)
      setBookmarked(articleId, wasBookmarked)
      return null
    }
  }

  const clear = () => {
    likedArticleIds.value = new Set()
    bookmarkedArticleIds.value = new Set()
    isInitialized.value = false
  }

  const reset = () => {
    clear()
  }

  return {
    likedArticleIds,
    bookmarkedArticleIds,
    isInitialized,
    initialize,
    refreshFromAuth,
    isLiked,
    isBookmarked,
    setLiked,
    setBookmarked,
    setLikedIds,
    setBookmarkedIds,
    markInitialized,
    toggleLike,
    toggleBookmark,
    clear,
    reset
  }
})
