<script setup lang="ts">
import { onMounted } from 'vue'
import { useBlogStore } from '@/stores'
import BlogSidebar from '@/components/common/BlogSidebar.vue'
import LeftSidebar from '@/components/common/LeftSidebar.vue'

const blogStore = useBlogStore()

onMounted(() => {
  blogStore.fetchCategories()
})
</script>

<template>
  <div class="flex flex-col lg:flex-row gap-6">
    <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
      <div class="lg:sticky lg:top-20">
        <LeftSidebar />
      </div>
    </div>
    
    <div class="flex-1 min-w-0 lg:order-2">
      <div class="mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2">
          分类目录
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          按技术领域探索文章
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <router-link
          v-for="category in blogStore.categories"
          :key="category.id"
          :to="`/categories/${category.slug}`"
          class="group glass-card-hover p-5 flex items-start gap-4"
        >
          <div
            class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 transition-transform group-hover:scale-110"
            :style="{ backgroundColor: category.color + '15' }"
          >
            <svg
              class="w-6 h-6"
              :style="{ color: category.color }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
              />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="text-base font-bold text-gray-900 dark:text-white mb-1 group-hover:text-primary transition-colors">
              {{ category.name }}
            </h3>
            <p
              v-if="category.description"
              class="text-gray-500 dark:text-gray-400 text-sm mb-2 line-clamp-2"
            >
              {{ category.description }}
            </p>
            <span
              class="text-xs font-medium"
              :style="{ color: category.color }"
            >
              {{ category.article_count }} 篇文章
            </span>
          </div>
          <svg
            class="w-5 h-5 text-gray-300 dark:text-gray-600 group-hover:text-primary group-hover:translate-x-0.5 transition-all flex-shrink-0 mt-1"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5l7 7-7 7"
            />
          </svg>
        </router-link>
      </div>

      <div
        v-if="blogStore.categories.length === 0"
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
          暂无分类
        </p>
      </div>
    </div>

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
