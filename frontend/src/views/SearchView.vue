<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBlogStore } from '@/stores'
import ArticleCard from '@/components/home/ArticleCard.vue'
import Pagination from '@/components/common/Pagination.vue'
import { usePageSize } from '@/composables/usePageSize'

const route = useRoute()
const router = useRouter()
const blogStore = useBlogStore()

const searchQuery = ref('')
const isSearching = ref(false)
const searchResultsRef = ref<HTMLElement | null>(null)
let currentSearchKeyword = ''

const { pageSize } = usePageSize()

const smoothScrollTo = (targetY: number) => {
  requestAnimationFrame(() => {
    window.scrollTo({
      top: targetY,
      behavior: 'smooth'
    })
  })
}

const scrollToResults = () => {
  requestAnimationFrame(() => {
    if (searchResultsRef.value) {
      const element = searchResultsRef.value
      const offset = 85
      const elementPosition = element.getBoundingClientRect().top
      const offsetPosition = elementPosition + window.pageYOffset - offset
      
      smoothScrollTo(offsetPosition)
    }
  })
}

const restoreScrollPosition = () => {
  const savedPosition = sessionStorage.getItem('scrollPosition')
  if (savedPosition) {
    const scrollY = parseInt(savedPosition)
    sessionStorage.removeItem('scrollPosition')
    
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        smoothScrollTo(scrollY)
      })
    })
    
    return true
  }
  return false
}

const performSearch = async (page: number = 1, updateUrl: boolean = true, shouldScroll: boolean = false) => {
  const keyword = currentSearchKeyword || searchQuery.value.trim()
  
  if (!keyword) {
    return
  }
  
  isSearching.value = true
  try {
    await blogStore.fetchArticles({ 
      search: keyword,
      page: page,
      page_size: pageSize.value
    })
    
    if (updateUrl) {
      const newQuery: Record<string, string> = { q: keyword }
      if (page !== 1) {
        newQuery.page = page.toString()
      }
      router.replace({ path: '/search', query: newQuery })
    }
    
    if (shouldScroll) {
      scrollToResults()
    }
  } finally {
    isSearching.value = false
  }
}

watch(pageSize, async (newSize, oldSize) => {
  if (newSize !== oldSize && currentSearchKeyword) {
    const currentPage = parseInt(route.query.page as string) || 1
    
    await performSearch(currentPage, false, false)
    
    const totalPages = blogStore.pagination.totalPages
    if (currentPage > totalPages && totalPages > 0) {
      const newPage = totalPages
      await performSearch(newPage, true, false)
    }
  }
})

watch(() => route.query.q, (newQuery) => {
  if (newQuery) {
    const keyword = newQuery as string
    searchQuery.value = keyword
    currentSearchKeyword = keyword
    const pageFromUrl = parseInt(route.query.page as string) || 1
    const isReturningFromArticle = sessionStorage.getItem('returningFromArticle') === 'true'
    
    performSearch(pageFromUrl, false, false)
    
    if (isReturningFromArticle) {
      const restored = restoreScrollPosition()
      if (!restored && pageFromUrl > 1) {
        scrollToResults()
      }
      sessionStorage.removeItem('returningFromArticle')
    }
  }
}, { immediate: true })

onMounted(() => {
  const query = route.query.q as string
  if (query) {
    searchQuery.value = query
    currentSearchKeyword = query
  }
})

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    currentSearchKeyword = searchQuery.value.trim()
    router.push({ path: '/search', query: { q: searchQuery.value } })
  }
}

const handlePageChange = (page: number) => {
  performSearch(page, true, true)
}
</script>

<template>
  <div class="pb-20">
    <div class="container mx-auto px-4">
      <div class="max-w-3xl mx-auto mb-12">
        <h1 class="text-3xl md:text-4xl font-bold text-center mb-8">
          <span class="gradient-text">搜索文章</span>
        </h1>

        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="输入关键词搜索（支持 * 和 ? 通配符）..."
            class="input-cyber text-lg py-4 pl-12 pr-4"
            @keyup.enter="handleSearch"
          />
          <svg class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <button
            @click="handleSearch"
            class="absolute right-2 top-1/2 -translate-y-1/2 btn-primary py-2"
          >
            搜索
          </button>
        </div>
      </div>

      <div v-if="isSearching" class="flex justify-center py-20">
        <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>

      <div v-else-if="route.query.q && blogStore.articles.length === 0" class="text-center py-20">
        <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-gray-100 dark:bg-dark-100 flex items-center justify-center">
          <svg class="w-10 h-10 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">未找到相关结果</h2>
        <p class="text-gray-500 dark:text-gray-400">尝试使用不同的关键词搜索</p>
      </div>

      <div v-else-if="blogStore.articles.length > 0" ref="searchResultsRef">
        <div class="text-center mb-8">
          <p class="text-gray-400">
            找到 <span class="text-primary font-semibold">{{ blogStore.pagination.total }}</span> 篇相关文章
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          <ArticleCard
            v-for="article in blogStore.articles"
            :key="article.id"
            :article="article"
            :highlight-keyword="currentSearchKeyword"
          />
        </div>

        <div v-if="blogStore.pagination.totalPages > 1" class="mt-8">
          <Pagination
            :current-page="blogStore.pagination.page"
            :total-pages="blogStore.pagination.totalPages"
            :total-items="blogStore.pagination.total"
            :page-size="pageSize"
            @page-change="handlePageChange"
          />
        </div>
      </div>

      <div v-else class="text-center py-20">
        <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-dark-100 flex items-center justify-center">
          <svg class="w-10 h-10 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-white mb-2">开始搜索</h2>
        <p class="text-gray-400">输入关键词搜索文章、标签、分类</p>
      </div>
    </div>
  </div>
</template>
