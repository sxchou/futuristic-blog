import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import type { User, SessionInfo } from '@/types'

const TOKEN_KEY = 'token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const TOKEN_EXPIRY_KEY = 'token_expiry'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_TOKEN_KEY))
  const tokenExpiry = ref<number | null>(
    localStorage.getItem(TOKEN_EXPIRY_KEY) 
      ? parseInt(localStorage.getItem(TOKEN_EXPIRY_KEY)!) 
      : null
  )
  const loading = ref(false)
  const isRefreshing = ref(false)
  const initializing = ref(false)
  const initPromise = ref<Promise<void> | null>(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  const setTokens = (newToken: string, newRefreshToken?: string, expiresIn?: number) => {
    token.value = newToken
    localStorage.setItem(TOKEN_KEY, newToken)
    
    if (newRefreshToken) {
      refreshToken.value = newRefreshToken
      localStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken)
    }
    
    if (expiresIn) {
      const expiry = Date.now() + expiresIn * 1000
      tokenExpiry.value = expiry
      localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toString())
    }
  }

  const clearTokens = () => {
    token.value = null
    refreshToken.value = null
    tokenExpiry.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(TOKEN_EXPIRY_KEY)
  }

  const isTokenExpiringSoon = (bufferSeconds: number = 300): boolean => {
    if (!tokenExpiry.value) return false
    return Date.now() + bufferSeconds * 1000 >= tokenExpiry.value
  }

  const refreshAccessToken = async (): Promise<boolean> => {
    if (!refreshToken.value || isRefreshing.value) return false
    
    isRefreshing.value = true
    try {
      const response = await authApi.refreshToken(refreshToken.value)
      setTokens(
        response.access_token, 
        response.refresh_token, 
        response.expires_in
      )
      return true
    } catch (error) {
      console.error('Token refresh failed:', error)
      clearTokens()
      return false
    } finally {
      isRefreshing.value = false
    }
  }

  const checkAndRefreshToken = async (): Promise<boolean> => {
    if (!token.value) return false
    
    if (isTokenExpiringSoon()) {
      return await refreshAccessToken()
    }
    return true
  }

  const login = async (credentials: { username: string; password: string }) => {
    loading.value = true
    try {
      const response = await authApi.login(credentials.username, credentials.password)
      setTokens(
        response.access_token, 
        response.refresh_token, 
        response.expires_in
      )
      await fetchUser()
      return true
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const register = async (data: { username: string; email: string; password: string }) => {
    loading.value = true
    try {
      await authApi.register(data)
      return true
    } catch (error) {
      console.error('Register failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchUser = async () => {
    if (!token.value) return
    try {
      user.value = await authApi.getMe()
    } catch (error) {
      console.error('Failed to fetch user:', error)
      logout()
    }
  }

  const logout = async () => {
    if (refreshToken.value) {
      try {
        await authApi.logout(refreshToken.value)
      } catch (error) {
        console.error('Logout API call failed:', error)
      }
    }
    clearTokens()
  }

  const logoutAll = async () => {
    try {
      await authApi.logoutAll()
    } catch (error) {
      console.error('Logout all API call failed:', error)
    }
    clearTokens()
  }

  const getSessions = async (): Promise<SessionInfo[]> => {
    return await authApi.getSessions()
  }

  const revokeSession = async (sessionId: number) => {
    return await authApi.revokeSession(sessionId)
  }

  const waitForInit = async (): Promise<void> => {
    if (initializing.value && initPromise.value) {
      return initPromise.value
    }
    if (!user.value && token.value) {
      return fetchUser()
    }
    return Promise.resolve()
  }

  if (token.value) {
    initializing.value = true
    initPromise.value = fetchUser().finally(() => {
      initializing.value = false
    })
  }

  return {
    user,
    token,
    refreshToken,
    loading,
    isRefreshing,
    initializing,
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    logoutAll,
    fetchUser,
    refreshAccessToken,
    checkAndRefreshToken,
    getSessions,
    revokeSession,
    setTokens,
    clearTokens,
    waitForInit
  }
})
