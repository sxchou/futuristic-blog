<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBlogStore, useAuthStore, useUserInteractionStore } from '@/stores'
import BlogSidebar from '@/components/common/BlogSidebar.vue'
import LeftSidebar from '@/components/common/LeftSidebar.vue'
import Pagination from '@/components/common/Pagination.vue'
import { usePageSize } from '@/composables/usePageSize'
import { formatDateShort } from '@/utils/date'
import { getMediaUrl } from '@/utils/media'

const route = useRoute()
const router = useRouter()
const blogStore = useBlogStore()
const authStore = useAuthStore()
const userInteractionStore = useUserInteractionStore()
const loading = ref(true)
const fetchError = ref(false)
const notFound = ref(false)
const articlesRef = ref<HTMLElement | null>(null)
/** 视图级请求令牌：防止被取消的旧请求复位加载状态或更新 URL */
let fetchToken = 0
let slugFetchTimeout: ReturnType<typeof setTimeout> | null = null

const { pageSize } = usePageSize()

const formatDate = (date: string) => formatDateShort(date)

const scrollToArticles = () => {
  requestAnimationFrame(() => {
    if (articlesRef.value) {
      const element = articlesRef.value
      const offset = 85
      const elementPosition = element.getBoundingClientRect().top
      const offsetPosition = elementPosition + window.pageYOffset - offset
      window.scrollTo({ top: offsetPosition, behavior: 'smooth' })
    }
  })
}

const fetchArticles = async (page: number = 1, updateUrl: boolean = true, shouldScroll: boolean = false) => {
  const token = ++fetchToken
  const slug = route.params.slug as string
  loading.value = true
  fetchError.value = false

  let tag = blogStore.getTagBySlug(slug)
  if (!tag) {
    // 标签列表可能尚未加载完成，加载后再查找一次
    await blogStore.fetchTags()
    tag = blogStore.getTagBySlug(slug)
  }

  if (!tag) {
    if (token !== fetchToken) return
    notFound.value = true
    loading.value = false
    return
  }
  notFound.value = false

  try {
    await blogStore.fetchArticles({
      tag_id: tag.id,
      page: page,
      page_size: pageSize.value
    })
    // 旧请求已被更新的操作取代，丢弃后续处理
    if (token !== fetchToken) return
    fetchError.value = !!blogStore.error
    applyInteractionState(blogStore.articles)
    if (updateUrl && !fetchError.value) {
      if (page !== 1) {
        router.replace({ query: { ...route.query, page: page.toString() } })
      } else if (route.query.page) {
        const newQuery = { ...route.query }
        delete newQuery.page
        router.replace({ query: newQuery })
      }
    }
    if (shouldScroll && !fetchError.value) scrollToArticles()
  } finally {
    if (token === fetchToken) {
      loading.value = false
    }
  }
}

watch(pageSize, async (newSize, oldSize) => {
  if (newSize !== oldSize) {
    const currentPage = parseInt(route.query.page as string) || 1
    await fetchArticles(currentPage, false, false)
    const totalPages = blogStore.pagination.totalPages
    if (currentPage > totalPages && totalPages > 0) {
      await fetchArticles(totalPages, true, false)
    }
  }
})

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

const applyInteractionState = (articles: any[]) => {
  articles.forEach(article => {
    if (userInteractionStore.isInitialized) {
      article.is_liked = userInteractionStore.isLiked(article.id)
      article.is_bookmarked = userInteractionStore.isBookmarked(article.id)
    }
  })
}

onMounted(async () => {
  const pageFromUrl = parseInt(route.query.page as string) || 1
  await blogStore.fetchTags()
  if (authStore.isAuthenticated) {
    await userInteractionStore.initialize()
  }
  await fetchArticles(pageFromUrl, false, false)
})

onUnmounted(() => {
  if (slugFetchTimeout) clearTimeout(slugFetchTimeout)
})

// 切换标签时防抖合并请求；store 层会取消未完成的旧请求
watch(() => route.params.slug, (newSlug, oldSlug) => {
  if (!newSlug || newSlug === oldSlug) return
  loading.value = true
  fetchError.value = false
  notFound.value = false
  if (slugFetchTimeout) clearTimeout(slugFetchTimeout)
  slugFetchTimeout = setTimeout(() => {
    const pageFromUrl = parseInt(route.query.page as string) || 1
    fetchArticles(pageFromUrl, false, false)
  }, 80)
})

const currentTag = () => {
  const slug = route.params.slug as string
  return blogStore.getTagBySlug(slug)
}

const handlePageChange = async (page: number) => {
  await fetchArticles(page, true, true)
}

const retryFetch = () => {
  const pageFromUrl = parseInt(route.query.page as string) || 1
  fetchArticles(pageFromUrl, false, false)
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
        <div class="flex items-center gap-2 mb-2">
          <router-link
            to="/tags"
            class="text-sm text-gray-400 hover:text-primary transition-colors"
          >
            标签
          </router-link>
          <svg
            class="w-4 h-4 text-gray-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 5l7 7-7 7"
          /></svg>
          <span
            class="text-sm"
            :style="{ color: currentTag()?.color || '#6b7280' }"
          >#{{ currentTag()?.name }}</span>
        </div>
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
          <span :style="{ color: currentTag()?.color }">#{{ currentTag()?.name || '标签文章' }}</span>
        </h1>
        <p class="text-sm text-gray-400 mt-2 flex items-center gap-2">
          <span>共 {{ blogStore.pagination.total }} 篇相关文章</span>
          <span
            v-if="loading"
            class="inline-block w-3.5 h-3.5 border-2 border-primary/30 border-t-primary rounded-full animate-spin"
            aria-hidden="true"
          />
        </p>
      </div>

      <transition
        name="content-fade"
        mode="out-in"
      >
        <!-- 加载骨架屏：请求进行中立即替换旧内容，杜绝新旧内容混合显示 -->
        <div
          v-if="loading"
          key="loading"
          class="space-y-4"
          aria-busy="true"
          aria-label="文章加载中"
        >
          <div
            v-for="i in 4"
            :key="i"
            class="article-card"
          >
            <div class="p-2 flex flex-col gap-3 sm:grid sm:grid-cols-[auto_1fr] sm:gap-4 animate-pulse">
              <div class="w-full h-52 sm:w-56 md:w-64 sm:h-36 bg-gray-200 dark:bg-dark-200 rounded-t-lg sm:rounded-lg" />
              <div class="flex-1 flex flex-col gap-2.5 py-1">
                <div class="h-3 w-16 rounded bg-gray-200 dark:bg-dark-200" />
                <div class="h-5 w-3/4 rounded bg-gray-200 dark:bg-dark-200" />
                <div class="h-3 w-full rounded bg-gray-200 dark:bg-dark-200" />
                <div class="h-3 w-5/6 rounded bg-gray-200 dark:bg-dark-200" />
                <div class="mt-auto pt-3 border-t border-gray-100 dark:border-white/5">
                  <div class="h-3 w-32 rounded bg-gray-200 dark:bg-dark-200" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 错误状态：网络异常时明确提示并提供重试 -->
        <div
          v-else-if="fetchError"
          key="error"
          class="text-center py-16"
        >
          <svg
            class="w-12 h-12 mx-auto mb-3 text-red-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <p class="text-gray-500 dark:text-gray-400 mb-4">
            {{ blogStore.error || '文章加载失败，请检查网络后重试' }}
          </p>
          <button
            type="button"
            class="px-5 py-2 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors"
            @click="retryFetch"
          >
            重新加载
          </button>
        </div>

        <!-- 标签不存在 -->
        <div
          v-else-if="notFound"
          key="not-found"
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
          <p class="text-gray-400">
            标签不存在或已被删除
          </p>
        </div>

        <!-- 空状态 -->
        <div
          v-else-if="blogStore.articles.length === 0"
          key="empty"
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
          <p class="text-gray-400">
            暂无文章
          </p>
        </div>

        <!-- 文章列表 -->
        <div
          v-else
          key="list"
          ref="articlesRef"
          class="space-y-4"
        >
          <article
            v-for="article in blogStore.articles"
            :key="article.id"
            class="article-card group relative"
          >
            <router-link
              :to="`/article/${article.slug}`"
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
                      data-tooltip="浏览量"
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
                    </span>
                    <button
                      class="article-meta-item article-action-btn relative text-inherit"
                      :data-tooltip="article.is_liked ? '取消点赞' : '点赞'"
                      @click="handleLike($event, article)"
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
                    </button>
                    <button
                      class="article-meta-item article-action-btn relative text-inherit"
                      data-tooltip="评论"
                      @click="goToComments($event, article.slug)"
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
                    </button>
                    <button
                      :class="[
                        'article-meta-item article-action-btn relative text-inherit',
                        { 'text-amber-500': article.is_bookmarked }
                      ]"
                      :data-tooltip="article.is_bookmarked ? '取消收藏' : '收藏'"
                      @click="handleBookmark($event, article)"
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
                    </button>
                  </div>
                </div>
              </div>
            </router-link>
          </article>
        </div>
      </transition>

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

    <aside
      class="lg:hidden mt-8 space-y-4"
      aria-label="侧边栏内容"
    >
      <LeftSidebar />
      <BlogSidebar />
    </aside>
  </div>
</template>
