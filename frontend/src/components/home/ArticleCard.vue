<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import type { ArticleListItem } from '@/types'
import { likeApi } from '@/api'

const props = defineProps<{
  article: ArticleListItem
}>()

const router = useRouter()
const isLiked = ref(props.article.is_liked || false)
const likeCount = ref(props.article.like_count || 0)
const isLiking = ref(false)

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const handleLike = async (e: Event) => {
  e.preventDefault()
  e.stopPropagation()
  
  if (isLiking.value) return
  
  isLiking.value = true
  try {
    const result = await likeApi.toggle(props.article.id)
    isLiked.value = result.is_liked
    likeCount.value = result.like_count
  } catch (error) {
    console.error('Failed to toggle like:', error)
  } finally {
    isLiking.value = false
  }
}

const goToComments = (e: Event) => {
  e.preventDefault()
  e.stopPropagation()
  router.push(`/article/${props.article.slug}#comments`)
}
</script>

<template>
  <router-link
    :to="`/article/${article.slug}`"
    class="group glass-card-hover p-4 flex flex-col h-full"
  >
    <div v-if="article.cover_image" class="relative mb-3 overflow-hidden rounded-lg">
      <img
        :src="article.cover_image"
        :alt="article.title"
        class="w-full h-32 object-cover transition-transform duration-500 group-hover:scale-110"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-dark to-transparent opacity-60" />
    </div>

    <div v-if="article.is_pinned || article.is_featured" class="mb-2 flex items-center gap-2">
      <span v-if="article.is_pinned" class="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-600 dark:text-amber-400 rounded border border-amber-500/30">
        <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/>
        </svg>
        置顶
      </span>
      <span v-if="article.is_featured" class="px-2 py-0.5 text-xs font-medium bg-gradient-to-r from-primary to-accent text-white rounded-full">
        精选
      </span>
    </div>

    <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-1 group-hover:text-primary transition-colors line-clamp-2">
      {{ article.title }}
    </h3>

    <p v-if="article.summary" class="text-gray-500 dark:text-gray-400 text-sm mb-2 line-clamp-2 flex-grow">
      {{ article.summary }}
    </p>

    <div v-if="article.category" class="mb-2">
      <span
        class="inline-flex items-center gap-1 text-sm"
        :style="{ color: article.category.color }"
      >
        <span class="w-1.5 h-1.5 rounded-full" :style="{ backgroundColor: article.category.color }" />
        {{ article.category.name }}
      </span>
    </div>

    <div class="flex flex-wrap gap-1 mb-2">
      <span
        v-for="tag in article.tags.slice(0, 2)"
        :key="tag.id"
        class="inline-flex items-center px-2 py-0.5 text-sm font-medium rounded-full border transition-all duration-300 hover:border-primary/50"
        :style="{ 
          color: tag.color, 
          backgroundColor: tag.color + '15',
          borderColor: tag.color + '40'
        }"
      >
        {{ tag.name }}
      </span>
    </div>

    <div class="flex items-center justify-between text-sm text-gray-500 mt-auto pt-2 border-t border-gray-200 dark:border-white/5">
      <span>{{ formatDate(article.created_at) }}</span>
      <div class="flex items-center gap-3">
        <span class="flex items-center gap-1">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ article.reading_time }}分钟
        </span>
        <span class="flex items-center gap-1">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          {{ article.view_count }}
        </span>
        <button
          @click="goToComments"
          class="flex items-center gap-1 hover:text-primary transition-colors"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          {{ article.comment_count || 0 }}
        </button>
        <button
          @click="handleLike"
          :disabled="isLiking"
          class="flex items-center gap-1 transition-colors"
          :class="isLiked ? 'text-red-500' : 'hover:text-red-500'"
        >
          <svg 
            class="w-3 h-3 transition-transform" 
            :class="{ 'scale-110': isLiked }"
            :fill="isLiked ? 'currentColor' : 'none'" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
          {{ likeCount }}
        </button>
      </div>
    </div>
  </router-link>
</template>
