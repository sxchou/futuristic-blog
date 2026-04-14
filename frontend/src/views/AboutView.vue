<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { profileApi } from '@/api'
import { useSocialLinksStore } from '@/stores'
import BlogSidebar from '@/components/common/BlogSidebar.vue'
import LeftSidebar from '@/components/common/LeftSidebar.vue'
import type { Profile } from '@/types'

const profile = ref<Profile | null>(null)
const isLoading = ref(true)
const socialLinksStore = useSocialLinksStore()

const fetchProfile = async () => {
  try {
    profile.value = await profileApi.getProfile()
  } catch (error) {
    console.error('Failed to fetch profile:', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchProfile()
  socialLinksStore.fetchProfile()
})
</script>

<template>
  <div class="flex flex-col lg:flex-row gap-6">
    <div class="lg:w-56 flex-shrink-0 hidden lg:block lg:order-1">
      <div class="lg:sticky lg:top-20">
        <LeftSidebar />
      </div>
    </div>
    
    <div class="flex-1 min-w-0 lg:order-2">
      <div class="mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2">
          关于我
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          了解博主的技术背景与成长历程
        </p>
      </div>

      <div
        v-if="isLoading"
        class="flex justify-center py-16"
      >
        <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>

      <template v-else-if="profile">
        <div class="glass-card p-6 md:p-8 mb-6">
          <div class="flex flex-col sm:flex-row items-center gap-6">
            <div class="relative">
              <div class="w-24 h-24 md:w-28 md:h-28 rounded-full bg-primary p-0.5">
                <div class="w-full h-full rounded-full bg-gray-100 dark:bg-dark-100 flex items-center justify-center text-3xl md:text-4xl font-bold text-primary">
                  {{ profile.name?.charAt(0)?.toUpperCase() || 'T' }}{{ profile.name?.charAt(1)?.toUpperCase() || 'E' }}
                </div>
              </div>
              <div class="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-cyber-green flex items-center justify-center">
                <svg
                  class="w-3.5 h-3.5 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2.5"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
            </div>

            <div class="flex-1 text-center sm:text-left">
              <h2 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-1">
                {{ profile.name }}
              </h2>
              <p
                v-if="profile.alias"
                class="text-base text-gray-400 mb-2"
              >
                {{ profile.alias }}
              </p>
              <p
                v-if="profile.slogan"
                class="text-primary font-medium text-sm mb-3"
              >
                {{ profile.slogan }}
              </p>
              <div
                v-if="profile.tags?.length"
                class="flex flex-wrap justify-center sm:justify-start gap-1.5 mb-3"
              >
                <span
                  v-for="tag in profile.tags"
                  :key="tag"
                  class="px-2.5 py-0.5 bg-primary/10 border border-primary/20 rounded-full text-primary text-xs font-medium"
                >
                  {{ tag }}
                </span>
              </div>
              <p
                v-if="profile.bio"
                class="text-gray-600 dark:text-gray-300 text-sm leading-relaxed"
              >
                {{ profile.bio }}
              </p>
            </div>
          </div>
        </div>

        <div
          v-if="profile.tech_stack?.length"
          class="glass-card p-6 mb-6"
        >
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
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
                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
              />
            </svg>
            技术栈图谱
          </h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div
              v-for="stack in profile.tech_stack"
              :key="stack.category"
              class="p-4 bg-gray-50 dark:bg-dark-300/50 rounded-xl border border-gray-100 dark:border-white/5"
            >
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-2.5">
                {{ stack.category }}
              </h3>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="item in stack.items"
                  :key="item"
                  class="tag-badge bg-gray-100 dark:bg-dark-200 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-white/10"
                >
                  {{ item }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="profile.journey?.length"
          class="glass-card p-6 mb-6"
        >
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <svg
              class="w-5 h-5 text-accent"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            专业旅程
          </h2>
          <div class="relative">
            <div class="absolute left-3.5 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary via-accent to-primary/20" />
            <div
              v-for="(item, index) in profile.journey"
              :key="index"
              class="relative pl-10 pb-6 last:pb-0"
            >
              <div class="absolute left-1 top-1 w-5 h-5 rounded-full bg-primary border-4 border-white dark:border-dark-200" />
              <div class="glass-card-hover p-4">
                <div class="text-primary font-medium text-sm mb-0.5">
                  {{ item.period }}
                </div>
                <h3 class="text-base font-bold text-gray-900 dark:text-white mb-0.5">
                  {{ item.position }}
                </h3>
                <div class="text-accent text-sm mb-1.5">
                  {{ item.company }}
                </div>
                <p class="text-gray-500 dark:text-gray-400 text-sm">
                  {{ item.achievements }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="profile.education"
          class="glass-card p-6 mb-6"
        >
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <svg
              class="w-5 h-5 text-cyber-green"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
              />
            </svg>
            教育背景
          </h2>
          <div class="glass-card-hover p-4 inline-block">
            <div class="text-primary font-medium text-sm mb-0.5">
              {{ profile.education.period }}
            </div>
            <h3 class="text-base font-bold text-gray-900 dark:text-white mb-0.5">
              {{ profile.education.school }}
            </h3>
            <div class="text-gray-600 dark:text-gray-300 text-sm">
              {{ profile.education.major }} · {{ profile.education.degree }}
            </div>
          </div>
        </div>

        <div
          v-if="profile.exploration_areas?.length"
          class="glass-card p-6 mb-6"
        >
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <svg
              class="w-5 h-5 text-cyber-yellow"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            技术探索方向
          </h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div
              v-for="area in profile.exploration_areas"
              :key="area"
              class="flex items-start gap-2.5 p-3 bg-gray-50 dark:bg-dark-300/50 rounded-lg border border-gray-100 dark:border-white/5 hover:border-primary/30 transition-colors"
            >
              <svg
                class="w-4 h-4 text-primary flex-shrink-0 mt-0.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              <span class="text-gray-600 dark:text-gray-300 text-sm">{{ area }}</span>
            </div>
          </div>
        </div>

        <div
          v-if="socialLinksStore.hasSocialLinks"
          class="glass-card p-6"
        >
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <svg
              class="w-5 h-5 text-cyber-pink"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            社交矩阵
          </h2>
          <div class="flex flex-wrap gap-3">
            <a
              v-for="link in socialLinksStore.socialLinks"
              :key="link.id"
              :href="link.url"
              :target="link.type === 'link' ? '_blank' : undefined"
              :rel="link.type === 'link' ? 'noopener noreferrer' : undefined"
              :class="['flex items-center gap-2 px-4 py-2.5 bg-gray-50 dark:bg-dark-300/50 border border-gray-200 dark:border-white/10 rounded-lg transition-colors text-sm', link.color, link.hoverColor]"
            >
              <svg
                v-if="link.icon === 'github'"
                class="w-4 h-4"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
              <svg
                v-else-if="link.icon === 'email'"
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
              <svg
                v-else-if="link.icon === 'blog'"
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
                />
              </svg>
              <span>{{ link.name }}</span>
            </a>
          </div>
        </div>
      </template>
    </div>

    <div class="lg:w-56 flex-shrink-0 hidden lg:block lg:order-3">
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
