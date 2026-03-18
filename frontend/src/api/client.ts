import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig } from 'axios'

const config: AxiosRequestConfig = {
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
}

const apiClient: AxiosInstance = axios.create(config)

const publicApiPatterns = [
  /^\/articles(\/[^/]+)?$/,
  /^\/articles\/archive\/list$/,
  /^\/categories/,
  /^\/tags/,
  /^\/likes\/\d+$/,
  /^\/comments\/article\/\d+$/,
  /^\/resources$/,
  /^\/site-config/,
  /^\/profile\/public/,
  /^\/files\/\d+\/download$/
]

const isPublicApi = (url: string): boolean => {
  const apiPath = url.split('?')[0]
  return publicApiPatterns.some(pattern => pattern.test(apiPath))
}

const publicRoutes = [
  '/',
  '/about',
  '/categories',
  '/tags',
  '/article',
  '/resources',
  '/archive',
  '/search'
]

const isPublicRoute = (): boolean => {
  const currentPath = window.location.pathname
  return publicRoutes.some(route => 
    currentPath === route || currentPath.startsWith(route + '/')
  )
}

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      
      const requestUrl = error.config?.url || ''
      const isPublic = isPublicApi(requestUrl) || isPublicRoute()
      
      if (!isPublic && 
          !window.location.pathname.includes('/login') && 
          !window.location.pathname.includes('/register') &&
          !window.location.pathname.includes('/forgot-password') &&
          !window.location.pathname.includes('/verify-email') &&
          !window.location.pathname.includes('/oauth/callback')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
