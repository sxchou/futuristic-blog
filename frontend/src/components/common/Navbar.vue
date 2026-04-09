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
  { name: '关于我', path: '/about' },
  { name: '分类', path: '/categories' },
  { name: '标签', path: '/tags' },
  { name: '资源', path: '/resources' },
  { name: '归档', path: '/archive' }
])

const isActive = (path: string) => {
  return route.path === path
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
  <header class="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-dark-100/80 backdrop-blur-xl border-b border-white/10">
    <nav class="container mx-auto px-4 py-2">
      <div class="flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2 group">
          <span class="text-xl font-bold gradient-text">{{ siteConfigStore.siteName }}</span>
        </router-link>

        <div class="hidden md:flex items-center gap-6">
          <router-link
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            class="relative text-gray-600 dark:text-gray-300 hover:text-primary transition-colors py-1 text-base"
            :class="{ 'text-primary': isActive(link.path) }"
          >
            {{ link.name }}
            <span
              v-if="isActive(link.path)"
              class="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary to-accent"
            />
          </router-link>
        </div>

        <div class="flex items-center gap-3">
          <button
            data-search-modal
            @click="openSearch"
            class="flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 rounded-lg text-gray-500 dark:text-gray-400 hover:border-primary/50 transition-colors"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span class="text-sm hidden sm:inline">搜索</span>
            <kbd class="px-1.5 py-0.5 bg-gray-200 dark:bg-dark-100 rounded text-sm hidden sm:inline">⌘K</kbd>
          </button>

          <button
            @click="themeStore.toggleTheme"
            class="p-1.5 rounded-lg bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 hover:border-primary/50 transition-colors"
          >
            <svg v-if="themeStore.isDark" class="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else class="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>

          <div v-if="!authStore.isAuthenticated" class="hidden sm:flex items-center gap-2">
            <router-link
              to="/login"
              class="px-3 py-1.5 text-gray-600 dark:text-gray-300 hover:text-primary transition-colors text-base"
            >
              登录
            </router-link>
            <router-link
              to="/register"
              class="px-3 py-1.5 bg-gradient-to-r from-primary to-accent text-white rounded-lg hover:opacity-90 transition-opacity text-base"
            >
              注册
            </router-link>
          </div>

          <div v-else class="hidden sm:flex items-center gap-3">
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
            class="md:hidden p-2 rounded-lg bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 hover:border-primary/50 transition-colors"
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
        <div v-if="isMenuOpen" class="md:hidden mt-4 pt-4 border-t border-gray-200 dark:border-white/10">
          <div class="flex flex-col gap-2">
            <router-link
              v-for="link in navLinks"
              :key="link.path"
              :to="link.path"
              class="px-4 py-2 rounded-lg text-gray-600 dark:text-gray-300 hover:text-primary hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
              :class="{ 'text-primary bg-primary/10': isActive(link.path) }"
              @click="isMenuOpen = false"
            >
              {{ link.name }}
            </router-link>
            
            <div class="border-t border-gray-200 dark:border-white/10 mt-2 pt-2">
              <template v-if="!authStore.isAuthenticated">
                <router-link
                  to="/login"
                  class="px-4 py-2 rounded-lg text-gray-600 dark:text-gray-300 hover:text-primary hover:bg-gray-100 dark:hover:bg-white/5 transition-colors block"
                  @click="isMenuOpen = false"
                >
                  登录
                </router-link>
                <router-link
                  to="/register"
                  class="px-4 py-2 rounded-lg bg-gradient-to-r from-primary to-accent text-white text-center block"
                  @click="isMenuOpen = false"
                >
                  注册
                </router-link>
              </template>
              <template v-else>
                <div class="flex items-center gap-3 px-4 py-3 mb-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <UserAvatar 
                    :profile="userProfileStore.profile" 
                    :show-dropdown="false"
                    size="sm"
                    @upload="handleAvatarUpload"
                    @reset="handleAvatarReset"
                  />
                  <div class="flex-1 min-w-0">
                    <p class="font-medium text-gray-900 dark:text-white truncate">
                      {{ userProfileStore.profile?.username || authStore.user?.username || '用户' }}
                    </p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">
                      {{ authStore.user?.is_admin ? '管理员' : '用户' }}
                    </p>
                  </div>
                </div>
                <router-link
                  to="/admin/my-profile"
                  class="px-4 py-2 rounded-lg text-gray-600 dark:text-gray-300 hover:text-primary hover:bg-gray-100 dark:hover:bg-white/5 transition-colors block"
                  @click="isMenuOpen = false"
                >
                  我的资料
                </router-link>
                <router-link
                  to="/admin"
                  class="px-4 py-2 rounded-lg text-gray-600 dark:text-gray-300 hover:text-primary hover:bg-gray-100 dark:hover:bg-white/5 transition-colors block"
                  @click="isMenuOpen = false"
                >
                  管理后台
                </router-link>
                <button
                  @click="handleLogout(); isMenuOpen = false"
                  class="px-4 py-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors w-full text-left"
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
