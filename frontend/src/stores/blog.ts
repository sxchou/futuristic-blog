import { defineStore } from 'pinia'
import { ref } from 'vue'
import { articleApi, categoryApi, tagApi, announcementApi } from '@/api'
import { isCancelError } from '@/utils/error'
import type { ArticleListItem, Category, Tag } from '@/types'
import type { Announcement } from '@/api/announcements'
import type { PublicStats } from '@/api/init'

let fetchArticlesController: AbortController | null = null
let fetchCategoriesPromise: Promise<void> | null = null
let fetchTagsPromise: Promise<void> | null = null
let fetchAnnouncementsPromise: Promise<void> | null = null

export const useBlogStore = defineStore('blog', () => {
  const articles = ref<ArticleListItem[]>([])
  const categories = ref<Category[]>([])
  const tags = ref<Tag[]>([])
  const announcements = ref<Announcement[]>([])
  const currentArticle = ref<ArticleListItem | null>(null)
  const loading = ref(false)
  const lastFetchTime = ref(0)
  const pagination = ref({
    page: 1,
    pageSize: 10,
    total: 0,
    totalPages: 0
  })
  const featuredArticles = ref<ArticleListItem[]>([])
  const publicStats = ref<PublicStats | null>(null)
  const currentFilter = ref<{
    category_id?: number
    tag_id?: number
    search?: string
  }>({})

  const fetchArticles = async (params?: {
    page?: number
    page_size?: number
    category_id?: number
    tag_id?: number
    is_featured?: boolean
    search?: string
  }) => {
    if (fetchArticlesController) {
      fetchArticlesController.abort()
    }
    fetchArticlesController = new AbortController()
    
    loading.value = true
    try {
      const response = await articleApi.getArticles({
        page: params?.page ?? pagination.value.page,
        page_size: params?.page_size ?? pagination.value.pageSize,
        ...params
      })
      articles.value = response.items
      pagination.value = {
        page: response.page,
        pageSize: response.page_size,
        total: response.total,
        totalPages: response.total_pages
      }
      lastFetchTime.value = Date.now()
      currentFilter.value = {
        category_id: params?.category_id,
        tag_id: params?.tag_id,
        search: params?.search
      }
    } catch (error: unknown) {
      if (error instanceof Error && (error.message === '请求已取消' || (error as unknown as Record<string, unknown>)?.isCancel)) {
        return
      }
      console.error('Failed to fetch articles:', error)
    } finally {
      loading.value = false
      fetchArticlesController = null
    }
  }

  const fetchCategories = async (force = false) => {
    if (!force && categories.value.length > 0) {
      return
    }
    
    if (fetchCategoriesPromise) {
      return fetchCategoriesPromise
    }
    
    fetchCategoriesPromise = (async () => {
      try {
        const data = await categoryApi.getCategories()
        categories.value = data
      } catch (error: unknown) {
        if (isCancelError(error)) {
          return
        }
        console.error('Failed to fetch categories:', error)
      } finally {
        fetchCategoriesPromise = null
      }
    })()
    
    return fetchCategoriesPromise
  }

  const fetchTags = async (force = false) => {
    if (!force && tags.value.length > 0) {
      return
    }
    
    if (fetchTagsPromise) {
      return fetchTagsPromise
    }
    
    fetchTagsPromise = (async () => {
      try {
        const data = await tagApi.getTags()
        tags.value = data
      } catch (error: unknown) {
        if (isCancelError(error)) {
          return
        }
        console.error('Failed to fetch tags:', error)
      } finally {
        fetchTagsPromise = null
      }
    })()
    
    return fetchTagsPromise
  }

  const fetchAnnouncements = async (force = false) => {
    if (!force && announcements.value.length > 0) {
      return
    }
    
    if (fetchAnnouncementsPromise) {
      return fetchAnnouncementsPromise
    }
    
    fetchAnnouncementsPromise = (async () => {
      try {
        const data = await announcementApi.getAnnouncements(true)
        announcements.value = data
      } catch (error: unknown) {
        if (isCancelError(error)) {
          return
        }
        console.error('Failed to fetch announcements:', error)
      } finally {
        fetchAnnouncementsPromise = null
      }
    })()
    
    return fetchAnnouncementsPromise
  }

  const addCategory = (category: Category) => {
    const existingIndex = categories.value.findIndex(c => c.id === category.id)
    if (existingIndex >= 0) {
      categories.value[existingIndex] = category
      categories.value.sort((a, b) => (a.order || 0) - (b.order || 0))
    } else {
      categories.value.push(category)
      categories.value.sort((a, b) => (a.order || 0) - (b.order || 0))
    }
  }

  const removeCategory = (categoryId: number) => {
    categories.value = categories.value.filter(c => c.id !== categoryId)
  }

  const addTag = (tag: Tag) => {
    const existingIndex = tags.value.findIndex(t => t.id === tag.id)
    if (existingIndex >= 0) {
      tags.value[existingIndex] = tag
    } else {
      tags.value.push(tag)
    }
  }

  const removeTag = (tagId: number) => {
    tags.value = tags.value.filter(t => t.id !== tagId)
  }

  const addArticle = (article: ArticleListItem) => {
    const existingIndex = articles.value.findIndex(a => a.id === article.id)
    if (existingIndex >= 0) {
      articles.value[existingIndex] = article
    } else {
      articles.value.unshift(article)
    }
  }

  const removeArticle = (articleId: number) => {
    articles.value = articles.value.filter(a => a.id !== articleId)
  }

  const getCategoryBySlug = (slug: string) => {
    return categories.value.find(c => c.slug === slug)
  }

  const getTagBySlug = (slug: string) => {
    return tags.value.find(t => t.slug === slug)
  }

  return {
    articles,
    categories,
    tags,
    announcements,
    currentArticle,
    loading,
    pagination,
    featuredArticles,
    publicStats,
    currentFilter,
    fetchArticles,
    fetchCategories,
    fetchTags,
    fetchAnnouncements,
    addCategory,
    removeCategory,
    addTag,
    removeTag,
    addArticle,
    removeArticle,
    getCategoryBySlug,
    getTagBySlug
  }
})
