<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBlogStore } from '@/stores'
import ArticleCard from '@/components/home/ArticleCard.vue'

const route = useRoute()
const router = useRouter()
const blogStore = useBlogStore()

const searchQuery = ref('')
const isSearching = ref(false)

const performSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  isSearching.value = true
  try {
    await blogStore.fetchArticles({ search: searchQuery.value })
  } finally {
    isSearching.value = false
  }
}

watch(() => route.query.q, (newQuery) => {
  if (newQuery) {
    searchQuery.value = newQuery as string
    performSearch()
  }
}, { immediate: true })

onMounted(() => {
  if (route.query.q) {
    searchQuery.value = route.query.q as string
    performSearch()
  }
})

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({ path: '/search', query: { q: searchQuery.value } })
    performSearch()
  }
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
            placeholder="输入关键词搜索..."
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

      <div v-else-if="blogStore.articles.length > 0">
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
