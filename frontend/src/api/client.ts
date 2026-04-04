import axios, { AxiosError } from 'axios'
import type { AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig, AxiosResponse } from 'axios'

const config: AxiosRequestConfig = {
  baseURL: '/api/v1',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
}

const apiClient: AxiosInstance = axios.create(config)

let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

const subscribeTokenRefresh = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb)
}

const onTokenRefreshed = (token: string) => {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

const pendingRequests = new Map<string, { controller: AbortController; timestamp: number }>()

const generateRequestKey = (config: InternalAxiosRequestConfig): string => {
  const { method, url, params } = config
  return [method, url, JSON.stringify(params)].join('&')
}

const PENDING_REQUEST_TTL = 500

const removePendingRequest = (config: InternalAxiosRequestConfig) => {
  const key = generateRequestKey(config)
  const pending = pendingRequests.get(key)
  if (pending) {
    if (Date.now() - pending.timestamp > PENDING_REQUEST_TTL) {
      pendingRequests.delete(key)
    }
  }
}

const addPendingRequest = (config: InternalAxiosRequestConfig) => {
  const key = generateRequestKey(config)
  const pending = pendingRequests.get(key)
  if (pending && Date.now() - pending.timestamp < PENDING_REQUEST_TTL) {
    config.signal = pending.controller.signal
  } else {
    const controller = new AbortController()
    config.signal = controller.signal
    pendingRequests.set(key, { controller, timestamp: Date.now() })
  }
}

interface CacheEntry {
  data: unknown
  timestamp: number
  etag?: string
}

const responseCache = new Map<string, CacheEntry>()

const CACHE_CONFIG: Record<string, number> = {
  '/categories': 300000,
  '/tags': 300000,
  '/resources': 120000,
  '/site-config': 600000,
  '/profile': 300000,
  '/articles': 60000,
  '/dashboard': 30000
}

const getCacheKey = (config: InternalAxiosRequestConfig): string => {
  return `${config.method}-${config.url}-${JSON.stringify(config.params)}`
}

const getCacheTTL = (url: string | undefined): number => {
  if (!url) return 60000
  for (const [endpoint, ttl] of Object.entries(CACHE_CONFIG)) {
    if (url === endpoint || url.startsWith(endpoint + '?') || url.startsWith(endpoint + '/')) {
      return ttl
    }
  }
  return 60000
}

const getCachedResponse = (config: InternalAxiosRequestConfig): unknown | null => {
  const key = getCacheKey(config)
  const cached = responseCache.get(key)
  const ttl = getCacheTTL(config.url)
  
  if (cached && Date.now() - cached.timestamp < ttl) {
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
  '/profile',
  '/articles',
  '/dashboard'
]

const shouldCache = (url: string | undefined): boolean => {
  if (!url) return false
  return cacheableEndpoints.some(endpoint => url === endpoint || url.startsWith(endpoint + '?') || url.startsWith(endpoint + '/'))
}

const nonCacheablePatterns = [
  /\/auth\//,
  /\/comments\//,
  /\/likes\//,
  /\/logs\//,
  /\/notifications\//,
  /\/upload/,
  /\/delete/,
  /\/create/,
  /\/update/
]

const isNonCacheable = (url: string | undefined): boolean => {
  if (!url) return true
  return nonCacheablePatterns.some(pattern => pattern.test(url))
}

const refreshToken = async (): Promise<string | null> => {
  const storedRefreshToken = localStorage.getItem('refresh_token')
  if (!storedRefreshToken) return null
  
  try {
    const response = await axios.post('/api/v1/auth/refresh', {
      refresh_token: storedRefreshToken
    })
    
    const { access_token, refresh_token: newRefreshToken, expires_in } = response.data
    
    localStorage.setItem('token', access_token)
    if (newRefreshToken) {
      localStorage.setItem('refresh_token', newRefreshToken)
    }
    if (expires_in) {
      const expiry = Date.now() + expires_in * 1000
      localStorage.setItem('token_expiry', expiry.toString())
    }
    
    return access_token
  } catch (error) {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('token_expiry')
    return null
  }
}

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    if (config.method?.toLowerCase() === 'get' && shouldCache(config.url) && !isNonCacheable(config.url)) {
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
    
    if (response.config.method?.toLowerCase() === 'get' && shouldCache(response.config.url) && !isNonCacheable(response.config.url)) {
      setCachedResponse(response.config, response.data)
    }
    
    return response
  },
  async (error: AxiosError) => {
    const originalConfig = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    
    if (error.config) {
      removePendingRequest(error.config)
    }
    
    if (axios.isCancel(error)) {
      const cancelError = new Error('请求已取消')
      ;(cancelError as unknown as Record<string, unknown>).isCancel = true
      return Promise.reject(cancelError)
    }
    
    if (error.response?.status === 401 && originalConfig && !originalConfig._retry) {
      if (originalConfig.url === '/auth/refresh') {
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('token_expiry')
        responseCache.clear()
        
        if (!window.location.pathname.includes('/login') && 
            !window.location.pathname.includes('/register') &&
            !window.location.pathname.includes('/forgot-password') &&
            !window.location.pathname.includes('/verify-email') &&
            !window.location.pathname.includes('/oauth/callback')) {
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
      
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string) => {
            originalConfig.headers.Authorization = `Bearer ${token}`
            resolve(apiClient(originalConfig))
          })
        })
      }
      
      originalConfig._retry = true
      isRefreshing = true
      
      try {
        const newToken = await refreshToken()
        
        if (newToken) {
          onTokenRefreshed(newToken)
          originalConfig.headers.Authorization = `Bearer ${newToken}`
          return apiClient(originalConfig)
        } else {
          localStorage.removeItem('token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('token_expiry')
          responseCache.clear()
          
          if (!window.location.pathname.includes('/login') && 
              !window.location.pathname.includes('/register') &&
              !window.location.pathname.includes('/forgot-password') &&
              !window.location.pathname.includes('/verify-email') &&
              !window.location.pathname.includes('/oauth/callback')) {
            window.location.href = '/login'
          }
          return Promise.reject(error)
        }
      } catch (refreshError) {
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('token_expiry')
        responseCache.clear()
        
        if (!window.location.pathname.includes('/login') && 
            !window.location.pathname.includes('/register') &&
            !window.location.pathname.includes('/forgot-password') &&
            !window.location.pathname.includes('/verify-email') &&
            !window.location.pathname.includes('/oauth/callback')) {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    
    return Promise.reject(error)
  }
)

export const clearCache = () => {
  responseCache.clear()
}

export const clearCacheByPattern = (pattern: string) => {
  for (const key of responseCache.keys()) {
    if (key.includes(pattern)) {
      responseCache.delete(key)
    }
  }
}

export const cancelAllRequests = () => {
  pendingRequests.forEach(({ controller }) => controller.abort())
  pendingRequests.clear()
}

export const getCacheStats = () => {
  return {
    size: responseCache.size,
    keys: Array.from(responseCache.keys())
  }
}

export default apiClient
