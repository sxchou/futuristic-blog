<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBlogStore, useAuthStore, useUserInteractionStore } from '@/stores'
import BlogSidebar from '@/components/common/BlogSidebar.vue'
import LeftSidebar from '@/components/common/LeftSidebar.vue'
import Pagination from '@/components/common/Pagination.vue'
import { usePageSize } from '@/composables/usePageSize'
import { getMediaUrl } from '@/utils/media'

const route = useRoute()
const router = useRouter()
const blogStore = useBlogStore()
const authStore = useAuthStore()
const userInteractionStore = useUserInteractionStore()

const searchQuery = ref('')
const isSearching = ref(false)
const searchResultsRef = ref<HTMLElement | null>(null)
let currentSearchKeyword = ''

const { pageSize } = usePageSize()

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

const scrollToResults = () => {
  requestAnimationFrame(() => {
    if (searchResultsRef.value) {
      const element = searchResultsRef.value
      const offset = 85
      const elementPosition = element.getBoundingClientRect().top
      const offsetPosition = elementPosition + window.pageYOffset - offset
      window.scrollTo({ top: offsetPosition, behavior: 'smooth' })
    }
  })
}

const applyInteractionState = (articles: any[]) => {
  articles.forEach(article => {
    if (userInteractionStore.isInitialized) {
      article.is_liked = userInteractionStore.isLiked(article.id)
      article.is_bookmarked = userInteractionStore.isBookmarked(article.id)
    }
  })
}

const performSearch = async (page: number = 1, updateUrl: boolean = true, shouldScroll: boolean = false) => {
  const keyword = currentSearchKeyword || searchQuery.value.trim()
  if (!keyword) return
  
  isSearching.value = true
  try {
    await blogStore.fetchArticles({
      search: keyword,
      page: page,
      page_size: pageSize.value
    })
    applyInteractionState(blogStore.articles)
    if (updateUrl) {
      const newQuery: Record<string, string> = { q: keyword }
      if (page !== 1) newQuery.page = page.toString()
      router.replace({ path: '/search', query: newQuery })
    }
    if (shouldScroll) scrollToResults()
  } finally {
    isSearching.value = false
  }
}

watch(pageSize, async (newSize, oldSize) => {
  if (newSize !== oldSize && currentSearchKeyword) {
    const currentPage = parseInt(route.query.page as string) || 1
    await performSearch(currentPage, false, false)
    const totalPages = blogStore.pagination.totalPages
    if (currentPage > totalPages && totalPages > 0) {
      await performSearch(totalPages, true, false)
    }
  }
})

watch(() => route.query.q, (newQuery) => {
  if (newQuery) {
    const keyword = newQuery as string
    searchQuery.value = keyword
    currentSearchKeyword = keyword
    const pageFromUrl = parseInt(route.query.page as string) || 1
    performSearch(pageFromUrl, false, false)
  }
}, { immediate: true })

onMounted(async () => {
  if (authStore.isAuthenticated) {
    await userInteractionStore.initialize()
  }
  const query = route.query.q as string
  if (query) {
    searchQuery.value = query
    currentSearchKeyword = query
  }
})

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    currentSearchKeyword = searchQuery.value.trim()
    router.push({ path: '/search', query: { q: searchQuery.value } })
  }
}

const handlePageChange = (page: number) => {
  performSearch(page, true, true)
}

const formatDate = (date: string) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
</script>

<template>
  <div class="flex flex-col lg:flex-row gap-6">
    <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
      <div class="lg:sticky lg:top-20">
        <LeftSidebar />
      </div>
    </div>
    
    <main class="flex-1 min-w-0 lg:order-2">
      <div class="mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2">
          搜索文章
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          输入关键词搜索文章
        </p>
      </div>

      <form class="mb-8" @submit.prevent="handleSearch">
        <div class="relative">
          <input id="input-search-view-query"
            v-model="searchQuery"
            type="text"
            name="search-query"
            placeholder="输入关键词搜索（支持 * 和 ? 通配符）..."
            class="w-full px-4 py-3.5 pl-11 bg-gray-50 dark:bg-dark-300 border border-gray-200 dark:border-white/10 rounded-xl text-gray-800 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all"
            @keyup.enter="handleSearch"
          >
          <svg
            class="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
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
          <button
            class="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-600 transition-colors"
            @click="handleSearch"
          >
            搜索
          </button>
        </div>
      </form>

      <div
        v-if="isSearching"
        class="flex justify-center py-20"
      >
        <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>

      <div
        v-else-if="route.query.q && blogStore.articles.length === 0"
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
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-1">
          未找到相关结果
        </h2>
        <p class="text-gray-500 dark:text-gray-400 text-sm">
          尝试使用不同的关键词搜索
        </p>
      </div>

      <div
        v-else-if="blogStore.articles.length > 0"
        ref="searchResultsRef"
      >
        <div class="mb-6">
          <p class="text-sm text-gray-400">
            找到 <span class="text-primary font-semibold">{{ blogStore.pagination.total }}</span> 篇相关文章
          </p>
        </div>

        <div class="space-y-4">
          <article
            v-for="article in blogStore.articles"
            :key="article.id"
            class="article-card group relative overflow-hidden"
          >
            <router-link
              :to="{ path: `/article/${article.slug}`, query: currentSearchKeyword ? { highlight: currentSearchKeyword } : {} }"
              class="block p-2"
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
                    <template v-if="article.highlighted_title">
                      <span v-html="article.highlighted_title" />
                    </template>
                    <template v-else>
                      {{ article.title }}
                    </template>
                  </h3>
                  <p
                    v-if="article.summary"
                    class="text-sm leading-relaxed mb-2 line-clamp-2 text-gray-500 dark:text-gray-400"
                  >
                    <template v-if="article.highlighted_summary">
                      <span v-html="article.highlighted_summary" />
                    </template>
                    <template v-else>
                      {{ article.summary }}
                    </template>
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
      </div>

      <div
        v-else
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
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-1">
          开始搜索
        </h2>
        <p class="text-gray-500 dark:text-gray-400 text-sm">
          输入关键词搜索文章、标签、分类
        </p>
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
