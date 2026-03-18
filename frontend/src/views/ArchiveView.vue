<template>
  <div class="pt-20 pb-16 min-h-screen">
    <div class="container mx-auto px-4">
      <div class="text-center mb-8">
        <h1 class="text-2xl md:text-3xl font-bold mb-2">
          <span class="gradient-text">文章归档</span>
        </h1>
        <p class="text-gray-500 dark:text-gray-400 text-sm">
          共 <span class="text-primary font-semibold">{{ totalArticles }}</span> 篇文章
        </p>
      </div>

      <div v-if="loading" class="flex flex-col items-center justify-center py-16">
        <div class="relative w-10 h-10 mb-3">
          <div class="absolute inset-0 border-2 border-primary/20 rounded-full"></div>
          <div class="absolute inset-0 border-2 border-transparent border-t-primary rounded-full animate-spin"></div>
        </div>
        <p class="text-gray-500 dark:text-gray-400 text-sm">加载中...</p>
      </div>

      <div v-else-if="archiveData.length === 0" class="text-center py-16">
        <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-100 dark:bg-white/5 flex items-center justify-center">
          <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <p class="text-gray-500 dark:text-gray-400 text-sm">暂无文章</p>
        <router-link to="/" class="text-primary text-sm hover:underline mt-3 inline-block">返回首页</router-link>
      </div>

      <div v-else class="max-w-4xl mx-auto">
        <div v-for="(yearData, yearIndex) in archiveData" :key="yearData.year">
          <div class="flex items-center gap-3 mb-4">
            <div class="flex items-center gap-2">
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-primary/20">
                {{ yearData.year }}
              </div>
              <span class="text-sm font-semibold text-gray-700 dark:text-gray-300">
                {{ yearData.months.reduce((sum, m) => sum + m.count, 0) }} 篇
              </span>
            </div>
            <div class="flex-1 h-px bg-gray-200 dark:bg-white/10"></div>
          </div>

          <div class="space-y-3 mb-8">
            <div 
              v-for="monthData in yearData.months" 
              :key="monthData.month"
              class="bg-gray-50 dark:bg-white/[0.02] rounded-xl border border-gray-200 dark:border-white/5 overflow-hidden"
            >
              <div class="px-4 py-2 flex items-center justify-between border-b border-gray-200 dark:border-white/5 bg-white/50 dark:bg-white/[0.02]">
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ monthData.month }}月</span>
                <span class="text-sm text-gray-500 dark:text-gray-400">{{ monthData.count }} 篇</span>
              </div>

              <div class="divide-y divide-gray-100 dark:divide-white/5">
                <router-link
                  v-for="article in monthData.articles"
                  :key="article.id"
                  :to="`/article/${article.slug}`"
                  class="group flex items-center gap-3 px-4 py-2.5 hover:bg-white dark:hover:bg-white/5 transition-colors"
                >
                  <span class="text-sm text-gray-500 dark:text-gray-400 w-12 flex-shrink-0">
                    {{ formatDate(article.created_at) }}
                  </span>
                  <span class="flex-1 text-sm text-gray-700 dark:text-gray-300 truncate group-hover:text-primary transition-colors">
                    {{ article.title }}
                  </span>
                  <span 
                    v-if="article.category" 
                    class="px-2 py-0.5 rounded text-xs flex-shrink-0"
                    :style="{ 
                      backgroundColor: `${article.category.color}15`,
                      color: article.category.color 
                    }"
                  >
                    {{ article.category.name }}
                  </span>
                </router-link>
              </div>
            </div>
          </div>

          <div v-if="yearIndex < archiveData.length - 1" class="h-px bg-gray-200 dark:bg-white/10 mb-8"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import apiClient from '@/api/client'

interface Article {
  id: number
  title: string
  slug: string
  created_at: string
  category: {
    id: number
    name: string
    slug: string
    color?: string
  } | null
}

interface MonthData {
  month: number
  count: number
  articles: Article[]
}

interface YearData {
  year: number
  months: MonthData[]
}

const archiveData = ref<YearData[]>([])
const loading = ref(true)

const totalArticles = computed(() => {
  return archiveData.value.reduce((total, year) => {
    return total + year.months.reduce((monthTotal, month) => monthTotal + month.count, 0)
  }, 0)
})

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${month}-${day}`
}

const fetchArchive = async () => {
  try {
    loading.value = true
    const response = await apiClient.get('/articles/archive/list')
    archiveData.value = response.data
  } catch (error) {
    console.error('Failed to fetch archive:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchArchive()
})
</script>
