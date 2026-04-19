import { defineStore } from 'pinia'
import { ref } from 'vue'
import { initApi } from '@/api'
import type { InitResponse } from '@/api/init'
import { useBlogStore } from './blog'
import { useSiteConfigStore } from './siteConfig'
import { useUserProfileStore } from './userProfile'
import { useUserInteractionStore } from './userInteraction'
import { useAuthStore } from './auth'

export const useInitStore = defineStore('init', () => {
  const isInitialized = ref(false)
  const loading = ref(false)
  let initPromise: Promise<void> | null = null

  const initialize = async (params?: {
    page?: number
    page_size?: number
    featured_page_size?: number
  }) => {
    if (isInitialized.value) return
    if (initPromise) return initPromise

    loading.value = true
    initPromise = (async () => {
      try {
        const data: InitResponse = await initApi.getInitData(params)
        
        const siteConfigStore = useSiteConfigStore()
        const blogStore = useBlogStore()
        const userProfileStore = useUserProfileStore()
        const userInteractionStore = useUserInteractionStore()
        const authStore = useAuthStore()

        if (data.site_config) {
          siteConfigStore.setConfigs(data.site_config)
        }
        
        if (data.categories) {
          blogStore.categories = data.categories
        }
        
        if (data.tags) {
          blogStore.tags = data.tags
        }
        
        if (data.announcements) {
          blogStore.announcements = data.announcements
        }
        
        if (data.articles) {
          blogStore.articles = data.articles.items
          blogStore.pagination = {
            page: data.articles.page,
            pageSize: data.articles.page_size,
            total: data.articles.total,
            totalPages: data.articles.total_pages
          }
        }
        
        if (data.github_stats) {
          siteConfigStore.githubStats = data.github_stats
        }
        
        if (authStore.isAuthenticated) {
          if (data.user_profile) {
            userProfileStore.profile = data.user_profile
          }
          
          if (data.liked_article_ids) {
            userInteractionStore.setLikedIds(data.liked_article_ids)
          }
          
          if (data.bookmarked_article_ids) {
            userInteractionStore.setBookmarkedIds(data.bookmarked_article_ids)
          }
          
          userInteractionStore.markInitialized()
        }
        
        isInitialized.value = true
      } catch (error) {
        console.error('Failed to initialize app:', error)
      } finally {
        loading.value = false
        initPromise = null
      }
    })()

    return initPromise
  }

  const reset = () => {
    isInitialized.value = false
    initPromise = null
  }

  return {
    isInitialized,
    loading,
    initialize,
    reset
  }
})
