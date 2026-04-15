<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBlogStore, useAuthStore, useUserInteractionStore, useSiteConfigStore } from '@/stores'
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
const siteConfigStore = useSiteConfigStore()
const loading = ref(true)
const articlesRef = ref<HTMLElement | null>(null)

const { pageSize } = usePageSize()

const isStackedLayout = computed(() => siteConfigStore.mobileArticleLayout === 'stacked')

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
  loading.value = true
  const slug = route.params.slug as string
  const category = blogStore.getCategoryBySlug(slug)
  if (category) {
    await blogStore.fetchArticles({
      category_id: category.id,
      page: page,
      page_size: pageSize.value
    })
    if (updateUrl) {
      if (page !== 1) {
        router.replace({ query: { ...route.query, page: page.toString() } })
      } else if (route.query.page) {
        const newQuery = { ...route.query }
        delete newQuery.page
        router.replace({ query: newQuery })
      }
    }
    if (shouldScroll) scrollToArticles()
  }
  loading.value = false
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

watch(() => route.params.slug, () => {
  fetchArticles(1, true, false)
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
  try {
    await userInteractionStore.toggleLike(article.id)
    article.is_liked = !article.is_liked
    article.like_count += article.is_liked ? 1 : -1
  } catch (error) {
    console.error('Failed to toggle like:', error)
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
  try {
    await userInteractionStore.toggleBookmark(article.id)
    article.is_bookmarked = !article.is_bookmarked
  } catch (error) {
    console.error('Failed to toggle bookmark:', error)
  } finally {
    article._bookmarking = false
  }
}

const goToComments = (e: Event, slug: string) => {
  e.preventDefault()
  e.stopPropagation()
  router.push(`/article/${slug}#comments`)
}

onMounted(async () => {
  const pageFromUrl = parseInt(route.query.page as string) || 1
  await blogStore.fetchCategories()
  if (authStore.isAuthenticated) {
    await userInteractionStore.initialize()
  }
  await fetchArticles(pageFromUrl, false, false)
})

const currentCategory = () => {
  const slug = route.params.slug as string
  return blogStore.getCategoryBySlug(slug)
}

const handlePageChange = (page: number) => {
  fetchArticles(page, true, true)
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
            to="/categories"
            class="text-sm text-gray-400 hover:text-primary transition-colors"
          >
            分类
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
          <span class="text-sm text-gray-600 dark:text-gray-300">{{ currentCategory()?.name }}</span>
        </div>
        <div class="flex items-center gap-3">
          <div
            v-if="currentCategory()"
            class="w-10 h-10 rounded-xl flex items-center justify-center"
            :style="{ backgroundColor: currentCategory()!.color + '15' }"
          >
            <svg
              class="w-5 h-5"
              :style="{ color: currentCategory()!.color }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
              />
            </svg>
          </div>
          <div>
            <h1 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
              {{ currentCategory()?.name || '分类文章' }}
            </h1>
            <p
              v-if="currentCategory()?.description"
              class="text-sm text-gray-500 dark:text-gray-400 mt-0.5"
            >
              {{ currentCategory()?.description }}
            </p>
          </div>
        </div>
        <p class="text-sm text-gray-400 mt-2">
          共 {{ blogStore.pagination.total }} 篇文章
        </p>
      </div>

      <div
        v-if="loading"
        class="flex justify-center py-20"
      >
        <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>

      <div
        v-else-if="blogStore.articles.length === 0"
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

      <div
        v-else
        ref="articlesRef"
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
          >
            <div 
              class="flex flex-col gap-3 sm:grid sm:grid-cols-[auto_1fr] sm:gap-4"
            >
              <div
                v-if="article.cover_image"
                :class="[
                  isStackedLayout 
                    ? 'relative w-full h-40 sm:w-56 md:w-64 sm:h-full overflow-hidden rounded-t-lg sm:rounded-lg' 
                    : 'absolute inset-0 sm:relative sm:w-56 md:w-64 sm:h-full overflow-hidden rounded-none sm:rounded-lg'
                ]"
              >
                <img
                  :src="getMediaUrl(article.cover_image)"
                  :alt="article.title"
                  class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110 rounded-t-lg sm:rounded-lg"
                  loading="lazy"
                >
                <template v-if="!isStackedLayout">
                  <div class="absolute inset-0 bg-gradient-to-r from-black/70 via-black/40 to-transparent sm:hidden" />
                  <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent sm:hidden" />
                </template>
              </div>
              <div
                v-else
                :class="[
                  isStackedLayout 
                    ? 'hidden' 
                    : 'absolute inset-0 sm:hidden'
                ]"
              >
                <div class="absolute inset-0 bg-gradient-to-br from-gray-700 via-gray-800 to-gray-900 dark:from-gray-800 dark:via-gray-900 dark:to-gray-800" />
              </div>

              <div 
                class="relative flex-1 min-w-0 flex flex-col"
                :class="[
                  isStackedLayout 
                    ? 'min-h-0' 
                    : 'min-h-[180px] sm:min-h-0'
                ]"
              >
                <div class="flex items-center gap-2 mb-2">
                  <span
                    v-if="article.is_pinned"
                    :class="[
                      'inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium rounded',
                      isStackedLayout 
                        ? 'bg-amber-500/10 text-amber-600' 
                        : 'bg-amber-500/20 text-amber-400 sm:bg-amber-500/10 sm:text-amber-600'
                    ]"
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
                    :class="[
                      'inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-primary/20 text-[10px] font-medium rounded',
                      isStackedLayout 
                        ? 'bg-primary/10 text-primary' 
                        : 'bg-primary/20 text-primary sm:bg-primary/10'
                    ]"
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
                    :class="[
                      'inline-flex items-center gap-1 text-xs',
                      isStackedLayout 
                        ? 'text-inherit' 
                        : 'text-white/90 sm:text-inherit'
                    ]"
                    :style="(isStackedLayout || !article.cover_image) ? { color: article.category.color } : {}"
                  >
                    <span
                      class="w-1.5 h-1.5 rounded-full"
                      :style="{ backgroundColor: article.category.color }"
                    />
                    {{ article.category.name }}
                  </span>
                </div>

                <h3 :class="[
                  'text-base font-bold leading-snug mb-2 group-hover:text-primary transition-colors line-clamp-2',
                  isStackedLayout 
                    ? 'text-gray-900 dark:text-white' 
                    : 'text-white sm:text-gray-900 dark:sm:text-white'
                ]">
                  {{ article.title }}
                </h3>
                <p
                  v-if="article.summary"
                  :class="[
                    'text-sm leading-relaxed mb-3 line-clamp-2',
                    isStackedLayout 
                      ? 'text-gray-500 dark:text-gray-400' 
                      : 'text-white/70 sm:text-gray-500 dark:sm:text-gray-400'
                  ]"
                >
                  {{ article.summary }}
                </p>

                <div class="flex flex-wrap gap-1 mb-3">
                  <span
                    v-for="tag in article.tags.slice(0, 3)"
                    :key="tag.id"
                    :class="[
                      'tag-badge text-[10px]',
                      isStackedLayout 
                        ? '' 
                        : 'bg-white/20 text-white/90 border-white/30 sm:bg-transparent sm:text-inherit sm:border-inherit'
                    ]"
                    :style="(isStackedLayout || !article.cover_image) ? { 
                      color: tag.color, 
                      backgroundColor: tag.color + '10',
                      borderColor: tag.color + '30'
                    } : {}"
                  >
                    {{ tag.name }}
                  </span>
                </div>

                <div :class="[
                  'article-meta mt-auto pt-3',
                  isStackedLayout 
                    ? 'border-t border-gray-100 dark:border-white/5' 
                    : 'border-t border-white/10 sm:border-gray-100 dark:sm:border-white/5'
                ]">
                  <span :class="[
                    'article-meta-item',
                    isStackedLayout 
                      ? 'text-inherit' 
                      : 'text-white/70 sm:text-inherit'
                  ]">
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
                  <span :class="[
                    'article-meta-item',
                    isStackedLayout 
                      ? 'text-inherit' 
                      : 'text-white/70 sm:text-inherit'
                  ]">
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
                    :class="[
                      'article-meta-item article-action-btn',
                      isStackedLayout 
                        ? 'text-inherit' 
                        : 'text-white/70 sm:text-inherit'
                    ]"
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
                    :class="[
                      'article-meta-item article-action-btn',
                      isStackedLayout 
                        ? 'text-inherit' 
                        : 'text-white/70 sm:text-inherit'
                    ]"
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
                      'article-meta-item article-action-btn',
                      isStackedLayout 
                        ? 'text-inherit' 
                        : 'text-white/70 sm:text-inherit',
                      { 'text-amber-500': article.is_bookmarked }
                    ]"
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
