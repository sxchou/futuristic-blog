import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore, useSiteConfigStore } from '@/stores'

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
        meta: { title: '仪表盘' }
      },
      {
        path: 'articles',
        name: 'AdminArticles',
        component: () => import('@/views/admin/ArticlesView.vue'),
        meta: { title: '文章管理' }
      },
      {
        path: 'categories',
        name: 'AdminCategories',
        component: () => import('@/views/admin/CategoriesView.vue'),
        meta: { title: '分类管理' }
      },
      {
        path: 'tags',
        name: 'AdminTags',
        component: () => import('@/views/admin/TagsView.vue'),
        meta: { title: '标签管理' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UsersView.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'resources',
        name: 'AdminResources',
        component: () => import('@/views/admin/ResourcesView.vue'),
        meta: { title: '资源管理' }
      },
      {
        path: 'email',
        name: 'AdminEmail',
        component: () => import('@/views/admin/EmailView.vue'),
        meta: { title: '邮件管理' }
      },
      {
        path: 'notifications',
        name: 'AdminNotifications',
        component: () => import('@/views/admin/NotificationView.vue'),
        meta: { title: '通知管理' }
      },
      {
        path: 'logs',
        name: 'AdminLogs',
        component: () => import('@/views/admin/LogsView.vue'),
        meta: { title: '日志管理' }
      },
      {
        path: 'comments',
        name: 'AdminComments',
        component: () => import('@/views/admin/CommentsView.vue'),
        meta: { title: '评论管理' }
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('@/views/admin/SettingsView.vue'),
        meta: { title: '网站设置' }
      },
      {
        path: 'profile',
        name: 'AdminSiteProfile',
        component: () => import('@/views/admin/ProfileView.vue'),
        meta: { title: '网站资料' }
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
        meta: { title: '授权管理' }
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
  scrollBehavior(_to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    if (from.name === undefined) {
      return false
    }
    return { top: 0 }
  }
})

const prefetchCache = new Set<string>()

const requestIdleCallbackPolyfill = (callback: () => void, options?: { timeout?: number }) => {
  if (typeof requestIdleCallback !== 'undefined') {
    requestIdleCallback(callback, options)
  } else {
    setTimeout(callback, 1)
  }
}

const prefetchComponents = (routeName: string) => {
  if (prefetchCache.has(routeName)) return
  prefetchCache.add(routeName)
  
  const prefetchMap: Record<string, () => Promise<unknown>> = {
    'Article': () => import('@/views/ArticleView.vue'),
    'Categories': () => import('@/views/CategoriesView.vue'),
    'Tags': () => import('@/views/TagsView.vue'),
    'Archive': () => import('@/views/ArchiveView.vue'),
    'Resources': () => import('@/views/ResourcesView.vue'),
  }
  
  if (prefetchMap[routeName]) {
    requestIdleCallbackPolyfill(() => {
      prefetchMap[routeName]()
    }, { timeout: 2000 })
  }
}

router.beforeEach(async (to, _from, next) => {
  const title = to.meta.title as string
  const siteConfigStore = useSiteConfigStore()
  const siteName = siteConfigStore.siteName || 'Futuristic Blog'
  document.title = title ? `${title} | ${siteName}` : siteName
  
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

export default router
