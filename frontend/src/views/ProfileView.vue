<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore, useUserInteractionStore, useUserProfileStore, useSiteConfigStore } from '@/stores'
import { likeApi, commentApi, bookmarkApi } from '@/api'
import type { ArticleListItem } from '@/types'
import Pagination from '@/components/common/Pagination.vue'
import BlogSidebar from '@/components/common/BlogSidebar.vue'
import LeftSidebar from '@/components/common/LeftSidebar.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { formatDateShort } from '@/utils/date'
import { getMediaUrl } from '@/utils/media'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const userInteractionStore = useUserInteractionStore()
const userProfileStore = useUserProfileStore()
const siteConfigStore = useSiteConfigStore()

const isStackedLayout = computed(() => siteConfigStore.mobileArticleLayout === 'stacked')

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

const activeTab = ref<'liked' | 'commented' | 'bookmarked'>('liked')
const articles = ref<ArticleListItem[]>([])
const loading = ref(false)
const pagination = ref({
  page: 1,
  pageSize: 10,
  total: 0,
  totalPages: 0
})

const tabConfig = [
  { key: 'liked' as const, label: '我的点赞', icon: 'heart' },
  { key: 'commented' as const, label: '我的评论', icon: 'chat' },
  { key: 'bookmarked' as const, label: '我的收藏', icon: 'bookmark' }
]

const formatDate = (date: string) => formatDateShort(date)

const fetchArticles = async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  
  loading.value = true
  try {
    let response
    switch (activeTab.value) {
      case 'liked':
        response = await likeApi.getUserLikedArticles(pagination.value.page, pagination.value.pageSize)
        break
      case 'commented':
        response = await commentApi.getUserCommentedArticles(pagination.value.page, pagination.value.pageSize)
        break
      case 'bookmarked':
        response = await bookmarkApi.getUserBookmarks(pagination.value.page, pagination.value.pageSize)
        break
    }
    
    articles.value = response.items.map(article => ({
      ...article,
      is_liked: userInteractionStore.isLiked(article.id),
      is_bookmarked: userInteractionStore.isBookmarked(article.id)
    }))
    pagination.value.total = response.total
    pagination.value.totalPages = response.total_pages
  } catch (error) {
    console.error('Failed to fetch articles:', error)
    articles.value = []
  } finally {
    loading.value = false
  }
}

const handleTabChange = (tab: 'liked' | 'commented' | 'bookmarked') => {
  if (tab !== activeTab.value) {
    activeTab.value = tab
    pagination.value.page = 1
    fetchArticles()
  }
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
  fetchArticles()
  window.scrollTo({ top: 0, behavior: 'smooth' })
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
    const result = await userInteractionStore.toggleBookmark(article.id)
    if (result) {
      article.is_bookmarked = result.is_bookmarked
      if (activeTab.value === 'bookmarked' && !result.is_bookmarked) {
        fetchArticles()
      }
    }
  } catch (error) {
    console.error('Failed to toggle bookmark:', error)
  } finally {
    article._bookmarking = false
  }
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
  try {
    const result = await userInteractionStore.toggleLike(article.id)
    if (result) {
      article.is_liked = result.is_liked
      article.like_count = result.like_count
      if (activeTab.value === 'liked' && !result.is_liked) {
        fetchArticles()
      }
    }
  } catch (error) {
    console.error('Failed to toggle like:', error)
  } finally {
    article._liking = false
  }
}

const goToComments = (e: Event, slug: string) => {
  e.preventDefault()
  e.stopPropagation()
  router.push(`/article/${slug}#comments`)
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  await Promise.all([
    userInteractionStore.initialize(),
    userProfileStore.fetchProfile()
  ])
  fetchArticles()
})

watch(() => route.path, (newPath) => {
  if (newPath === '/profile') {
    fetchArticles()
  }
})
</script>

<template>
  <div class="flex flex-col lg:flex-row gap-6">
      <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
        <div class="lg:sticky lg:top-20">
          <LeftSidebar />
        </div>
      </div>
      
      <main class="flex-1 min-w-0 lg:order-2">
        <div class="glass-card p-2 mb-6">
          <div class="flex items-center gap-4 mb-2">
            <div class="relative flex-shrink-0">
              <UserAvatar
                :profile="userProfileStore.profile"
                size="lg"
                :show-dropdown="false"
              />
              <span
                v-if="authStore.user?.is_verified"
                class="absolute -bottom-0.5 -right-0.5 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center ring-2 ring-white dark:ring-dark-200"
              >
                <svg
                  class="w-3 h-3 text-white"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
              </span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <h1 class="text-xl font-bold text-gray-900 dark:text-white">
                  {{ userProfileStore.profile?.username || authStore.user?.username }}
                </h1>
                <span
                  v-if="authStore.user?.is_admin"
                  class="px-2 py-0.5 bg-primary/10 dark:bg-primary/20 text-primary text-xs font-medium rounded"
                >
                  管理员
                </span>
              </div>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {{ authStore.user?.email }}
              </p>
            </div>
            <router-link
              to="/admin/my-profile"
              class="px-4 py-2 text-sm font-medium text-primary border border-primary/30 hover:bg-primary/5 rounded-lg transition-colors"
            >
              编辑资料
            </router-link>
          </div>

          <div class="flex border-b border-gray-200 dark:border-white/10">
            <button
              v-for="tab in tabConfig"
              :key="tab.key"
              class="flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors relative"
              :class="activeTab === tab.key ? 'text-primary' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
              @click="handleTabChange(tab.key)"
            >
              <svg
                v-if="tab.icon === 'heart'"
                class="w-4 h-4"
                :fill="activeTab === tab.key ? 'currentColor' : 'none'"
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
              <svg
                v-else-if="tab.icon === 'chat'"
                class="w-4 h-4"
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
              <svg
                v-else-if="tab.icon === 'bookmark'"
                class="w-4 h-4"
                :fill="activeTab === tab.key ? 'currentColor' : 'none'"
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
              {{ tab.label }}
              <span
                v-if="activeTab === tab.key"
                class="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-full"
              />
            </button>
          </div>
        </div>

        <div
          v-if="loading"
          class="flex justify-center py-20"
        >
          <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
        </div>

        <div
          v-else-if="articles.length === 0"
          class="glass-card p-2 text-center"
        >
          <svg
            class="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              v-if="activeTab === 'liked'"
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
            />
            <path
              v-else-if="activeTab === 'commented'"
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
            <path
              v-else
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
            />
          </svg>
          <p class="text-gray-500 dark:text-gray-400">
            {{ activeTab === 'liked' ? '还没有点赞过文章' : activeTab === 'commented' ? '还没有评论过文章' : '还没有收藏过文章' }}
          </p>
          <router-link
            to="/"
            class="inline-block mt-4 px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
          >
            去浏览文章
          </router-link>
        </div>

        <div
          v-else
          class="space-y-4"
        >
          <article
            v-for="article in articles"
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
                      ? 'relative w-full h-52 sm:w-56 md:w-64 sm:h-full overflow-hidden rounded-t-lg sm:rounded-lg' 
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
                    <span 
                      :class="[
                        'article-meta-item relative',
                        isStackedLayout 
                          ? 'text-inherit' 
                          : 'text-white/70 sm:text-inherit'
                      ]"
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
                      :class="[
                        'article-meta-item article-action-btn relative',
                        isStackedLayout 
                          ? 'text-inherit' 
                          : 'text-white/70 sm:text-inherit'
                      ]"
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
                      :class="[
                        'article-meta-item article-action-btn relative',
                        isStackedLayout 
                          ? 'text-inherit' 
                          : 'text-white/70 sm:text-inherit'
                      ]"
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
                        'article-meta-item article-action-btn relative',
                        isStackedLayout 
                          ? 'text-inherit' 
                          : 'text-white/70 sm:text-inherit',
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
          v-if="pagination.totalPages > 1"
          class="mt-8"
        >
          <Pagination
            :current-page="pagination.page"
            :total-pages="pagination.totalPages"
            @page-change="handlePageChange"
          />
        </div>
      </main>

      <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
        <div class="lg:sticky lg:top-20">
          <BlogSidebar hide-user-card />
        </div>
      </div>

      <aside class="lg:hidden mt-8 space-y-4" aria-label="侧边栏内容">
        <LeftSidebar />
        <BlogSidebar hide-user-card />
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
