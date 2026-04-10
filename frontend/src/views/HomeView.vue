<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBlogStore } from '@/stores'
import { dashboardApi, articleApi } from '@/api'
import BlogSidebar from '@/components/common/BlogSidebar.vue'
import Pagination from '@/components/common/Pagination.vue'
import { usePageSize } from '@/composables/usePageSize'
import { formatDateShort } from '@/utils/date'

const route = useRoute()
const router = useRouter()
const blogStore = useBlogStore()
const isLoading = ref(false)
const articlesSectionRef = ref<HTMLElement | null>(null)
let searchTimeout: ReturnType<typeof setTimeout> | null = null

const { pageSize } = usePageSize()

const stats = ref({
  articles: 0,
  views: 0,
  likes: 0,
  comments: 0
})

const featuredArticlesList = ref<any[]>([])
const currentSlide = ref(0)
let slideInterval: ReturnType<typeof setInterval> | null = null

const featuredArticles = computed(() => featuredArticlesList.value)
const currentFeatured = computed(() => featuredArticles.value[currentSlide.value])

const nextSlide = () => {
  if (featuredArticles.value.length > 0) {
    currentSlide.value = (currentSlide.value + 1) % featuredArticles.value.length
  }
}

const prevSlide = () => {
  if (featuredArticles.value.length > 0) {
    currentSlide.value = currentSlide.value === 0 ? featuredArticles.value.length - 1 : currentSlide.value - 1
  }
}

const fetchStats = async () => {
  try {
    const response = await dashboardApi.getPublicStats()
    stats.value = {
      articles: response.data.total_articles,
      views: response.data.total_views,
      likes: response.data.total_likes,
      comments: response.data.total_comments
    }
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

const fetchFeaturedArticles = async () => {
  try {
    const response = await articleApi.getArticles({ is_featured: true, page: 1, page_size: 5 })
    featuredArticlesList.value = response.items
  } catch (error) {
    console.error('Failed to fetch featured articles:', error)
  }
}

const formatDate = (date: string) => formatDateShort(date)

const scrollToArticlesSection = () => {
  requestAnimationFrame(() => {
    if (articlesSectionRef.value) {
      const element = articlesSectionRef.value
      const offset = 85
      const elementPosition = element.getBoundingClientRect().top
      const offsetPosition = elementPosition + window.pageYOffset - offset
      window.scrollTo({ top: offsetPosition, behavior: 'smooth' })
    }
  })
}

const debouncedFetch = (page: number, updateUrl: boolean = true, shouldScroll: boolean = false) => {
  if (searchTimeout) clearTimeout(searchTimeout)
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
      if (shouldScroll) scrollToArticlesSection()
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
  
  await Promise.all([
    blogStore.fetchArticles({ page: pageFromUrl, page_size: pageSize.value }),
    blogStore.fetchCategories(),
    blogStore.fetchTags(),
    fetchStats(),
    fetchFeaturedArticles()
  ])
  
  if (featuredArticles.value.length > 1) {
    slideInterval = setInterval(nextSlide, 6000)
  }
})

onUnmounted(() => {
  if (searchTimeout) clearTimeout(searchTimeout)
  if (slideInterval) clearInterval(slideInterval)
})

const handlePageChange = (page: number) => {
  debouncedFetch(page, true, true)
}
</script>

<template>
  <div>
    <section v-if="featuredArticles.length > 0" class="mb-8">
      <div class="glass-card overflow-hidden">
        <router-link
          :to="`/article/${currentFeatured?.slug}`"
          class="block group"
        >
          <div class="relative">
            <div v-if="currentFeatured?.cover_image" class="relative h-64 sm:h-72 md:h-80 overflow-hidden">
              <img
                :src="currentFeatured.cover_image"
                :alt="currentFeatured.title"
                class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
            </div>
            <div v-else class="relative h-48 sm:h-56 md:h-64 bg-gradient-to-br from-primary/20 via-accent/10 to-primary/5">
              <div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
            </div>
            
            <div class="absolute bottom-0 left-0 right-0 p-5 md:p-8">
              <div class="flex items-center gap-2 mb-3">
                <span class="px-2.5 py-0.5 bg-gradient-to-r from-primary to-accent text-white text-xs font-medium rounded-full">
                  精选推荐
                </span>
                <span v-if="currentFeatured?.category" class="px-2.5 py-0.5 bg-white/20 backdrop-blur-sm text-white text-xs rounded-full">
                  {{ currentFeatured.category.name }}
                </span>
              </div>
              <h2 class="text-xl md:text-2xl lg:text-3xl font-bold text-white mb-2 group-hover:text-primary transition-colors line-clamp-2">
                {{ currentFeatured?.title }}
              </h2>
              <p v-if="currentFeatured?.summary" class="text-white/70 text-sm md:text-base line-clamp-2 max-w-2xl mb-3">
                {{ currentFeatured.summary }}
              </p>
              <div class="flex items-center gap-4 text-white/50 text-sm">
                <span>{{ formatDate(currentFeatured?.created_at) }}</span>
                <span class="flex items-center gap-1">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  {{ currentFeatured?.view_count }}
                </span>
              </div>
            </div>
          </div>
        </router-link>
        
        <div v-if="featuredArticles.length > 1" class="flex items-center justify-between px-5 md:px-8 py-3 border-t border-gray-100 dark:border-white/5">
          <div class="flex gap-1.5">
            <button
              v-for="(_, index) in featuredArticles"
              :key="index"
              @click="currentSlide = index"
              class="h-1.5 rounded-full transition-all duration-300"
              :class="currentSlide === index ? 'bg-primary w-6' : 'bg-gray-300 dark:bg-gray-600 w-1.5 hover:bg-primary/50'"
            />
          </div>
          <div class="flex gap-1">
            <button @click="prevSlide" class="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-dark-300 text-gray-400 hover:text-primary transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
            </button>
            <button @click="nextSlide" class="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-dark-300 text-gray-400 hover:text-primary transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
            </button>
          </div>
        </div>
      </div>
    </section>

    <div class="flex flex-col lg:flex-row gap-8">
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
            </svg>
            最新文章
          </h2>
          <span class="text-sm text-gray-400">共 {{ blogStore.pagination.total }} 篇</span>
        </div>

        <div v-if="isLoading && blogStore.articles.length === 0" class="flex justify-center py-16">
          <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        </div>

        <div v-else ref="articlesSectionRef" class="space-y-4">
          <article
            v-for="article in blogStore.articles"
            :key="article.id"
            class="article-card group"
          >
            <router-link :to="`/article/${article.slug}`" class="flex flex-col sm:flex-row gap-4">
              <div v-if="article.cover_image" class="sm:w-48 md:w-56 flex-shrink-0">
                <div class="relative overflow-hidden rounded-xl aspect-video sm:aspect-square sm:h-full">
                  <img
                    :src="article.cover_image"
                    :alt="article.title"
                    class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                    loading="lazy"
                  />
                  <div class="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
                </div>
              </div>

              <div class="flex-1 min-w-0 flex flex-col">
                <div class="flex items-center gap-2 mb-2">
                  <span v-if="article.is_pinned" class="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-amber-500/10 text-amber-600 text-[10px] font-medium rounded">
                    <svg class="w-2.5 h-2.5" viewBox="0 0 24 24" fill="currentColor"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>
                    置顶
                  </span>
                  <span v-if="article.is_featured" class="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-primary/10 text-primary text-[10px] font-medium rounded">
                    <svg class="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                    精选
                  </span>
                  <span v-if="article.category" class="inline-flex items-center gap-1 text-xs" :style="{ color: article.category.color }">
                    <span class="w-1.5 h-1.5 rounded-full" :style="{ backgroundColor: article.category.color }" />
                    {{ article.category.name }}
                  </span>
                </div>

                <h3 class="article-card-title">{{ article.title }}</h3>
                <p v-if="article.summary" class="article-card-excerpt">{{ article.summary }}</p>

                <div class="flex flex-wrap gap-1 mb-3">
                  <span
                    v-for="tag in article.tags.slice(0, 3)"
                    :key="tag.id"
                    class="tag-badge text-[10px]"
                    :style="{ 
                      color: tag.color, 
                      backgroundColor: tag.color + '10',
                      borderColor: tag.color + '30'
                    }"
                  >
                    {{ tag.name }}
                  </span>
                </div>

                <div class="article-meta mt-auto pt-3 border-t border-gray-100 dark:border-white/5">
                  <span class="article-meta-item">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {{ formatDate(article.created_at) }}
                  </span>
                  <span class="article-meta-item">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    {{ article.view_count }}
                  </span>
                  <span class="article-meta-item">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                    {{ article.like_count }}
                  </span>
                  <span class="article-meta-item">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    {{ article.comment_count || 0 }}
                  </span>
                </div>
              </div>
            </router-link>
          </article>
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

      <div class="lg:w-80 xl:w-84 flex-shrink-0">
        <div class="lg:sticky lg:top-20">
          <BlogSidebar />
        </div>
      </div>
    </div>
  </div>
</template>
