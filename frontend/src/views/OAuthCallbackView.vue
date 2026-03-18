<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore, useDialogStore } from '@/stores'
import { oauthApi } from '@/api/oauth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const dialog = useDialogStore()

const isLoading = ref(true)
const error = ref('')

const handleCallback = async () => {
  const provider = route.params.provider as string
  const code = route.query.code as string
  const state = route.query.state as string

  if (!code || !state) {
    error.value = '无效的回调参数'
    isLoading.value = false
    return
  }

  try {
    const response = await oauthApi.handleCallback(provider, code, state)
    
    localStorage.setItem('token', response.access_token)
    await authStore.fetchUser()
    
    await dialog.showSuccess('登录成功！', '欢迎回来')
    
    const redirect = route.query.redirect as string
    router.push(redirect || '/')
  } catch (err: any) {
    error.value = err.response?.data?.detail || '登录失败，请重试'
    isLoading.value = false
  }
}

onMounted(() => {
  handleCallback()
})
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-dark flex items-center justify-center px-4">
    <div class="text-center">
      <div v-if="isLoading" class="space-y-4">
        <div class="w-12 h-12 mx-auto border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        <p class="text-gray-500 dark:text-gray-400">正在登录...</p>
      </div>
      
      <div v-else class="space-y-4">
        <div class="w-12 h-12 mx-auto rounded-full bg-red-500/10 flex items-center justify-center">
          <svg class="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <p class="text-red-500">{{ error }}</p>
        <router-link to="/login" class="text-primary hover:underline">
          返回登录
        </router-link>
      </div>
    </div>
  </div>
</template>
