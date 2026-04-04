<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useBlogStore } from '@/stores'
import { dashboardApi, articleApi } from '@/api'

const blogStore = useBlogStore()

const stats = ref({
  articles: 0,
  views: 0,
  likes: 0,
  comments: 0
})

const loading = ref(true)
const featuredArticlesList = ref<Array<any>>([])

const featuredArticles = computed(() => featuredArticlesList.value)

const currentSlide = ref(0)

let slideInterval: ReturnType<typeof setInterval> | null = null

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

const goToSlide = (index: number) => {
  currentSlide.value = index
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
  } finally {
    loading.value = false
  }
}

const fetchFeaturedArticles = async () => {
  try {
    const response = await articleApi.getArticles({ 
      is_featured: true, 
      page: 1, 
      page_size: 50 
    })
    featuredArticlesList.value = response.items
  } catch (error) {
    console.error('Failed to fetch featured articles:', error)
  }
}

onMounted(async () => {
  await Promise.all([
    blogStore.fetchCategories(),
    blogStore.fetchTags(),
    fetchStats(),
    fetchFeaturedArticles()
  ])
  
  if (featuredArticles.value.length > 1) {
    slideInterval = setInterval(nextSlide, 5000)
  }
})

onUnmounted(() => {
  if (slideInterval) {
    clearInterval(slideInterval)
  }
})
</script>

<template>
  <section class="relative overflow-hidden pb-12 md:pb-16">
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-80 h-80 bg-primary/10 rounded-full blur-3xl animate-pulse" />
      <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-accent/10 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s" />
    </div>

    <div class="container mx-auto px-4 relative z-10">
      <div class="text-center mb-8">
        <h2 class="text-2xl md:text-3xl font-bold mb-1">
          <span class="gradient-text">探索技术前沿</span>
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">记录学习历程，分享技术心得，探索无限可能</p>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-10">
        <div class="glass-card p-4 md:p-5 text-center group hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/10">
          <div class="w-12 h-12 mx-auto mb-3 rounded-xl bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-1">
            {{ loading ? '...' : stats.articles }}
          </div>
          <div class="text-gray-500 dark:text-gray-400 text-sm">篇文章</div>
        </div>

        <div class="glass-card p-4 md:p-5 text-center group hover:border-accent/50 transition-all duration-300 hover:shadow-lg hover:shadow-accent/10">
          <div class="w-12 h-12 mx-auto mb-3 rounded-xl bg-accent/10 flex items-center justify-center group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
          </div>
          <div class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-1">
            {{ blogStore.categories.length || '...' }}
          </div>
          <div class="text-gray-500 dark:text-gray-400 text-sm">个分类</div>
        </div>

        <div class="glass-card p-4 md:p-5 text-center group hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/10">
          <div class="w-12 h-12 mx-auto mb-3 rounded-xl bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
          </div>
          <div class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-1">
            {{ blogStore.tags.length || '...' }}
          </div>
          <div class="text-gray-500 dark:text-gray-400 text-sm">个标签</div>
        </div>

        <div class="glass-card p-4 md:p-5 text-center group hover:border-accent/50 transition-all duration-300 hover:shadow-lg hover:shadow-accent/10">
          <div class="w-12 h-12 mx-auto mb-3 rounded-xl bg-accent/10 flex items-center justify-center group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </div>
          <div class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-1">
            {{ loading ? '...' : stats.views }}
          </div>
          <div class="text-gray-500 dark:text-gray-400 text-sm">次访问</div>
        </div>

        <div class="glass-card p-4 md:p-5 text-center group hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/10">
          <div class="w-12 h-12 mx-auto mb-3 rounded-xl bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </div>
          <div class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-1">
            {{ loading ? '...' : stats.likes }}
          </div>
          <div class="text-gray-500 dark:text-gray-400 text-sm">个点赞</div>
        </div>

        <div class="glass-card p-4 md:p-5 text-center group hover:border-accent/50 transition-all duration-300 hover:shadow-lg hover:shadow-accent/10">
          <div class="w-12 h-12 mx-auto mb-3 rounded-xl bg-accent/10 flex items-center justify-center group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <div class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-1">
            {{ loading ? '...' : stats.comments }}
          </div>
          <div class="text-gray-500 dark:text-gray-400 text-sm">条评论</div>
        </div>
      </div>

      <div v-if="featuredArticles.length > 0" class="glass-card p-6 md:p-8">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl md:text-2xl font-bold flex items-center gap-2">
            <svg class="w-6 h-6 text-primary" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
            <span class="gradient-text">精选推荐</span>
          </h2>
          <div class="flex items-center gap-2">
            <button
              @click="prevSlide"
              class="w-8 h-8 rounded-full bg-gray-100 dark:bg-dark-200 flex items-center justify-center hover:bg-primary/20 transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              @click="nextSlide"
              class="w-8 h-8 rounded-full bg-gray-100 dark:bg-dark-200 flex items-center justify-center hover:bg-primary/20 transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>

        <div class="relative overflow-hidden">
          <div
            class="flex transition-transform duration-500 ease-out"
            :style="{ transform: `translateX(-${currentSlide * 100}%)` }"
          >
            <div
              v-for="article in featuredArticles"
              :key="article.id"
              class="w-full flex-shrink-0 px-1"
            >
              <router-link
                :to="`/article/${article.slug}`"
                class="block group"
              >
                <div class="flex flex-col md:flex-row gap-4 md:gap-6">
                  <div v-if="article.cover_image" class="md:w-1/3 flex-shrink-0">
                    <div class="relative overflow-hidden rounded-xl aspect-video md:aspect-square">
                      <img
                        :src="article.cover_image"
                        :alt="article.title"
                        class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                      />
                      <div class="absolute inset-0 bg-gradient-to-t from-dark/60 to-transparent" />
                    </div>
                  </div>
                  <div class="flex-1 flex flex-col justify-center">
                    <h3 class="text-lg md:text-xl font-bold text-gray-900 dark:text-white mb-2 group-hover:text-primary transition-colors line-clamp-2">
                      {{ article.title }}
                    </h3>
                    <p v-if="article.summary" class="text-gray-500 dark:text-gray-400 text-sm md:text-base mb-3 line-clamp-2">
                      {{ article.summary }}
                    </p>
                    <div class="flex items-center gap-4 text-sm text-gray-400">
                      <span v-if="article.category" class="flex items-center gap-1">
                        <span class="w-1.5 h-1.5 rounded-full" :style="{ backgroundColor: article.category.color }" />
                        {{ article.category.name }}
                      </span>
                      <span class="flex items-center gap-1">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        {{ article.view_count }}
                      </span>
                      <span class="flex items-center gap-1">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                        </svg>
                        {{ article.like_count }}
                      </span>
                    </div>
                  </div>
                </div>
              </router-link>
            </div>
          </div>
        </div>

        <div v-if="featuredArticles.length > 1" class="flex justify-center gap-2 mt-6">
          <button
            v-for="(_, index) in featuredArticles"
            :key="index"
            @click="goToSlide(index)"
            class="w-2 h-2 rounded-full transition-all duration-300"
            :class="currentSlide === index ? 'bg-primary w-6' : 'bg-gray-300 dark:bg-gray-600 hover:bg-primary/50'"
          />
        </div>
      </div>
    </div>
  </section>
</template>
