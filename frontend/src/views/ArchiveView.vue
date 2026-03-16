<template>
  <div class="min-h-screen bg-white dark:bg-dark pt-20 pb-16">
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2">
          文章归档
        </h1>
        <p class="text-gray-500 dark:text-gray-400 text-sm">
          共 <span class="text-primary font-bold">{{ totalArticles }}</span> 篇文章
        </p>
      </div>

      <div v-if="loading" class="flex justify-center py-20">
        <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
      </div>

      <div v-else-if="archiveData.length === 0" class="text-center py-20">
        <div class="w-24 h-24 mx-auto mb-6 rounded-full bg-gray-100 dark:bg-white/5 flex items-center justify-center">
          <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <p class="text-gray-500 dark:text-gray-400">暂无文章</p>
      </div>

      <div v-else class="relative">
        <div class="absolute left-4 md:left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary via-accent to-primary/30 md:-translate-x-1/2"></div>

        <div v-for="(yearData, yearIndex) in archiveData" :key="yearData.year" class="relative">
          <div class="flex items-center justify-center mb-8">
            <div class="relative z-10 px-6 py-3 bg-gradient-to-r from-primary to-accent rounded-full text-white font-bold text-lg shadow-lg shadow-primary/30">
              {{ yearData.year }} 年
            </div>
          </div>

          <div v-for="(monthData, monthIndex) in yearData.months" :key="monthData.month" class="relative mb-12">
            <div class="flex items-center mb-6" :class="isEven(yearIndex * 12 + monthIndex) ? 'md:flex-row' : 'md:flex-row-reverse'">
              <div class="hidden md:block md:w-1/2" :class="isEven(yearIndex * 12 + monthIndex) ? 'md:pr-12 md:text-right' : 'md:pl-12'"></div>
              
              <div class="absolute left-4 md:left-1/2 w-4 h-4 bg-accent rounded-full border-4 border-white dark:border-gray-900 md:-translate-x-1/2 z-10 shadow-lg"></div>
              
              <div class="hidden md:block md:w-1/2" :class="isEven(yearIndex * 12 + monthIndex) ? 'md:pl-12' : 'md:pr-12 md:text-right'"></div>
            </div>

            <div class="ml-12 md:ml-0" :class="isEven(yearIndex * 12 + monthIndex) ? 'md:mr-auto md:pr-12 md:w-1/2 md:text-right' : 'md:ml-auto md:pl-12 md:w-1/2'">
              <div class="glass-card p-6 hover:shadow-xl hover:shadow-primary/10 transition-all duration-300">
                <div class="flex items-center gap-3 mb-4" :class="isEven(yearIndex * 12 + monthIndex) ? 'md:flex-row-reverse' : ''">
                  <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                    <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div :class="isEven(yearIndex * 12 + monthIndex) ? 'md:text-right' : ''">
                    <h3 class="text-lg font-bold text-gray-900 dark:text-white">
                      {{ monthData.month }} 月
                    </h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                      {{ monthData.count }} 篇文章
                    </p>
                  </div>
                </div>

                <div class="space-y-3">
                  <router-link
                    v-for="article in monthData.articles"
                    :key="article.id"
                    :to="`/article/${article.slug}`"
                    class="group flex items-start gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
                    :class="isEven(yearIndex * 12 + monthIndex) ? 'md:flex-row-reverse md:text-right' : ''"
                  >
                    <div class="flex-shrink-0 w-2 h-2 mt-2 rounded-full bg-primary/50 group-hover:bg-primary transition-colors"></div>
                    <div class="flex-1 min-w-0">
                      <h4 class="text-gray-900 dark:text-white font-medium group-hover:text-primary transition-colors truncate">
                        {{ article.title }}
                      </h4>
                      <div class="flex items-center gap-2 mt-1 text-sm text-gray-500 dark:text-gray-400" :class="isEven(yearIndex * 12 + monthIndex) ? 'md:justify-end' : ''">
                        <span>{{ formatDate(article.created_at) }}</span>
                        <span v-if="article.category" class="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs">
                          {{ article.category.name }}
                        </span>
                      </div>
                    </div>
                  </router-link>
                </div>
              </div>
            </div>
          </div>
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

const isEven = (index: number) => index % 2 === 0

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
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

<style scoped>
.glass-card {
  @apply bg-white/80 dark:bg-dark-100/80 backdrop-blur-xl border border-gray-200 dark:border-white/10 rounded-2xl;
}
</style>
