<script setup lang="ts">
defineProps<{
  showFeatured?: boolean
  articleCount?: number
}>()
</script>

<template>
  <div class="flex flex-col lg:flex-row gap-6">
    <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
      <div class="lg:sticky lg:top-20">
        <div class="glass-card p-3 animate-pulse">
          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16 mb-3" />
          <div class="space-y-2">
            <div
              v-for="i in 4"
              :key="i"
              class="flex items-center gap-2"
            >
              <div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-dark-300" />
              <div class="flex-1">
                <div class="h-2 bg-gray-200 dark:bg-dark-300 rounded w-20" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <main class="flex-1 min-w-0 lg:order-2">
      <section
        v-if="showFeatured"
        class="mb-6"
      >
        <div class="glass-card overflow-hidden">
          <div class="relative h-48 sm:h-56 md:h-64 lg:h-72 xl:h-80 bg-gray-200 dark:bg-dark-300 animate-pulse" />
          <div class="flex items-center justify-between px-2 py-1 border-t border-gray-100 dark:border-white/5">
            <div class="flex gap-1">
              <div
                v-for="i in 5"
                :key="i"
                class="h-1 w-1 rounded-full bg-gray-300 dark:bg-gray-600"
              />
            </div>
          </div>
        </div>
      </section>

      <div class="flex items-center justify-between mb-6">
        <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-24 animate-pulse" />
        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-16 animate-pulse" />
      </div>

      <div class="space-y-4">
        <article
          v-for="i in (articleCount || 6)"
          :key="i"
          class="glass-card p-2 animate-pulse"
        >
          <div class="flex flex-col sm:flex-row gap-4">
            <div class="w-full sm:w-56 md:w-64 h-40 sm:h-32 bg-gray-200 dark:bg-dark-300 rounded-lg" />
            <div class="flex-1 py-2">
              <div class="flex items-center gap-2 mb-2">
                <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-12" />
              </div>
              <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-3/4 mb-2" />
              <div class="space-y-1.5 mb-3">
                <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
              </div>
              <div class="flex gap-1 mb-3">
                <div
                  v-for="t in 3"
                  :key="t"
                  class="h-5 bg-gray-200 dark:bg-dark-300 rounded-full w-14"
                />
              </div>
              <div class="flex items-center gap-3">
                <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
              </div>
            </div>
          </div>
        </article>
      </div>
    </main>
    
    <div class="lg:w-80 flex-shrink-0 hidden lg:block lg:order-3">
      <div class="lg:sticky lg:top-20 space-y-6">
        <div class="glass-card p-3 animate-pulse">
          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12 mb-3" />
          <div class="grid grid-cols-2 gap-2">
            <div
              v-for="i in 4"
              :key="i"
              class="text-center p-2 bg-gray-100 dark:bg-dark-300/50 rounded-lg"
            >
              <div class="w-4 h-4 mx-auto mb-0.5 rounded-full bg-gray-200 dark:bg-dark-300" />
              <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto" />
              <div class="h-2 bg-gray-200 dark:bg-dark-300 rounded w-6 mx-auto mt-0.5" />
            </div>
          </div>
        </div>
        <div class="glass-card p-3 animate-pulse">
          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16 mb-3" />
          <div class="space-y-1.5">
            <div
              v-for="i in 5"
              :key="i"
              class="h-6 bg-gray-200 dark:bg-dark-300 rounded"
            />
          </div>
        </div>
        <div class="glass-card p-3 animate-pulse">
          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12 mb-3" />
          <div class="flex flex-wrap gap-1">
            <div
              v-for="i in 8"
              :key="i"
              class="h-5 bg-gray-200 dark:bg-dark-300 rounded-full w-14"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
