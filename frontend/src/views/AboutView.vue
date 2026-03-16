<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { profileApi } from '@/api'
import type { Profile } from '@/types'

const profile = ref<Profile | null>(null)
const isLoading = ref(true)

const fetchProfile = async () => {
  try {
    profile.value = await profileApi.getProfile()
  } catch (error) {
    console.error('Failed to fetch profile:', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchProfile)
</script>

<template>
  <div class="pt-20 pb-16">
    <div class="container mx-auto px-4">
      <div class="max-w-5xl mx-auto">
        <div class="text-center mb-8">
          <h1 class="text-2xl md:text-3xl font-bold mb-2">
            <span class="gradient-text">关于我</span>
          </h1>
          <p class="text-gray-500 dark:text-gray-400 text-sm">了解博主的技术背景与成长历程</p>
        </div>
        
        <div v-if="isLoading" class="flex justify-center py-16">
          <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        </div>

        <template v-else-if="profile">
          <div class="glass-card p-8 md:p-12 mb-8">
            <div class="flex flex-col md:flex-row items-center gap-8">
              <div class="relative">
                <div class="w-32 h-32 md:w-40 md:h-40 rounded-full bg-gradient-to-br from-primary to-accent p-1">
                  <div class="w-full h-full rounded-full bg-gray-100 dark:bg-dark-100 flex items-center justify-center text-4xl md:text-5xl font-bold text-primary">
                    {{ profile.name?.charAt(0)?.toUpperCase() || 'T' }}{{ profile.name?.charAt(1)?.toUpperCase() || 'E' }}
                  </div>
                </div>
                <div class="absolute -bottom-2 -right-2 w-10 h-10 rounded-full bg-cyber-green flex items-center justify-center">
                  <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>

              <div class="flex-1 text-center md:text-left">
                <h1 class="text-2xl md:text-3xl font-bold mb-2">
                  <span class="gradient-text">{{ profile.name }}</span>
                </h1>
                <p v-if="profile.alias" class="text-xl text-gray-400 mb-4">{{ profile.alias }}</p>
                <p v-if="profile.slogan" class="text-primary font-medium mb-4">{{ profile.slogan }}</p>
                <div v-if="profile.tags?.length" class="flex flex-wrap justify-center md:justify-start gap-2 mb-6">
                  <span
                    v-for="tag in profile.tags"
                    :key="tag"
                    class="px-3 py-1 bg-primary/10 border border-primary/30 rounded-full text-primary text-sm"
                  >
                    {{ tag }}
                  </span>
                </div>
                <p v-if="profile.bio" class="text-gray-600 dark:text-gray-300 leading-relaxed">{{ profile.bio }}</p>
              </div>
            </div>
          </div>

          <div v-if="profile.tech_stack?.length" class="glass-card p-8 mb-8">
            <h2 class="text-2xl font-bold mb-6 flex items-center gap-3">
              <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              <span class="gradient-text">技术栈图谱</span>
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div
                v-for="stack in profile.tech_stack"
                :key="stack.category"
                class="p-4 bg-gray-50 dark:bg-dark-100/50 rounded-xl border border-gray-200 dark:border-white/5"
              >
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">{{ stack.category }}</h3>
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="item in stack.items"
                    :key="item"
                    class="tag"
                  >
                    {{ item }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="profile.journey?.length" class="glass-card p-8 mb-8">
            <h2 class="text-2xl font-bold mb-6 flex items-center gap-3">
              <svg class="w-6 h-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <span class="gradient-text">专业旅程</span>
            </h2>
            <div class="relative">
              <div class="absolute left-4 md:left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary via-accent to-primary" />
              
              <div
                v-for="(item, index) in profile.journey"
                :key="index"
                class="relative pl-12 md:pl-0 pb-12 last:pb-0"
                :class="{ 'md:pr-[50%] md:text-right': index % 2 === 0, 'md:pl-[50%]': index % 2 !== 0 }"
              >
                <div
                  class="absolute left-2 md:left-1/2 top-0 w-4 h-4 rounded-full bg-primary border-4 border-white dark:border-dark transform md:-translate-x-1/2"
                />
                
                <div class="glass-card-hover p-6">
                  <div class="text-primary font-medium mb-1">{{ item.period }}</div>
                  <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-1">{{ item.position }}</h3>
                  <div class="text-accent mb-2">{{ item.company }}</div>
                  <p class="text-gray-500 dark:text-gray-400">{{ item.achievements }}</p>
                </div>
              </div>
            </div>
          </div>

          <div v-if="profile.education" class="glass-card p-8 mb-8">
            <h2 class="text-2xl font-bold mb-6 flex items-center gap-3">
              <svg class="w-6 h-6 text-cyber-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <span class="gradient-text">教育背景</span>
            </h2>
            <div class="glass-card-hover p-6 inline-block">
              <div class="text-primary font-medium mb-1">{{ profile.education.period }}</div>
              <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-1">{{ profile.education.school }}</h3>
              <div class="text-gray-600 dark:text-gray-300">{{ profile.education.major }} · {{ profile.education.degree }}</div>
            </div>
          </div>

          <div v-if="profile.exploration_areas?.length" class="glass-card p-8 mb-8">
            <h2 class="text-2xl font-bold mb-6 flex items-center gap-3">
              <svg class="w-6 h-6 text-cyber-yellow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <span class="gradient-text">技术探索方向</span>
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                v-for="area in profile.exploration_areas"
                :key="area"
                class="flex items-start gap-3 p-4 bg-gray-50 dark:bg-dark-100/50 rounded-lg border border-gray-200 dark:border-white/5 hover:border-primary/30 transition-colors"
              >
                <svg class="w-5 h-5 text-primary flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span class="text-gray-600 dark:text-gray-300">{{ area }}</span>
              </div>
            </div>
          </div>

          <div v-if="profile.social_github || profile.social_blog || profile.social_email" class="glass-card p-8">
            <h2 class="text-2xl font-bold mb-6 flex items-center gap-3">
              <svg class="w-6 h-6 text-cyber-pink" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <span class="gradient-text">社交矩阵</span>
            </h2>
            <div class="flex flex-wrap gap-4">
              <a
                v-if="profile.social_github"
                :href="profile.social_github"
                target="_blank"
                class="flex items-center gap-3 px-6 py-3 bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 rounded-lg hover:border-primary/50 hover:text-primary transition-colors"
              >
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                <span>GitHub</span>
              </a>
              <a
                v-if="profile.social_email"
                :href="`mailto:${profile.social_email}`"
                class="flex items-center gap-3 px-6 py-3 bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 rounded-lg hover:border-accent/50 hover:text-accent transition-colors"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span>Email</span>
              </a>
              <a
                v-if="profile.social_blog"
                :href="profile.social_blog"
                target="_blank"
                class="flex items-center gap-3 px-6 py-3 bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 rounded-lg hover:border-cyber-green/50 hover:text-cyber-green transition-colors"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                <span>Blog</span>
              </a>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
