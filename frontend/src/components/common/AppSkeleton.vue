<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const currentPath = ref(window.location.pathname)

watch(
  () => route.path,
  (newPath) => {
    if (newPath && newPath !== '/') {
      currentPath.value = newPath
    }
  },
  { immediate: true }
)

const skeletonType = computed(() => {
  const path = currentPath.value
  
  if (path === '/login') return 'login'
  if (path === '/register') return 'register'
  if (path === '/forgot-password') return 'forgot-password'
  if (path === '/verify-email') return 'verify-email'
  if (path === '/pending-verification') return 'pending-verification'
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
  if (path === '/') return 'home'
  return 'other'
})
</script>

<template>
  <div class="fixed inset-0 z-[100] bg-white dark:bg-dark-100 flex flex-col overflow-hidden">
    <header class="fixed top-0 left-0 right-0 z-50 bg-white/90 dark:bg-dark-100/90 backdrop-blur-xl border-b border-gray-200/60 dark:border-white/5">
      <nav class="blog-container py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-dark-300 animate-pulse" />
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
            <div class="h-8 w-10 md:w-24 bg-gray-200 dark:bg-dark-300 rounded-lg animate-pulse" />
            <div class="w-8 h-8 rounded-lg bg-gray-200 dark:bg-dark-300 animate-pulse" />
            <div class="w-8 h-8 rounded-lg bg-gray-200 dark:bg-dark-300 animate-pulse" />
          </div>
        </div>
      </nav>
    </header>
    
    <main class="flex-1 pt-16">
      <div class="blog-container py-8">
        <template v-if="skeletonType === 'login'">
          <div class="flex items-center justify-center px-4 pb-32">
            <div class="w-full max-w-[386px]">
              <div class="glass-card p-5 animate-pulse">
                <div class="text-center mb-4">
                  <div class="w-12 h-12 mx-auto mb-2 rounded-full bg-gray-200 dark:bg-dark-300" />
                  <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-24 mx-auto mb-1" />
                  <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-20 mx-auto" />
                </div>
                <div class="space-y-3">
                  <div>
                    <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16 mb-1" />
                    <div class="h-9 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                  </div>
                  <div>
                    <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mb-1" />
                    <div class="h-9 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                  </div>
                  <div>
                    <div class="flex justify-between mb-1">
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                    </div>
                    <div class="h-10 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                  </div>
                  <div class="h-9 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                </div>
                <div class="mt-4 pt-4 border-t border-gray-200 dark:border-white/10">
                  <div class="flex items-center justify-center gap-2">
                    <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                    <div class="h-3 bg-primary/30 rounded w-10" />
                  </div>
                </div>
                <div class="mt-4 pt-4 border-t border-gray-200 dark:border-white/10">
                  <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-20 mx-auto mb-3" />
                  <div class="flex justify-center gap-3">
                    <div
                      v-for="i in 3"
                      :key="i"
                      class="w-10 h-10 rounded-lg bg-gray-200 dark:bg-dark-300"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'register'">
          <div class="flex items-center justify-center px-4 pb-32">
            <div class="w-full max-w-[386px]">
              <div class="glass-card p-5 animate-pulse">
                <div class="text-center mb-4">
                  <div class="w-12 h-12 mx-auto mb-2 rounded-full bg-gray-200 dark:bg-dark-300" />
                  <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-20 mx-auto mb-1" />
                  <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-24 mx-auto" />
                </div>
                <div class="space-y-3">
                  <div>
                    <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16 mb-1" />
                    <div class="h-9 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                  </div>
                  <div>
                    <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mb-1" />
                    <div class="h-9 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                  </div>
                  <div>
                    <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mb-1" />
                    <div class="h-9 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                  </div>
                  <div>
                    <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mb-1" />
                    <div class="h-9 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                  </div>
                  <div class="h-9 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                </div>
                <div class="mt-4 pt-4 border-t border-gray-200 dark:border-white/10">
                  <div class="flex items-center justify-center gap-2">
                    <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                    <div class="h-3 bg-primary/30 rounded w-10" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'forgot-password'">
          <div class="flex items-center justify-center px-4 pb-32">
            <div class="w-full max-w-[386px]">
              <div class="glass-card p-5 animate-pulse">
                <div class="text-center mb-4">
                  <div class="w-12 h-12 mx-auto mb-2 rounded-full bg-gray-200 dark:bg-dark-300" />
                  <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-24 mx-auto mb-1" />
                  <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-32 mx-auto" />
                </div>
                <div class="space-y-3">
                  <div>
                    <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mb-1" />
                    <div class="h-9 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                  </div>
                  <div class="h-9 bg-gray-200 dark:bg-dark-300 rounded-lg" />
                </div>
                <div class="mt-4 pt-4 border-t border-gray-200 dark:border-white/10">
                  <div class="flex items-center justify-center gap-2">
                    <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                    <div class="h-3 bg-primary/30 rounded w-10" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'verify-email' || skeletonType === 'pending-verification'">
          <div class="flex items-center justify-center px-4 pb-32">
            <div class="w-full max-w-[386px]">
              <div class="glass-card p-5 animate-pulse">
                <div class="text-center">
                  <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-200 dark:bg-dark-300" />
                  <div class="h-6 bg-gray-200 dark:bg-dark-300 rounded w-32 mx-auto mb-2" />
                  <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-48 mx-auto mb-4" />
                  <div class="h-9 bg-gray-200 dark:bg-dark-300 rounded-lg w-32 mx-auto" />
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'article'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
              <div class="lg:sticky lg:top-20">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="p-4 bg-gray-50/50 dark:bg-white/[0.02] rounded-xl">
                    <div class="flex flex-col items-center">
                      <div class="relative mb-3">
                        <div class="absolute inset-0 bg-primary/10 dark:bg-primary/20 rounded-full blur-xl opacity-60" />
                        <div class="relative w-14 h-14 rounded-full bg-gray-200 dark:bg-dark-300" />
                      </div>
                      <div class="text-center mb-3 w-full">
                        <div class="flex items-center justify-center gap-2 mb-2 flex-wrap">
                          <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded-full w-12" />
                        </div>
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-36 mx-auto" />
                      </div>
                      <div class="w-full pt-3 border-t border-gray-200/50 dark:border-white/5 flex items-center justify-between">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse mt-6">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14" />
                  </h3>
                  <div class="flex flex-col gap-3">
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    
                    <div class="mt-2 p-3 bg-gray-50 dark:bg-white/[0.02] rounded-lg border border-gray-200/60 dark:border-white/5">
                      <div class="flex items-center gap-2 mb-1.5">
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-24" />
                      </div>
                      <div class="flex items-center gap-1 flex-wrap">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="flex-1 min-w-0 lg:order-2">
              <div class="glass-card p-6 animate-pulse">
                <div class="flex items-center gap-2 mb-4">
                  <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded-full w-10" />
                  <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded-full w-10" />
                </div>
                <div class="space-y-1 mb-4">
                  <div class="h-6 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                  <div class="h-6 bg-gray-200 dark:bg-dark-300 rounded w-1/2" />
                </div>
                <div class="flex flex-wrap items-center gap-3 mb-4">
                  <div class="flex items-center gap-1.5">
                    <div class="w-4 h-4 rounded-full bg-gray-200 dark:bg-dark-300" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </div>
                  <div class="flex items-center gap-1.5">
                    <div class="w-4 h-4 rounded bg-gray-200 dark:bg-dark-300" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                  </div>
                  <div class="flex items-center gap-1.5">
                    <div class="w-4 h-4 rounded bg-gray-200 dark:bg-dark-300" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                  </div>
                  <div class="flex items-center gap-1.5">
                    <div class="w-4 h-4 rounded bg-gray-200 dark:bg-dark-300" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                  </div>
                </div>
                <div class="flex flex-wrap items-center gap-2 mb-4">
                  <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded-md w-16" />
                  <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded-full w-12" />
                  <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded-full w-14" />
                  <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded-full w-10" />
                </div>
                <div class="p-4 bg-gray-50 dark:bg-dark-200/50 rounded-xl mb-6">
                  <div class="space-y-1.5">
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                  </div>
                </div>
                <div class="h-48 sm:h-64 bg-gray-200 dark:bg-dark-300 rounded-lg mb-6" />
                <div class="space-y-3">
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-4/5" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-2/3" />
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                  </h3>
                  <div class="space-y-1 mt-3">
                    <div
                      v-for="i in 15"
                      :key="i"
                      class="block w-full text-left text-sm py-2 transition-colors truncate"
                      :style="{ paddingLeft: `${(i % 4) * 12}px` }"
                    >
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded" :style="{ width: `${50 + Math.random() * 50}%` }" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-10 mb-3" />
                  <div class="space-y-3">
                    <div class="flex items-start gap-2">
                      <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded mt-0.5" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full mb-1" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16 mb-3" />
                  <div class="grid grid-cols-2 gap-2">
                    <div
                      v-for="i in 4"
                      :key="i"
                      class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg"
                    >
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16 mb-3" />
                  <div class="space-y-0.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex items-center justify-between px-2 py-1.5 rounded-lg"
                    >
                      <div class="flex items-center gap-1.5">
                        <div class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                        <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-4" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14 mb-3" />
                  <div class="flex flex-wrap gap-1">
                    <div
                      v-for="i in 8"
                      :key="i"
                      class="h-5 px-2 bg-gray-200 dark:bg-dark-300 rounded"
                      :style="{ width: `${40 + Math.random() * 30}px` }"
                    />
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14 mb-3" />
                  <div class="space-y-2">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex gap-2"
                    >
                      <div class="w-5 h-5 rounded bg-gray-200 dark:bg-dark-300 flex-shrink-0" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full mb-0.5" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'resources'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
              <div class="lg:sticky lg:top-20">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="p-4 bg-gray-50/50 dark:bg-white/[0.02] rounded-xl">
                    <div class="flex flex-col items-center">
                      <div class="relative mb-3">
                        <div class="absolute inset-0 bg-primary/10 dark:bg-primary/20 rounded-full blur-xl opacity-60" />
                        <div class="relative w-14 h-14 rounded-full bg-gray-200 dark:bg-dark-300" />
                      </div>
                      <div class="text-center mb-3 w-full">
                        <div class="flex items-center justify-center gap-2 mb-2 flex-wrap">
                          <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded-full w-12" />
                        </div>
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-36 mx-auto" />
                      </div>
                      <div class="w-full pt-3 border-t border-gray-200/50 dark:border-white/5 flex items-center justify-between">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse mt-6">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14" />
                  </h3>
                  <div class="flex flex-col gap-3">
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    
                    <div class="mt-2 p-3 bg-gray-50 dark:bg-white/[0.02] rounded-lg border border-gray-200/60 dark:border-white/5">
                      <div class="flex items-center gap-2 mb-1.5">
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-24" />
                      </div>
                      <div class="flex items-center gap-1 flex-wrap">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="flex-1 min-w-0 lg:order-2">
              <div class="mb-8">
                <div class="h-8 bg-gray-200 dark:bg-dark-300 rounded w-32 mb-2" />
                <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-48" />
              </div>
              <div class="flex flex-wrap justify-center gap-2 mb-8">
                <div class="px-3 py-1 rounded-full border bg-gray-100 dark:bg-dark-100/50 border-gray-200 dark:border-white/10 animate-pulse">
                  <span class="inline-block w-10 h-[14px] bg-gray-200 dark:bg-dark-300 rounded" />
                </div>
                <div
                  v-for="i in 6"
                  :key="i"
                  class="px-[18px] py-1 rounded-full border bg-gray-100 dark:bg-dark-100/50 border-gray-200 dark:border-white/10 animate-pulse"
                >
                  <span class="inline-block w-[68px] h-[14px] bg-gray-200 dark:bg-dark-300 rounded" />
                </div>
              </div>
              <div class="space-y-8">
                <div
                  v-for="(count, idx) in [7, 7, 3, 2, 1, 1]"
                  :key="idx"
                  class="animate-pulse"
                >
                  <div class="flex items-center gap-3 mb-4">
                    <div class="w-9 h-9 rounded-lg bg-gray-200 dark:bg-dark-300 animate-pulse flex-shrink-0" />
                    <div class="h-6 bg-gray-200 dark:bg-dark-300 rounded w-24 animate-pulse" />
                  </div>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div
                      v-for="j in count"
                      :key="j"
                      class="glass-card p-5 min-h-[90px]"
                    >
                      <div class="flex items-start gap-3">
                        <div class="w-11 h-11 rounded-lg bg-gray-200 dark:bg-dark-300 flex-shrink-0" />
                        <div class="flex-1 space-y-2.5">
                          <div class="h-[18px] bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                          <div class="h-[14px] bg-gray-200 dark:bg-dark-300 rounded w-full" />
                          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-2/3" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-10 mb-3" />
                  <div class="space-y-3">
                    <div class="flex items-start gap-2">
                      <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded mt-0.5" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full mb-1" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16 mb-3" />
                  <div class="grid grid-cols-2 gap-2">
                    <div
                      v-for="i in 4"
                      :key="i"
                      class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg"
                    >
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16 mb-3" />
                  <div class="space-y-0.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex items-center justify-between px-2 py-1.5 rounded-lg"
                    >
                      <div class="flex items-center gap-1.5">
                        <div class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                        <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-4" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14 mb-3" />
                  <div class="flex flex-wrap gap-1">
                    <div
                      v-for="i in 8"
                      :key="i"
                      class="h-5 px-2 bg-gray-200 dark:bg-dark-300 rounded"
                      :style="{ width: `${40 + Math.random() * 30}px` }"
                    />
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14 mb-3" />
                  <div class="space-y-2">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex gap-2"
                    >
                      <div class="w-5 h-5 rounded bg-gray-200 dark:bg-dark-300 flex-shrink-0" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full mb-0.5" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'tags'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
              <div class="lg:sticky lg:top-20">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="p-4 bg-gray-50/50 dark:bg-white/[0.02] rounded-xl">
                    <div class="flex flex-col items-center">
                      <div class="relative mb-3">
                        <div class="absolute inset-0 bg-primary/10 dark:bg-primary/20 rounded-full blur-xl opacity-60" />
                        <div class="relative w-14 h-14 rounded-full bg-gray-200 dark:bg-dark-300" />
                      </div>
                      <div class="text-center mb-3 w-full">
                        <div class="flex items-center justify-center gap-2 mb-2 flex-wrap">
                          <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded-full w-12" />
                        </div>
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-36 mx-auto" />
                      </div>
                      <div class="w-full pt-3 border-t border-gray-200/50 dark:border-white/5 flex items-center justify-between">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                    </div>
                  </div>
                </div>
                <div class="sidebar-widget sidebar-widget-compact animate-pulse mt-6">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14" />
                  </h3>
                  <div class="flex flex-col gap-3">
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    
                    <div class="mt-2 p-3 bg-gray-50 dark:bg-white/[0.02] rounded-lg border border-gray-200/60 dark:border-white/5">
                      <div class="flex items-center gap-2 mb-1.5">
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-24" />
                      </div>
                      <div class="flex items-center gap-1 flex-wrap">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="flex-1 min-w-0 lg:order-2">
              <div class="mb-8">
                <div class="h-8 bg-gray-200 dark:bg-dark-300 rounded w-20 mb-2" />
                <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-32" />
              </div>
              <div class="glass-card p-6 mb-8 animate-pulse">
                <div class="flex flex-wrap gap-3">
                  <div
                    v-for="i in 12"
                    :key="i"
                    class="px-3 py-1.5 rounded-full bg-gray-200 dark:bg-dark-300"
                    :style="{ width: `${60 + Math.random() * 40}px` }"
                  >
                    <div class="h-4 bg-gray-300/50 dark:bg-gray-600/50 rounded w-full" />
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                  </h3>
                  <div class="space-y-3">
                    <div class="flex items-start gap-2">
                      <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded mt-0.5" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full mb-1" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="grid grid-cols-2 gap-2">
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-0.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex items-center justify-between px-2 py-1.5 rounded-lg"
                    >
                      <div class="flex items-center gap-1.5">
                        <div class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                        <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-4" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="flex flex-wrap gap-1">
                    <div
                      v-for="i in 8"
                      :key="i"
                      class="h-5 px-2 bg-gray-200 dark:bg-dark-300 rounded"
                      :style="{ width: `${40 + Math.random() * 30}px` }"
                    />
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-2">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex gap-2"
                    >
                      <div class="w-5 h-5 rounded bg-gray-200 dark:bg-dark-300 flex-shrink-0" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full mb-0.5" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'categories'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
              <div class="lg:sticky lg:top-20">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="p-4 bg-gray-50/50 dark:bg-white/[0.02] rounded-xl">
                    <div class="flex flex-col items-center">
                      <div class="relative mb-3">
                        <div class="absolute inset-0 bg-primary/10 dark:bg-primary/20 rounded-full blur-xl opacity-60" />
                        <div class="relative w-14 h-14 rounded-full bg-gray-200 dark:bg-dark-300" />
                      </div>
                      <div class="text-center mb-3 w-full">
                        <div class="flex items-center justify-center gap-2 mb-2 flex-wrap">
                          <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded-full w-12" />
                        </div>
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-36 mx-auto" />
                      </div>
                      <div class="w-full pt-3 border-t border-gray-200/50 dark:border-white/5 flex items-center justify-between">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                    </div>
                  </div>
                </div>
                <div class="sidebar-widget sidebar-widget-compact animate-pulse mt-6">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14" />
                  </h3>
                  <div class="flex flex-col gap-3">
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    
                    <div class="mt-2 p-3 bg-gray-50 dark:bg-white/[0.02] rounded-lg border border-gray-200/60 dark:border-white/5">
                      <div class="flex items-center gap-2 mb-1.5">
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-24" />
                      </div>
                      <div class="flex items-center gap-1 flex-wrap">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="flex-1 min-w-0 lg:order-2">
              <div class="mb-8">
                <div class="h-8 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2" />
                <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-40" />
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div
                  v-for="i in 6"
                  :key="i"
                  class="glass-card p-5 animate-pulse"
                >
                  <div class="flex items-start gap-4">
                    <div class="w-12 h-12 rounded-xl bg-gray-200 dark:bg-dark-300" />
                    <div class="flex-1">
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-20 mb-2" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full mb-1" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-3/4 mb-2" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                  </h3>
                  <div class="space-y-3">
                    <div class="flex items-start gap-2">
                      <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded mt-0.5" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full mb-1" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="grid grid-cols-2 gap-2">
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-0.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex items-center justify-between px-2 py-1.5 rounded-lg"
                    >
                      <div class="flex items-center gap-1.5">
                        <div class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                        <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-4" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="flex flex-wrap gap-1">
                    <div
                      v-for="i in 8"
                      :key="i"
                      class="h-5 px-2 bg-gray-200 dark:bg-dark-300 rounded"
                      :style="{ width: `${40 + Math.random() * 30}px` }"
                    />
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-2">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex gap-2"
                    >
                      <div class="w-5 h-5 rounded bg-gray-200 dark:bg-dark-300 flex-shrink-0" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full mb-0.5" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'archive'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
              <div class="lg:sticky lg:top-20">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="p-4 bg-gray-50/50 dark:bg-white/[0.02] rounded-xl">
                    <div class="flex flex-col items-center">
                      <div class="relative mb-3">
                        <div class="absolute inset-0 bg-primary/10 dark:bg-primary/20 rounded-full blur-xl opacity-60" />
                        <div class="relative w-14 h-14 rounded-full bg-gray-200 dark:bg-dark-300" />
                      </div>
                      <div class="text-center mb-3 w-full">
                        <div class="flex items-center justify-center gap-2 mb-2 flex-wrap">
                          <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded-full w-12" />
                        </div>
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-36 mx-auto" />
                      </div>
                      <div class="w-full pt-3 border-t border-gray-200/50 dark:border-white/5 flex items-center justify-between">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                    </div>
                  </div>
                </div>
                <div class="sidebar-widget sidebar-widget-compact animate-pulse mt-6">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14" />
                  </h3>
                  <div class="flex flex-col gap-3">
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    
                    <div class="mt-2 p-3 bg-gray-50 dark:bg-white/[0.02] rounded-lg border border-gray-200/60 dark:border-white/5">
                      <div class="flex items-center gap-2 mb-1.5">
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-24" />
                      </div>
                      <div class="flex items-center gap-1 flex-wrap">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="flex-1 min-w-0 lg:order-2">
              <div class="mb-6">
                <div class="h-8 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2 animate-pulse" />
                <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-32 animate-pulse" />
              </div>
              <div class="flex flex-wrap items-center gap-2 mb-6">
                <div class="h-9 w-48 bg-gray-200 dark:bg-dark-300 rounded-lg animate-pulse" />
                <div class="h-9 w-28 bg-gray-200 dark:bg-dark-300 rounded-lg animate-pulse" />
                <div class="flex items-center gap-1">
                  <div class="w-7 h-7 bg-gray-200 dark:bg-dark-300 rounded animate-pulse" />
                  <div class="w-7 h-7 bg-gray-200 dark:bg-dark-300 rounded animate-pulse" />
                </div>
              </div>
              
              <div class="relative">
                <div class="absolute left-4 md:left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-gray-200 via-gray-200/50 to-transparent dark:from-dark-300 dark:via-dark-300/50" />
                
                <div
                  v-for="i in 2"
                  :key="i"
                  class="relative mb-8"
                >
                  <div class="flex items-center gap-3 mb-4 pl-12 md:pl-20">
                    <div class="absolute left-2 md:left-6 w-4 h-4 rounded-full bg-gray-200 dark:bg-dark-300 animate-pulse ring-4 ring-white dark:ring-dark-100" />
                    <div class="flex items-center gap-2">
                      <div class="h-7 w-12 bg-gray-200 dark:bg-dark-300 rounded animate-pulse" />
                      <div class="h-4 w-10 bg-gray-200 dark:bg-dark-300 rounded animate-pulse" />
                    </div>
                  </div>
                  
                  <div class="space-y-2 pl-12 md:pl-20">
                    <div
                      v-for="j in 3"
                      :key="j"
                      class="relative"
                    >
                      <div class="absolute left-[-32px] md:left-[-48px] top-3 w-2 h-2 rounded-full bg-gray-200 dark:bg-dark-300 animate-pulse" />
                      
                      <div class="glass-card overflow-hidden animate-pulse">
                        <div class="flex items-center justify-between px-4 py-2.5">
                          <div class="flex items-center gap-2">
                            <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                            <div class="h-4 w-8 bg-gray-200 dark:bg-dark-300 rounded" />
                            <div class="h-3 w-6 bg-gray-200 dark:bg-dark-300 rounded" />
                          </div>
                        </div>
                        <div class="border-t border-gray-100 dark:border-white/5">
                          <div
                            v-for="k in 2"
                            :key="k"
                            class="flex items-center gap-3 px-4 py-2 border-b border-gray-50 dark:border-white/5"
                          >
                            <div class="h-3 w-12 bg-gray-200 dark:bg-dark-300 rounded" />
                            <div class="h-4 w-10 bg-gray-200 dark:bg-dark-300 rounded" />
                            <div class="flex-1 h-4 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                            <div class="h-3 w-8 bg-gray-200 dark:bg-dark-300 rounded" />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                  </h3>
                  <div class="space-y-3">
                    <div class="flex items-start gap-2">
                      <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded mt-0.5" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full mb-1" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="grid grid-cols-2 gap-2">
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-0.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex items-center justify-between px-2 py-1.5 rounded-lg"
                    >
                      <div class="flex items-center gap-1.5">
                        <div class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                        <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-4" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="flex flex-wrap gap-1">
                    <div
                      v-for="i in 8"
                      :key="i"
                      class="h-5 px-2 bg-gray-200 dark:bg-dark-300 rounded"
                      :style="{ width: `${40 + Math.random() * 30}px` }"
                    />
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-2">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex gap-2"
                    >
                      <div class="w-5 h-5 rounded bg-gray-200 dark:bg-dark-300 flex-shrink-0" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full mb-0.5" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'about' || skeletonType === 'links'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
              <div class="lg:sticky lg:top-20">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="p-4 bg-gray-50/50 dark:bg-white/[0.02] rounded-xl">
                    <div class="flex flex-col items-center">
                      <div class="relative mb-3">
                        <div class="absolute inset-0 bg-primary/10 dark:bg-primary/20 rounded-full blur-xl opacity-60" />
                        <div class="relative w-14 h-14 rounded-full bg-gray-200 dark:bg-dark-300" />
                      </div>
                      <div class="text-center mb-3 w-full">
                        <div class="flex items-center justify-center gap-2 mb-2 flex-wrap">
                          <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded-full w-12" />
                        </div>
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-36 mx-auto" />
                      </div>
                      <div class="w-full pt-3 border-t border-gray-200/50 dark:border-white/5 flex items-center justify-between">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                    </div>
                  </div>
                </div>
                <div class="sidebar-widget sidebar-widget-compact animate-pulse mt-6">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14" />
                  </h3>
                  <div class="flex flex-col gap-3">
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    
                    <div class="mt-2 p-3 bg-gray-50 dark:bg-white/[0.02] rounded-lg border border-gray-200/60 dark:border-white/5">
                      <div class="flex items-center gap-2 mb-1.5">
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-24" />
                      </div>
                      <div class="flex items-center gap-1 flex-wrap">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="flex-1 min-w-0 lg:order-2">
              <div class="mb-8">
                <div class="h-9 bg-gray-200 dark:bg-dark-300 rounded w-20 mb-2 animate-pulse" />
                <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-56 animate-pulse" />
              </div>
              
              <div class="glass-card p-6 md:p-8 mb-6 animate-pulse">
                <div class="flex flex-col sm:flex-row items-center gap-6">
                  <div class="relative flex-shrink-0">
                    <div class="w-24 h-24 md:w-28 md:h-28 rounded-full bg-primary/20 p-0.5">
                      <div class="w-full h-full rounded-full bg-gray-100 dark:bg-dark-100 flex items-center justify-center">
                        <div class="h-8 w-14 bg-gray-200 dark:bg-dark-300 rounded" />
                      </div>
                    </div>
                    <div class="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-gray-200 dark:bg-dark-300 flex items-center justify-center">
                      <div class="w-3 h-3 bg-gray-300 dark:bg-dark-400 rounded-sm" />
                    </div>
                  </div>
                  <div class="flex-1 text-center sm:text-left min-w-0">
                    <div class="h-8 bg-gray-200 dark:bg-dark-300 rounded w-32 mb-1 mx-auto sm:mx-0" />
                    <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-20 mb-2 mx-auto sm:mx-0" />
                    <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-40 mb-3 mx-auto sm:mx-0" />
                    <div class="flex flex-wrap justify-center sm:justify-start gap-1.5 mb-3">
                      <div
                        v-for="i in 4"
                        :key="i"
                        class="h-5 px-2.5 bg-gray-200 dark:bg-dark-300 rounded-full"
                        style="width: 50px;"
                      />
                    </div>
                    <div class="space-y-1.5">
                      <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                      <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="glass-card p-6 mb-6 animate-pulse">
                <div class="flex items-center gap-2 mb-4">
                  <div class="w-5 h-5 bg-gray-200 dark:bg-dark-300 rounded" />
                  <div class="h-6 bg-gray-200 dark:bg-dark-300 rounded w-24" />
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div
                    v-for="i in 4"
                    :key="i"
                    class="p-4 bg-gray-50 dark:bg-dark-300/50 rounded-xl border border-gray-100 dark:border-white/5"
                  >
                    <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-16 mb-2.5" />
                    <div class="flex flex-wrap gap-1.5">
                      <div
                        v-for="j in 3"
                        :key="j"
                        class="h-5 px-2 bg-gray-200 dark:bg-dark-300 rounded"
                        style="width: 48px;"
                      />
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="glass-card p-6 mb-6 animate-pulse">
                <div class="flex items-center gap-2 mb-4">
                  <div class="w-5 h-5 bg-gray-200 dark:bg-dark-300 rounded" />
                  <div class="h-6 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                </div>
                <div class="relative">
                  <div class="absolute left-3.5 top-0 bottom-0 w-0.5 bg-gradient-to-b from-gray-200 via-gray-200 to-gray-200/20 dark:from-dark-300 dark:via-dark-300" />
                  <div
                    v-for="i in 2"
                    :key="i"
                    class="relative pl-10 pb-6 last:pb-0"
                  >
                    <div class="absolute left-1 top-1 w-5 h-5 rounded-full bg-gray-200 dark:bg-dark-300 border-4 border-white dark:border-dark-200" />
                    <div class="p-4 bg-gray-50 dark:bg-dark-300/50 rounded-lg border border-gray-100 dark:border-white/5">
                      <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-16 mb-0.5" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-32 mb-0.5" />
                      <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-1.5" />
                      <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="glass-card p-6 mb-6 animate-pulse">
                <div class="flex items-center gap-2 mb-4">
                  <div class="w-5 h-5 bg-gray-200 dark:bg-dark-300 rounded" />
                  <div class="h-6 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                </div>
                <div class="p-4 bg-gray-50 dark:bg-dark-300/50 rounded-lg border border-gray-100 dark:border-white/5">
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-20 mb-0.5" />
                  <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-32 mb-0.5" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-48" />
                </div>
              </div>
              
              <div class="glass-card p-6 mb-6 animate-pulse">
                <div class="flex items-center gap-2 mb-4">
                  <div class="w-5 h-5 bg-gray-200 dark:bg-dark-300 rounded" />
                  <div class="h-6 bg-gray-200 dark:bg-dark-300 rounded w-24" />
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div
                    v-for="i in 4"
                    :key="i"
                    class="flex items-start gap-2.5 p-3 bg-gray-50 dark:bg-dark-300/50 rounded-lg border border-gray-100 dark:border-white/5"
                  >
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded flex-shrink-0 mt-0.5" />
                    <div class="flex-1 h-4 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                  </div>
                </div>
              </div>
              
              <div class="glass-card p-6 animate-pulse">
                <div class="flex items-center gap-2 mb-4">
                  <div class="w-5 h-5 bg-gray-200 dark:bg-dark-300 rounded" />
                  <div class="h-6 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                </div>
                <div class="flex flex-wrap gap-3">
                  <div
                    v-for="i in 4"
                    :key="i"
                    class="flex items-center gap-2 px-4 py-2.5 bg-gray-50 dark:bg-dark-300/50 border border-gray-200 dark:border-white/10 rounded-lg"
                  >
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-4 w-12 bg-gray-200 dark:bg-dark-300 rounded" />
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                  </h3>
                  <div class="space-y-3">
                    <div class="flex items-start gap-2">
                      <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded mt-0.5" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full mb-1" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="grid grid-cols-2 gap-2">
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-0.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex items-center justify-between px-2 py-1.5 rounded-lg"
                    >
                      <div class="flex items-center gap-1.5">
                        <div class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                        <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-4" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="flex flex-wrap gap-1">
                    <div
                      v-for="i in 8"
                      :key="i"
                      class="h-5 px-2 bg-gray-200 dark:bg-dark-300 rounded"
                      :style="{ width: `${40 + Math.random() * 30}px` }"
                    />
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-2">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex gap-2"
                    >
                      <div class="w-5 h-5 rounded bg-gray-200 dark:bg-dark-300 flex-shrink-0" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full mb-0.5" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'profile'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
              <div class="lg:sticky lg:top-20">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="p-4 bg-gray-50/50 dark:bg-white/[0.02] rounded-xl">
                    <div class="flex flex-col items-center">
                      <div class="relative mb-3">
                        <div class="absolute inset-0 bg-primary/10 dark:bg-primary/20 rounded-full blur-xl opacity-60" />
                        <div class="relative w-14 h-14 rounded-full bg-gray-200 dark:bg-dark-300" />
                      </div>
                      <div class="text-center mb-3 w-full">
                        <div class="flex items-center justify-center gap-2 mb-2 flex-wrap">
                          <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded-full w-12" />
                        </div>
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-36 mx-auto" />
                      </div>
                      <div class="w-full pt-3 border-t border-gray-200/50 dark:border-white/5 flex items-center justify-between">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                    </div>
                  </div>
                </div>
                <div class="sidebar-widget sidebar-widget-compact animate-pulse mt-6">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14" />
                  </h3>
                  <div class="flex flex-col gap-3">
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    
                    <div class="mt-2 p-3 bg-gray-50 dark:bg-white/[0.02] rounded-lg border border-gray-200/60 dark:border-white/5">
                      <div class="flex items-center gap-2 mb-1.5">
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-24" />
                      </div>
                      <div class="flex items-center gap-1 flex-wrap">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="flex-1 min-w-0 lg:order-2">
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
                    v-for="i in 4"
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
                  class="glass-card p-2 animate-pulse"
                >
                  <div class="flex flex-col gap-3 sm:grid sm:grid-cols-[auto_1fr] sm:gap-4">
                    <div class="w-full h-52 sm:w-56 md:w-64 sm:h-full bg-gray-200 dark:bg-dark-300 rounded-lg" />
                    <div class="relative flex-1 min-w-0 flex flex-col min-h-0">
                      <div class="flex items-center gap-2 mb-2">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                      <div class="space-y-1.5 mb-2">
                        <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                        <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-1/2" />
                      </div>
                      <div class="space-y-1.5 mb-2">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                      </div>
                      <div class="flex flex-wrap gap-1 mb-2">
                        <div
                          v-for="t in 3"
                          :key="t"
                          class="h-4 bg-gray-200 dark:bg-dark-300 rounded-full w-12"
                        />
                      </div>
                      <div class="article-meta mt-auto pt-2 border-t border-gray-100 dark:border-white/5">
                        <div class="flex items-center gap-1 w-full">
                          <div class="w-3.5 h-3.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                        </div>
                      </div>
                      <div class="article-meta pt-2">
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                  </h3>
                  <div class="space-y-3">
                    <div class="flex items-start gap-2">
                      <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded mt-0.5" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full mb-1" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="grid grid-cols-2 gap-2">
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-0.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex items-center justify-between px-2 py-1.5 rounded-lg"
                    >
                      <div class="flex items-center gap-1.5">
                        <div class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                        <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-4" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="flex flex-wrap gap-1">
                    <div
                      v-for="i in 8"
                      :key="i"
                      class="h-5 px-2 bg-gray-200 dark:bg-dark-300 rounded"
                      :style="{ width: `${40 + Math.random() * 30}px` }"
                    />
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-2">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex gap-2"
                    >
                      <div class="w-5 h-5 rounded bg-gray-200 dark:bg-dark-300 flex-shrink-0" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full mb-0.5" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'search'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
              <div class="lg:sticky lg:top-20">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="p-4 bg-gray-50/50 dark:bg-white/[0.02] rounded-xl">
                    <div class="flex flex-col items-center">
                      <div class="relative mb-3">
                        <div class="absolute inset-0 bg-primary/10 dark:bg-primary/20 rounded-full blur-xl opacity-60" />
                        <div class="relative w-14 h-14 rounded-full bg-gray-200 dark:bg-dark-300" />
                      </div>
                      <div class="text-center mb-3 w-full">
                        <div class="flex items-center justify-center gap-2 mb-2 flex-wrap">
                          <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded-full w-12" />
                        </div>
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-36 mx-auto" />
                      </div>
                      <div class="w-full pt-3 border-t border-gray-200/50 dark:border-white/5 flex items-center justify-between">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                    </div>
                  </div>
                </div>
                <div class="sidebar-widget sidebar-widget-compact animate-pulse mt-6">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14" />
                  </h3>
                  <div class="flex flex-col gap-3">
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    
                    <div class="mt-2 p-3 bg-gray-50 dark:bg-white/[0.02] rounded-lg border border-gray-200/60 dark:border-white/5">
                      <div class="flex items-center gap-2 mb-1.5">
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-24" />
                      </div>
                      <div class="flex items-center gap-1 flex-wrap">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="flex-1 min-w-0 lg:order-2">
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
                  class="glass-card p-2 animate-pulse"
                >
                  <div class="flex flex-col gap-3 sm:grid sm:grid-cols-[auto_1fr] sm:gap-4">
                    <div class="w-full h-52 sm:w-56 md:w-64 sm:h-full bg-gray-200 dark:bg-dark-300 rounded-lg" />
                    <div class="relative flex-1 min-w-0 flex flex-col min-h-0">
                      <div class="flex items-center gap-2 mb-2">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                      <div class="space-y-1.5 mb-2">
                        <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                        <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-1/2" />
                      </div>
                      <div class="space-y-1.5 mb-2">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                      </div>
                      <div class="flex flex-wrap gap-1 mb-2">
                        <div
                          v-for="t in 3"
                          :key="t"
                          class="h-4 bg-gray-200 dark:bg-dark-300 rounded-full w-12"
                        />
                      </div>
                      <div class="article-meta mt-auto pt-2 border-t border-gray-100 dark:border-white/5">
                        <div class="flex items-center gap-1 w-full">
                          <div class="w-3.5 h-3.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                        </div>
                      </div>
                      <div class="article-meta pt-2">
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                  </h3>
                  <div class="space-y-3">
                    <div class="flex items-start gap-2">
                      <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded mt-0.5" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full mb-1" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="grid grid-cols-2 gap-2">
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-0.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex items-center justify-between px-2 py-1.5 rounded-lg"
                    >
                      <div class="flex items-center gap-1.5">
                        <div class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                        <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-4" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="flex flex-wrap gap-1">
                    <div
                      v-for="i in 8"
                      :key="i"
                      class="h-5 px-2 bg-gray-200 dark:bg-dark-300 rounded"
                      :style="{ width: `${40 + Math.random() * 30}px` }"
                    />
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-2">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex gap-2"
                    >
                      <div class="w-5 h-5 rounded bg-gray-200 dark:bg-dark-300 flex-shrink-0" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full mb-0.5" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'category' || skeletonType === 'tag'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
              <div class="lg:sticky lg:top-20">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="p-4 bg-gray-50/50 dark:bg-white/[0.02] rounded-xl">
                    <div class="flex flex-col items-center">
                      <div class="relative mb-3">
                        <div class="absolute inset-0 bg-primary/10 dark:bg-primary/20 rounded-full blur-xl opacity-60" />
                        <div class="relative w-14 h-14 rounded-full bg-gray-200 dark:bg-dark-300" />
                      </div>
                      <div class="text-center mb-3 w-full">
                        <div class="flex items-center justify-center gap-2 mb-2 flex-wrap">
                          <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded-full w-12" />
                        </div>
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-36 mx-auto" />
                      </div>
                      <div class="w-full pt-3 border-t border-gray-200/50 dark:border-white/5 flex items-center justify-between">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                    </div>
                  </div>
                </div>
                <div class="sidebar-widget sidebar-widget-compact animate-pulse mt-6">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14" />
                  </h3>
                  <div class="flex flex-col gap-3">
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    
                    <div class="mt-2 p-3 bg-gray-50 dark:bg-white/[0.02] rounded-lg border border-gray-200/60 dark:border-white/5">
                      <div class="flex items-center gap-2 mb-1.5">
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-24" />
                      </div>
                      <div class="flex items-center gap-1 flex-wrap">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="flex-1 min-w-0 lg:order-2">
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
                  class="glass-card p-2 animate-pulse"
                >
                  <div class="flex flex-col gap-3 sm:grid sm:grid-cols-[auto_1fr] sm:gap-4">
                    <div class="w-full h-52 sm:w-56 md:w-64 sm:h-full bg-gray-200 dark:bg-dark-300 rounded-lg" />
                    <div class="relative flex-1 min-w-0 flex flex-col min-h-0">
                      <div class="flex items-center gap-2 mb-2">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                      <div class="space-y-1.5 mb-2">
                        <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                        <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-1/2" />
                      </div>
                      <div class="space-y-1.5 mb-2">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                      </div>
                      <div class="flex flex-wrap gap-1 mb-2">
                        <div
                          v-for="t in 3"
                          :key="t"
                          class="h-4 bg-gray-200 dark:bg-dark-300 rounded-full w-12"
                        />
                      </div>
                      <div class="article-meta mt-auto pt-2 border-t border-gray-100 dark:border-white/5">
                        <div class="flex items-center gap-1 w-full">
                          <div class="w-3.5 h-3.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                        </div>
                      </div>
                      <div class="article-meta pt-2">
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                  </h3>
                  <div class="space-y-3">
                    <div class="flex items-start gap-2">
                      <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded mt-0.5" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full mb-1" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="grid grid-cols-2 gap-2">
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-0.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex items-center justify-between px-2 py-1.5 rounded-lg"
                    >
                      <div class="flex items-center gap-1.5">
                        <div class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                        <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-4" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="flex flex-wrap gap-1">
                    <div
                      v-for="i in 8"
                      :key="i"
                      class="h-5 px-2 bg-gray-200 dark:bg-dark-300 rounded"
                      :style="{ width: `${40 + Math.random() * 30}px` }"
                    />
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-2">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex gap-2"
                    >
                      <div class="w-5 h-5 rounded bg-gray-200 dark:bg-dark-300 flex-shrink-0" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full mb-0.5" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else-if="skeletonType === 'home'">
          <div class="flex flex-col lg:flex-row gap-6">
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
              <div class="lg:sticky lg:top-20">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <div class="p-4 bg-gray-50/50 dark:bg-white/[0.02] rounded-xl">
                    <div class="flex flex-col items-center">
                      <div class="relative mb-3">
                        <div class="absolute inset-0 bg-primary/10 dark:bg-primary/20 rounded-full blur-xl opacity-60" />
                        <div class="relative w-14 h-14 rounded-full bg-gray-200 dark:bg-dark-300" />
                      </div>
                      <div class="text-center mb-3 w-full">
                        <div class="flex items-center justify-center gap-2 mb-2 flex-wrap">
                          <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                          <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded-full w-12" />
                        </div>
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-36 mx-auto" />
                      </div>
                      <div class="w-full pt-3 border-t border-gray-200/50 dark:border-white/5 flex items-center justify-between">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse mt-6">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-14" />
                  </h3>
                  <div class="flex flex-col gap-3">
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg">
                      <div class="flex items-center gap-2">
                        <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                      </div>
                      <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                    </div>
                    
                    <div class="mt-2 p-3 bg-gray-50 dark:bg-white/[0.02] rounded-lg border border-gray-200/60 dark:border-white/5">
                      <div class="flex items-center gap-2 mb-1.5">
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-24" />
                      </div>
                      <div class="flex items-center gap-1 flex-wrap">
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="flex-1 min-w-0 lg:order-2">
              <section class="mb-8">
                <div class="glass-card overflow-hidden animate-pulse">
                  <div class="relative h-48 sm:h-56 md:h-64 lg:h-72 xl:h-80 bg-gray-200 dark:bg-dark-300">
                    <div class="absolute bottom-0 left-0 right-0 px-2 py-4">
                      <div class="flex items-center gap-1 mb-2">
                        <div class="h-5 w-16 bg-gray-300/50 dark:bg-gray-600/50 rounded-full" />
                        <div class="h-5 w-12 bg-gray-300/50 dark:bg-gray-600/50 rounded-full" />
                      </div>
                      <div class="h-6 bg-gray-300/50 dark:bg-gray-600/50 rounded w-3/4 mb-2" />
                      <div class="h-4 bg-gray-300/50 dark:bg-gray-600/50 rounded w-2/3 mb-2" />
                      <div class="flex items-center gap-2">
                        <div class="h-3 w-20 bg-gray-300/50 dark:bg-gray-600/50 rounded" />
                        <div class="h-3 w-12 bg-gray-300/50 dark:bg-gray-600/50 rounded" />
                      </div>
                    </div>
                  </div>
                  <div class="flex items-center justify-between px-2 py-1 border-t border-gray-100 dark:border-white/5">
                    <div class="flex gap-1">
                      <div
                        v-for="i in 5"
                        :key="i"
                        class="h-1 rounded-full bg-gray-300 dark:bg-gray-600"
                        :class="i === 1 ? 'w-3' : 'w-1'"
                      />
                    </div>
                    <div class="flex gap-0.5">
                      <div class="p-0.5 rounded bg-gray-200 dark:bg-dark-300">
                        <div class="w-3 h-3 bg-gray-300 dark:bg-gray-600 rounded" />
                      </div>
                      <div class="p-0.5 rounded bg-gray-200 dark:bg-dark-300">
                        <div class="w-3 h-3 bg-gray-300 dark:bg-gray-600 rounded" />
                      </div>
                    </div>
                  </div>
                </div>
              </section>
              
              <div class="flex items-center justify-between mb-8">
                <div class="flex items-center gap-2">
                  <div class="w-5 h-5 bg-gray-200 dark:bg-dark-300 rounded animate-pulse" />
                  <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-20 animate-pulse" />
                </div>
                <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-16 animate-pulse" />
              </div>
              
              <div class="space-y-4">
                <div
                  v-for="i in 3"
                  :key="i"
                  class="glass-card p-2 animate-pulse"
                >
                  <div class="flex flex-col gap-3 sm:grid sm:grid-cols-[auto_1fr] sm:gap-4">
                    <div class="w-full h-52 sm:w-56 md:w-64 sm:h-full bg-gray-200 dark:bg-dark-300 rounded-lg" />
                    <div class="relative flex-1 min-w-0 flex flex-col min-h-0">
                      <div class="flex items-center gap-2 mb-2">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                      </div>
                      <div class="space-y-1.5 mb-2">
                        <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                        <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-1/2" />
                      </div>
                      <div class="space-y-1.5 mb-2">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                      </div>
                      <div class="flex flex-wrap gap-1 mb-2">
                        <div
                          v-for="t in 3"
                          :key="t"
                          class="h-4 bg-gray-200 dark:bg-dark-300 rounded-full w-12"
                        />
                      </div>
                      <div class="article-meta mt-auto pt-2 border-t border-gray-100 dark:border-white/5">
                        <div class="flex items-center gap-1 w-full">
                          <div class="w-3.5 h-3.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-20" />
                        </div>
                      </div>
                      <div class="article-meta pt-2">
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-12" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                          <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                        </div>
                        <div class="flex items-center gap-1">
                          <div class="w-3.5 h-3.5 rounded bg-gray-200 dark:bg-dark-300" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                  </h3>
                  <div class="space-y-3">
                    <div class="flex items-start gap-2">
                      <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded mt-0.5" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full mb-1" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="grid grid-cols-2 gap-2">
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-0.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex items-center justify-between px-2 py-1.5 rounded-lg"
                    >
                      <div class="flex items-center gap-1.5">
                        <div class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                        <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-4" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="flex flex-wrap gap-1">
                    <div
                      v-for="i in 8"
                      :key="i"
                      class="h-5 px-2 bg-gray-200 dark:bg-dark-300 rounded"
                      :style="{ width: `${40 + Math.random() * 30}px` }"
                    />
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-2">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex gap-2"
                    >
                      <div class="w-5 h-5 rounded bg-gray-200 dark:bg-dark-300 flex-shrink-0" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full mb-0.5" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-else>
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
            
            <div class="flex-1 min-w-0 lg:order-2">
              <div class="glass-card p-6 animate-pulse">
                <div class="h-8 bg-gray-200 dark:bg-dark-300 rounded w-1/2 mb-6" />
                <div class="space-y-4">
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-5/6" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-4/5" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full" />
                  <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                </div>
              </div>
            </div>
            
            <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
              <div class="lg:sticky lg:top-20 space-y-6">
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-10" />
                  </h3>
                  <div class="space-y-3">
                    <div class="flex items-start gap-2">
                      <div class="w-4 h-4 bg-gray-200 dark:bg-dark-300 rounded mt-0.5" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-24 mb-2" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-full mb-1" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-3/4" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="grid grid-cols-2 gap-2">
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                    <div class="text-center p-2 bg-gray-50 dark:bg-dark-300/50 rounded-lg">
                      <div class="w-4 h-4 mx-auto mb-0.5 bg-gray-200 dark:bg-dark-300 rounded" />
                      <div class="h-5 bg-gray-200 dark:bg-dark-300 rounded w-8 mx-auto mb-0.5" />
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-10 mx-auto" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-0.5">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex items-center justify-between px-2 py-1.5 rounded-lg"
                    >
                      <div class="flex items-center gap-1.5">
                        <div class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-dark-300" />
                        <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                      </div>
                      <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-4" />
                    </div>
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="flex flex-wrap gap-1">
                    <div
                      v-for="i in 8"
                      :key="i"
                      class="h-5 px-2 bg-gray-200 dark:bg-dark-300 rounded"
                      :style="{ width: `${40 + Math.random() * 30}px` }"
                    />
                  </div>
                </div>
                
                <div class="sidebar-widget sidebar-widget-compact animate-pulse">
                  <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
                    <div class="w-3.5 h-3.5 bg-gray-200 dark:bg-dark-300 rounded" />
                    <div class="h-3.5 bg-gray-200 dark:bg-dark-300 rounded w-16" />
                  </h3>
                  <div class="space-y-2">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="flex gap-2"
                    >
                      <div class="w-5 h-5 rounded bg-gray-200 dark:bg-dark-300 flex-shrink-0" />
                      <div class="flex-1">
                        <div class="h-4 bg-gray-200 dark:bg-dark-300 rounded w-full mb-0.5" />
                        <div class="h-3 bg-gray-200 dark:bg-dark-300 rounded w-8" />
                      </div>
                    </div>
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
              <div class="w-7 h-7 rounded-full bg-gray-200 dark:bg-dark-300 animate-pulse" />
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
