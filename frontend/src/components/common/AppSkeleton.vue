<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const skeletonType = computed(() => {
  const path = route.path
  if (path.startsWith('/article/')) return 'article'
  if (path === '/resources') return 'resources'
  if (path === '/tags') return 'tags'
  if (path === '/categories') return 'categories'
  if (path === '/archive') return 'archive'
  if (path === '/about') return 'about'
  if (path === '/links') return 'links'
  if (path === '/profile') return 'profile'
  if (path === '/search') return 'search'
  if (path.startsWith('/categories/')) return 'category'
  if (path.startsWith('/tags/')) return 'tag'
  return 'home'
})
</script>

<template>
  <div class="fixed inset-0 z-[100] bg-white dark:bg-dark-100 flex flex-col overflow-hidden">
    <header class="fixed top-0 left-0 right-0 z-50 bg-white/90 dark:bg-dark-100/90 backdrop-blur-xl border-b border-gray-200/60 dark:border-white/5">
      <nav class="blog-container py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-gray-200 dark:bg-dark-300 animate-pulse" />
            <div class="h-5 w-28 bg-gray-200 dark:bg-dark-300 rounded animate-pulse" />
          </div>
          
          <div class="hidden md:flex items-center gap-1">
            <div
              v-for="i in 6"
              :key="i"
              class="h-7 w-12 bg-gray-200 dark:bg-dark-300 rounded-md animate-pulse"
            />
          </div>
          
          <div class="flex items-center gap-2">
            <div class="h-8 w-40 bg-gray-200 dark:bg-dark-300 rounded-lg animate-pulse" />
            <div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-dark-300 animate-pulse" />
          </div>
        </div>
      </nav>
    </header>
    
    <main class="flex-1 pt-16">
      <div class="blog-container py-8">
        <template v-if="skeletonType === 'article'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block">
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
            
            <div class="flex-1 min-w-0">
              <div class="glass-card p-6 animate-pulse">
                <div class="h-8 bg-gray-200 dark:bg-dark-300 rounded w-3/4 mb-4" />
                <div class="flex items-center gap-4 mb-6">
                  <div class="h-4 w-24 bg-gray-200 dark:bg-dark-300 rounded" />
                  <div class="h-4 w-20 bg-gray-200 dark:bg-dark-300 rounded" />
                  <div class="h-4 w-16 bg-gray-200 dark:bg-dark-300 rounded" />
                </div>
                <div class="h-64 bg-gray-200 dark:bg-dark-300 rounded-lg mb-6" />
                <div class="space-y-3">
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-4/5" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="glass-card p-3 animate-pulse">
                  <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12 mb-3" />
                  <div class="space-y-2">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="h-6 bg-gray-200 dark:bg-dark-300 rounded"
                    />
                  </div>
                </div>
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
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'resources'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block">
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
            
            <div class="flex-1 min-w-0">
              <div class="mb-8">
                <div class="h-8 bg-gray-200 dark:bg-dark-300 rounded w-32 mb-2" />
                <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-48" />
              </div>
              <div class="flex flex-wrap justify-center gap-2 mb-8">
                <div
                  v-for="i in 5"
                  :key="i"
                  class="px-3 py-1.5 rounded-full border bg-gray-100 dark:bg-dark-100/50 border-gray-200 dark:border-white/10 animate-pulse"
                >
                  <span class="inline-block w-12 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                </div>
              </div>
              <div class="space-y-8">
                <div
                  v-for="i in 2"
                  :key="i"
                  class="animate-pulse"
                >
                  <div class="h-6 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-4" />
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div
                      v-for="j in 4"
                      :key="j"
                      class="glass-card p-4"
                    >
                      <div class="flex items-start gap-3">
                        <div class="w-10 h-10 rounded-lg bg-gray-200 dark:bg-dark-300" />
                        <div class="flex-1">
                          <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-3/4 mb-2" />
                          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-80 flex-shrink-0 hidden lg:block">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="glass-card p-3 animate-pulse">
                  <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12 mb-3" />
                  <div class="space-y-1.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="h-6 bg-gray-200 dark:bg-dark-300 rounded"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'tags' || skeletonType === 'categories'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block">
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
            
            <div class="flex-1 min-w-0">
              <div class="mb-6">
                <div class="h-8 bg-gray-200 dark:bg-dark-300 rounded w-20 mb-2" />
                <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-32" />
              </div>
              <div class="flex flex-wrap gap-3">
                <div
                  v-for="i in 12"
                  :key="i"
                  class="px-4 py-2 rounded-lg bg-gray-100 dark:bg-dark-200 animate-pulse"
                >
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                </div>
              </div>
            </div>
            
            <div class="lg:w-80 flex-shrink-0 hidden lg:block">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="glass-card p-3 animate-pulse">
                  <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12 mb-3" />
                  <div class="space-y-1.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="h-6 bg-gray-200 dark:bg-dark-300 rounded"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'archive'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block">
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
            
            <div class="flex-1 min-w-0">
              <div class="mb-6">
                <div class="h-8 bg-gray-200 dark:bg-dark-300 rounded w-20 mb-2" />
                <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-48" />
              </div>
              <div class="space-y-6">
                <div
                  v-for="i in 3"
                  :key="i"
                  class="animate-pulse"
                >
                  <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-3" />
                  <div class="space-y-2 ml-4">
                    <div
                      v-for="j in 4"
                      :key="j"
                      class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-3/4"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-80 flex-shrink-0 hidden lg:block">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="glass-card p-3 animate-pulse">
                  <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12 mb-3" />
                  <div class="space-y-1.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="h-6 bg-gray-200 dark:bg-dark-300 rounded"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'about' || skeletonType === 'links'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block">
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
            
            <div class="flex-1 min-w-0">
              <div class="glass-card p-6 animate-pulse">
                <div class="h-8 bg-gray-200 dark:bg-dark-300 rounded w-32 mb-6" />
                <div class="space-y-4">
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-4/5" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                </div>
              </div>
            </div>
            
            <div class="lg:w-80 flex-shrink-0 hidden lg:block">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="glass-card p-3 animate-pulse">
                  <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12 mb-3" />
                  <div class="space-y-1.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="h-6 bg-gray-200 dark:bg-dark-300 rounded"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'profile'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block">
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
            
            <div class="flex-1 min-w-0">
              <div class="glass-card p-2 mb-6 animate-pulse">
                <div class="flex items-center gap-4 mb-2">
                  <div class="w-12 h-12 rounded-full bg-gray-200 dark:bg-dark-300" />
                  <div class="flex-1">
                    <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-1" />
                    <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-40" />
                  </div>
                  <div class="h-8 w-16 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                </div>
                <div class="flex border-t border-gray-200 dark:border-white/10 pt-2">
                  <div
                    v-for="i in 3"
                    :key="i"
                    class="flex items-center gap-2 px-4 py-2"
                  >
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </div>
                </div>
              </div>
              <div class="space-y-4">
                <div
                  v-for="i in 3"
                  :key="i"
                  class="glass-card p-4 animate-pulse"
                >
                  <div class="flex gap-4">
                    <div class="w-56 h-32 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                    <div class="flex-1 py-2">
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-3/4 mb-3" />
                      <div class="space-y-2 mb-3">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                      </div>
                      <div class="flex gap-2">
                        <div
                          v-for="t in 3"
                          :key="t"
                          class="h-5 bg-gray-200 dark:bg-dark-300 rounded-full w-14"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block">
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
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'search'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block">
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
            
            <div class="flex-1 min-w-0">
              <div class="mb-8">
                <div class="h-8 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2" />
                <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-32" />
              </div>
              <div class="mb-8">
                <div class="relative">
                  <div class="h-12 bg-gray-200 dark:bg-dark-300 rounded-xl w-full max-w-lg" />
                </div>
              </div>
              <div class="space-y-4">
                <div
                  v-for="i in 3"
                  :key="i"
                  class="glass-card p-4 animate-pulse"
                >
                  <div class="flex gap-4">
                    <div class="w-56 h-32 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                    <div class="flex-1 py-2">
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-3/4 mb-3" />
                      <div class="space-y-2 mb-3">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                      </div>
                      <div class="flex gap-2">
                        <div
                          v-for="t in 3"
                          :key="t"
                          class="h-5 bg-gray-200 dark:bg-dark-300 rounded-full w-14"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block">
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
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'category' || skeletonType === 'tag'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block">
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
            
            <div class="flex-1 min-w-0">
              <div class="mb-8">
                <div class="flex items-center gap-2 mb-2">
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                  <svg
                    class="w-4 h-4 text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  ><path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 5l7 7-7 7"
                  /></svg>
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                </div>
                <div class="flex items-center gap-3 mb-2">
                  <div class="w-10 h-10 rounded-xl bg-gray-200 dark:bg-dark-300 animate-pulse" />
                  <div class="h-8 bg-gray-200 dark:bg-dark-300 rounded w-32" />
                </div>
                <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-24" />
              </div>
              <div class="space-y-4">
                <div
                  v-for="i in 3"
                  :key="i"
                  class="glass-card p-4 animate-pulse"
                >
                  <div class="flex gap-4">
                    <div class="w-56 h-32 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                    <div class="flex-1 py-2">
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-3/4 mb-3" />
                      <div class="space-y-2 mb-3">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                      </div>
                      <div class="flex gap-2">
                        <div
                          v-for="t in 3"
                          :key="t"
                          class="h-5 bg-gray-200 dark:bg-dark-300 rounded-full w-14"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block">
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
              </div>
            </div>
          </div>
        </template>
        
        <template v-else>
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block">
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
            
            <div class="flex-1 min-w-0">
              <div class="space-y-4">
                <div
                  v-for="i in 3"
                  :key="i"
                  class="glass-card p-4 animate-pulse"
                >
                  <div class="flex gap-4">
                    <div class="w-56 h-32 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                    <div class="flex-1 py-2">
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-3/4 mb-3" />
                      <div class="space-y-2 mb-3">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                      </div>
                      <div class="flex gap-2">
                        <div
                          v-for="t in 3"
                          :key="t"
                          class="h-5 bg-gray-200 dark:bg-dark-300 rounded-full w-14"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-80 flex-shrink-0 hidden lg:block">
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
              </div>
            </div>
          </div>
        </template>
      </div>
    </main>
    
    <footer class="border-t border-gray-200/60 dark:border-white/5 bg-gray-50/50 dark:bg-dark-100/50">
      <div class="blog-container py-10">
        <div class="grid grid-cols-1 md:grid-cols-12 gap-8">
          <div class="md:col-span-5">
            <div class="flex items-center gap-2.5 mb-3">
              <div class="w-7 h-7 rounded-lg bg-gray-200 dark:bg-dark-300 animate-pulse" />
              <div class="h-4 w-24 bg-gray-200 dark:bg-dark-300 rounded animate-pulse" />
            </div>
            <div class="space-y-2 mb-4">
              <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full" />
              <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-4/5" />
            </div>
            <div class="flex gap-2">
              <div
                v-for="i in 4"
                :key="i"
                class="w-8 h-8 rounded-lg bg-gray-200 dark:bg-dark-300 animate-pulse"
              />
            </div>
          </div>
          
          <div class="md:col-span-3">
            <div class="h-4 w-12 bg-gray-200 dark:bg-dark-300 rounded mb-3 animate-pulse" />
            <div class="space-y-2">
              <div
                v-for="i in 5"
                :key="i"
                class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16"
              />
            </div>
          </div>
          
          <div class="md:col-span-4">
            <div class="h-4 w-16 bg-gray-200 dark:bg-dark-300 rounded mb-3 animate-pulse" />
            <div class="flex flex-wrap gap-1.5">
              <div
                v-for="i in 6"
                :key="i"
                class="h-5 w-14 bg-gray-200 dark:bg-dark-300 rounded-full animate-pulse"
              />
            </div>
          </div>
        </div>
        
        <div class="mt-8 pt-6 border-t border-gray-200/60 dark:border-white/5 flex flex-col sm:flex-row justify-between items-center gap-2">
          <div class="h-3 w-48 bg-gray-200 dark:bg-dark-300 rounded animate-pulse" />
          <div class="h-3 w-40 bg-gray-200 dark:bg-dark-300 rounded animate-pulse" />
        </div>
      </div>
    </footer>
  </div>
</template>
