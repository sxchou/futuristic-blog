<script setup lang="ts">
import { onMounted } from 'vue'
import { useSiteConfigStore, useSocialLinksStore } from '@/stores'

const siteConfigStore = useSiteConfigStore()
const socialLinksStore = useSocialLinksStore()
const currentYear = new Date().getFullYear()

onMounted(() => {
  siteConfigStore.fetchConfigs()
  socialLinksStore.fetchProfile()
})
</script>

<template>
  <footer class="border-t border-gray-200/60 dark:border-white/5 bg-gray-50/50 dark:bg-dark-100/50">
    <div class="blog-container py-10">
      <div class="grid grid-cols-1 md:grid-cols-12 gap-8">
        <div class="md:col-span-5">
          <div class="flex items-center gap-2.5 mb-3">
            <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <svg class="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span class="text-base font-bold text-gray-900 dark:text-white">{{ siteConfigStore.siteName }}</span>
          </div>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-4 max-w-sm leading-relaxed">
            {{ siteConfigStore.siteDescription || 'Code for Future, Share for Growth. 一个充满未来感的个人技术博客，分享全栈开发、AI应用、架构设计等技术探索。' }}
          </p>
          <div v-if="socialLinksStore.hasSocialLinks" class="flex gap-2">
            <a
              v-for="link in socialLinksStore.socialLinks"
              :key="link.id"
              :href="link.url"
              :target="link.type === 'link' ? '_blank' : undefined"
              :rel="link.type === 'link' ? 'noopener noreferrer' : undefined"
              class="w-8 h-8 rounded-lg bg-gray-100 dark:bg-dark-300 border border-gray-200 dark:border-white/5 flex items-center justify-center text-gray-400 hover:text-primary hover:border-primary/30 transition-all"
              :title="link.name"
            >
              <svg v-if="link.icon === 'github'" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              <svg v-else-if="link.icon === 'email'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <svg v-else-if="link.icon === 'blog'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
            </a>
          </div>
        </div>

        <div class="md:col-span-3">
          <h4 class="text-sm font-semibold text-gray-900 dark:text-white mb-3">导航</h4>
          <ul class="space-y-2">
            <li><router-link to="/" class="text-sm text-gray-500 dark:text-gray-400 hover:text-primary transition-colors">首页</router-link></li>
            <li><router-link to="/categories" class="text-sm text-gray-500 dark:text-gray-400 hover:text-primary transition-colors">分类</router-link></li>
            <li><router-link to="/tags" class="text-sm text-gray-500 dark:text-gray-400 hover:text-primary transition-colors">标签</router-link></li>
            <li><router-link to="/archive" class="text-sm text-gray-500 dark:text-gray-400 hover:text-primary transition-colors">归档</router-link></li>
            <li><router-link to="/about" class="text-sm text-gray-500 dark:text-gray-400 hover:text-primary transition-colors">关于</router-link></li>
          </ul>
        </div>

        <div class="md:col-span-4">
          <h4 class="text-sm font-semibold text-gray-900 dark:text-white mb-3">技术栈</h4>
          <div class="flex flex-wrap gap-1.5">
            <span class="tag text-xs">Vue 3</span>
            <span class="tag text-xs">TypeScript</span>
            <span class="tag text-xs">FastAPI</span>
            <span class="tag text-xs">Python</span>
            <span class="tag text-xs">TailwindCSS</span>
            <span class="tag text-xs">PostgreSQL</span>
          </div>
        </div>
      </div>

      <div class="mt-8 pt-6 border-t border-gray-200/60 dark:border-white/5 flex flex-col sm:flex-row justify-between items-center gap-2">
        <p class="text-xs text-gray-400">
          © {{ currentYear }} {{ siteConfigStore.siteName }}. All rights reserved.
        </p>
        <p class="text-xs text-gray-400">
          Built with <span class="text-primary">♥</span> using Vue 3 + FastAPI
        </p>
      </div>
    </div>
  </footer>
</template>
