<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { resourceApi } from '@/api'
import { isCancelError } from '@/utils/error'
import { dataPrefetch } from '@/utils/prefetch'
import type { Resource } from '@/types'
import type { ResourceCategory } from '@/api/resources'
import BlogSidebar from '@/components/common/BlogSidebar.vue'
import LeftSidebar from '@/components/common/LeftSidebar.vue'

const RESOURCE_CATEGORIES: ResourceCategory[] = [
  { id: 1, name: '部署平台', slug: 'deployment-platforms', description: '应用部署与托管平台', icon: '🚀', order: 1, is_active: true },
  { id: 2, name: '常用工具', slug: 'common-tools', description: '日常开发常用工具集合', icon: '🔧', order: 2, is_active: true },
  { id: 3, name: '学习网站', slug: 'learning-sites', description: '优质学习资源网站', icon: '📚', order: 3, is_active: true },
  { id: 4, name: '开发工具', slug: 'dev-tools', description: '常用开发工具', icon: '🛠️', order: 4, is_active: true },
  { id: 5, name: '设计灵感', slug: 'design-inspiration', description: '设计参考与灵感', icon: '🎨', order: 5, is_active: true },
  { id: 6, name: 'API服务', slug: 'api-services', description: 'API接口服务', icon: '🔌', order: 6, is_active: true },
]

const resources = ref<Resource[]>([])
const categories = ref<ResourceCategory[]>(RESOURCE_CATEGORIES)
const loading = ref(true)
const activeCategory = ref<number | null>(null)

let resourcesCache: { data: Resource[]; timestamp: number } | null = null
const CACHE_TTL = 600000

const fetchResources = async (force = false) => {
  if (!force) {
    const globalCache = dataPrefetch.get<Resource[]>('resources')
    if (globalCache) {
      resources.value = globalCache
      loading.value = false
      return
    }
    
    const now = Date.now()
    if (resourcesCache && now - resourcesCache.timestamp < CACHE_TTL) {
      resources.value = resourcesCache.data
      loading.value = false
      return
    }
  }
  
  try {
    const data = await resourceApi.getResources()
    resources.value = data
    resourcesCache = { data, timestamp: Date.now() }
    dataPrefetch.set('resources', data)
  } catch (error: unknown) {
    if (isCancelError(error)) {
      return
    }
    console.error('Failed to fetch resources:', error)
  } finally {
    loading.value = false
  }
}

const getCategoryIcon = (categoryId?: number | null) => {
  if (!categoryId) return null
  const category = categories.value.find(c => c.id === categoryId)
  return category?.icon || null
}

const filteredResources = computed(() => {
  if (activeCategory.value === null) {
    return resources.value
  }
  return resources.value.filter(r => r.category_id === activeCategory.value)
})

const groupedResources = computed(() => {
  const groups: Array<{ categoryName: string; categoryId: number | null; resources: Resource[] }> = []
  const categoryMap = new Map<number | null, Resource[]>()
  
  filteredResources.value.forEach(r => {
    const catId = r.category_id ?? null
    if (!categoryMap.has(catId)) {
      categoryMap.set(catId, [])
    }
    categoryMap.get(catId)!.push(r)
  })
  
  activeCategories.value.forEach(category => {
    const resources = categoryMap.get(category.id ?? null)
    if (resources && resources.length > 0) {
      groups.push({
        categoryName: category.name,
        categoryId: category.id ?? null,
        resources
      })
    }
  })
  
  const uncategorized = categoryMap.get(null)
  if (uncategorized && uncategorized.length > 0) {
    groups.push({
      categoryName: '未分类',
      categoryId: null,
      resources: uncategorized
    })
  }
  
  return groups
})

const activeCategories = computed(() => categories.value)

onMounted(async () => {
  await fetchResources()
})
</script>

<template>
  <div class="flex flex-col lg:flex-row gap-6">
    <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
      <div class="lg:sticky lg:top-20">
        <LeftSidebar />
      </div>
    </div>
    
    <main class="flex-1 min-w-0 lg:order-2">
      <div class="pb-16">
        <div class="mb-8">
          <h1 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2">
            资源导航
          </h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            精选优质开发资源，助力技术成长
          </p>
        </div>

        <div class="flex flex-wrap justify-center gap-2 mb-8 min-h-[40px]">
          <button
            class="px-3 py-1.5 text-sm rounded-full border transition-all duration-300 flex items-center gap-1.5"
              :class="activeCategory === null
                ? 'bg-primary/20 border-primary text-primary'
                : 'bg-gray-100 dark:bg-dark-100/50 border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 hover:border-primary/50'"
              @click="activeCategory = null"
            >
              <svg
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 6h16M4 10h16M4 14h16M4 18h16"
                />
              </svg>
              全部
            </button>
            <button
              v-for="category in activeCategories"
              :key="category.id"
              class="px-3 py-1.5 text-sm rounded-full border transition-all duration-300 flex items-center gap-1.5"
              :class="activeCategory === category.id
                ? 'bg-primary/20 border-primary text-primary'
                : 'bg-gray-100 dark:bg-dark-100/50 border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 hover:border-primary/50'"
              @click="activeCategory = activeCategory === category.id ? null : category.id"
            >
              <span v-if="category.icon">{{ category.icon }}</span>
              <svg
                v-else
                class="w-4 h-4"
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
              {{ category.name }}
            </button>
        </div>

        <div
          class="space-y-10"
        >
          <div
            v-for="group in groupedResources"
            :key="`category-${group.categoryId}`"
          >
            <h2 class="text-lg md:text-xl font-bold text-gray-900 dark:text-white mb-5 flex items-center gap-3">
              <span class="w-9 h-9 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                <span
                  v-if="getCategoryIcon(group.categoryId)"
                  class="text-lg"
                >{{ getCategoryIcon(group.categoryId) }}</span>
                <svg
                  v-else
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
              {{ group.categoryName }}
            </h2>
            
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <a
                v-for="resource in group.resources"
                :key="resource.id"
                :href="resource.url"
                target="_blank"
                class="glass-card-hover p-5 group"
              >
                <div class="flex items-start gap-3">
                  <div class="w-11 h-11 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
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
                    class="w-5 h-5 text-gray-400 dark:text-gray-500 group-hover:text-primary group-hover:translate-x-1 transition-all flex-shrink-0"
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
          
          <div
            v-if="groupedResources.length === 0"
            class="text-center py-16 text-gray-500 dark:text-gray-400"
          >
            <svg
              class="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600"
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
            <p class="text-lg">暂无资源</p>
          </div>
        </div>
      </div>
    </main>
    
    <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
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
