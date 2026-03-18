import axios, { AxiosError } from 'axios'
import type { AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig, AxiosResponse } from 'axios'

const config: AxiosRequestConfig = {
  baseURL: '/api/v1',
  timeout: 15000,
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
  /^\/files$/,
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

const pendingRequests = new Map<string, { controller: AbortController; count: number }>()

const generateRequestKey = (config: InternalAxiosRequestConfig): string => {
  const { method, url, params, data } = config
  return [method, url, JSON.stringify(params), JSON.stringify(data)].join('&')
}

const removePendingRequest = (config: InternalAxiosRequestConfig) => {
  const key = generateRequestKey(config)
  const pending = pendingRequests.get(key)
  if (pending) {
    pending.count--
    if (pending.count <= 0) {
      pendingRequests.delete(key)
    }
  }
}

const addPendingRequest = (config: InternalAxiosRequestConfig) => {
  const key = generateRequestKey(config)
  const pending = pendingRequests.get(key)
  if (pending) {
    pending.count++
    config.signal = pending.controller.signal
  } else {
    const controller = new AbortController()
    config.signal = controller.signal
    pendingRequests.set(key, { controller, count: 1 })
  }
}

const responseCache = new Map<string, { data: unknown; timestamp: number }>()
const CACHE_TTL = 60000

const getCacheKey = (config: InternalAxiosRequestConfig): string => {
  return `${config.method}-${config.url}-${JSON.stringify(config.params)}`
}

const getCachedResponse = (config: InternalAxiosRequestConfig): unknown | null => {
  const key = getCacheKey(config)
  const cached = responseCache.get(key)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data
  }
  responseCache.delete(key)
  return null
}

const setCachedResponse = (config: InternalAxiosRequestConfig, data: unknown) => {
  const key = getCacheKey(config)
  responseCache.set(key, { data, timestamp: Date.now() })
}

const cacheableEndpoints = [
  '/categories',
  '/tags',
  '/resources',
  '/site-config',
  '/profile'
]

const shouldCache = (url: string | undefined): boolean => {
  if (!url) return false
  return cacheableEndpoints.some(endpoint => url === endpoint || url.startsWith(endpoint + '?'))
}

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    if (config.method?.toLowerCase() === 'get' && shouldCache(config.url)) {
      const cached = getCachedResponse(config)
      if (cached) {
        config.adapter = () => Promise.resolve({
          data: cached,
          status: 200,
          statusText: 'OK (from cache)',
          headers: {},
          config
        } as AxiosResponse)
        return config
      }
    }
    
    if (config.method?.toLowerCase() === 'get') {
      removePendingRequest(config)
      addPendingRequest(config)
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response) => {
    if (response.config) {
      removePendingRequest(response.config)
    }
    
    if (response.config.method?.toLowerCase() === 'get' && shouldCache(response.config.url)) {
      setCachedResponse(response.config, response.data)
    }
    
    return response
  },
  (error: AxiosError) => {
    if (error.config) {
      removePendingRequest(error.config)
    }
    
    if (axios.isCancel(error)) {
      return Promise.resolve({} as AxiosResponse)
    }
    
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      responseCache.clear()
      
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

export const clearCache = () => {
  responseCache.clear()
}

export const cancelAllRequests = () => {
  pendingRequests.forEach(({ controller }) => controller.abort())
  pendingRequests.clear()
}

export default apiClient
