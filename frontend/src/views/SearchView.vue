<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBlogStore } from '@/stores'
import BlogSidebar from '@/components/common/BlogSidebar.vue'
import LeftSidebar from '@/components/common/LeftSidebar.vue'
import Pagination from '@/components/common/Pagination.vue'
import { usePageSize } from '@/composables/usePageSize'
import { getMediaUrl } from '@/utils/media'

const route = useRoute()
const router = useRouter()
const blogStore = useBlogStore()

const searchQuery = ref('')
const isSearching = ref(false)
const searchResultsRef = ref<HTMLElement | null>(null)
let currentSearchKeyword = ''

const { pageSize } = usePageSize()

const scrollToResults = () => {
  requestAnimationFrame(() => {
    if (searchResultsRef.value) {
      const element = searchResultsRef.value
      const offset = 85
      const elementPosition = element.getBoundingClientRect().top
      const offsetPosition = elementPosition + window.pageYOffset - offset
      window.scrollTo({ top: offsetPosition, behavior: 'smooth' })
    }
  })
}

const performSearch = async (page: number = 1, updateUrl: boolean = true, shouldScroll: boolean = false) => {
  const keyword = currentSearchKeyword || searchQuery.value.trim()
  if (!keyword) return
  
  isSearching.value = true
  try {
    await blogStore.fetchArticles({
      search: keyword,
      page: page,
      page_size: pageSize.value
    })
    if (updateUrl) {
      const newQuery: Record<string, string> = { q: keyword }
      if (page !== 1) newQuery.page = page.toString()
      router.replace({ path: '/search', query: newQuery })
    }
    if (shouldScroll) scrollToResults()
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
      await performSearch(totalPages, true, false)
    }
  }
})

watch(() => route.query.q, (newQuery) => {
  if (newQuery) {
    const keyword = newQuery as string
    searchQuery.value = keyword
    currentSearchKeyword = keyword
    const pageFromUrl = parseInt(route.query.page as string) || 1
    performSearch(pageFromUrl, false, false)
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

const formatDate = (date: string) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
</script>

<template>
  <div class="flex flex-col lg:flex-row gap-6">
    <div class="lg:w-56 flex-shrink-0 hidden lg:block">
      <div class="lg:sticky lg:top-20">
        <LeftSidebar />
      </div>
    </div>
    
    <div class="flex-1 min-w-0">
      <div class="mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2">
          搜索文章
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          输入关键词搜索文章
        </p>
      </div>

      <div class="mb-8">
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="输入关键词搜索（支持 * 和 ? 通配符）..."
            class="w-full px-4 py-3.5 pl-11 bg-gray-50 dark:bg-dark-300 border border-gray-200 dark:border-white/10 rounded-xl text-gray-800 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all"
            @keyup.enter="handleSearch"
          >
          <svg
            class="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <button
            class="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-600 transition-colors"
            @click="handleSearch"
          >
            搜索
          </button>
        </div>
      </div>

      <div
        v-if="isSearching"
        class="flex justify-center py-20"
      >
        <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>

      <div
        v-else-if="route.query.q && blogStore.articles.length === 0"
        class="text-center py-16"
      >
        <svg
          class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-1">
          未找到相关结果
        </h2>
        <p class="text-gray-500 dark:text-gray-400 text-sm">
          尝试使用不同的关键词搜索
        </p>
      </div>

      <div
        v-else-if="blogStore.articles.length > 0"
        ref="searchResultsRef"
      >
        <div class="mb-6">
          <p class="text-sm text-gray-400">
            找到 <span class="text-primary font-semibold">{{ blogStore.pagination.total }}</span> 篇相关文章
          </p>
        </div>

        <div class="space-y-4">
          <router-link
            v-for="article in blogStore.articles"
            :key="article.id"
            :to="{ path: `/article/${article.slug}`, query: currentSearchKeyword ? { highlight: currentSearchKeyword } : {} }"
            class="article-card group flex flex-col sm:flex-row gap-4"
          >
            <div
              v-if="article.cover_image"
              class="relative flex-shrink-0 overflow-hidden rounded-xl h-32 sm:w-40 sm:h-24"
            >
              <img
                :src="getMediaUrl(article.cover_image)"
                :alt="article.title"
                class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              >
            </div>
            <div class="flex-1 min-w-0 flex flex-col">
              <h3 class="article-card-title">
                <template v-if="article.highlighted_title">
                  <span v-html="article.highlighted_title" />
                </template>
                <template v-else>
                  {{ article.title }}
                </template>
              </h3>
              <p class="article-card-excerpt">
                <template v-if="article.highlighted_summary">
                  <span v-html="article.highlighted_summary" />
                </template>
                <template v-else>
                  {{ article.summary }}
                </template>
              </p>
              <div class="flex items-center gap-3 mt-auto pt-2">
                <span
                  v-if="article.category"
                  class="inline-flex items-center gap-1 text-xs font-medium"
                  :style="{ color: article.category.color }"
                >
                  <span
                    class="w-1.5 h-1.5 rounded-full"
                    :style="{ backgroundColor: article.category.color }"
                  />
                  {{ article.category.name }}
                </span>
                <span class="text-xs text-gray-400">{{ formatDate(article.created_at) }}</span>
                <span class="text-xs text-gray-400 flex items-center gap-1">
                  <svg
                    class="w-3 h-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  ><path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  /></svg>
                  {{ article.view_count }}
                </span>
              </div>
            </div>
          </router-link>
        </div>

        <div
          v-if="blogStore.pagination.totalPages > 1"
          class="mt-8"
        >
          <Pagination
            :current-page="blogStore.pagination.page"
            :total-pages="blogStore.pagination.totalPages"
            :total-items="blogStore.pagination.total"
            :page-size="pageSize"
            @page-change="handlePageChange"
          />
        </div>
      </div>

      <div
        v-else
        class="text-center py-16"
      >
        <svg
          class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-1">
          开始搜索
        </h2>
        <p class="text-gray-500 dark:text-gray-400 text-sm">
          输入关键词搜索文章、标签、分类
        </p>
      </div>
    </div>

    <div class="lg:w-56 flex-shrink-0 hidden lg:block">
      <div class="lg:sticky lg:top-20">
        <BlogSidebar />
      </div>
    </div>
  </div>
</template>
