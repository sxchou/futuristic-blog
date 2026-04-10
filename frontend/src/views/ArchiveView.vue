<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import apiClient from '@/api/client'
import BlogSidebar from '@/components/common/BlogSidebar.vue'

interface Article {
  id: number
  title: string
  slug: string
  summary?: string
  created_at: string
  view_count?: number
  like_count?: number
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
const searchQuery = ref('')
const selectedYear = ref<number | null>(null)
const expandedMonths = ref<Set<string>>(new Set())

const totalArticles = computed(() => {
  return archiveData.value.reduce((total, year) => {
    return total + year.months.reduce((monthTotal, month) => monthTotal + month.count, 0)
  }, 0)
})

const availableYears = computed(() => {
  return archiveData.value.map(y => y.year).sort((a, b) => b - a)
})

const filteredData = computed(() => {
  let data = archiveData.value
  if (selectedYear.value) {
    data = data.filter(y => y.year === selectedYear.value)
  }
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    data = data.map(yearData => ({
      ...yearData,
      months: yearData.months.map(monthData => ({
        ...monthData,
        articles: monthData.articles.filter(article =>
          article.title.toLowerCase().includes(query) ||
          article.category?.name.toLowerCase().includes(query)
        )
      })).filter(m => m.articles.length > 0)
    })).filter(y => y.months.length > 0)
  }
  return data
})

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${month}-${day}`
}

const highlightText = (text: string, keyword: string): string => {
  if (!keyword || !text) return text
  const escapeRegExp = (str: string) => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const pattern = escapeRegExp(keyword)
  const regex = new RegExp(`(${pattern})`, 'gi')
  return text.replace(regex, '<mark class="search-highlight">$1</mark>')
}

const getMonthKey = (year: number, month: number) => `${year}-${month}`

const toggleMonth = (year: number, month: number) => {
  const key = getMonthKey(year, month)
  if (expandedMonths.value.has(key)) {
    expandedMonths.value.delete(key)
  } else {
    expandedMonths.value.add(key)
  }
}

const isMonthExpanded = (year: number, month: number) => {
  return expandedMonths.value.has(getMonthKey(year, month))
}

const expandAll = () => {
  const allKeys = new Set<string>()
  archiveData.value.forEach(yearData => {
    yearData.months.forEach(monthData => {
      allKeys.add(getMonthKey(yearData.year, monthData.month))
    })
  })
  expandedMonths.value = allKeys
}

const collapseAll = () => {
  expandedMonths.value = new Set()
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedYear.value = null
}

const fetchArchive = async () => {
  try {
    loading.value = true
    const response = await apiClient.get('/articles/archive/list')
    archiveData.value = response.data
    const firstYear = archiveData.value[0]
    if (firstYear) {
      firstYear.months.forEach(m => {
        expandedMonths.value.add(getMonthKey(firstYear.year, m.month))
      })
    }
  } catch (error) {
    console.error('Failed to fetch archive:', error)
  } finally {
    loading.value = false
  }
}

watch(selectedYear, () => {
  expandedMonths.value = new Set()
  if (selectedYear.value) {
    const yearData = archiveData.value.find(y => y.year === selectedYear.value)
    if (yearData) {
      yearData.months.forEach(m => {
        expandedMonths.value.add(getMonthKey(yearData.year, m.month))
      })
    }
  }
})

onMounted(() => {
  fetchArchive()
})
</script>

<template>
  <div class="flex flex-col lg:flex-row gap-8">
    <div class="flex-1 min-w-0">
      <div class="mb-6">
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2">
          文章归档
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          共 <span class="text-primary font-semibold">{{ totalArticles }}</span> 篇文章
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2 mb-6">
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索文章..."
            class="w-48 px-3 py-1.5 pl-8 text-sm bg-white dark:bg-dark-200 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none transition-colors"
          >
          <svg
            class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
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
        </div>
        <select
          v-model="selectedYear"
          class="px-3 py-1.5 text-sm bg-white dark:bg-dark-200 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none transition-colors"
        >
          <option :value="null">
            全部年份
          </option>
          <option
            v-for="year in availableYears"
            :key="year"
            :value="year"
          >
            {{ year }}年
          </option>
        </select>
        <div class="flex items-center gap-1">
          <button
            class="px-2 py-1.5 text-xs text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-primary/10 rounded transition-colors"
            title="展开全部"
            @click="expandAll"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            ><path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
            /></svg>
          </button>
          <button
            class="px-2 py-1.5 text-xs text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-primary/10 rounded transition-colors"
            title="收起全部"
            @click="collapseAll"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            ><path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25"
            /></svg>
          </button>
        </div>
      </div>

      <div
        v-if="loading"
        class="flex justify-center py-20"
      >
        <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>

      <div
        v-else-if="filteredData.length === 0"
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
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p class="text-gray-500 dark:text-gray-400 mb-3 text-sm">
          {{ searchQuery || selectedYear ? '没有找到匹配的文章' : '暂无文章' }}
        </p>
        <button
          v-if="searchQuery || selectedYear"
          class="text-primary hover:underline text-sm"
          @click="clearFilters"
        >
          清除筛选条件
        </button>
        <router-link
          v-else
          to="/"
          class="text-primary hover:underline text-sm"
        >
          返回首页
        </router-link>
      </div>

      <div
        v-else
        class="relative"
      >
        <div class="absolute left-4 md:left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary via-accent/50 to-transparent" />

        <div
          v-for="(yearData, yearIndex) in filteredData"
          :key="yearData.year"
          class="relative mb-8"
        >
          <div class="flex items-center gap-3 mb-4 pl-12 md:pl-20">
            <div class="absolute left-2 md:left-6 w-4 h-4 rounded-full bg-primary shadow-lg shadow-primary/30 ring-4 ring-white dark:ring-dark-100" />
            <div class="flex items-center gap-2">
              <span class="text-xl md:text-2xl font-bold text-gray-900 dark:text-white">{{ yearData.year }}</span>
              <span class="text-sm text-gray-500 dark:text-gray-400">
                ({{ yearData.months.reduce((sum, m) => sum + m.count, 0) }}篇)
              </span>
            </div>
          </div>

          <div class="space-y-2 pl-12 md:pl-20">
            <div
              v-for="monthData in yearData.months"
              :key="monthData.month"
              class="relative"
            >
              <div class="absolute left-[-32px] md:left-[-48px] top-3 w-2 h-2 rounded-full bg-gray-300 dark:bg-gray-600" />

              <div class="glass-card overflow-hidden">
                <button
                  class="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
                  @click="toggleMonth(yearData.year, monthData.month)"
                >
                  <div class="flex items-center gap-2">
                    <svg
                      class="w-4 h-4 text-gray-400 transition-transform"
                      :class="{ 'rotate-90': isMonthExpanded(yearData.year, monthData.month) }"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                    <span class="font-medium text-gray-900 dark:text-white text-sm">{{ monthData.month }}月</span>
                    <span class="text-xs text-gray-500 dark:text-gray-400">{{ monthData.count }}篇</span>
                  </div>
                </button>

                <div
                  v-show="isMonthExpanded(yearData.year, monthData.month)"
                  class="border-t border-gray-100 dark:border-white/5"
                >
                  <router-link
                    v-for="article in monthData.articles"
                    :key="article.id"
                    :to="`/article/${article.slug}`"
                    class="group flex items-center gap-3 px-4 py-2 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors border-b border-gray-50 dark:border-white/5 last:border-b-0"
                  >
                    <span class="text-xs text-gray-400 w-12 flex-shrink-0 font-mono">{{ formatDate(article.created_at) }}</span>
                    <span
                      v-if="article.category"
                      class="px-1.5 py-0.5 rounded text-[10px] font-medium flex-shrink-0"
                      :style="{ backgroundColor: `${article.category.color}20`, color: article.category.color }"
                      v-html="highlightText(article.category.name, searchQuery)"
                    />
                    <span
                      class="flex-1 text-sm text-gray-700 dark:text-gray-300 truncate group-hover:text-primary transition-colors"
                      v-html="highlightText(article.title, searchQuery)"
                    />
                    <div class="flex items-center gap-2 text-xs text-gray-400 flex-shrink-0">
                      <span
                        v-if="article.view_count"
                        class="flex items-center gap-0.5"
                      >
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
                      <svg
                        class="w-4 h-4 text-gray-300 dark:text-gray-600 group-hover:text-primary group-hover:translate-x-0.5 transition-all"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </div>
                  </router-link>
                </div>
              </div>
            </div>
          </div>

          <div
            v-if="yearIndex < filteredData.length - 1"
            class="h-4"
          />
        </div>
      </div>
    </div>

    <div class="lg:w-80 xl:w-84 flex-shrink-0">
      <div class="lg:sticky lg:top-20">
        <BlogSidebar />
      </div>
    </div>
  </div>
</template>
