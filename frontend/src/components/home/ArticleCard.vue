<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import type { ArticleListItem } from '@/types'
import { likeApi } from '@/api'
import { formatDateShort } from '@/utils/date'

const props = defineProps<{
  article: ArticleListItem
  highlightKeyword?: string
}>()

const router = useRouter()
const isLiked = ref(props.article.is_liked || false)
const likeCount = ref(props.article.like_count || 0)
const isLiking = ref(false)

const formatDate = (date: string) => formatDateShort(date)

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

const getArticleLink = () => {
  const link: any = { path: `/article/${props.article.slug}` }
  if (props.highlightKeyword) {
    link.query = { highlight: props.highlightKeyword }
  }
  return link
}
</script>

<template>
  <router-link
    :to="getArticleLink()"
    class="article-card group"
  >
    <div
      v-if="article.cover_image"
      class="article-card__cover"
    >
      <img
        :src="article.cover_image"
        :alt="article.title"
        class="article-card__cover-img"
        loading="lazy"
      >
      <div class="article-card__cover-overlay" />
    </div>

    <div class="article-card__content">
      <div class="article-card__header">
        <div
          v-if="article.category"
          class="article-card__category"
        >
          <span
            class="article-card__category-dot"
            :style="{ backgroundColor: article.category.color }"
          />
          <span
            class="article-card__category-name"
            :style="{ color: article.category.color }"
          >
            {{ article.category.name }}
          </span>
        </div>
        <div
          v-if="article.is_pinned || article.is_featured"
          class="article-card__badges"
        >
          <span
            v-if="article.is_pinned"
            class="article-card__badge article-card__badge--pinned"
            title="置顶"
          >
            <svg
              class="w-2.5 h-2.5"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z" />
            </svg>
          </span>
          <span
            v-if="article.is_featured"
            class="article-card__badge article-card__badge--featured"
            title="精选"
          >
            <svg
              class="w-2.5 h-2.5"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
          </span>
        </div>
      </div>

      <h3 class="article-card__title">
        <template v-if="article.highlighted_title">
          <span v-html="article.highlighted_title" />
        </template>
        <template v-else>
          {{ article.title }}
        </template>
      </h3>

      <p
        v-if="article.summary || article.highlighted_summary"
        class="article-card__summary"
      >
        <template v-if="article.highlighted_summary">
          <span
            class="inline"
            v-html="article.highlighted_summary"
          />
        </template>
        <template v-else>
          {{ article.summary }}
        </template>
      </p>

      <div class="article-card__tags">
        <span
          v-for="tag in article.tags.slice(0, 2)"
          :key="tag.id"
          class="article-card__tag"
          :style="{
            color: tag.color,
            backgroundColor: tag.color + '15',
            borderColor: tag.color + '40'
          }"
        >
          {{ tag.name }}
        </span>
      </div>

      <div class="article-card__meta">
        <span class="article-card__meta-date">{{ formatDate(article.created_at) }}</span>
        <div class="article-card__meta-actions">
          <span class="article-card__meta-item">
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
          <button
            class="article-card__meta-item article-card__meta-btn"
            @click="goToComments"
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
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            {{ article.comment_count || 0 }}
          </button>
          <button
            :disabled="isLiking"
            class="article-card__meta-item article-card__meta-btn"
            :class="isLiked ? 'article-card__meta-btn--liked' : ''"
            @click="handleLike"
          >
            <svg
              class="w-3 h-3 transition-transform"
              :class="{ 'scale-110': isLiked }"
              :fill="isLiked ? 'currentColor' : 'none'"
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
            {{ likeCount }}
          </button>
        </div>
      </div>
    </div>
  </router-link>
</template>

<style scoped>
.article-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 1rem;
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  text-decoration: none;
}

.article-card:hover {
  border-color: rgba(0, 212, 255, 0.3);
  box-shadow: 0 10px 15px -3px rgba(0, 212, 255, 0.05);
}

.dark .article-card {
  background: #1a1a2e;
  border-color: rgba(255, 255, 255, 0.05);
}

.dark .article-card:hover {
  border-color: rgba(0, 212, 255, 0.3);
}

@media (min-width: 640px) {
  .article-card {
    flex-direction: row;
    gap: 0.75rem;
  }
}

.article-card__content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.article-card__header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.article-card__category {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.article-card__category-dot {
  width: 0.375rem;
  height: 0.375rem;
  border-radius: 9999px;
}

.article-card__category-name {
  font-size: 0.75rem;
  font-weight: 500;
}

.article-card__badges {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.article-card__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  border-radius: 9999px;
}

.article-card__badge--pinned {
  background: rgba(245, 158, 11, 0.9);
  color: white;
}

.article-card__badge--featured {
  background: linear-gradient(to right, #00d4ff, #7c3aed);
  color: white;
}

.article-card__title {
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 0.25rem;
  transition: color 0.3s ease;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}

.article-card:hover .article-card__title {
  color: #00d4ff;
}

.dark .article-card__title {
  color: #f1f5f9;
}

.dark .article-card:hover .article-card__title {
  color: #00d4ff;
}

.article-card__summary {
  color: #6b7280;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}

.dark .article-card__summary {
  color: #9ca3af;
}

.article-card__tags {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}

.article-card__tag {
  display: inline-flex;
  align-items: center;
  padding: 0.125rem 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: 9999px;
  border-width: 1px;
  border-style: solid;
}

.article-card__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: auto;
  padding-top: 0.375rem;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.dark .article-card__meta {
  color: #6b7280;
  border-top-color: rgba(255, 255, 255, 0.05);
}

.article-card__meta-date {
  white-space: nowrap;
}

.article-card__meta-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.article-card__meta-item {
  display: flex;
  align-items: center;
  gap: 0.125rem;
}

.article-card__meta-btn {
  cursor: pointer;
  background: transparent;
  border: none;
  padding: 0;
  transition: color 0.3s ease;
}

.article-card__meta-btn:hover {
  color: #00d4ff;
}

.article-card__meta-btn--liked {
  color: #ef4444;
}

.article-card__meta-btn--liked:hover {
  color: #ef4444;
}
</style>
