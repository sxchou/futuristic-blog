<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { resourceApi } from '@/api'
import type { Resource } from '@/types'

const resources = ref<Resource[]>([])
const loading = ref(true)
const activeCategory = ref('全部')

const categories = computed(() => {
  const cats = new Set(resources.value.map(r => r.category))
  return ['全部', ...cats]
})

const filteredResources = computed(() => {
  if (activeCategory.value === '全部') {
    return resources.value
  }
  return resources.value.filter(r => r.category === activeCategory.value)
})

const groupedResources = computed(() => {
  const groups: Record<string, Resource[]> = {}
  filteredResources.value.forEach(r => {
    if (!groups[r.category]) {
      groups[r.category] = []
    }
    groups[r.category].push(r)
  })
  return groups
})

const categoryIcons: Record<string, string> = {
  '学习网站': 'book',
  '开发工具': 'code',
  '设计灵感': 'palette',
  'API服务': 'api'
}

onMounted(async () => {
  try {
    resources.value = await resourceApi.getResources()
  } catch (error) {
    console.error('Failed to fetch resources:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="pb-16">
    <div class="container mx-auto px-4">
      <div class="text-center mb-8">
        <h1 class="text-3xl md:text-4xl font-bold mb-2">
          <span class="gradient-text">资源导航</span>
        </h1>
        <p class="text-gray-500 dark:text-gray-400 text-base">精选优质开发资源，助力技术成长</p>
      </div>

      <div class="flex flex-wrap justify-center gap-3 mb-12">
        <button
          v-for="category in categories"
          :key="category"
          @click="activeCategory = category"
          class="px-4 py-2 rounded-full border transition-all duration-300"
          :class="activeCategory === category
            ? 'bg-primary/20 border-primary text-primary'
            : 'bg-gray-100 dark:bg-dark-100/50 border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 hover:border-primary/50'"
        >
          {{ category }}
        </button>
      </div>

      <div v-if="loading" class="flex justify-center py-20">
        <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>

      <div v-else class="max-w-6xl mx-auto space-y-12">
        <div v-for="(items, category) in groupedResources" :key="category">
          <h2 class="text-xl md:text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-3">
            <span class="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
              <svg v-if="categoryIcons[category] === 'book'" class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <svg v-else-if="categoryIcons[category] === 'code'" class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              <svg v-else-if="categoryIcons[category] === 'palette'" class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
              </svg>
              <svg v-else class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </span>
            {{ category }}
          </h2>
          
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <a
              v-for="resource in items"
              :key="resource.id"
              :href="resource.url"
              target="_blank"
              class="glass-card-hover p-6 group"
            >
              <div class="flex items-start gap-4">
                <div class="w-12 h-12 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                  <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-1 group-hover:text-primary transition-colors">
                    {{ resource.title }}
                  </h3>
                  <p v-if="resource.description" class="text-gray-500 dark:text-gray-400 text-sm line-clamp-2">
                    {{ resource.description }}
                  </p>
                </div>
                <svg class="w-5 h-5 text-gray-400 dark:text-gray-500 group-hover:text-primary group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
