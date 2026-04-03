<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBlogStore } from '@/stores'
import ArticleCard from '@/components/home/ArticleCard.vue'
import Pagination from '@/components/common/Pagination.vue'
import { usePageSize } from '@/composables/usePageSize'

const route = useRoute()
const router = useRouter()
const blogStore = useBlogStore()
const loading = ref(true)
const articlesRef = ref<HTMLElement | null>(null)

const { pageSize } = usePageSize()

const smoothScrollTo = (targetY: number) => {
  requestAnimationFrame(() => {
    window.scrollTo({
      top: targetY,
      behavior: 'smooth'
    })
  })
}

const scrollToArticles = () => {
  requestAnimationFrame(() => {
    if (articlesRef.value) {
      const element = articlesRef.value
      const offset = 85
      const elementPosition = element.getBoundingClientRect().top
      const offsetPosition = elementPosition + window.pageYOffset - offset
      
      smoothScrollTo(offsetPosition)
    }
  })
}

const restoreScrollPosition = () => {
  const savedPosition = sessionStorage.getItem('scrollPosition')
  if (savedPosition) {
    const scrollY = parseInt(savedPosition)
    sessionStorage.removeItem('scrollPosition')
    
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        smoothScrollTo(scrollY)
      })
    })
    
    return true
  }
  return false
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
    
    if (shouldScroll) {
      scrollToArticles()
    }
  }
  loading.value = false
}

watch(pageSize, async (newSize, oldSize) => {
  if (newSize !== oldSize) {
    const currentPage = parseInt(route.query.page as string) || 1
    
    await fetchArticles(currentPage, false, false)
    
    const totalPages = blogStore.pagination.totalPages
    if (currentPage > totalPages && totalPages > 0) {
      const newPage = totalPages
      await fetchArticles(newPage, true, false)
    }
  }
})

watch(() => route.params.slug, () => {
  fetchArticles(1, true, false)
})

onMounted(async () => {
  const pageFromUrl = parseInt(route.query.page as string) || 1
  const isReturningFromArticle = sessionStorage.getItem('returningFromArticle') === 'true'
  
  await blogStore.fetchTags()
  await fetchArticles(pageFromUrl, false, false)
  
  if (isReturningFromArticle) {
    const restored = restoreScrollPosition()
    if (!restored && pageFromUrl > 1) {
      scrollToArticles()
    }
    sessionStorage.removeItem('returningFromArticle')
  }
})

const currentTag = () => {
  const slug = route.params.slug as string
  return blogStore.getTagBySlug(slug)
}

const handlePageChange = (page: number) => {
  fetchArticles(page, true, true)
}
</script>

<template>
  <div class="pb-20">
    <div class="container mx-auto px-4">
      <div class="text-center mb-12">
        <h1 class="text-4xl md:text-5xl font-bold mb-4">
          <span :style="{ color: currentTag()?.color }">#{{ currentTag()?.name || '标签文章' }}</span>
        </h1>
        <p class="text-gray-400 text-lg">
          共 {{ blogStore.pagination.total }} 篇相关文章
        </p>
      </div>

      <div v-if="loading" class="flex justify-center py-20">
        <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>

      <div v-else-if="blogStore.articles.length === 0" class="text-center py-20">
        <p class="text-gray-400 text-lg">暂无文章</p>
      </div>

      <div v-else ref="articlesRef" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
        <ArticleCard
          v-for="article in blogStore.articles"
          :key="article.id"
          :article="article"
        />
      </div>

      <div v-if="blogStore.pagination.totalPages > 1" class="mt-8">
        <Pagination
          :current-page="blogStore.pagination.page"
          :total-pages="blogStore.pagination.totalPages"
          :total-items="blogStore.pagination.total"
          :page-size="pageSize"
          @page-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>
