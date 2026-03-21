<script setup lang="ts">
import { onMounted } from 'vue'
import { useBlogStore } from '@/stores'

const blogStore = useBlogStore()

onMounted(() => {
  blogStore.fetchCategories()
})
</script>

<template>
  <div class="pb-16">
    <div class="container mx-auto px-4">
      <div class="text-center mb-8">
        <h1 class="text-3xl md:text-4xl font-bold mb-2">
          <span class="gradient-text">技术领域</span>
        </h1>
        <p class="text-gray-500 dark:text-gray-400 text-base">按技术领域探索文章</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
        <router-link
          v-for="category in blogStore.categories"
          :key="category.id"
          :to="`/categories/${category.slug}`"
          class="group glass-card-hover p-8 text-center"
        >
          <div
            class="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center transition-transform group-hover:scale-110"
            :style="{ backgroundColor: `${category.color}20` }"
          >
            <svg class="w-8 h-8" :style="{ color: category.color }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
          </div>
          <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-2 group-hover:text-primary transition-colors">
            {{ category.name }}
          </h3>
          <p v-if="category.description" class="text-gray-500 dark:text-gray-400 text-sm mb-4">
            {{ category.description }}
          </p>
          <div class="text-sm" :style="{ color: category.color }">
            {{ category.article_count }} 篇文章
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>
