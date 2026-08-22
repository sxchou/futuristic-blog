import { defineStore } from 'pinia'
import { ref } from 'vue'
import { articleApi, categoryApi, tagApi, announcementApi } from '@/api'
import { isCancelError } from '@/utils/error'
import { performanceMonitor } from '@/utils/performance'
import type { ArticleListItem, Category, Tag } from '@/types'
import type { Announcement } from '@/api/announcements'

let fetchArticlesController: AbortController | null = null
/** 请求序号：只有最新一次请求允许更新状态，防止过期响应覆盖新数据 */
let fetchArticlesSeq = 0
let fetchCategoriesPromise: Promise<void> | null = null
let fetchTagsPromise: Promise<void> | null = null
let fetchAnnouncementsPromise: Promise<void> | null = null

interface ArticleFilter {
  category_id?: number
  tag_id?: number
  search?: string
}

const filterKeyOf = (filter: ArticleFilter): string =>
  `${filter.category_id ?? ''}-${filter.tag_id ?? ''}-${filter.search ?? ''}`

export const useBlogStore = defineStore('blog', () => {
  const articles = ref<ArticleListItem[]>([])
  const categories = ref<Category[]>([])
  const tags = ref<Tag[]>([])
  const announcements = ref<Announcement[]>([])
  const currentArticle = ref<ArticleListItem | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastFetchTime = ref(0)
  const pagination = ref({
    page: 1,
    pageSize: 10,
    total: 0,
    totalPages: 0
  })
  const featuredArticles = ref<ArticleListItem[]>([])
  const currentFilter = ref<ArticleFilter>({})

  const fetchArticles = async (params?: {
    page?: number
    page_size?: number
    category_id?: number
    tag_id?: number
    is_featured?: boolean
    search?: string
  }) => {
    // 请求序号守卫：仅最新请求可以更新状态
    const seq = ++fetchArticlesSeq

    // 取消上一个未完成的请求（如用户快速切换分类/标签）
    if (fetchArticlesController) {
      fetchArticlesController.abort()
    }
    const controller = new AbortController()
    fetchArticlesController = controller

    // 筛选条件立即同步，确保界面状态与请求一致
    const nextFilter: ArticleFilter = {
      category_id: params?.category_id,
      tag_id: params?.tag_id,
      search: params?.search
    }
    const filterChanged = filterKeyOf(nextFilter) !== filterKeyOf(currentFilter.value)
    currentFilter.value = nextFilter
    error.value = null
    loading.value = true

    // 筛选条件变化时立即清空旧内容，杜绝新旧内容混合显示
    if (filterChanged) {
      articles.value = []
      pagination.value = {
        page: 1,
        pageSize: pagination.value.pageSize,
        total: 0,
        totalPages: 0
      }
    }

    const startTime = performance.now()
    try {
      const response = await articleApi.getArticles(
        {
          page: params?.page ?? pagination.value.page,
          page_size: params?.page_size ?? pagination.value.pageSize,
          ...params
        },
        { signal: controller.signal }
      )

      // 过期响应守卫：用户已发起更新的请求，丢弃本次结果
      if (seq !== fetchArticlesSeq) return

      articles.value = response.items
      pagination.value = {
        page: response.page,
        pageSize: response.page_size,
        total: response.total,
        totalPages: response.total_pages
      }
      lastFetchTime.value = Date.now()
      performanceMonitor.recordOperation('fetchArticles', performance.now() - startTime, true)
    } catch (err: unknown) {
      if (seq !== fetchArticlesSeq) return
      if (isCancelError(err)) return
      console.error('Failed to fetch articles:', err)
      error.value = '文章加载失败，请检查网络后重试'
      performanceMonitor.recordOperation('fetchArticles', performance.now() - startTime, false)
    } finally {
      // 仅最新请求负责复位加载状态，避免被取消的旧请求提前关闭加载指示
      if (seq === fetchArticlesSeq) {
        loading.value = false
        if (fetchArticlesController === controller) {
          fetchArticlesController = null
        }
      }
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
    error,
    pagination,
    featuredArticles,
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
