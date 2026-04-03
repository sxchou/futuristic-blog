<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBlogStore } from '@/stores'
import ArticleCard from './ArticleCard.vue'
import Pagination from '@/components/common/Pagination.vue'
import { usePageSize } from '@/composables/usePageSize'

const route = useRoute()
const router = useRouter()
const blogStore = useBlogStore()
const isLoading = ref(false)
const articlesSectionRef = ref<HTMLElement | null>(null)
let searchTimeout: ReturnType<typeof setTimeout> | null = null

const { pageSize } = usePageSize()

const displayArticles = computed(() => blogStore.articles.slice(0, pageSize.value))

const scrollToArticlesSection = () => {
  requestAnimationFrame(() => {
    if (articlesSectionRef.value) {
      const element = articlesSectionRef.value
      const offset = 85
      const elementPosition = element.getBoundingClientRect().top
      const offsetPosition = elementPosition + window.pageYOffset - offset
      
      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      })
    }
  })
}

const debouncedFetch = (page: number, updateUrl: boolean = true, shouldScroll: boolean = false) => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(async () => {
    isLoading.value = true
    try {
      await blogStore.fetchArticles({ page, page_size: pageSize.value })
      
      if (updateUrl && page !== 1) {
        router.replace({ query: { ...route.query, page: page.toString() } })
      } else if (updateUrl && page === 1 && route.query.page) {
        const newQuery = { ...route.query }
        delete newQuery.page
        router.replace({ query: newQuery })
      }
      
      if (shouldScroll) {
        scrollToArticlesSection()
      }
    } finally {
      isLoading.value = false
    }
  }, 100)
}

watch(pageSize, async (newSize, oldSize) => {
  if (newSize !== oldSize && blogStore.articles.length > 0) {
    const currentPage = parseInt(route.query.page as string) || 1
    
    await blogStore.fetchArticles({ page: currentPage, page_size: newSize })
    
    const totalPages = blogStore.pagination.totalPages
    if (currentPage > totalPages && totalPages > 0) {
      const newPage = totalPages
      await blogStore.fetchArticles({ page: newPage, page_size: newSize })
      
      if (newPage === 1) {
        const newQuery = { ...route.query }
        delete newQuery.page
        router.replace({ query: newQuery })
      } else {
        router.replace({ query: { ...route.query, page: newPage.toString() } })
      }
    }
  }
})

watch(() => route.path, async (newPath) => {
  if (newPath === '/') {
    const pageFromUrl = parseInt(route.query.page as string) || 1
    await blogStore.fetchArticles({ page: pageFromUrl, page_size: pageSize.value })
  }
})

onMounted(async () => {
  const pageFromUrl = parseInt(route.query.page as string) || 1
  
  if (blogStore.articles.length === 0 || blogStore.pagination.page !== pageFromUrl) {
    await blogStore.fetchArticles({ page: pageFromUrl, page_size: pageSize.value })
  }
})

const handlePageChange = (page: number) => {
  debouncedFetch(page, true, true)
}

onUnmounted(() => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
})
</script>

<template>
  <section class="pb-12 relative">
    <div class="container mx-auto px-4">
      <div class="text-center mb-8">
        <h2 class="text-3xl md:text-4xl font-bold mb-2">
          <span class="gradient-text">最新文章</span>
        </h2>
        <p class="text-gray-500 dark:text-gray-400 text-base">探索技术前沿，分享工程实践</p>
      </div>

      <div v-if="isLoading && blogStore.articles.length === 0" class="flex justify-center py-12">
        <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>

      <div v-else ref="articlesSectionRef" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <ArticleCard
          v-for="article in displayArticles"
          :key="article.id"
          :article="article"
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
  </section>
</template>
