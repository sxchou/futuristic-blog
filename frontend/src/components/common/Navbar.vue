<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useThemeStore, useAuthStore, useSiteConfigStore, useUserProfileStore } from '@/stores'
import UserAvatar from './UserAvatar.vue'

const route = useRoute()
const router = useRouter()
const themeStore = useThemeStore()
const authStore = useAuthStore()
const siteConfigStore = useSiteConfigStore()
const userProfileStore = useUserProfileStore()

const isMenuOpen = ref(false)

const navLinks = computed(() => [
  { name: '首页', path: '/' },
  { name: '分类', path: '/categories' },
  { name: '标签', path: '/tags' },
  { name: '归档', path: '/archive' },
  { name: '关于', path: '/about' }
])

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const handleLogout = () => {
  authStore.logout()
  userProfileStore.clearProfile()
  router.push('/')
}

const openSearch = () => {
  window.dispatchEvent(new CustomEvent('open-search'))
}

const handleAvatarUpload = () => {
  userProfileStore.refreshProfile()
}

const handleAvatarReset = () => {
  userProfileStore.refreshProfile()
}

watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated) {
    userProfileStore.fetchProfile()
  } else {
    userProfileStore.clearProfile()
  }
})

onMounted(() => {
  siteConfigStore.fetchConfigs()
  if (authStore.isAuthenticated) {
    userProfileStore.fetchProfile()
  }
})
</script>

<template>
  <header class="fixed top-0 left-0 right-0 z-50 bg-white/90 dark:bg-dark-100/90 backdrop-blur-xl border-b border-gray-200/60 dark:border-white/5">
    <nav class="blog-container py-3">
      <div class="flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2.5 group">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <span class="text-lg font-bold text-gray-900 dark:text-white group-hover:text-primary transition-colors">{{ siteConfigStore.siteName }}</span>
        </router-link>

        <div class="hidden md:flex items-center gap-1">
          <router-link
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            class="px-3 py-1.5 rounded-md text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-primary/5 transition-all"
            :class="{ 'text-primary bg-primary/5': isActive(link.path) }"
          >
            {{ link.name }}
          </router-link>
        </div>

        <div class="flex items-center gap-2">
          <button
            data-search-modal
            @click="openSearch"
            class="flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 dark:bg-dark-300 border border-gray-200 dark:border-white/5 rounded-lg text-gray-400 hover:text-primary hover:border-primary/30 transition-all"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span class="text-xs hidden sm:inline">搜索</span>
            <kbd class="px-1 py-0.5 bg-gray-200 dark:bg-dark-400 rounded text-[10px] hidden sm:inline">⌘K</kbd>
          </button>

          <button
            @click="themeStore.toggleTheme"
            class="p-1.5 rounded-lg bg-gray-50 dark:bg-dark-300 border border-gray-200 dark:border-white/5 hover:border-primary/30 hover:text-primary transition-all"
          >
            <svg v-if="themeStore.isDark" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>

          <div v-if="!authStore.isAuthenticated" class="hidden sm:flex items-center gap-1.5">
            <router-link
              to="/login"
              class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-primary transition-colors"
            >
              登录
            </router-link>
            <router-link
              to="/register"
              class="px-3 py-1.5 bg-primary text-white text-sm rounded-lg hover:bg-primary-600 transition-colors"
            >
              注册
            </router-link>
          </div>

          <div v-else class="hidden sm:flex items-center">
            <UserAvatar 
              :profile="userProfileStore.profile" 
              :show-dropdown="true"
              size="sm"
              @upload="handleAvatarUpload"
              @reset="handleAvatarReset"
            />
          </div>

          <button
            @click="isMenuOpen = !isMenuOpen"
            class="md:hidden p-1.5 rounded-lg bg-gray-50 dark:bg-dark-300 border border-gray-200 dark:border-white/5 hover:border-primary/30 transition-all"
          >
            <svg v-if="!isMenuOpen" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 -translate-y-2"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-2"
      >
        <div v-if="isMenuOpen" class="md:hidden mt-3 pt-3 border-t border-gray-200 dark:border-white/5">
          <div class="flex flex-col gap-1">
            <router-link
              v-for="link in navLinks"
              :key="link.path"
              :to="link.path"
              class="px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-primary/5 transition-colors"
              :class="{ 'text-primary bg-primary/5': isActive(link.path) }"
              @click="isMenuOpen = false"
            >
              {{ link.name }}
            </router-link>
            
            <div class="border-t border-gray-200 dark:border-white/5 mt-2 pt-2">
              <template v-if="!authStore.isAuthenticated">
                <router-link
                  to="/login"
                  class="px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-primary/5 transition-colors block"
                  @click="isMenuOpen = false"
                >
                  登录
                </router-link>
                <router-link
                  to="/register"
                  class="px-3 py-2 rounded-lg bg-primary text-white text-sm text-center block"
                  @click="isMenuOpen = false"
                >
                  注册
                </router-link>
              </template>
              <template v-else>
                <div class="flex items-center gap-3 px-3 py-2 mb-1 bg-gray-50 dark:bg-dark-300 rounded-lg">
                  <UserAvatar 
                    :profile="userProfileStore.profile" 
                    :show-dropdown="false"
                    size="sm"
                    @upload="handleAvatarUpload"
                    @reset="handleAvatarReset"
                  />
                  <div class="flex-1 min-w-0">
                    <p class="font-medium text-gray-900 dark:text-white text-sm truncate">
                      {{ userProfileStore.profile?.username || authStore.user?.username || '用户' }}
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ authStore.user?.is_admin ? '管理员' : '用户' }}
                    </p>
                  </div>
                </div>
                <router-link
                  to="/admin/my-profile"
                  class="px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-primary/5 transition-colors block"
                  @click="isMenuOpen = false"
                >
                  我的资料
                </router-link>
                <router-link
                  to="/admin"
                  class="px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-primary/5 transition-colors block"
                  @click="isMenuOpen = false"
                >
                  管理后台
                </router-link>
                <button
                  @click="handleLogout(); isMenuOpen = false"
                  class="px-3 py-2 rounded-lg text-sm text-gray-400 hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/5 transition-colors w-full text-left"
                >
                  退出
                </button>
              </template>
            </div>
          </div>
        </div>
      </transition>
    </nav>
  </header>
</template>
