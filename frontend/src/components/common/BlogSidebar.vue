<script setup lang="ts">
import { computed } from 'vue'
import { useBlogStore } from '@/stores'
import { dashboardApi } from '@/api'
import { ref, onMounted } from 'vue'

const blogStore = useBlogStore()

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

onMounted(() => {
  fetchStats()
})
</script>

<template>
  <aside class="blog-sidebar">
    <div class="sidebar-widget">
      <h3 class="sidebar-widget-title">博客统计</h3>
      <div class="grid grid-cols-2 gap-3">
        <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
          <div class="text-xl font-bold text-primary">{{ stats.articles }}</div>
          <div class="text-xs text-gray-500">文章</div>
        </div>
        <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
          <div class="text-xl font-bold text-accent">{{ stats.views }}</div>
          <div class="text-xs text-gray-500">浏览</div>
        </div>
        <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
          <div class="text-xl font-bold text-cyber-pink">{{ stats.likes }}</div>
          <div class="text-xs text-gray-500">点赞</div>
        </div>
        <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
          <div class="text-xl font-bold text-cyber-green">{{ stats.comments }}</div>
          <div class="text-xs text-gray-500">评论</div>
        </div>
      </div>
    </div>

    <div v-if="blogStore.categories.length" class="sidebar-widget">
      <h3 class="sidebar-widget-title">分类目录</h3>
      <div class="space-y-1">
        <router-link
          v-for="category in blogStore.categories"
          :key="category.id"
          :to="`/categories/${category.slug}`"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-primary/5 transition-all group"
        >
          <div class="flex items-center gap-2">
            <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: category.color }" />
            <span>{{ category.name }}</span>
          </div>
          <span class="text-xs text-gray-400 group-hover:text-primary">{{ category.article_count }}</span>
        </router-link>
      </div>
    </div>

    <div v-if="popularTags.length" class="sidebar-widget">
      <h3 class="sidebar-widget-title">热门标签</h3>
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

    <div v-if="popularArticles.length" class="sidebar-widget">
      <h3 class="sidebar-widget-title">热门文章</h3>
      <div class="space-y-3">
        <router-link
          v-for="(article, index) in popularArticles"
          :key="article.id"
          :to="`/article/${article.slug}`"
          class="flex gap-3 group"
        >
          <span class="flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold"
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
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
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
