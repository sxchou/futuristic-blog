<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { resourceApi, resourceCategoryApi } from '@/api'
import type { Resource } from '@/types'
import type { ResourceCategory } from '@/api/resourceCategories'

const resources = ref<Resource[]>([])
const categories = ref<ResourceCategory[]>([])
const loading = ref(true)
const activeCategory = ref<number | null>(null)

const fetchCategories = async () => {
  try {
    categories.value = await resourceCategoryApi.getCategories()
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

const fetchResources = async () => {
  try {
    resources.value = await resourceApi.getResources()
  } catch (error) {
    console.error('Failed to fetch resources:', error)
  } finally {
    loading.value = false
  }
}

const getCategoryName = (categoryId?: number | null) => {
  if (!categoryId) return '未分类'
  const category = categories.value.find(c => c.id === categoryId)
  return category ? category.name : '未分类'
}

const filteredResources = computed(() => {
  if (activeCategory.value === null) {
    return resources.value
  }
  return resources.value.filter(r => r.category_id === activeCategory.value)
})

const groupedResources = computed(() => {
  const groups: Record<string, Resource[]> = {}
  filteredResources.value.forEach(r => {
    const catName = getCategoryName(r.category_id)
    if (!groups[catName]) {
      groups[catName] = []
    }
    groups[catName].push(r)
  })
  return groups
})

const activeCategories = computed(() => categories.value.filter(c => c.is_active))

onMounted(async () => {
  await Promise.all([fetchCategories(), fetchResources()])
})
</script>

<template>
  <div class="pb-16">
    <div class="blog-container">
      <div class="text-center mb-8">
        <h1 class="text-2xl md:text-3xl font-bold mb-1">
          <span class="gradient-text">资源导航</span>
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          精选优质开发资源，助力技术成长
        </p>
      </div>

      <div class="flex flex-wrap justify-center gap-3 mb-12">
        <button
          class="px-4 py-2 rounded-full border transition-all duration-300"
          :class="activeCategory === null
            ? 'bg-primary/20 border-primary text-primary'
            : 'bg-gray-100 dark:bg-dark-100/50 border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 hover:border-primary/50'"
          @click="activeCategory = null"
        >
          全部
        </button>
        <button
          v-for="category in activeCategories"
          :key="category.id"
          class="px-4 py-2 rounded-full border transition-all duration-300"
          :class="activeCategory === category.id
            ? 'bg-primary/20 border-primary text-primary'
            : 'bg-gray-100 dark:bg-dark-100/50 border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 hover:border-primary/50'"
          @click="activeCategory = category.id"
        >
          {{ category.name }}
        </button>
      </div>

      <div
        v-if="loading"
        class="flex justify-center py-20"
      >
        <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>

      <div
        v-else
        class="max-w-6xl mx-auto space-y-12"
      >
        <div
          v-for="(items, category) in groupedResources"
          :key="category"
        >
          <h2 class="text-xl md:text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-3">
            <span class="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
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
                  d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                />
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
                <div class="w-12 h-12 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                  <span
                    v-if="resource.icon"
                    class="text-xl"
                  >{{ resource.icon }}</span>
                  <svg
                    v-else
                    class="w-6 h-6 text-primary"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                    />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-1 group-hover:text-primary transition-colors">
                    {{ resource.title }}
                  </h3>
                  <p
                    v-if="resource.description"
                    class="text-gray-500 dark:text-gray-400 text-sm line-clamp-2"
                  >
                    {{ resource.description }}
                  </p>
                </div>
                <svg
                  class="w-5 h-5 text-gray-400 dark:text-gray-500 group-hover:text-primary group-hover:translate-x-1 transition-all"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
