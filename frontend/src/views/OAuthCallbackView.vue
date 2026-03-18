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
const needsEmail = ref(false)
const tempToken = ref('')
const username = ref('')
const email = ref('')
const isSubmitting = ref(false)

const handleCallback = async () => {
  const provider = route.params.provider as string
  
  const accessToken = route.query.access_token as string
  const needsEmailParam = route.query.needs_email as string
  const tempTokenParam = route.query.temp_token as string
  const usernameParam = route.query.username as string
  const userId = route.query.user_id as string
  const errorParam = route.query.error as string
  
  if (errorParam) {
    error.value = errorParam
    isLoading.value = false
    return
  }
  
  if (needsEmailParam === 'true' && tempTokenParam) {
    needsEmail.value = true
    tempToken.value = tempTokenParam
    username.value = usernameParam || ''
    isLoading.value = false
    return
  }
  
  if (accessToken) {
    localStorage.setItem('token', accessToken)
    await authStore.fetchUser()
    
    await dialog.showSuccess('登录成功！', '欢迎回来')
    
    const redirect = route.query.redirect as string
    router.push(redirect || '/')
    return
  }
  
  const code = route.query.code as string
  const state = route.query.state as string

  if (!code || !state) {
    error.value = '无效的回调参数'
    isLoading.value = false
    return
  }

  try {
    const response = await oauthApi.handleCallback(provider, code, state)
    
    if (response.needs_email && response.temp_token) {
      needsEmail.value = true
      tempToken.value = response.temp_token
      username.value = response.user.username
      isLoading.value = false
      return
    }
    
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

const submitEmail = async () => {
  if (!email.value) {
    dialog.showError('请输入邮箱地址')
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email.value)) {
    dialog.showError('请输入有效的邮箱地址')
    return
  }

  isSubmitting.value = true
  try {
    await oauthApi.submitEmail(email.value, tempToken.value)
    await dialog.showSuccess('验证邮件已发送', '请检查您的邮箱完成验证')
    router.push('/login')
  } catch (err: any) {
    dialog.showError(err.response?.data?.detail || '发送验证邮件失败')
  } finally {
    isSubmitting.value = false
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
      
      <div v-else-if="needsEmail" class="w-full max-w-md mx-auto space-y-6">
        <div class="space-y-2">
          <div class="w-16 h-16 mx-auto rounded-full bg-primary/10 flex items-center justify-center">
            <svg class="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white">完善账户信息</h2>
          <p class="text-gray-500 dark:text-gray-400">
            您好，<span class="font-medium text-gray-700 dark:text-gray-300">{{ username }}</span>！
          </p>
          <p class="text-gray-500 dark:text-gray-400">
            请提供您的邮箱地址以完成注册
          </p>
        </div>
        
        <form @submit.prevent="submitEmail" class="space-y-4">
          <div>
            <input
              v-model="email"
              type="email"
              placeholder="请输入您的邮箱地址"
              class="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition"
              :disabled="isSubmitting"
            />
          </div>
          
          <button
            type="submit"
            :disabled="isSubmitting"
            class="w-full py-3 px-4 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isSubmitting" class="flex items-center justify-center gap-2">
              <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              发送中...
            </span>
            <span v-else>发送验证邮件</span>
          </button>
        </form>
        
        <router-link to="/login" class="block text-sm text-gray-500 hover:text-primary">
          返回登录
        </router-link>
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
