<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useBlogStore, useAuthStore, useUserProfileStore } from '@/stores'

const props = defineProps<{
  hideUserCard?: boolean
}>()

const blogStore = useBlogStore()
const authStore = useAuthStore()
const userProfileStore = useUserProfileStore()

const announcements = computed(() => blogStore.announcements)

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

const getTypeIcon = (type: string) => {
  const icons = {
    info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
    success: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    error: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
  }
  return icons[type as keyof typeof icons] || icons.info
}

const getTypeColor = (type: string) => {
  const colors = {
    info: 'text-blue-500',
    warning: 'text-amber-500',
    success: 'text-emerald-500',
    error: 'text-red-500'
  }
  return colors[type as keyof typeof colors] || colors.info
}

const formatDate = (date: string) => {
  if (!date) return ''
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated) {
    userProfileStore.fetchProfile()
  } else {
    userProfileStore.clearProfile()
  }
})

onMounted(() => {
  if (authStore.isAuthenticated && !userProfileStore.profile) {
    userProfileStore.fetchProfile()
  }
})
</script>

<template>
  <aside class="blog-sidebar">
    <div
      v-if="announcements.length > 0"
      class="sidebar-widget sidebar-widget-compact"
    >
      <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
        <svg
          class="w-4 h-4 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"
          />
        </svg>
        公告
      </h3>
      
      <div class="space-y-3">
        <div
          v-for="announcement in announcements"
          :key="announcement.id"
          class="group"
        >
          <div class="flex items-start gap-2">
            <svg
              :class="['w-4 h-4 mt-0.5 flex-shrink-0', getTypeColor(announcement.type)]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                :d="getTypeIcon(announcement.type)"
              />
            </svg>
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                {{ announcement.title }}
              </h4>
              <p class="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                {{ announcement.content }}
              </p>
              <p class="text-xs text-gray-400 dark:text-gray-500 mt-1.5">
                {{ formatDate(announcement.updated_at || announcement.created_at) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="blogStore.categories.length"
      class="sidebar-widget sidebar-widget-compact"
    >
      <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
        <svg
          class="w-3.5 h-3.5 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
          />
        </svg>
        分类目录
      </h3>
      <div class="space-y-0.5">
        <router-link
          v-for="category in blogStore.categories"
          :key="category.id"
          :to="`/categories/${category.slug}`"
          class="sidebar-link flex items-center justify-between px-2 py-1.5 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:text-primary transition-all group"
        >
          <div class="flex items-center gap-1.5">
            <span
              class="w-1.5 h-1.5 rounded-full"
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
      class="sidebar-widget sidebar-widget-compact"
    >
      <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
        <svg
          class="w-3.5 h-3.5 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
          />
        </svg>
        热门标签
      </h3>
      <div class="flex flex-wrap gap-1">
        <router-link
          v-for="tag in popularTags"
          :key="tag.id"
          :to="`/tags/${tag.slug}`"
          class="sidebar-link tag-badge text-xs text-gray-500 dark:text-gray-400 hover:text-primary hover:border-primary/30"
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
      class="sidebar-widget sidebar-widget-compact"
    >
      <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
        <svg
          class="w-3.5 h-3.5 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z"
          />
        </svg>
        热门文章
      </h3>
      <div class="space-y-2">
        <router-link
          v-for="(article, index) in popularArticles"
          :key="article.id"
          :to="`/article/${article.slug}`"
          class="sidebar-link flex gap-3 p-2 rounded-lg group"
        >
          <span
            class="flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold"
            :class="index === 0 ? 'bg-gradient-to-br from-amber-400 to-orange-500 text-white' : index === 1 ? 'bg-gradient-to-br from-gray-300 to-gray-400 text-white' : index === 2 ? 'bg-gradient-to-br from-amber-600 to-amber-700 text-white' : 'bg-gray-100 dark:bg-dark-300 text-gray-400'"
          >
            {{ index + 1 }}
          </span>
          <div class="flex-1 min-w-0">
            <h4 class="text-sm text-gray-700 dark:text-gray-300 group-hover:text-primary transition-colors line-clamp-2 leading-snug">
              {{ article.title }}
            </h4>
            <div class="flex items-center gap-2 mt-1">
              <span class="flex items-center gap-0.5 text-xs text-gray-400">
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
              <span
                v-if="article.like_count"
                class="flex items-center gap-0.5 text-xs text-gray-400"
              >
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
                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                  />
                </svg>
                {{ article.like_count }}
              </span>
            </div>
          </div>
        </router-link>
      </div>
    </div>
  </aside>
</template>
