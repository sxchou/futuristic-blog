<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/api'
import { useDialogStore, useAuthStore } from '@/stores'
import { checkServerHealth } from '@/api/client'

const dialog = useDialogStore()
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const isVerifying = ref(true)
const isVerified = ref(false)
const errorMessage = ref('')
const email = ref('')

onMounted(async () => {
  const token = route.query.token as string
  
  if (!token) {
    isVerifying.value = false
    errorMessage.value = '无效的验证链接'
    return
  }
  
  try {
    const isHealthy = await checkServerHealth()
    if (!isHealthy) {
      isVerifying.value = false
      errorMessage.value = '服务暂时不可用，请稍后重试'
      return
    }

    const response = await authApi.verifyEmail(token)
    
    isVerified.value = true
    
    if (response.access_token) {
      authStore.setTokens(
        response.access_token,
        response.refresh_token,
        response.expires_in
      )
      
      await authStore.fetchUser()
    }
    
    await dialog.showSuccess('邮箱验证成功！', '欢迎加入我们')
    
    setTimeout(() => {
      router.push('/')
    }, 1500)
  } catch (error: any) {
    console.error('Verification failed:', error)
    if (error.response?.data?.detail?.includes('过期')) {
      errorMessage.value = '验证链接已过期'
    } else {
      errorMessage.value = error.response?.data?.detail || '验证失败'
    }
  } finally {
    isVerifying.value = false
  }
})

const handleResend = async () => {
  if (!email.value) {
    await dialog.showError('请输入您的邮箱地址', '提示')
    return
  }
  
  try {
    const isHealthy = await checkServerHealth()
    if (!isHealthy) {
      await dialog.showError('服务暂时不可用，请稍后重试', '错误')
      return
    }

    await authApi.resendVerification(email.value)
    await dialog.showSuccess('验证邮件已发送，请查收', '成功')
  } catch (error: any) {
    console.error('Resend failed:', error)
    await dialog.showError(error.response?.data?.detail || '发送失败', '错误')
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="flex items-center justify-center px-4 pt-8 pb-32">
    <div class="w-full max-w-md mx-auto">
      <div class="glass-card p-8 text-center">
        <div
          v-if="isVerifying"
          class="py-8"
        >
          <div class="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
          <p class="text-gray-400">
            正在验证您的邮箱...
          </p>
        </div>
          
        <div
          v-else-if="isVerified"
          class="py-8"
        >
          <div class="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg
              class="w-10 h-10 text-green-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h1 class="text-xl font-bold text-gray-900 dark:text-white mb-4">
            邮箱验证成功！
          </h1>
          <p class="text-gray-400 mb-6">
            正在跳转到首页...
          </p>
        </div>
          
        <div
          v-else
          class="py-8"
        >
          <div class="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg
              class="w-10 h-10 text-red-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
          <h1 class="text-xl font-bold text-gray-900 dark:text-white mb-4">
            验证失败
          </h1>
          <p class="text-gray-400 mb-6">
            {{ errorMessage }}
          </p>
            
          <div class="border-t border-gray-200 dark:border-white/10 pt-6 mt-6">
            <p class="text-sm text-gray-500 mb-4">
              重新发送验证邮件：
            </p>
            <form class="flex gap-2" @submit.prevent="handleResend">
              <label
                for="verify-email"
                class="sr-only"
              >邮箱地址</label>
              <input
                id="verify-email"
                v-model="email"
                type="email"
                name="email"
                autocomplete="email"
                placeholder="输入您的邮箱"
                class="flex-1 px-4 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary focus:outline-none"
              >
              <button
                class="btn-secondary whitespace-nowrap"
                @click="handleResend"
              >
                发送
              </button>
            </form>
          </div>
            
          <button
            class="btn-primary w-full mt-6"
            @click="goToLogin"
          >
            返回登录
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
