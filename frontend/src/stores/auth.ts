import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  const login = async (credentials: { username: string; password: string }) => {
    loading.value = true
    try {
      const response = await authApi.login(credentials.username, credentials.password)
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)
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

  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }

  if (token.value) {
    fetchUser()
  }

  return {
    user,
    token,
    loading,
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    fetchUser
  }
})
