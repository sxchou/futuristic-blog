import { defineStore } from 'pinia'
import { ref } from 'vue'
import { initApi } from '@/api'
import { isCancelError } from '@/utils/error'
import type { InitResponse } from '@/api/init'
import { useBlogStore } from './blog'
import { useSiteConfigStore } from './siteConfig'
import { useUserProfileStore } from './userProfile'
import { useUserInteractionStore } from './userInteraction'
import { useAuthStore } from './auth'

export const useInitStore = defineStore('init', () => {
  const isCoreInitialized = ref(false)
  const isArticlesInitialized = ref(false)
  const coreLoading = ref(false)
  const articlesLoading = ref(false)
  let corePromise: Promise<void> | null = null
  let articlesPromise: Promise<void> | null = null

  const initializeCore = async () => {
    if (isCoreInitialized.value) return
    if (corePromise) return corePromise

    coreLoading.value = true
    corePromise = (async () => {
      try {
        const data: InitResponse = await initApi.getInitData({
          page: 1,
          page_size: 100,
          featured_page_size: 5
        })
        
        const siteConfigStore = useSiteConfigStore()
        const blogStore = useBlogStore()
        const authStore = useAuthStore()
        const userProfileStore = useUserProfileStore()
        const userInteractionStore = useUserInteractionStore()

        if (data.site_config) {
          siteConfigStore.setConfigs(data.site_config)
        }
        
        if (data.categories) {
          blogStore.categories = data.categories
        }
        
        if (data.tags) {
          blogStore.tags = data.tags
        }
        
        if (data.announcements && data.announcements.length > 0) {
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
        
        if (data.featured_articles && data.featured_articles.items.length > 0) {
          blogStore.featuredArticles = data.featured_articles.items
        }
        
        if (data.github_stats) {
          siteConfigStore.setGithubStats(data.github_stats)
        }
        
        if (data.public_stats) {
          blogStore.publicStats = data.public_stats
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
        
        isCoreInitialized.value = true
      } catch (error: unknown) {
        if (isCancelError(error)) {
          corePromise = null
          return
        }
        console.error('Failed to initialize core data:', error)
      } finally {
        coreLoading.value = false
        corePromise = null
      }
    })()

    return corePromise
  }

  const initializeArticles = async (params?: {
    page?: number
    page_size?: number
    featured_page_size?: number
  }) => {
    if (isArticlesInitialized.value) return
    if (articlesPromise) return articlesPromise

    articlesLoading.value = true
    articlesPromise = (async () => {
      try {
        const data: InitResponse = await initApi.getInitData(params)
        
        const siteConfigStore = useSiteConfigStore()
        const blogStore = useBlogStore()
        const userProfileStore = useUserProfileStore()
        const userInteractionStore = useUserInteractionStore()
        const authStore = useAuthStore()

        if (data.site_config && !isCoreInitialized.value) {
          siteConfigStore.setConfigs(data.site_config)
        }
        
        if (data.categories && blogStore.categories.length === 0) {
          blogStore.categories = data.categories
        }
        
        if (data.tags && blogStore.tags.length === 0) {
          blogStore.tags = data.tags
        }
        
        if (data.announcements && data.announcements.length > 0 && blogStore.announcements.length === 0) {
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
        
        if (data.github_stats && !siteConfigStore.githubStats) {
          siteConfigStore.setGithubStats(data.github_stats)
        }
        
        if (data.public_stats && !blogStore.publicStats) {
          blogStore.publicStats = data.public_stats
        }
        
        if (authStore.isAuthenticated) {
          if (data.user_profile && !userProfileStore.profile) {
            userProfileStore.profile = data.user_profile
          }
          
          if (data.liked_article_ids && !userInteractionStore.isInitialized) {
            userInteractionStore.setLikedIds(data.liked_article_ids)
          }
          
          if (data.bookmarked_article_ids && !userInteractionStore.isInitialized) {
            userInteractionStore.setBookmarkedIds(data.bookmarked_article_ids)
          }
          
          userInteractionStore.markInitialized()
        }
        
        isArticlesInitialized.value = true
        isCoreInitialized.value = true
      } catch (error: unknown) {
        if (isCancelError(error)) {
          articlesPromise = null
          return
        }
        console.error('Failed to initialize articles:', error)
      } finally {
        articlesLoading.value = false
        articlesPromise = null
      }
    })()

    return articlesPromise
  }

  const initialize = async (params?: {
    page?: number
    page_size?: number
    featured_page_size?: number
  }) => {
    if (isCoreInitialized.value && isArticlesInitialized.value) return
    if (!isCoreInitialized.value) {
      await initializeCore()
    }
    return initializeArticles(params)
  }

  const reset = () => {
    isCoreInitialized.value = false
    isArticlesInitialized.value = false
    corePromise = null
    articlesPromise = null
  }

  const resetArticles = () => {
    isArticlesInitialized.value = false
    articlesPromise = null
  }

  return {
    isCoreInitialized,
    isArticlesInitialized,
    isInitialized: isArticlesInitialized,
    coreLoading,
    loading: articlesLoading,
    initializeCore,
    initializeArticles,
    initialize,
    reset,
    resetArticles
  }
})
