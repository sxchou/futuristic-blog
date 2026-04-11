<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBlogStore } from '@/stores'
import BlogSidebar from '@/components/common/BlogSidebar.vue'
import Pagination from '@/components/common/Pagination.vue'
import { usePageSize } from '@/composables/usePageSize'
import { getMediaUrl } from '@/utils/media'

const route = useRoute()
const router = useRouter()
const blogStore = useBlogStore()
const loading = ref(true)
const articlesRef = ref<HTMLElement | null>(null)

const { pageSize } = usePageSize()

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
  const tag = blogStore.getTagBySlug(slug)
  if (tag) {
    await blogStore.fetchArticles({
      tag_id: tag.id,
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

onMounted(async () => {
  const pageFromUrl = parseInt(route.query.page as string) || 1
  await blogStore.fetchTags()
  await fetchArticles(pageFromUrl, false, false)
})

const currentTag = () => {
  const slug = route.params.slug as string
  return blogStore.getTagBySlug(slug)
}

const handlePageChange = (page: number) => {
  fetchArticles(page, true, true)
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
  <div class="flex flex-col lg:flex-row gap-8">
    <div class="flex-1 min-w-0">
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
        <p class="text-sm text-gray-400 mt-2">
          共 {{ blogStore.pagination.total }} 篇相关文章
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
        <router-link
          v-for="article in blogStore.articles"
          :key="article.id"
          :to="`/article/${article.slug}`"
          class="article-card group flex flex-col sm:flex-row gap-4"
        >
          <div
            v-if="article.cover_image"
            class="relative flex-shrink-0 overflow-hidden rounded-xl h-32 sm:w-40 sm:h-24"
          >
            <img
                :src="getMediaUrl(article.cover_image)"
                :alt="article.title"
                class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              >
          </div>
          <div class="flex-1 min-w-0 flex flex-col">
            <h3 class="article-card-title">
              {{ article.title }}
            </h3>
            <p
              v-if="article.summary"
              class="article-card-excerpt"
            >
              {{ article.summary }}
            </p>
            <div class="flex items-center gap-3 mt-auto pt-2">
              <span
                v-if="article.category"
                class="inline-flex items-center gap-1 text-xs font-medium"
                :style="{ color: article.category.color }"
              >
                <span
                  class="w-1.5 h-1.5 rounded-full"
                  :style="{ backgroundColor: article.category.color }"
                />
                {{ article.category.name }}
              </span>
              <span class="text-xs text-gray-400">{{ formatDate(article.created_at) }}</span>
              <span class="text-xs text-gray-400 flex items-center gap-1">
                <svg
                  class="w-3 h-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                /></svg>
                {{ article.view_count }}
              </span>
            </div>
          </div>
        </router-link>
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

    <div class="lg:w-80 xl:w-84 flex-shrink-0">
      <div class="lg:sticky lg:top-20">
        <BlogSidebar />
      </div>
    </div>
  </div>
</template>
