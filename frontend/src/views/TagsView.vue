<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useBlogStore } from '@/stores'

const blogStore = useBlogStore()
const hoveredTag = ref<number | null>(null)

onMounted(() => {
  blogStore.fetchTags()
})

const sortedTags = computed(() => {
  return [...blogStore.tags].sort((a, b) => b.article_count - a.article_count)
})

const maxCount = computed(() => {
  return Math.max(...blogStore.tags.map(t => t.article_count), 1)
})

const getTagStyle = (tag: { article_count: number; color: string }) => {
  const ratio = tag.article_count / maxCount.value
  const scale = 0.8 + ratio * 0.4
  return {
    transform: `scale(${hoveredTag.value === null ? scale : hoveredTag.value === tag.article_count ? 1.2 : scale * 0.9})`,
    color: tag.color,
    borderColor: tag.color,
    textShadow: `0 0 10px ${tag.color}40`
  }
}
</script>

<template>
  <div class="pb-16 min-h-screen">
    <div class="container mx-auto px-4">
      <div class="text-center mb-8">
        <h1 class="text-2xl md:text-3xl font-bold mb-1">
          <span class="gradient-text">标签云</span>
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">探索不同技术标签</p>
      </div>

      <div class="flex flex-wrap justify-center gap-4 max-w-5xl mx-auto">
        <router-link
          v-for="tag in sortedTags"
          :key="tag.id"
          :to="`/tags/${tag.slug}`"
          class="px-5 py-2 rounded-full border-2 transition-all duration-300 hover:shadow-lg"
          :style="getTagStyle(tag)"
          @mouseenter="hoveredTag = tag.article_count"
          @mouseleave="hoveredTag = null"
        >
          <span class="font-medium">{{ tag.name }}</span>
          <span class="ml-2 text-sm opacity-70">{{ tag.article_count }}</span>
        </router-link>
      </div>

      <div class="mt-16 max-w-4xl mx-auto">
        <h2 class="text-lg md:text-xl font-bold text-center mb-8">
          <span class="gradient-text">热门标签</span>
        </h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <router-link
            v-for="tag in sortedTags.slice(0, 8)"
            :key="tag.id"
            :to="`/tags/${tag.slug}`"
            class="glass-card-hover p-4 text-center"
          >
            <div class="text-2xl font-bold mb-1" :style="{ color: tag.color }">
              {{ tag.article_count }}
            </div>
            <div class="text-gray-400">{{ tag.name }}</div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
