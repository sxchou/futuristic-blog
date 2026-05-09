import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore, useSiteConfigStore, useInitStore } from '@/stores'

const CHUNK_LOAD_ERROR_KEY = 'chunk_load_error_reload'

const isChunkLoadError = (error: unknown): boolean => {
  if (error instanceof Error) {
    return (
      error.message.includes('Failed to fetch dynamically imported module') ||
      error.message.includes('Loading chunk') ||
      error.message.includes('Loading CSS chunk') ||
      error.message.includes('Unable to preload CSS') ||
      error.name === 'ChunkLoadError'
    )
  }
  return false
}

const handleChunkLoadError = (error: unknown): boolean => {
  if (!isChunkLoadError(error)) return false
  
  const reloadCount = parseInt(sessionStorage.getItem(CHUNK_LOAD_ERROR_KEY) || '0')
  
  if (reloadCount < 2) {
    sessionStorage.setItem(CHUNK_LOAD_ERROR_KEY, String(reloadCount + 1))
    window.location.reload()
    return true
  }
  
  sessionStorage.removeItem(CHUNK_LOAD_ERROR_KEY)
  return false
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('@/views/AboutView.vue'),
    meta: { title: '关于我' }
  },
  {
    path: '/categories',
    name: 'Categories',
    component: () => import('@/views/CategoriesView.vue'),
    meta: { title: '分类' }
  },
  {
    path: '/categories/:slug',
    name: 'CategoryArticles',
    component: () => import('@/views/CategoryArticlesView.vue'),
    meta: { title: '分类文章' }
  },
  {
    path: '/tags',
    name: 'Tags',
    component: () => import('@/views/TagsView.vue'),
    meta: { title: '标签' }
  },
  {
    path: '/tags/:slug',
    name: 'TagArticles',
    component: () => import('@/views/TagArticlesView.vue'),
    meta: { title: '标签文章' }
  },
  {
    path: '/article/:slug',
    name: 'Article',
    component: () => import('@/views/ArticleView.vue'),
    meta: { title: '文章详情' }
  },
  {
    path: '/resources',
    name: 'Resources',
    component: () => import('@/views/ResourcesView.vue'),
    meta: { title: '资源导航' }
  },
  {
    path: '/archive',
    name: 'Archive',
    component: () => import('@/views/ArchiveView.vue'),
    meta: { title: '文章归档' }
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('@/views/SearchView.vue'),
    meta: { title: '搜索' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { title: '个人中心', requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { title: '注册' }
  },
  {
    path: '/verify-email',
    name: 'VerifyEmail',
    component: () => import('@/views/VerifyEmailView.vue'),
    meta: { title: '验证邮箱' }
  },
  {
    path: '/pending-verification',
    name: 'PendingVerification',
    component: () => import('@/views/PendingVerificationView.vue'),
    meta: { title: '邮箱验证' }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPasswordView.vue'),
    meta: { title: '忘记密码' }
  },
  {
    path: '/oauth/callback/:provider',
    name: 'OAuthCallback',
    component: () => import('@/views/OAuthCallbackView.vue'),
    meta: { title: 'OAuth登录' }
  },
  {
    path: '/oauth/verify-email',
    name: 'OAuthVerifyEmail',
    component: () => import('@/views/OAuthVerifyEmailView.vue'),
    meta: { title: '验证邮箱' }
  },
  {
    path: '/oauth/pending-verification',
    name: 'OAuthPendingVerification',
    component: () => import('@/views/OAuthPendingVerificationView.vue'),
    meta: { title: '邮箱验证' }
  },
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/DashboardView.vue'),
        meta: { title: '仪表盘', permission: 'dashboard.view' }
      },
      {
        path: 'articles',
        name: 'AdminArticles',
        component: () => import('@/views/admin/ArticlesView.vue'),
        meta: { title: '文章管理', permission: 'article.view' }
      },
      {
        path: 'categories',
        name: 'AdminCategories',
        component: () => import('@/views/admin/CategoriesView.vue'),
        meta: { title: '分类管理', permission: 'category.view' }
      },
      {
        path: 'tags',
        name: 'AdminTags',
        component: () => import('@/views/admin/TagsView.vue'),
        meta: { title: '标签管理', permission: 'tag.view' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UsersView.vue'),
        meta: { title: '用户管理', permission: 'user.view' }
      },
      {
        path: 'resources',
        name: 'AdminResources',
        component: () => import('@/views/admin/ResourcesView.vue'),
        meta: { title: '资源管理', permission: 'resource.view' }
      },
      {
        path: 'email',
        name: 'AdminEmail',
        component: () => import('@/views/admin/EmailView.vue'),
        meta: { title: '邮件管理', permission: 'email.view' }
      },
      {
        path: 'notifications',
        name: 'AdminNotifications',
        component: () => import('@/views/admin/NotificationView.vue'),
        meta: { title: '通知管理', permission: 'notification.view' }
      },
      {
        path: 'logs',
        name: 'AdminLogs',
        component: () => import('@/views/admin/LogsView.vue'),
        meta: { title: '日志管理', permission: 'log.view' }
      },
      {
        path: 'comments',
        name: 'AdminComments',
        component: () => import('@/views/admin/CommentsView.vue'),
        meta: { title: '评论管理', permission: 'comment.view' }
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('@/views/admin/SettingsView.vue'),
        meta: { title: '网站设置', permission: 'settings.view' }
      },
      {
        path: 'announcements',
        name: 'AdminAnnouncements',
        component: () => import('@/views/admin/AnnouncementsView.vue'),
        meta: { title: '公告管理', permission: 'announcement.view' }
      },
      {
        path: 'profile',
        name: 'AdminSiteProfile',
        component: () => import('@/views/admin/ProfileView.vue'),
        meta: { title: '网站资料', permission: 'profile.view' }
      },
      {
        path: 'my-profile',
        name: 'AdminMyProfile',
        component: () => import('@/views/admin/UserProfileView.vue'),
        meta: { title: '我的资料' }
      },
      {
        path: 'oauth',
        name: 'AdminOAuth',
        component: () => import('@/views/admin/OAuthView.vue'),
        meta: { title: '授权管理', permission: 'oauth.view' }
      },
      {
        path: 'storage',
        name: 'AdminStorage',
        component: () => import('@/views/admin/StorageView.vue'),
        meta: { title: '存储管理', permission: 'storage.view' }
      },
      {
        path: 'roles',
        name: 'AdminRoles',
        component: () => import('@/views/admin/RolesView.vue'),
        meta: { title: '角色管理', permission: 'role.view' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: '页面未找到' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    
    if (to.hash) {
      return false
    }
    
    if (from.name === undefined) {
      return { top: 0, behavior: 'auto' }
    }
    
    return { top: 0, behavior: 'smooth' }
  }
})

if ('scrollRestoration' in history) {
  history.scrollRestoration = 'manual'
}

const prefetchCache = new Set<string>()

const requestIdleCallbackPolyfill = (callback: () => void, options?: { timeout?: number }) => {
  if (typeof requestIdleCallback !== 'undefined') {
    requestIdleCallback(callback, options)
  } else {
    setTimeout(callback, 1)
  }
}

const prefetchMap: Record<string, () => Promise<unknown>> = {
  'Home': () => import('@/views/HomeView.vue'),
  'Article': () => import('@/views/ArticleView.vue'),
  'About': () => import('@/views/AboutView.vue'),
  'Categories': () => import('@/views/CategoriesView.vue'),
  'CategoryArticles': () => import('@/views/CategoryArticlesView.vue'),
  'Tags': () => import('@/views/TagsView.vue'),
  'TagArticles': () => import('@/views/TagArticlesView.vue'),
  'Archive': () => import('@/views/ArchiveView.vue'),
  'Resources': () => import('@/views/ResourcesView.vue'),
  'Search': () => import('@/views/SearchView.vue'),
}

const prefetchComponents = (routeName: string) => {
  if (prefetchCache.has(routeName)) return
  prefetchCache.add(routeName)
  
  if (prefetchMap[routeName]) {
    requestIdleCallbackPolyfill(() => {
      prefetchMap[routeName]()
    }, { timeout: 2000 })
  }
}

const prefetchAllCommonPages = () => {
  const commonPages = ['Article', 'Archive', 'Resources', 'Categories', 'Tags', 'About', 'Search']
  let index = 0
  const prefetchNext = () => {
    if (index >= commonPages.length) return
    const page = commonPages[index++]
    prefetchComponents(page)
    requestIdleCallbackPolyfill(prefetchNext, { timeout: 1000 })
  }
  requestIdleCallbackPolyfill(prefetchNext, { timeout: 2000 })
}

const prefetchArticleComponent = () => {
  prefetchComponents('Article')
}

export { prefetchComponents, prefetchAllCommonPages, prefetchArticleComponent }

router.beforeEach(async (to, _from, next) => {
  const title = to.meta.title as string
  const siteConfigStore = useSiteConfigStore()
  const siteName = siteConfigStore.siteName || 'Futuristic Blog'
  document.title = title ? `${title} | ${siteName}` : siteName
  
  if (!to.path.startsWith('/admin') && !to.path.startsWith('/login') && !to.path.startsWith('/register')) {
    const initStore = useInitStore()
    if (!initStore.isCoreInitialized) {
      initStore.initializeCore()
    }
  }
  
  if (to.meta.requiresAuth) {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
    
    await authStore.waitForInit()
  }
  
  if (to.name) {
    prefetchComponents(to.name as string)
  }
  
  next()
})

router.onError((error) => {
  if (handleChunkLoadError(error)) {
    return
  }
  console.error('Router error:', error)
})

export default router
