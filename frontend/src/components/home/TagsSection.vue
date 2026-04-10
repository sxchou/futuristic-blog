<script setup lang="ts">
import { computed } from 'vue'
import { useBlogStore } from '@/stores'

const blogStore = useBlogStore()

const sortedTags = computed(() => {
  return [...blogStore.tags].sort((a, b) => b.article_count - a.article_count)
})

const getTagSize = (count: number) => {
  const maxCount = Math.max(...blogStore.tags.map(t => t.article_count), 1)
  const ratio = count / maxCount
  return 0.8 + ratio * 0.6
}
</script>

<template>
  <section class="pb-20 relative overflow-hidden">
    <div class="absolute inset-0 bg-gradient-to-b from-gray-50 via-gray-100/50 to-gray-50 dark:from-dark-100 dark:via-dark-100/50 dark:to-dark-100" />
    
    <div class="container mx-auto px-4 relative z-10">
      <div class="text-center mb-12">
        <h2 class="text-2xl md:text-3xl font-bold mb-1">
          <span class="gradient-text">热门标签</span>
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          探索不同技术领域
        </p>
      </div>

      <div class="flex flex-wrap justify-center gap-4 max-w-4xl mx-auto">
        <router-link
          v-for="tag in sortedTags"
          :key="tag.id"
          :to="`/tags/${tag.slug}`"
          class="group relative px-4 py-2 rounded-full border transition-all duration-300 hover:scale-110 bg-white dark:bg-transparent"
          :style="{
            fontSize: `${getTagSize(tag.article_count)}rem`,
            borderColor: tag.color,
            color: tag.color
          }"
        >
          <span class="relative z-10 font-medium">{{ tag.name }}</span>
          <span
            class="absolute inset-0 rounded-full opacity-0 group-hover:opacity-20 transition-opacity"
            :style="{ backgroundColor: tag.color }"
          />
          <span
            class="absolute -top-2 -right-2 px-2 py-0.5 text-xs bg-white dark:bg-dark-100 rounded-full border shadow-sm"
            :style="{ borderColor: tag.color, color: tag.color }"
          >
            {{ tag.article_count }}
          </span>
        </router-link>
      </div>
    </div>
  </section>
</template>
