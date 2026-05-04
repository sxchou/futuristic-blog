<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore, useSiteConfigStore, useUserProfileStore, useThemeStore, usePermissionStore, useDialogStore } from '@/stores'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const siteConfigStore = useSiteConfigStore()
const userProfileStore = useUserProfileStore()
const themeStore = useThemeStore()
const permissionStore = usePermissionStore()
const dialog = useDialogStore()

const isSidebarOpen = ref(false)

const allMenuItems = [
  { name: '仪表盘', path: '/admin', icon: 'dashboard', permission: 'dashboard.view' },
  { name: '文章管理', path: '/admin/articles', icon: 'article', permission: 'article.view' },
  { name: '分类管理', path: '/admin/categories', icon: 'category', permission: 'category.view' },
  { name: '标签管理', path: '/admin/tags', icon: 'tag', permission: 'tag.view' },
  { name: '资源管理', path: '/admin/resources', icon: 'resource', permission: 'resource.view' },
  { name: '评论管理', path: '/admin/comments', icon: 'comments', permission: 'comment.view' },
  { name: '角色管理', path: '/admin/roles', icon: 'role', permission: 'role.view' },
  { name: '用户管理', path: '/admin/users', icon: 'user', permission: 'user.view' },
  { name: '邮件服务', path: '/admin/email', icon: 'email', permission: 'email.view' },
  { name: '通知设置', path: '/admin/notifications', icon: 'notification', permission: 'notification.view' },
  { name: '系统日志', path: '/admin/logs', icon: 'logs', permission: 'log.view' },
  { name: '公告中心', path: '/admin/announcements', icon: 'announcement', permission: 'announcement.view' },
  { name: '文件存储', path: '/admin/storage', icon: 'storage', permission: 'storage.view' },
  { name: '我的资料', path: '/admin/my-profile', icon: 'profile', permission: null },
  { name: '网站资料', path: '/admin/profile', icon: 'site-profile', permission: 'profile.view' },
  { name: '系统设置', path: '/admin/settings', icon: 'settings', permission: 'settings.view' },
  { name: 'OAuth授权', path: '/admin/oauth', icon: 'oauth', permission: 'oauth.view' },
]

const menuItems = computed(() => {
  return allMenuItems
})

const hasMenuPermission = (item: { permission: string | null }) => {
  if (!item.permission) return true
  return permissionStore.hasPermission(item.permission)
}

const currentRoutePermission = computed(() => {
  const currentPath = route.path
  const menuItem = allMenuItems.find(item => {
    if (item.path === '/admin') {
      return currentPath === '/admin'
    }
    return currentPath.startsWith(item.path)
  })
  return menuItem?.permission || null
})

const hasCurrentRoutePermission = computed(() => {
  if (!currentRoutePermission.value) return true
  return permissionStore.hasPermission(currentRoutePermission.value)
})

const isActive = (path: string) => {
  if (path === '/admin') {
    return route.path === '/admin'
  }
  return route.path.startsWith(path)
}

const handleMenuClick = (item: { permission: string | null; name: string; path: string }) => {
  if (window.innerWidth < 1024) {
    isSidebarOpen.value = false
  }
  router.push(item.path)
}

const handleLogout = async () => {
  const confirmed = await dialog.showConfirm({
    title: '退出登录',
    message: '确定要退出登录吗？',
    confirmText: '退出',
    cancelText: '取消'
  })
  if (!confirmed) return
  authStore.logout()
  router.push('/')
}

const sidebarAvatarStyle = computed(() => {
  const profile = userProfileStore.profile
  if (profile?.avatar_type === 'custom' && profile.avatar_url) {
    return {
      backgroundImage: `url(${profile.avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (profile?.avatar_type === 'oauth' && profile.oauth_avatar_url) {
    return {
      backgroundImage: `url(${profile.oauth_avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (profile?.default_avatar_gradient && profile.default_avatar_gradient.length >= 1) {
    return {
      backgroundColor: profile.default_avatar_gradient[0]
    }
  }
  
  return {
    backgroundColor: '#667eea'
  }
})

const showSidebarAvatarInitial = computed(() => {
  const profile = userProfileStore.profile
  return !profile?.avatar_type || profile.avatar_type === 'default' || 
         (profile.avatar_type === 'custom' && !profile.avatar_url) ||
         (profile.avatar_type === 'oauth' && !profile.oauth_avatar_url)
})

const getLogoUrl = (url: string) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  if (url.startsWith('/')) return url
  return `/${url}`
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    userProfileStore.fetchProfile()
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-100 dark:bg-dark-100 flex">
    <aside
      :class="[
        'fixed top-0 left-0 z-50 w-52 bg-white dark:bg-dark-100 border-r border-gray-200 dark:border-white/10 transform transition-transform duration-300 flex-shrink-0 h-[100dvh]',
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      ]"
    >
      <div class="flex flex-col h-full overflow-hidden">
        <div class="p-4 border-b border-gray-200 dark:border-white/10 shrink-0">
          <router-link
            to="/"
            class="flex items-center gap-2"
          >
            <div
              v-if="siteConfigStore.siteLogoUrl"
              class="w-7 h-7 rounded-full overflow-hidden bg-gray-100 dark:bg-dark-200 shrink-0"
            >
              <img
                :src="getLogoUrl(siteConfigStore.siteLogoUrl)"
                :alt="siteConfigStore.siteName"
                class="w-full h-full object-contain"
              >
            </div>
            <div
              v-else
              class="w-7 h-7 rounded-full bg-black flex items-center justify-center relative overflow-hidden shrink-0"
            >
              <svg
                viewBox="0 0 100 100"
                class="w-5 h-5"
              >
                <defs>
                  <linearGradient
                    id="admin-logo-grad"
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
                  font-size="50"
                  font-weight="bold"
                  fill="url(#admin-logo-grad)"
                  text-anchor="middle"
                >
                  F
                </text>
              </svg>
            </div>
            <span class="text-base font-bold text-gray-900 dark:text-white">{{ siteConfigStore.siteName }}</span>
          </router-link>
        </div>

        <nav class="flex-1 p-3 space-y-1 overflow-y-auto">
          <a
            v-for="item in menuItems"
            :key="item.path"
            href="javascript:void(0)"
            :class="[
              'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors text-sm',
              isActive(item.path)
                ? 'bg-primary/20 text-primary'
                : hasMenuPermission(item)
                  ? 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 hover:text-gray-900 dark:hover:text-white'
                  : 'text-gray-300 dark:text-gray-600 cursor-not-allowed'
            ]"
            @click="handleMenuClick(item)"
          >
            <svg
              v-if="item.icon === 'dashboard'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'article'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'category'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'tag'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'comments'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'user'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'role'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'resource'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'email'"
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
              v-else-if="item.icon === 'notification'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'logs'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'settings'"
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
            <svg
              v-else-if="item.icon === 'announcement'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'profile'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'site-profile'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 12a9 9 0 01-18 0 9 9 0 0118 0z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'oauth'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
              />
            </svg>
            <svg
              v-else-if="item.icon === 'storage'"
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
              />
            </svg>
            <span>{{ item.name }}</span>
            <svg
              v-if="item.permission && !hasMenuPermission(item)"
              class="w-3 h-3 ml-auto text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </a>
        </nav>

        <div class="p-3 border-t border-gray-200 dark:border-white/10 shrink-0">
          <div class="flex items-center gap-2 mb-3">
            <div 
              class="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm overflow-hidden"
              :style="sidebarAvatarStyle"
            >
              <span v-if="showSidebarAvatarInitial">{{ authStore.user?.username?.charAt(0).toUpperCase() || 'A' }}</span>
            </div>
            <div>
              <p class="text-gray-900 dark:text-white font-medium text-sm">
                {{ authStore.user?.username || 'Admin' }}
              </p>
              <p class="text-gray-500 text-xs">
                <template v-if="authStore.user?.roles && authStore.user.roles.length > 0">
                  {{ authStore.user.roles.map(r => r.name).join('、') }}
                </template>
                <template v-else>普通用户</template>
              </p>
            </div>
          </div>
          <button
            class="w-full py-1.5 text-gray-400 hover:text-red-400 transition-colors text-left text-sm"
            @click="handleLogout"
          >
            退出登录
          </button>
        </div>
      </div>
    </aside>

    <div class="flex-1 flex flex-col min-h-screen min-w-0 lg:ml-52">
      <header class="sticky top-0 z-40 bg-white/90 dark:bg-dark-100/90 backdrop-blur-lg border-b border-gray-200 dark:border-white/10 px-3 sm:px-4 py-3">
        <div class="flex items-center justify-between">
          <button
            class="lg:hidden p-1.5 rounded-lg bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 hover:border-primary/50 transition-colors"
            @click="isSidebarOpen = !isSidebarOpen"
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
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>

          <div class="flex items-center gap-2 sm:gap-4">
            <button
              class="p-1.5 rounded-lg bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 hover:border-primary/30 hover:text-primary transition-all"
              title="切换主题"
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

            <router-link
              to="/"
              class="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-4 py-2 bg-primary/10 hover:bg-primary/20 border border-primary/20 hover:border-primary/40 rounded-lg transition-all duration-300 group"
            >
              <svg
                class="w-4 h-4 text-primary group-hover:scale-110 transition-transform"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                />
              </svg>
              <span class="text-xs sm:text-sm font-medium text-primary">访问前台</span>
            </router-link>
          </div>
        </div>
      </header>

      <main class="flex-1 p-3 sm:p-4">
        <div
          v-if="!hasCurrentRoutePermission"
          class="min-h-[60vh] flex items-center justify-center"
        >
          <div class="glass-card p-8 max-w-md w-full text-center">
            <div class="relative mb-6">
              <div class="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center">
                <svg
                  class="w-10 h-10 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              </div>
            </div>

            <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
              权限不足
            </h2>
            <p class="text-gray-500 dark:text-gray-400 mb-6">
              无此页面访问权限，请联系管理员
            </p>

            <div class="bg-gray-50 dark:bg-dark-200 rounded-xl p-4 mb-6">
              <div class="flex items-center gap-3 mb-3">
                <div
                  class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm overflow-hidden"
                  :style="sidebarAvatarStyle"
                >
                  <span v-if="showSidebarAvatarInitial">{{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}</span>
                </div>
                <div class="text-left">
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ authStore.user?.username || '未知用户' }}
                  </p>
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    {{ permissionStore.myRoles?.map(r => r.name).join('、') || '' }}
                  </p>
                </div>
              </div>
              
              <div class="border-t border-gray-200 dark:border-gray-700 pt-3">
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-500 dark:text-gray-400">缺少权限</span>
                  <span class="px-2 py-0.5 bg-primary/10 text-primary rounded font-mono text-xs">
                    {{ currentRoutePermission }}
                  </span>
                </div>
              </div>
            </div>

            <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mb-6">
              <div class="flex items-start gap-2">
                <svg
                  class="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p class="text-sm text-blue-700 dark:text-blue-300 text-left">
                  如需获取此权限，请联系系统管理员为您分配相应的角色或权限。
                </p>
              </div>
            </div>

            <div class="flex flex-col sm:flex-row gap-3">
              <router-link
                to="/"
                class="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-100 dark:bg-dark-200 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-200 dark:hover:bg-dark-300 transition-colors"
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
                    d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                  />
                </svg>
                返回首页
              </router-link>
              <router-link
                to="/admin/my-profile"
                class="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-100 dark:bg-dark-200 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-200 dark:hover:bg-dark-300 transition-colors"
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
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  />
                </svg>
                我的资料
              </router-link>
            </div>
          </div>
        </div>
        <router-view v-else />
      </main>
    </div>

    <div
      v-if="isSidebarOpen"
      class="fixed inset-0 bg-black/50 z-40 lg:hidden"
      @click="isSidebarOpen = false"
    />
  </div>
</template>
