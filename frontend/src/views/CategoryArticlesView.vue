<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useBlogStore } from '@/stores'
import ArticleCard from '@/components/home/ArticleCard.vue'
import Pagination from '@/components/common/Pagination.vue'
import { usePageSize } from '@/composables/usePageSize'

const route = useRoute()
const blogStore = useBlogStore()
const loading = ref(true)
const articlesRef = ref<HTMLElement | null>(null)

const { pageSize } = usePageSize()

const fetchArticles = async (page: number = 1) => {
  loading.value = true
  const slug = route.params.slug as string
  const category = blogStore.getCategoryBySlug(slug)
  if (category) {
    await blogStore.fetchArticles({ 
      category_id: category.id,
      page: page,
      page_size: pageSize.value
    })
  }
  loading.value = false
}

watch(pageSize, (newSize, oldSize) => {
  if (newSize !== oldSize) {
    fetchArticles(1)
  }
})

watch(() => route.params.slug, () => {
  fetchArticles(1)
})

onMounted(() => {
  blogStore.fetchCategories().then(() => fetchArticles(1))
})

const currentCategory = () => {
  const slug = route.params.slug as string
  return blogStore.getCategoryBySlug(slug)
}

const handlePageChange = (page: number) => {
  fetchArticles(page)
  
  if (articlesRef.value) {
    const element = articlesRef.value
    const offset = 85
    const elementPosition = element.getBoundingClientRect().top
    const offsetPosition = elementPosition + window.pageYOffset - offset
    
    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    })
  }
}
</script>

<template>
  <div class="pb-20">
    <div class="container mx-auto px-4">
      <div class="text-center mb-12">
        <h1 class="text-4xl md:text-5xl font-bold mb-4">
          <span class="gradient-text">{{ currentCategory()?.name || '分类文章' }}</span>
        </h1>
        <p v-if="currentCategory()?.description" class="text-gray-400 text-lg">
          {{ currentCategory()?.description }}
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
