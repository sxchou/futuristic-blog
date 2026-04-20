<script setup lang="ts">
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-dark-100 flex flex-col">
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
