<template>
  <div class="pb-16 min-h-screen">
    <div class="container mx-auto px-4">
      <div class="text-center mb-12">
        <h1 class="text-3xl md:text-4xl font-bold mb-2">
          <span class="gradient-text">文章归档</span>
        </h1>
        <p class="text-gray-500 dark:text-gray-400 text-base">
          共 <span class="text-primary font-semibold">{{ totalArticles }}</span> 篇文章
        </p>
      </div>

      <div v-if="loading" class="flex flex-col items-center justify-center py-20">
        <div class="relative w-12 h-12 mb-4">
          <div class="absolute inset-0 border-4 border-primary/20 rounded-full"></div>
          <div class="absolute inset-0 border-4 border-transparent border-t-primary rounded-full animate-spin"></div>
        </div>
        <p class="text-gray-500 dark:text-gray-400 text-sm">加载中...</p>
      </div>

      <div v-else-if="archiveData.length === 0" class="text-center py-20">
        <div class="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gray-100 dark:bg-white/5 flex items-center justify-center">
          <svg class="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <p class="text-gray-500 dark:text-gray-400 mb-4">暂无文章</p>
        <router-link to="/" class="btn-primary inline-block">返回首页</router-link>
      </div>

      <div v-else class="max-w-4xl mx-auto">
        <div v-for="(yearData, yearIndex) in archiveData" :key="yearData.year" class="mb-12">
          <div class="flex items-center gap-4 mb-6">
            <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-primary/20">
              {{ yearData.year }}
            </div>
            <div>
              <h2 class="text-lg md:text-xl font-bold text-gray-900 dark:text-white">{{ yearData.year }}年</h2>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ yearData.months.reduce((sum, m) => sum + m.count, 0) }} 篇文章
              </p>
            </div>
            <div class="flex-1 h-px bg-gradient-to-r from-gray-200 dark:from-white/10 to-transparent"></div>
          </div>

          <div class="space-y-4">
            <div 
              v-for="monthData in yearData.months" 
              :key="monthData.month"
              class="glass-card-hover overflow-hidden"
            >
              <div class="px-6 py-4 bg-gradient-to-r from-gray-50 to-transparent dark:from-white/[0.02] dark:to-transparent border-b border-gray-200 dark:border-white/5">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                      <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div>
                      <h3 class="font-bold text-gray-900 dark:text-white">{{ monthData.month }}月</h3>
                      <p class="text-xs text-gray-500 dark:text-gray-400">{{ yearData.year }}年</p>
                    </div>
                  </div>
                  <span class="px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium">
                    {{ monthData.count }} 篇
                  </span>
                </div>
              </div>

              <div class="divide-y divide-gray-100 dark:divide-white/5">
                <router-link
                  v-for="article in monthData.articles"
                  :key="article.id"
                  :to="`/article/${article.slug}`"
                  class="group flex items-center gap-4 px-6 py-4 hover:bg-gray-50 dark:hover:bg-white/5 transition-all duration-300"
                >
                  <div class="flex items-center gap-3 w-20 flex-shrink-0">
                    <div class="w-8 h-8 rounded-lg bg-gray-100 dark:bg-white/5 flex items-center justify-center group-hover:bg-primary/10 transition-colors">
                      <svg class="w-4 h-4 text-gray-400 group-hover:text-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <span class="text-sm text-gray-500 dark:text-gray-400 font-medium">
                      {{ formatDate(article.created_at) }}
                    </span>
                  </div>

                  <div class="flex-1 min-w-0">
                    <h4 class="text-sm text-gray-900 dark:text-white font-medium truncate group-hover:text-primary transition-colors">
                      {{ article.title }}
                    </h4>
                  </div>

                  <div class="flex items-center gap-3 flex-shrink-0">
                    <span 
                      v-if="article.category" 
                      class="px-3 py-1 rounded-lg text-xs font-medium transition-all duration-300 group-hover:scale-105"
                      :style="{ 
                        backgroundColor: `${article.category.color}15`,
                        color: article.category.color 
                      }"
                    >
                      {{ article.category.name }}
                    </span>
                    <svg class="w-5 h-5 text-gray-300 dark:text-gray-600 group-hover:text-primary group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </router-link>
              </div>
            </div>
          </div>

          <div v-if="yearIndex < archiveData.length - 1" class="mt-12">
            <div class="h-px bg-gradient-to-r from-transparent via-gray-200 dark:via-white/10 to-transparent"></div>
          </div>
        </div>

        <div class="mt-12 text-center">
          <router-link to="/" class="btn-secondary inline-flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            返回首页
          </router-link>
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
