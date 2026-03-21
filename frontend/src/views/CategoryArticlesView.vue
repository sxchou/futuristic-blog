<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useBlogStore } from '@/stores'
import ArticleCard from '@/components/home/ArticleCard.vue'

const route = useRoute()
const blogStore = useBlogStore()
const loading = ref(true)

const fetchArticles = async () => {
  loading.value = true
  const slug = route.params.slug as string
  const category = blogStore.getCategoryBySlug(slug)
  if (category) {
    await blogStore.fetchArticles({ category_id: category.id })
  }
  loading.value = false
}

watch(() => route.params.slug, fetchArticles)

onMounted(() => {
  blogStore.fetchCategories().then(fetchArticles)
})

const currentCategory = () => {
  const slug = route.params.slug as string
  return blogStore.getCategoryBySlug(slug)
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

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
        <ArticleCard
          v-for="article in blogStore.articles"
          :key="article.id"
          :article="article"
        />
      </div>
    </div>
  </div>
</template>
