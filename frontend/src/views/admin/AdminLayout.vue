<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore, useSiteConfigStore, useUserProfileStore } from '@/stores'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const siteConfigStore = useSiteConfigStore()
const userProfileStore = useUserProfileStore()

const isSidebarOpen = ref(true)

const menuItems = [
  { name: '仪表盘', path: '/admin', icon: 'dashboard' },
  { name: '文章管理', path: '/admin/articles', icon: 'article' },
  { name: '分类管理', path: '/admin/categories', icon: 'category' },
  { name: '标签管理', path: '/admin/tags', icon: 'tag' },
  { name: '评论管理', path: '/admin/comments', icon: 'comments' },
  { name: '用户管理', path: '/admin/users', icon: 'user' },
  { name: '资源管理', path: '/admin/resources', icon: 'resource' },
  { name: '邮件管理', path: '/admin/email', icon: 'email' },
  { name: '通知管理', path: '/admin/notifications', icon: 'notification' },
  { name: '日志管理', path: '/admin/logs', icon: 'logs' },
  { name: '网站设置', path: '/admin/settings', icon: 'settings' },
  { name: '授权管理', path: '/admin/oauth', icon: 'oauth' },
  { name: '我的资料', path: '/admin/my-profile', icon: 'profile' },
  { name: '网站资料', path: '/admin/profile', icon: 'site-profile' },
]

const isActive = (path: string) => {
  if (path === '/admin') {
    return route.path === '/admin'
  }
  return route.path.startsWith(path)
}

const handleLogout = () => {
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

onMounted(() => {
  siteConfigStore.fetchConfigs()
  if (authStore.isAuthenticated) {
    userProfileStore.fetchProfile()
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-100 dark:bg-dark-200 flex">
    <aside
      :class="[
        'fixed lg:static inset-y-0 left-0 z-50 w-52 bg-white dark:bg-dark-100 border-r border-gray-200 dark:border-white/10 transform transition-transform duration-300',
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      ]"
    >
      <div class="flex flex-col h-full">
        <div class="p-4 border-b border-gray-200 dark:border-white/10">
          <router-link to="/" class="flex items-center gap-2">
            <span class="text-base font-bold gradient-text">{{ siteConfigStore.siteName }}</span>
          </router-link>
        </div>

        <nav class="flex-1 p-3 space-y-1">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            :class="[
              'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors text-sm',
              isActive(item.path)
                ? 'bg-primary/20 text-primary'
                : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 hover:text-gray-900 dark:hover:text-white'
            ]"
          >
            <svg v-if="item.icon === 'dashboard'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
            <svg v-else-if="item.icon === 'article'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <svg v-else-if="item.icon === 'category'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            <svg v-else-if="item.icon === 'tag'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            <svg v-else-if="item.icon === 'comments'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <svg v-else-if="item.icon === 'user'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else-if="item.icon === 'resource'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            <svg v-else-if="item.icon === 'email'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <svg v-else-if="item.icon === 'notification'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <svg v-else-if="item.icon === 'logs'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
            </svg>
            <svg v-else-if="item.icon === 'settings'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <svg v-else-if="item.icon === 'profile'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <svg v-else-if="item.icon === 'site-profile'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-18 0 9 9 0 0118 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
            </svg>
            <svg v-else-if="item.icon === 'oauth'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
            </svg>
            <span>{{ item.name }}</span>
          </router-link>
        </nav>

        <div class="p-3 border-t border-gray-200 dark:border-white/10">
          <div class="flex items-center gap-2 mb-3">
            <div 
              class="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm overflow-hidden"
              :style="sidebarAvatarStyle"
            >
              <span v-if="showSidebarAvatarInitial">{{ authStore.user?.username?.charAt(0).toUpperCase() || 'A' }}</span>
            </div>
            <div>
              <p class="text-gray-900 dark:text-white font-medium text-sm">{{ authStore.user?.username || 'Admin' }}</p>
              <p class="text-gray-500 text-xs">{{ authStore.user?.is_admin ? '管理员' : '普通用户' }}</p>
            </div>
          </div>
          <button
            @click="handleLogout"
            class="w-full py-1.5 text-gray-400 hover:text-red-400 transition-colors text-left text-sm"
          >
            退出登录
          </button>
        </div>
      </div>
    </aside>

    <div class="flex-1 flex flex-col min-h-screen">
      <header class="sticky top-0 z-40 bg-white/80 dark:bg-dark-200/80 backdrop-blur-lg border-b border-gray-200 dark:border-white/10 px-4 py-3">
        <div class="flex items-center justify-between">
          <button
            @click="isSidebarOpen = !isSidebarOpen"
            class="lg:hidden p-1.5 rounded-lg bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 hover:border-primary/50 transition-colors"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <div class="flex items-center gap-4">
            <router-link
              to="/"
              class="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary/10 to-accent/10 hover:from-primary/20 hover:to-accent/20 border border-primary/20 hover:border-primary/40 rounded-lg transition-all duration-300 group"
            >
              <svg class="w-4 h-4 text-primary group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              <span class="text-sm font-medium bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">访问前台</span>
            </router-link>
          </div>
        </div>
      </header>

      <main class="flex-1 p-4">
        <router-view />
      </main>
    </div>

    <div
      v-if="isSidebarOpen"
      @click="isSidebarOpen = false"
      class="fixed inset-0 bg-black/50 z-40 lg:hidden"
    />
  </div>
</template>
