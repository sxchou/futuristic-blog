<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useBlogStore, useAuthStore, useUserProfileStore } from '@/stores'
import { dashboardApi } from '@/api'
import UserAvatar from './UserAvatar.vue'

const props = defineProps<{
  hideUserCard?: boolean
}>()

const blogStore = useBlogStore()
const authStore = useAuthStore()
const userProfileStore = useUserProfileStore()

const stats = ref({
  articles: 0,
  views: 0,
  likes: 0,
  comments: 0
})

const popularArticles = computed(() => {
  return [...blogStore.articles]
    .sort((a, b) => b.view_count - a.view_count)
    .slice(0, 5)
})

const popularTags = computed(() => {
  return [...blogStore.tags]
    .sort((a, b) => b.article_count - a.article_count)
    .slice(0, 15)
})

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

watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated) {
    userProfileStore.fetchProfile()
  } else {
    userProfileStore.clearProfile()
  }
})

onMounted(() => {
  fetchStats()
  if (authStore.isAuthenticated && !userProfileStore.profile) {
    userProfileStore.fetchProfile()
  }
})
</script>

<template>
  <aside class="blog-sidebar">
    <div
      v-if="!props.hideUserCard"
      class="sidebar-widget"
    >
      <template v-if="authStore.isAuthenticated && authStore.user">
        <div class="p-4 bg-gradient-to-br from-primary/5 via-accent/3 to-primary/5 dark:from-primary/10 dark:via-accent/5 dark:to-primary/10 rounded-xl border border-primary/10 dark:border-primary/20">
          <div class="flex items-center gap-3">
            <div class="relative flex-shrink-0">
              <UserAvatar
                :profile="userProfileStore.profile"
                size="md"
                :show-dropdown="false"
              />
              <span
                v-if="authStore.user.is_verified"
                class="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-emerald-500 rounded-full flex items-center justify-center ring-2 ring-white dark:ring-dark-200"
              >
                <svg
                  class="w-2.5 h-2.5 text-white"
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
              <div class="flex items-center gap-1.5">
                <h4 class="text-sm font-bold text-gray-900 dark:text-white truncate">
                  {{ userProfileStore.profile?.username || authStore.user.username }}
                </h4>
                <span
                  v-if="authStore.user.is_admin"
                  class="px-1.5 py-0.5 bg-primary/10 dark:bg-primary/20 text-primary text-[10px] font-medium rounded"
                >
                  管理员
                </span>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                {{ authStore.user.email }}
              </p>
            </div>
          </div>
          <div class="mt-3 pt-3 border-t border-gray-200/50 dark:border-white/5 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>用户ID: {{ authStore.user.id }}</span>
            <router-link
              to="/profile"
              class="text-primary hover:text-primary/80 transition-colors"
            >
              个人中心
            </router-link>
          </div>
        </div>
      </template>
      <template v-else>
        <div class="p-4 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-dark-300 dark:to-dark-400 rounded-xl border border-gray-200 dark:border-white/5">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-full bg-gray-200 dark:bg-dark-500 flex items-center justify-center">
              <svg
                class="w-6 h-6 text-gray-400 dark:text-gray-500"
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
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-bold text-gray-900 dark:text-white">
                欢迎访问
              </h4>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                登录以获取更多功能
              </p>
            </div>
          </div>
          <div class="mt-3 pt-3 border-t border-gray-200/50 dark:border-white/5 flex gap-2">
            <router-link
              to="/login"
              class="flex-1 py-2 text-center text-sm text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-dark-500 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-400 transition-colors"
            >
              登录
            </router-link>
            <router-link
              to="/register"
              class="flex-1 py-2 text-center text-sm text-white bg-primary rounded-lg hover:bg-primary/90 transition-colors"
            >
              注册
            </router-link>
          </div>
        </div>
      </template>
    </div>
    
    <div class="sidebar-widget">
      <h3 class="sidebar-widget-title">
        博客统计
      </h3>
      <div class="grid grid-cols-2 gap-3">
        <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
          <div class="text-xl font-bold text-primary">
            {{ stats.articles }}
          </div>
          <div class="text-xs text-gray-500">
            文章
          </div>
        </div>
        <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
          <div class="text-xl font-bold text-accent">
            {{ stats.views }}
          </div>
          <div class="text-xs text-gray-500">
            浏览
          </div>
        </div>
        <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
          <div class="text-xl font-bold text-cyber-pink">
            {{ stats.likes }}
          </div>
          <div class="text-xs text-gray-500">
            点赞
          </div>
        </div>
        <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
          <div class="text-xl font-bold text-cyber-green">
            {{ stats.comments }}
          </div>
          <div class="text-xs text-gray-500">
            评论
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="blogStore.categories.length"
      class="sidebar-widget"
    >
      <h3 class="sidebar-widget-title">
        分类目录
      </h3>
      <div class="space-y-1">
        <router-link
          v-for="category in blogStore.categories"
          :key="category.id"
          :to="`/categories/${category.slug}`"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-primary/5 transition-all group"
        >
          <div class="flex items-center gap-2">
            <span
              class="w-2 h-2 rounded-full"
              :style="{ backgroundColor: category.color }"
            />
            <span>{{ category.name }}</span>
          </div>
          <span class="text-xs text-gray-400 group-hover:text-primary">{{ category.article_count }}</span>
        </router-link>
      </div>
    </div>

    <div
      v-if="popularTags.length"
      class="sidebar-widget"
    >
      <h3 class="sidebar-widget-title">
        热门标签
      </h3>
      <div class="flex flex-wrap gap-1.5">
        <router-link
          v-for="tag in popularTags"
          :key="tag.id"
          :to="`/tags/${tag.slug}`"
          class="tag-badge text-gray-500 dark:text-gray-400 hover:text-primary hover:border-primary/30"
          :style="{ 
            color: tag.color, 
            backgroundColor: tag.color + '10',
            borderColor: tag.color + '30'
          }"
        >
          {{ tag.name }}
        </router-link>
      </div>
    </div>

    <div
      v-if="popularArticles.length"
      class="sidebar-widget"
    >
      <h3 class="sidebar-widget-title">
        热门文章
      </h3>
      <div class="space-y-3">
        <router-link
          v-for="(article, index) in popularArticles"
          :key="article.id"
          :to="`/article/${article.slug}`"
          class="flex gap-3 group"
        >
          <span
            class="flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold"
            :class="index < 3 ? 'bg-primary/10 text-primary' : 'bg-gray-100 dark:bg-dark-300 text-gray-400'"
          >
            {{ index + 1 }}
          </span>
          <div class="flex-1 min-w-0">
            <h4 class="text-sm text-gray-700 dark:text-gray-300 group-hover:text-primary transition-colors line-clamp-2 leading-snug">
              {{ article.title }}
            </h4>
            <div class="article-meta mt-1">
              <span class="article-meta-item">
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
                {{ article.view_count }}
              </span>
            </div>
          </div>
        </router-link>
      </div>
    </div>
  </aside>
</template>
