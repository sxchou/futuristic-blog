import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { articleApi, categoryApi, tagApi } from '@/api'
import type { ArticleListItem, Category, Tag } from '@/types'

let fetchArticlesController: AbortController | null = null
let fetchCategoriesPromise: Promise<void> | null = null
let fetchTagsPromise: Promise<void> | null = null

export const useBlogStore = defineStore('blog', () => {
  const articles = ref<ArticleListItem[]>([])
  const categories = ref<Category[]>([])
  const tags = ref<Tag[]>([])
  const currentArticle = ref<ArticleListItem | null>(null)
  const loading = ref(false)
  const lastFetchTime = ref(0)
  const pagination = ref({
    page: 1,
    pageSize: 10,
    total: 0,
    totalPages: 0
  })

  const featuredArticles = computed(() => articles.value.filter(a => a.is_featured))

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
    } catch (error) {
      if (error instanceof Error && error.message === '请求已取消') {
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
        categories.value = await categoryApi.getCategories()
      } catch (error) {
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
        tags.value = await tagApi.getTags()
      } catch (error) {
        console.error('Failed to fetch tags:', error)
      } finally {
        fetchTagsPromise = null
      }
    })()
    
    return fetchTagsPromise
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
    currentArticle,
    loading,
    pagination,
    featuredArticles,
    fetchArticles,
    fetchCategories,
    fetchTags,
    getCategoryBySlug,
    getTagBySlug
  }
})
