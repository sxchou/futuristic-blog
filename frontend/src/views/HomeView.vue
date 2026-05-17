<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBlogStore, useAuthStore, useUserInteractionStore, useInitStore } from '@/stores'
import { prefetchAllCommonPages, prefetchArticleComponent } from '@/router'
import { prefetchAllData, dataPrefetch } from '@/utils/prefetch'
import Pagination from '@/components/common/Pagination.vue'
import { usePageSize } from '@/composables/usePageSize'
import { formatDateShort } from '@/utils/date'
import { getMediaUrl } from '@/utils/media'

const BlogSidebar = defineAsyncComponent(() => import('@/components/common/BlogSidebar.vue'))
const LeftSidebar = defineAsyncComponent(() => import('@/components/common/LeftSidebar.vue'))

const route = useRoute()
const router = useRouter()
const blogStore = useBlogStore()
const authStore = useAuthStore()
const userInteractionStore = useUserInteractionStore()
const initStore = useInitStore()
const isLoading = ref(false)
const articlesSectionRef = ref<HTMLElement | null>(null)
let searchTimeout: ReturnType<typeof setTimeout> | null = null

const activeTooltip = ref<{ articleId: number; action: string } | null>(null)

const showTooltip = (articleId: number, action: string) => {
  activeTooltip.value = { articleId, action }
}

const hideTooltip = () => {
  activeTooltip.value = null
}

const isTooltipVisible = (articleId: number, action: string) => {
  return activeTooltip.value?.articleId === articleId && activeTooltip.value?.action === action
}

const { pageSize } = usePageSize()

const featuredArticlesList = computed(() => blogStore.featuredArticles.slice(0, 5))

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

const pauseAutoPlay = () => {
  if (slideInterval) {
    clearInterval(slideInterval)
    slideInterval = null
  }
}

const resumeAutoPlay = () => {
  if (featuredArticles.value.length > 1 && !slideInterval) {
    slideInterval = setInterval(nextSlide, 6000)
  }
}

const touchStartX = ref(0)
const touchEndX = ref(0)
const isSwiping = ref(false)
const hasSwiped = ref(false)
const swipeEndTime = ref(0)
const isTouching = ref(false)

const handleTouchStart = (e: TouchEvent) => {
  touchStartX.value = e.touches[0].clientX
  isSwiping.value = true
  hasSwiped.value = false
  isTouching.value = true
  pauseAutoPlay()
}

const handleTouchMove = (e: TouchEvent) => {
  if (!isSwiping.value) return
  touchEndX.value = e.touches[0].clientX
}

const handleTouchEnd = () => {
  if (!isSwiping.value) return
  isSwiping.value = false
  isTouching.value = false
  
  const swipeThreshold = 50
  const diff = touchStartX.value - touchEndX.value
  
  if (Math.abs(diff) > swipeThreshold) {
    hasSwiped.value = true
    swipeEndTime.value = Date.now()
    if (diff > 0) {
      nextSlide()
    } else {
      prevSlide()
    }
  }
  
  touchStartX.value = 0
  touchEndX.value = 0
  
  setTimeout(() => {
    resumeAutoPlay()
  }, 1000)
}

const handleCarouselClick = (e: MouseEvent) => {
  if (hasSwiped.value || isTouching.value || Date.now() - swipeEndTime.value < 500) {
    e.preventDefault()
    e.stopPropagation()
    return
  }
  hasSwiped.value = false
}

const formatDate = (date: string) => formatDateShort(date)

const handleLike = async (e: Event, article: any) => {
  e.preventDefault()
  e.stopPropagation()
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  if (article._liking) return
  article._liking = true

  const prevLiked = article.is_liked
  const prevCount = article.like_count
  article.is_liked = !prevLiked
  article.like_count = prevLiked ? prevCount - 1 : prevCount + 1

  try {
    const result = await userInteractionStore.toggleLike(article.id)
    if (result) {
      article.is_liked = result.is_liked
      article.like_count = result.like_count
    } else {
      article.is_liked = prevLiked
      article.like_count = prevCount
    }
  } catch (error) {
    console.error('Failed to toggle like:', error)
    article.is_liked = prevLiked
    article.like_count = prevCount
  } finally {
    article._liking = false
  }
}

const handleBookmark = async (e: Event, article: any) => {
  e.preventDefault()
  e.stopPropagation()
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  if (article._bookmarking) return
  article._bookmarking = true

  const prevBookmarked = article.is_bookmarked
  const prevBookmarkCount = article.bookmark_count || 0
  article.is_bookmarked = !prevBookmarked
  article.bookmark_count = prevBookmarked ? prevBookmarkCount - 1 : prevBookmarkCount + 1

  try {
    const result = await userInteractionStore.toggleBookmark(article.id)
    if (result) {
      article.is_bookmarked = result.is_bookmarked
      article.bookmark_count = result.bookmark_count
    } else {
      article.is_bookmarked = prevBookmarked
      article.bookmark_count = prevBookmarkCount
    }
  } catch (error) {
    console.error('Failed to toggle bookmark:', error)
    article.is_bookmarked = prevBookmarked
    article.bookmark_count = prevBookmarkCount
  } finally {
    article._bookmarking = false
  }
}

const goToComments = (e: Event, slug: string) => {
  e.preventDefault()
  e.stopPropagation()
  router.push(`/article/${slug}#comments`)
}

const articleHoverPrefetchCache = new Set<string>()

const handleArticleHover = (slug: string) => {
  prefetchArticleComponent()
  if (articleHoverPrefetchCache.has(slug)) return
  articleHoverPrefetchCache.add(slug)
  import('@/api').then(({ articleApi }) => {
    articleApi.getArticle(slug).then(data => {
      dataPrefetch.set(`article-${slug}`, data)
    }).catch(() => { /* prefetch failure is silent */ })
  }).catch(() => { /* prefetch failure is silent */ })
}

const applyInteractionState = (articles: any[]) => {
  articles.forEach(article => {
    if (userInteractionStore.isInitialized) {
      article.is_liked = userInteractionStore.isLiked(article.id)
      article.is_bookmarked = userInteractionStore.isBookmarked(article.id)
    }
  })
}

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
      applyInteractionState(blogStore.articles)
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
    applyInteractionState(blogStore.articles)
    const totalPages = blogStore.pagination.totalPages
    if (currentPage > totalPages && totalPages > 0) {
      const newPage = totalPages
      await blogStore.fetchArticles({ page: newPage, page_size: newSize })
      applyInteractionState(blogStore.articles)
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
    applyInteractionState(blogStore.articles)
  }
})

onMounted(async () => {
  const pageFromUrl = parseInt(route.query.page as string) || 1
  
  if (!initStore.isCoreInitialized) {
    await initStore.initializeCore()
  }
  
  const hasFilter = blogStore.currentFilter.category_id || 
                    blogStore.currentFilter.tag_id || 
                    blogStore.currentFilter.search
  
  const needsFetch = hasFilter || 
                     blogStore.articles.length === 0 ||
                     blogStore.pagination.page !== pageFromUrl || 
                     blogStore.pagination.pageSize !== pageSize.value
  
  if (needsFetch) {
    await blogStore.fetchArticles({ page: pageFromUrl, page_size: pageSize.value })
  }
  
  applyInteractionState(blogStore.articles)
  
  if (featuredArticles.value.length > 1) {
    slideInterval = setInterval(nextSlide, 6000)
  }

  prefetchAllCommonPages()
  prefetchAllData()
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
  <div
    class="flex flex-col lg:flex-row gap-6"
  >
      <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
        <div class="lg:sticky lg:top-20">
          <LeftSidebar />
        </div>
      </div>
      
      <main class="flex-1 min-w-0 lg:order-2">
        <section
          v-if="featuredArticles.length > 0"
          class="mb-6"
        >
          <div 
            class="glass-card overflow-hidden select-none"
            @touchstart="handleTouchStart"
            @touchmove="handleTouchMove"
            @touchend="handleTouchEnd"
            @mouseenter="pauseAutoPlay"
            @mouseleave="resumeAutoPlay"
          >
            <router-link
              :to="`/article/${currentFeatured?.slug}`"
              class="block group"
              @click="handleCarouselClick"
              @mouseenter="handleArticleHover(currentFeatured?.slug || '')"
            >
              <Transition
                name="carousel-fade"
                mode="out-in"
              >
                <div
                  :key="currentSlide"
                  class="relative"
                >
                  <div
                    v-if="currentFeatured?.cover_image"
                    class="relative h-48 sm:h-56 md:h-64 lg:h-72 xl:h-80 overflow-hidden"
                  >
                      <img
                        :src="getMediaUrl(currentFeatured.cover_image)"
                        :alt="currentFeatured.title"
                        class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105 rounded-none"
                        loading="eager"
                        decoding="async"
                      >
                      <div class="absolute inset-0 bg-gradient-to-r from-black/70 via-black/40 to-transparent dark:from-black/70 dark:via-black/40 dark:to-transparent" />
                      <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent dark:from-black/60 dark:to-transparent" />
                    </div>
                    <div
                      v-else
                      class="relative h-48 sm:h-56 md:h-64 lg:h-72 xl:h-80 overflow-hidden"
                    >
                      <div class="absolute inset-0 bg-gradient-to-br from-primary/10 via-accent/5 to-primary/10 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 transition-colors duration-500" />
                      <div class="absolute inset-0 bg-gradient-to-r from-black/30 via-transparent to-black/20 dark:from-black/50 dark:via-black/30 dark:to-black/40 transition-colors duration-500" />
                      <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent dark:from-black/60 dark:to-transparent transition-colors duration-500" />
                    </div>
                    
                    <div class="absolute bottom-0 left-0 right-0 px-2 py-4">
                      <div class="flex items-center gap-1 mb-2">
                        <span class="px-1.5 py-0.5 bg-primary text-white text-xs font-medium rounded-full shadow-lg">
                          精选推荐
                        </span>
                        <span
                          v-if="currentFeatured?.category"
                          class="px-1.5 py-0.5 bg-white/20 dark:bg-white/25 backdrop-blur-sm text-white text-xs rounded-full shadow-sm"
                        >
                          {{ currentFeatured.category.name }}
                        </span>
                      </div>
                      <h2 class="text-lg font-bold text-white group-hover:text-primary transition-colors overflow-hidden text-ellipsis whitespace-nowrap drop-shadow-lg mb-1">
                        {{ currentFeatured?.title }}
                      </h2>
                      <p
                        v-if="currentFeatured?.summary"
                        class="text-white/70 dark:text-white/75 text-sm truncate max-w-xl drop-shadow-md mb-2"
                      >
                        {{ currentFeatured.summary }}
                      </p>
                      <div class="flex items-center gap-2 text-white/50 dark:text-white/60 text-xs">
                        <span class="drop-shadow-sm">{{ formatDate(currentFeatured?.created_at) }}</span>
                        <span class="flex items-center gap-0.5 drop-shadow-sm">
                          <svg
                            class="w-3 h-3"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              stroke-width="2"
                              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              stroke-width="2"
                              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                            />
                          </svg>
                          {{ currentFeatured?.view_count }}
                        </span>
                      </div>
                    </div>
                  </div>
                </Transition>
            </router-link>
            
            <div
              v-if="featuredArticles.length > 1"
              class="flex items-center justify-between px-2 py-1 border-t border-gray-100 dark:border-white/5"
            >
              <div class="flex gap-1">
                <button
                  v-for="(_, index) in featuredArticles"
                  :key="index"
                  class="h-1 rounded-full transition-all duration-300"
                  :class="currentSlide === index ? 'bg-primary w-3' : 'bg-gray-300 dark:bg-gray-600 w-1 hover:bg-primary/50'"
                  @click="currentSlide = index"
                />
              </div>
              <div class="flex gap-0.5">
                <button
                  class="p-0.5 rounded hover:bg-gray-100 dark:hover:bg-dark-300 text-gray-400 hover:text-primary transition-colors"
                  @click="prevSlide"
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
                    d="M15 19l-7-7 7-7"
                  /></svg>
                </button>
                <button
                  class="p-0.5 rounded hover:bg-gray-100 dark:hover:bg-dark-300 text-gray-400 hover:text-primary transition-colors"
                  @click="nextSlide"
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
                    d="M9 5l7 7-7 7"
                  /></svg>
                </button>
              </div>
            </div>
          </div>
        </section>

        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <svg
              class="w-5 h-5 text-primary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"
              />
            </svg>
            最新文章
          </h2>
          <span class="text-sm text-gray-400">共 {{ blogStore.pagination.total }} 篇</span>
        </div>

        <div
          v-if="isLoading && blogStore.articles.length === 0"
          class="flex justify-center py-16"
        >
          <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        </div>

        <div
          v-else
          ref="articlesSectionRef"
          class="space-y-4"
        >
          <article
            v-for="article in blogStore.articles"
            :key="article.id"
            class="article-card group relative overflow-hidden"
          >
            <router-link
              :to="`/article/${article.slug}`"
              class="block p-2"
              @mouseenter="handleArticleHover(article.slug)"
            >
              <div 
                class="flex flex-col gap-3 sm:grid sm:grid-cols-[auto_1fr] sm:gap-4"
              >
                <div
                  v-if="article.cover_image"
                  class="relative w-full h-52 sm:w-56 md:w-64 sm:h-full overflow-hidden rounded-t-lg sm:rounded-lg"
                >
                  <img
                    :src="getMediaUrl(article.cover_image)"
                    :alt="article.title"
                    class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110 rounded-t-lg sm:rounded-lg"
                    loading="lazy"
                  >
                </div>

                <div 
                  class="relative flex-1 min-w-0 flex flex-col min-h-0"
                >
                  <div class="flex items-center gap-2 mb-2">
                    <span
                      v-if="article.is_pinned"
                      class="inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium rounded bg-amber-500/10 text-amber-600"
                    >
                      <svg
                        class="w-2.5 h-2.5"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                      ><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z" /></svg>
                      置顶
                    </span>
                    <span
                      v-if="article.is_featured"
                      class="inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium rounded bg-primary/10 text-primary"
                    >
                      <svg
                        class="w-2.5 h-2.5"
                        fill="currentColor"
                        viewBox="0 0 24 24"
                      ><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>
                      精选
                    </span>
                    <span
                      v-if="article.category"
                      class="inline-flex items-center gap-1 text-xs"
                      :style="{ color: article.category.color }"
                    >
                      <span
                        class="w-1.5 h-1.5 rounded-full"
                        :style="{ backgroundColor: article.category.color }"
                      />
                      {{ article.category.name }}
                    </span>
                  </div>

                  <h3 class="text-base font-bold leading-snug mb-2 group-hover:text-primary transition-colors line-clamp-2 text-gray-900 dark:text-white">
                    {{ article.title }}
                  </h3>
                  <p
                    v-if="article.summary"
                    class="text-sm leading-relaxed mb-2 line-clamp-2 text-gray-500 dark:text-gray-400"
                  >
                    {{ article.summary }}
                  </p>

                  <div class="flex flex-wrap gap-1 mb-2">
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

                  <div class="article-meta mt-auto pt-2 border-t border-gray-100 dark:border-white/5">
                    <span
                      v-if="article.author || article.author_name"
                      class="article-meta-item text-inherit w-full"
                    >
                      <svg
                        class="w-3.5 h-3.5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                        />
                      </svg>
                      <span class="truncate">{{ article.author?.username || article.author_name || '已注销用户' }}</span>
                    </span>
                  </div>
                  <div class="article-meta pt-2">
                    <span class="article-meta-item text-inherit">
                      <svg
                        class="w-3.5 h-3.5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                      </svg>
                      {{ formatDate(article.created_at) }}
                    </span>
                    <span 
                      class="article-meta-item relative text-inherit"
                      @mouseenter="showTooltip(article.id, 'view')"
                      @mouseleave="hideTooltip"
                    >
                      <svg
                        class="w-3.5 h-3.5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                        />
                      </svg>
                      {{ article.view_count }}
                      <span
                        v-if="isTooltipVisible(article.id, 'view')"
                        class="action-tooltip"
                      >
                        浏览量
                      </span>
                    </span>
                    <button
                      class="article-meta-item article-action-btn relative text-inherit"
                      @click="handleLike($event, article)"
                      @mouseenter="showTooltip(article.id, 'like')"
                      @mouseleave="hideTooltip"
                    >
                      <svg
                        class="w-3.5 h-3.5"
                        :fill="article.is_liked ? 'currentColor' : 'none'"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                        />
                      </svg>
                      {{ article.like_count }}
                      <span
                        v-if="isTooltipVisible(article.id, 'like')"
                        class="action-tooltip"
                      >
                        {{ article.is_liked ? '取消点赞' : '点赞' }}
                      </span>
                    </button>
                    <button
                      class="article-meta-item article-action-btn relative text-inherit"
                      @click="goToComments($event, article.slug)"
                      @mouseenter="showTooltip(article.id, 'comment')"
                      @mouseleave="hideTooltip"
                    >
                      <svg
                        class="w-3.5 h-3.5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      </svg>
                      {{ article.comment_count || 0 }}
                      <span
                        v-if="isTooltipVisible(article.id, 'comment')"
                        class="action-tooltip"
                      >
                        评论
                      </span>
                    </button>
                    <button
                      :class="[
                        'article-meta-item article-action-btn relative text-inherit',
                        { 'text-amber-500': article.is_bookmarked }
                      ]"
                      @click="handleBookmark($event, article)"
                      @mouseenter="showTooltip(article.id, 'bookmark')"
                      @mouseleave="hideTooltip"
                    >
                      <svg
                        class="w-3.5 h-3.5"
                        :fill="article.is_bookmarked ? 'currentColor' : 'none'"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
                        />
                      </svg>
                      {{ article.bookmark_count || 0 }}
                      <span
                        v-if="isTooltipVisible(article.id, 'bookmark')"
                        class="action-tooltip"
                      >
                        {{ article.is_bookmarked ? '取消收藏' : '收藏' }}
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            </router-link>
          </article>
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
      </main>

      <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
        <div class="lg:sticky lg:top-20">
          <BlogSidebar />
        </div>
      </div>

      <aside class="lg:hidden mt-8 space-y-4" aria-label="侧边栏内容">
        <LeftSidebar />
        <BlogSidebar />
      </aside>
    </div>
</template>

<style scoped>
.carousel-fade-enter-active,
.carousel-fade-leave-active {
  transition: opacity 0.4s ease;
}

.carousel-fade-enter-from,
.carousel-fade-leave-to {
  opacity: 0;
}

.article-card {
  padding: 0 !important;
  display: block !important;
}

.action-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 8px;
  background: #ffffff;
  color: #1a1a2e;
  font-size: 12px;
  font-weight: normal;
  border-radius: 4px;
  white-space: nowrap;
  pointer-events: none;
  z-index: 9999;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  animation: tooltip-fade-in 0.15s ease;
}

.dark .action-tooltip {
  background: #0f0f1a;
  color: #f1f5f9;
}

@keyframes tooltip-fade-in {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}
</style>
