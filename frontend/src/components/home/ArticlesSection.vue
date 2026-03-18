<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useBlogStore } from '@/stores'
import ArticleCard from './ArticleCard.vue'
import Pagination from '@/components/common/Pagination.vue'

const blogStore = useBlogStore()
const isLoading = ref(false)
let searchTimeout: ReturnType<typeof setTimeout> | null = null

const debouncedFetch = (page: number) => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(async () => {
    isLoading.value = true
    try {
      await blogStore.fetchArticles({ page, page_size: 12 })
    } finally {
      isLoading.value = false
    }
  }, 300)
}

onMounted(() => {
  debouncedFetch(1)
})

const handlePageChange = (page: number) => {
  debouncedFetch(page)
  
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

onUnmounted(() => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
})
</script>

<template>
  <section class="py-12 relative">
    <div class="container mx-auto px-4">
      <div class="text-center mb-8">
        <h2 class="text-2xl md:text-3xl font-bold mb-2">
          <span class="gradient-text">最新文章</span>
        </h2>
        <p class="text-gray-500 dark:text-gray-400 text-sm">探索技术前沿，分享工程实践</p>
      </div>

      <div v-if="isLoading && blogStore.articles.length === 0" class="flex justify-center py-12">
        <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <ArticleCard
          v-for="article in blogStore.articles"
          :key="article.id"
          :article="article"
        />
      </div>

      <div v-if="blogStore.pagination.totalPages > 1" class="mt-8">
        <Pagination
          :current-page="blogStore.pagination.page"
          :total-pages="blogStore.pagination.totalPages"
          :total-items="blogStore.pagination.total"
          :page-size="12"
          @page-change="handlePageChange"
        />
      </div>
    </div>
  </section>
</template>
