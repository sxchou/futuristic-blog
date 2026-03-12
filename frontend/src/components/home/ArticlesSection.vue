<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useBlogStore } from '@/stores'
import ArticleCard from './ArticleCard.vue'

const blogStore = useBlogStore()
const isLoading = ref(false)

onMounted(async () => {
  isLoading.value = true
  await blogStore.fetchArticles({ page: 1 })
  isLoading.value = false
})

const loadMore = async () => {
  if (blogStore.pagination.page >= blogStore.pagination.totalPages) return
  isLoading.value = true
  await blogStore.fetchArticles({ page: blogStore.pagination.page + 1 })
  isLoading.value = false
}
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

      <div v-if="blogStore.pagination.page < blogStore.pagination.totalPages" class="text-center mt-8">
        <button
          @click="loadMore"
          :disabled="isLoading"
          class="btn-secondary"
        >
          <span v-if="isLoading" class="flex items-center gap-2">
            <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            加载中...
          </span>
          <span v-else>加载更多</span>
        </button>
      </div>
    </div>
  </section>
</template>
