<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useThemeStore, useAuthStore, useSiteConfigStore, useUserProfileStore } from '@/stores'
import UserAvatar from './UserAvatar.vue'
import AuthMenu from './AuthMenu.vue'

const route = useRoute()
const router = useRouter()
const themeStore = useThemeStore()
const authStore = useAuthStore()
const siteConfigStore = useSiteConfigStore()
const userProfileStore = useUserProfileStore()

const isMenuOpen = ref(false)
const isDesktopDropdownOpen = ref(false)

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

const getLogoUrl = (url: string) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  if (url.startsWith('/')) return url
  return `/${url}`
}

watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated) {
    userProfileStore.fetchProfile()
  } else {
    userProfileStore.clearProfile()
  }
})

watch(isDesktopDropdownOpen, (isOpen) => {
  if (isOpen) {
    document.addEventListener('click', handleDesktopDropdownClickOutside)
  } else {
    document.removeEventListener('click', handleDesktopDropdownClickOutside)
  }
})

const handleDesktopDropdownClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.desktop-dropdown-container')) {
    isDesktopDropdownOpen.value = false
  }
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    userProfileStore.fetchProfile()
  }
})
</script>

<template>
  <header class="fixed top-0 left-0 right-0 z-50 bg-white/90 dark:bg-dark-100/90 backdrop-blur-xl border-b border-gray-200/60 dark:border-white/5">
    <nav class="blog-container py-3">
      <div class="flex items-center justify-between">
        <router-link
          to="/"
          class="flex items-center gap-2.5 group"
        >
          <div
            v-if="siteConfigStore.siteLogoUrl"
            class="w-8 h-8 rounded-lg overflow-hidden bg-gray-100 dark:bg-dark-200"
          >
            <img
              :src="getLogoUrl(siteConfigStore.siteLogoUrl)"
              :alt="siteConfigStore.siteName"
              class="w-full h-full object-contain"
            >
          </div>
          <div
            v-else
            class="w-8 h-8 rounded-lg bg-black flex items-center justify-center relative overflow-hidden"
          >
            <svg
              viewBox="0 0 100 100"
              class="w-6 h-6"
            >
              <defs>
                <linearGradient
                  id="navbar-logo-grad"
                  x1="0%"
                  y1="0%"
                  x2="100%"
                  y2="100%"
                >
                  <stop
                    offset="0%"
                    style="stop-color:#00d4ff;stop-opacity:1"
                  />
                  <stop
                    offset="100%"
                    style="stop-color:#7c3aed;stop-opacity:1"
                  />
                </linearGradient>
              </defs>
              <text
                x="50"
                y="68"
                font-family="monospace"
                font-size="55"
                font-weight="bold"
                fill="url(#navbar-logo-grad)"
                text-anchor="middle"
              >F</text>
              <circle
                cx="75"
                cy="25"
                r="8"
                fill="#00d4ff"
                opacity="0.8"
              />
              <circle
                cx="85"
                cy="35"
                r="4"
                fill="#7c3aed"
                opacity="0.6"
              />
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
            class="flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 dark:bg-dark-300 border border-gray-200 dark:border-white/5 rounded-lg text-gray-400 hover:text-primary hover:border-primary/30 transition-all"
            @click="openSearch"
          >
            <svg
              class="w-3.5 h-3.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <span class="text-xs hidden sm:inline">搜索</span>
            <kbd class="px-1 py-0.5 bg-gray-200 dark:bg-dark-400 rounded text-[10px] hidden sm:inline">⌘K</kbd>
          </button>

          <button
            class="p-1.5 rounded-lg bg-gray-50 dark:bg-dark-300 border border-gray-200 dark:border-white/5 hover:border-primary/30 hover:text-primary transition-all"
            @click="themeStore.toggleTheme"
          >
            <svg
              v-if="themeStore.isDark"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
              />
            </svg>
            <svg
              v-else
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
              />
            </svg>
          </button>

          <div
            v-if="!authStore.isAuthenticated"
            class="hidden md:flex items-center"
          >
            <AuthMenu />
          </div>

          <div
            v-else
            class="hidden md:flex items-center relative desktop-dropdown-container"
          >
            <button
              class="p-1.5 rounded-lg bg-gray-50 dark:bg-dark-300 border border-gray-200 dark:border-white/5 hover:border-primary/30 hover:text-primary transition-all"
              @click="isDesktopDropdownOpen = !isDesktopDropdownOpen"
            >
              <svg
                class="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            
            <transition
              enter-active-class="transition duration-200 ease-out"
              enter-from-class="opacity-0 scale-95 -translate-y-2"
              enter-to-class="opacity-100 scale-100 translate-y-0"
              leave-active-class="transition duration-150 ease-in"
              leave-from-class="opacity-100 scale-100 translate-y-0"
              leave-to-class="opacity-0 scale-95 -translate-y-2"
            >
              <div
                v-if="isDesktopDropdownOpen"
                class="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden z-50"
              >
                <div class="p-3 border-b border-gray-200 dark:border-gray-700">
                  <div class="flex items-center gap-3">
                    <div
                      class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-sm overflow-hidden"
                      :style="{
                        backgroundColor: userProfileStore.profile?.default_avatar_gradient?.[0] || '#667eea',
                        backgroundImage: userProfileStore.profile?.avatar_type === 'custom' && userProfileStore.profile?.avatar_url 
                          ? `url(${userProfileStore.profile.avatar_url})` 
                          : userProfileStore.profile?.oauth_avatar_url 
                            ? `url(${userProfileStore.profile.oauth_avatar_url})` 
                            : 'none',
                        backgroundSize: 'cover',
                        backgroundPosition: 'center'
                      }"
                    >
                      <span v-if="!userProfileStore.profile?.avatar_url && !userProfileStore.profile?.oauth_avatar_url">
                        {{ (userProfileStore.profile?.username || authStore.user?.username || 'U').charAt(0).toUpperCase() }}
                      </span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="font-medium text-gray-900 dark:text-white truncate">
                        {{ userProfileStore.profile?.username || authStore.user?.username || '用户' }}
                      </p>
                      <p class="text-xs text-gray-500 dark:text-gray-400">
                        {{ authStore.user?.is_admin ? '管理员' : '用户' }}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div class="p-2">
                  <router-link
                    to="/profile"
                    class="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
                    @click="isDesktopDropdownOpen = false"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    个人中心
                  </router-link>
                  
                  <router-link
                    to="/admin/my-profile"
                    class="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
                    @click="isDesktopDropdownOpen = false"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7zM12 11a4 4 0 100-8 4 4 0 000 8z"
                      />
                    </svg>
                    个人资料
                  </router-link>
                  
                  <router-link
                    to="/admin"
                    class="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
                    @click="isDesktopDropdownOpen = false"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                      />
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                    </svg>
                    管理后台
                  </router-link>
                </div>
                
                <div class="p-2 border-t border-gray-200 dark:border-gray-700">
                  <button
                    class="w-full px-3 py-2 text-left text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors flex items-center gap-2"
                    @click="handleLogout(); isDesktopDropdownOpen = false"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                      />
                    </svg>
                    退出登录
                  </button>
                </div>
              </div>
            </transition>
          </div>

          <button
            class="md:hidden p-1.5 rounded-lg bg-gray-50 dark:bg-dark-300 border border-gray-200 dark:border-white/5 hover:border-primary/30 transition-all"
            @click="isMenuOpen = !isMenuOpen"
          >
            <svg
              v-if="!isMenuOpen"
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
            <svg
              v-else
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
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
        <div
          v-if="isMenuOpen"
          class="md:hidden mt-3 pt-3 border-t border-gray-200 dark:border-white/5"
        >
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
                  to="/profile"
                  class="px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-primary/5 transition-colors block"
                  @click="isMenuOpen = false"
                >
                  个人中心
                </router-link>
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
                  class="px-3 py-2 rounded-lg text-sm text-gray-400 hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/5 transition-colors w-full text-left"
                  @click="handleLogout(); isMenuOpen = false"
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
