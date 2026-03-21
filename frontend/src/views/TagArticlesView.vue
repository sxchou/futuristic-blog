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
  const tag = blogStore.getTagBySlug(slug)
  if (tag) {
    await blogStore.fetchArticles({ tag_id: tag.id })
  }
  loading.value = false
}

watch(() => route.params.slug, fetchArticles)

onMounted(() => {
  blogStore.fetchTags().then(fetchArticles)
})

const currentTag = () => {
  const slug = route.params.slug as string
  return blogStore.getTagBySlug(slug)
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
