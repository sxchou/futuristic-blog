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
  <footer class="border-t border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-dark-100/50">
    <div class="container mx-auto px-4 py-8">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div class="md:col-span-2">
          <div class="flex items-center gap-2 mb-2">
            <span class="text-lg font-bold gradient-text">{{ siteConfigStore.siteName }}</span>
          </div>
          <p class="text-gray-500 dark:text-gray-400 mb-3 max-w-md text-sm">
            {{ siteConfigStore.siteDescription || 'Code for Future, Share for Growth. 一个充满未来感的个人技术博客，分享全栈开发、AI应用、架构设计等技术探索。' }}
          </p>
          <div class="flex gap-2">
            <template v-if="socialLinksStore.hasSocialLinks">
              <a
                v-for="link in socialLinksStore.socialLinks"
                :key="link.id"
                :href="link.url"
                :target="link.type === 'link' ? '_blank' : undefined"
                :rel="link.type === 'link' ? 'noopener noreferrer' : undefined"
                :class="['p-1.5 rounded-lg bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 transition-colors', link.color, link.hoverColor]"
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
            </template>
          </div>
        </div>

        <div>
          <h4 class="text-gray-900 dark:text-white font-semibold mb-2 text-sm">快速链接</h4>
          <ul class="space-y-1">
            <li><router-link to="/" class="text-gray-500 dark:text-gray-400 hover:text-primary transition-colors text-sm">首页</router-link></li>
            <li><router-link to="/about" class="text-gray-500 dark:text-gray-400 hover:text-primary transition-colors text-sm">关于我</router-link></li>
            <li><router-link to="/categories" class="text-gray-500 dark:text-gray-400 hover:text-primary transition-colors text-sm">分类</router-link></li>
            <li><router-link to="/tags" class="text-gray-500 dark:text-gray-400 hover:text-primary transition-colors text-sm">标签</router-link></li>
            <li><router-link to="/resources" class="text-gray-500 dark:text-gray-400 hover:text-primary transition-colors text-sm">资源导航</router-link></li>
            <li><router-link to="/archive" class="text-gray-500 dark:text-gray-400 hover:text-primary transition-colors text-sm">文章归档</router-link></li>
          </ul>
        </div>

        <div>
          <h4 class="text-gray-900 dark:text-white font-semibold mb-2 text-sm">技术栈</h4>
          <div class="flex flex-wrap gap-1">
            <span class="tag text-xs">Vue 3</span>
            <span class="tag text-xs">TypeScript</span>
            <span class="tag text-xs">FastAPI</span>
            <span class="tag text-xs">Python</span>
            <span class="tag text-xs">TailwindCSS</span>
          </div>
        </div>
      </div>

      <div class="mt-6 pt-4 border-t border-gray-200 dark:border-white/10 flex flex-col md:flex-row justify-between items-center gap-2">
        <p class="text-gray-500 text-xs">
          © {{ currentYear }} {{ siteConfigStore.siteName }}. All rights reserved.
        </p>
        <p class="text-gray-500 text-xs">
          Built with <span class="text-primary">♥</span> using Vue 3 + FastAPI
        </p>
      </div>
    </div>
  </footer>
</template>
