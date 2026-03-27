<script setup lang="ts">
import { ref, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, useSiteConfigStore, useDialogStore } from '@/stores'
import { authApi } from '@/api'

const router = useRouter()
const authStore = useAuthStore()
const siteConfigStore = useSiteConfigStore()
const dialog = useDialogStore()

const form = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const isLoading = ref(false)
const errorMessage = ref('')
const showSuccess = ref(false)
const registeredEmail = ref('')
const isVerifying = ref(false)
const tokenExpiresAt = ref<Date | null>(null)
const isExpired = ref(false)
let pollingTimer: ReturnType<typeof setInterval> | null = null
let countdownTimer: ReturnType<typeof setInterval> | null = null

const countdownText = computed(() => {
  if (!tokenExpiresAt.value || isExpired.value) return ''
  
  const now = new Date()
  const diff = tokenExpiresAt.value.getTime() - now.getTime()
  
  if (diff <= 0) {
    return ''
  }
  
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟${seconds}秒`
  } else if (minutes > 0) {
    return `${minutes}分钟${seconds}秒`
  } else {
    return `${seconds}秒`
  }
})

const updateCountdown = () => {
  if (!tokenExpiresAt.value) return
  
  const now = new Date()
  const diff = tokenExpiresAt.value.getTime() - now.getTime()
  
  if (diff <= 0) {
    isExpired.value = true
    stopCountdown()
    stopPolling()
  }
}

const startCountdown = () => {
  if (countdownTimer) return
  
  countdownTimer = setInterval(updateCountdown, 1000)
}

const stopCountdown = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

const startPolling = (email: string) => {
  pollingTimer = setInterval(async () => {
    try {
      const response = await authApi.checkVerification(email)
      
      if (response.is_verified && response.access_token) {
        stopPolling()
        stopCountdown()
        isVerifying.value = true
        
        authStore.setTokens(
          response.access_token,
          response.refresh_token,
          response.expires_in
        )
        
        if (response.user) {
          authStore.setUser(response.user)
        }
        
        await dialog.showSuccess('邮箱验证成功！', '欢迎加入我们')
        router.push('/')
      }
    } catch (error) {
      console.error('Polling error:', error)
    }
  }, 3000)
}

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

onUnmounted(() => {
  stopPolling()
  stopCountdown()
})

const handleRegister = async () => {
  if (!form.value.username || !form.value.email || !form.value.password) {
    errorMessage.value = '请填写所有必填字段'
    return
  }

  if (form.value.password !== form.value.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  if (form.value.password.length < 6) {
    errorMessage.value = '密码长度至少为6位'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await authStore.register({
      username: form.value.username,
      email: form.value.email,
      password: form.value.password
    })
    registeredEmail.value = form.value.email
    showSuccess.value = true
    
    if (response && response.verification_token_expires) {
      tokenExpiresAt.value = new Date(response.verification_token_expires)
      const now = new Date()
      if (tokenExpiresAt.value.getTime() > now.getTime()) {
        startCountdown()
      } else {
        isExpired.value = true
      }
    }
    
    if (!isExpired.value) {
      startPolling(form.value.email)
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || '注册失败，请稍后重试'
  } finally {
    isLoading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="flex items-center justify-center px-4 pt-8 pb-32">
    <div class="w-full max-w-[386px]">
      <div class="glass-card p-5">
        <div v-if="!showSuccess">
          <div class="text-center mb-4">
            <div class="w-12 h-12 mx-auto mb-2 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <span class="text-base font-bold text-white">{{ siteConfigStore.siteLogo }}</span>
            </div>
            <h1 class="text-lg font-bold gradient-text">创建账户</h1>
            <p class="text-gray-500 dark:text-gray-400 mt-0.5 text-xs">加入我们的技术社区</p>
          </div>

          <form @submit.prevent="handleRegister" class="space-y-3">
            <div>
              <label for="register-username" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">用户名</label>
              <input
                v-model="form.username"
                type="text"
                id="register-username"
                name="username"
                autocomplete="username"
                class="w-full px-3 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
                placeholder="请输入用户名"
              />
            </div>

            <div>
              <label for="register-email" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">邮箱</label>
              <input
                v-model="form.email"
                type="email"
                id="register-email"
                name="email"
                autocomplete="email"
                class="w-full px-3 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
                placeholder="请输入邮箱"
              />
            </div>

            <div>
              <label for="register-password" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">密码</label>
              <input
                v-model="form.password"
                type="password"
                id="register-password"
                name="new-password"
                autocomplete="new-password"
                class="w-full px-3 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
                placeholder="请输入密码"
              />
            </div>

            <div>
              <label for="register-confirm-password" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">确认密码</label>
              <input
                v-model="form.confirmPassword"
                type="password"
                id="register-confirm-password"
                name="confirm-password"
                autocomplete="new-password"
                class="w-full px-3 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
                placeholder="请再次输入密码"
              />
            </div>

            <div v-if="errorMessage" class="p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p class="text-red-400 text-xs">{{ errorMessage }}</p>
            </div>

            <button
              type="submit"
              :disabled="isLoading"
              class="w-full py-2 bg-gradient-to-r from-primary to-accent text-white font-medium rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 text-sm"
            >
              <span v-if="isLoading" class="flex items-center justify-center gap-1.5">
                <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                注册中...
              </span>
              <span v-else>注册</span>
            </button>
          </form>

          <div class="mt-3 text-center">
            <p class="text-gray-500 dark:text-gray-400 text-xs">
              已有账户？
              <router-link to="/login" class="text-primary hover:underline">立即登录</router-link>
            </p>
          </div>
        </div>

        <div v-else class="text-center py-4">
          <div v-if="isVerifying" class="py-4">
            <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-3" />
            <p class="text-gray-400 text-sm">验证成功，正在登录...</p>
          </div>
          <template v-else>
            <div class="w-[76px] h-12 rounded-full flex items-center justify-center mx-auto mb-3" :class="isExpired ? 'bg-red-500/20' : 'bg-primary/20'">
              <svg class="w-7 h-7" :class="isExpired ? 'text-red-500' : 'text-primary'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="isExpired" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h2 class="text-base font-bold text-gray-900 dark:text-white mb-2">{{ isExpired ? '链接已失效' : '注册成功！' }}</h2>
            <p class="text-gray-400 text-xs mb-0.5">验证邮件已发送至</p>
            <p class="text-primary font-medium text-sm mb-3">{{ registeredEmail }}</p>
            
            <div v-if="isExpired" class="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-3">
              <p class="text-red-400 text-xs">验证链接已过期，请重新注册</p>
            </div>
            
            <template v-else>
              <p class="text-xs text-gray-500 mb-2">
                请点击邮件中的链接验证邮箱
              </p>
              <div v-if="countdownText" class="text-xs text-orange-500 mb-3">
                链接有效期：{{ countdownText }}
              </div>
              <div class="flex items-center justify-center gap-2 text-xs text-gray-400 mb-3">
                <div class="w-3 h-3 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
                <span>等待验证中...</span>
              </div>
            </template>
            
            <button @click="goToLogin" class="btn-primary w-full text-sm py-2">
              {{ isExpired ? '重新注册' : '前往登录' }}
            </button>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
