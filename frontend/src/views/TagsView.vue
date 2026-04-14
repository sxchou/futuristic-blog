<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useBlogStore } from '@/stores'
import BlogSidebar from '@/components/common/BlogSidebar.vue'
import LeftSidebar from '@/components/common/LeftSidebar.vue'

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

const getTagSize = (count: number) => {
  const ratio = count / maxCount.value
  if (ratio > 0.7) return 'text-xl font-bold'
  if (ratio > 0.4) return 'text-base font-semibold'
  return 'text-sm font-medium'
}
</script>

<template>
  <div class="flex flex-col lg:flex-row gap-6">
    <div class="lg:w-56 flex-shrink-0 hidden lg:block lg:order-1">
      <div class="lg:sticky lg:top-20">
        <LeftSidebar />
      </div>
    </div>
    
    <div class="flex-1 min-w-0 lg:order-2">
      <div class="mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2">
          标签云
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          探索不同技术标签
        </p>
      </div>

      <div class="glass-card p-6 mb-8">
        <div class="flex flex-wrap gap-3">
          <router-link
            v-for="tag in sortedTags"
            :key="tag.id"
            :to="`/tags/${tag.slug}`"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border transition-all duration-300 hover:shadow-md"
            :class="getTagSize(tag.article_count)"
            :style="{
              color: tag.color,
              borderColor: tag.color + '40',
              backgroundColor: tag.color + '10',
              textShadow: hoveredTag === tag.id ? `0 0 8px ${tag.color}40` : 'none'
            }"
            @mouseenter="hoveredTag = tag.id"
            @mouseleave="hoveredTag = null"
          >
            #{{ tag.name }}
            <span class="text-xs opacity-60">{{ tag.article_count }}</span>
          </router-link>
        </div>
      </div>

      <div class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <svg
            class="w-5 h-5 text-primary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"
            />
          </svg>
          热门标签
        </h2>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <router-link
            v-for="tag in sortedTags.slice(0, 8)"
            :key="tag.id"
            :to="`/tags/${tag.slug}`"
            class="glass-card-hover p-4 text-center group"
          >
            <div
              class="text-2xl font-bold mb-1 transition-colors"
              :style="{ color: tag.color }"
            >
              {{ tag.article_count }}
            </div>
            <div class="text-sm text-gray-500 dark:text-gray-400 group-hover:text-primary transition-colors">
              #{{ tag.name }}
            </div>
          </router-link>
        </div>
      </div>

      <div
        v-if="blogStore.tags.length === 0"
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
            d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
          />
        </svg>
        <p class="text-gray-400">
          暂无标签
        </p>
      </div>
    </div>

    <div class="lg:w-56 flex-shrink-0 hidden lg:block lg:order-3">
      <div class="lg:sticky lg:top-20">
        <BlogSidebar />
      </div>
    </div>

    <aside class="lg:hidden mt-8 space-y-4" aria-label="侧边栏内容">
      <LeftSidebar />
      <BlogSidebar />
    </aside>
  </div>
</template>
