<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDialogStore, useAuthStore } from '@/stores'
import { oauthApi } from '@/api/oauth'
import { usePendingOAuth } from '@/composables/usePendingOAuth'
import { useOAuthAnalytics } from '@/composables/useOAuthAnalytics'

const route = useRoute()
const router = useRouter()
const dialog = useDialogStore()
const authStore = useAuthStore()
const { setPendingState, clearPendingState, getPendingState } = usePendingOAuth()
const { trackEvent } = useOAuthAnalytics()

const isLoading = ref(true)
const isSubmitting = ref(false)
const showChangeEmailForm = ref(false)
const newEmail = ref('')
const confirmEmail = ref('')

const tempToken = ref('')
const username = ref('')
const hasEmail = ref(false)
const email = ref('')
const providerName = ref('')
const expiresAt = ref<Date | null>(null)
const isExpired = ref(false)

let pollInterval: ReturnType<typeof setInterval> | null = null
let countdownInterval: ReturnType<typeof setInterval> | null = null

const providerDisplayName = computed(() => {
  const names: Record<string, string> = {
    google: 'Google',
    github: 'GitHub',
    twitter: 'Twitter/X',
    x: 'X',
    wechat: '微信',
    qq: 'QQ'
  }
  return names[providerName.value] || providerName.value
})

const countdownText = computed(() => {
  if (!expiresAt.value || isExpired.value) return ''
  
  const now = new Date()
  const diff = expiresAt.value.getTime() - now.getTime()
  
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
  if (!expiresAt.value) return
  
  const now = new Date()
  const diff = expiresAt.value.getTime() - now.getTime()
  
  if (diff <= 0) {
    isExpired.value = true
    stopCountdown()
    stopPolling()
  }
}

const startCountdown = () => {
  if (countdownInterval) return
  
  countdownInterval = setInterval(updateCountdown, 1000)
}

const stopCountdown = () => {
  if (countdownInterval) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
}

const checkVerificationStatus = async () => {
  if (!tempToken.value) return
  
  try {
    const info = await oauthApi.getPendingVerification(tempToken.value)
    
    if (info.is_verified && info.email) {
      stopPolling()
      
      try {
        const response = await oauthApi.verifyEmail(tempToken.value, info.email)
        
        clearPendingState()
        trackEvent('oauth_verification_complete', { provider: providerName.value })
        
        authStore.setTokens(
          response.access_token,
          response.refresh_token || '',
          response.expires_in || 43200 * 60
        )
        await authStore.fetchUser()
        
        await dialog.showSuccess('邮箱验证成功！', '欢迎加入我们')
        
        setTimeout(() => {
          window.location.href = '/'
        }, 500)
      } catch (verifyErr: any) {
        console.error('Verify email error:', verifyErr)
        clearPendingState()
        await dialog.showSuccess('邮箱验证成功！', '正在跳转...')
        setTimeout(() => {
          window.location.href = '/login'
        }, 1000)
      }
    }
  } catch (err) {
    console.error('Poll verification status error:', err)
  }
}

const startPolling = () => {
  if (pollInterval) return
  
  pollInterval = setInterval(checkVerificationStatus, 3000)
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

const loadPendingInfo = async () => {
  let token = route.query.temp_token as string
  
  if (!token) {
    const savedState = getPendingState()
    if (savedState) {
      token = savedState.tempToken
    }
  }
  
  if (!token) {
    await dialog.showError('无效的验证链接', '错误')
    router.push('/login')
    return
  }
  
  tempToken.value = token
  
  try {
    const info = await oauthApi.getPendingVerification(token)
    username.value = info.username
    hasEmail.value = info.has_email
    email.value = info.email
    providerName.value = info.provider_name
    
    if (info.expires_at) {
      expiresAt.value = new Date(info.expires_at)
      const now = new Date()
      if (expiresAt.value.getTime() <= now.getTime()) {
        isExpired.value = true
      } else {
        startCountdown()
      }
    }
    
    setPendingState(token, info.username, info.provider_name, info.email)
    trackEvent('oauth_pending_verification_view', { provider: info.provider_name, hasEmail: info.has_email })
    
    if (info.is_verified) {
      await checkVerificationStatus()
    } else if (!isExpired.value) {
      startPolling()
    }
  } catch (err: any) {
    await dialog.showError(err.response?.data?.detail || '获取验证信息失败', '错误')
    clearPendingState()
    router.push('/login')
  } finally {
    isLoading.value = false
  }
}

const handleResendVerification = async () => {
  if (isSubmitting.value) return
  
  isSubmitting.value = true
  try {
    const response = await oauthApi.resendVerification(tempToken.value)
    trackEvent('oauth_resend_verification', { provider: providerName.value })
    await dialog.showSuccess(
      `验证邮件已发送到 ${response.email}`,
      '请检查您的邮箱'
    )
  } catch (err: any) {
    await dialog.showError(err.response?.data?.detail || '发送验证邮件失败', '错误')
  } finally {
    isSubmitting.value = false
  }
}

const handleChangeEmail = () => {
  showChangeEmailForm.value = true
  newEmail.value = ''
  confirmEmail.value = ''
  trackEvent('oauth_change_email_start', { provider: providerName.value })
}

const handleCancelChangeEmail = () => {
  showChangeEmailForm.value = false
  newEmail.value = ''
  confirmEmail.value = ''
}

const handleSubmitNewEmail = async () => {
  if (!newEmail.value || !confirmEmail.value) {
    await dialog.showError('请填写所有字段', '错误')
    return
  }
  
  if (newEmail.value !== confirmEmail.value) {
    await dialog.showError('两次输入的邮箱地址不一致', '错误')
    return
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(newEmail.value)) {
    await dialog.showError('请输入有效的邮箱地址', '错误')
    return
  }
  
  isSubmitting.value = true
  try {
    const response = await oauthApi.changeEmail(tempToken.value, newEmail.value)
    trackEvent('oauth_change_email', { provider: providerName.value })
    await dialog.showSuccess(
      `验证邮件已发送到 ${response.email}`,
      '请检查您的邮箱'
    )
    showChangeEmailForm.value = false
    hasEmail.value = true
    email.value = response.email
  } catch (err: any) {
    await dialog.showError(err.response?.data?.detail || '发送验证邮件失败', '错误')
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  loadPendingInfo()
})

onUnmounted(() => {
  stopPolling()
  stopCountdown()
})
</script>

<template>
  <div class="flex items-center justify-center px-4 pt-8 pb-32">
    <div class="w-full max-w-md">
      <div v-if="isLoading" class="text-center space-y-4">
        <div class="w-12 h-12 mx-auto border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        <p class="text-gray-500 dark:text-gray-400">正在加载...</p>
      </div>
      
      <div v-else class="space-y-6">
        <div class="text-center space-y-3">
          <div class="w-16 h-16 mx-auto rounded-full flex items-center justify-center" :class="isExpired ? 'bg-red-500/10' : 'bg-amber-500/10'">
            <svg class="w-8 h-8" :class="isExpired ? 'text-red-500' : 'text-amber-500'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="isExpired" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ isExpired ? '链接已失效' : '邮箱未验证' }}</h1>
          <p class="text-gray-500 dark:text-gray-400">
            您好，<span class="font-medium text-gray-700 dark:text-gray-300">{{ username }}</span>！
          </p>
        </div>
        
        <div v-if="isExpired" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div class="flex items-start gap-3">
            <svg class="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div class="space-y-1">
              <p class="text-sm font-medium text-red-800 dark:text-red-200">
                验证链接已失效
              </p>
              <p class="text-sm text-red-700 dark:text-red-300">
                验证链接已过期，请重新发送验证邮件或更换邮箱地址。
              </p>
            </div>
          </div>
        </div>
        
        <div v-else class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div class="flex items-start gap-3">
            <svg class="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div class="space-y-1">
              <p class="text-sm font-medium text-blue-800 dark:text-blue-200">
                正在等待邮箱验证
              </p>
              <p class="text-sm text-blue-700 dark:text-blue-300">
                验证完成后将自动跳转，无需刷新页面
              </p>
            </div>
          </div>
        </div>
        
        <div v-if="!isExpired" class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 space-y-2">
          <div class="flex items-start gap-3">
            <svg class="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div class="space-y-1">
              <p class="text-sm font-medium text-amber-800 dark:text-amber-200">
                您的邮箱地址尚未验证
              </p>
              <p class="text-sm text-amber-700 dark:text-amber-300">
                请验证您的邮箱地址以完成账户设置。验证后您将能够使用所有功能。
              </p>
            </div>
          </div>
        </div>
        
        <div v-if="hasEmail && !showChangeEmailForm" class="space-y-4">
          <div class="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500 dark:text-gray-400">当前邮箱</span>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ email }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500 dark:text-gray-400">登录方式</span>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ providerDisplayName }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500 dark:text-gray-400">预计送达时间</span>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">10秒内</span>
            </div>
            <div v-if="!isExpired && countdownText" class="flex items-center justify-between">
              <span class="text-sm text-gray-500 dark:text-gray-400">链接有效期</span>
              <span class="text-sm font-medium text-orange-600 dark:text-orange-400">{{ countdownText }}</span>
            </div>
          </div>
          
          <div class="space-y-3">
            <button
              @click="handleResendVerification"
              :disabled="isSubmitting"
              class="w-full py-3 px-4 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <div v-if="isSubmitting" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              {{ isSubmitting ? '发送中...' : '重新发送验证邮件' }}
            </button>
            
            <button
              @click="handleChangeEmail"
              class="w-full py-3 px-4 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition"
            >
              更换邮箱地址
            </button>
          </div>
        </div>
        
        <div v-else-if="showChangeEmailForm" class="space-y-4">
          <div class="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
            <p class="text-sm text-gray-600 dark:text-gray-400">
              请输入新的邮箱地址，我们将发送验证邮件到该地址。
            </p>
          </div>
          
          <form @submit.prevent="handleSubmitNewEmail" class="space-y-4">
            <div>
              <label for="new-email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                新邮箱地址
              </label>
              <input
                v-model="newEmail"
                type="email"
                id="new-email"
                name="new-email"
                autocomplete="email"
                placeholder="请输入新的邮箱地址"
                class="w-full px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition text-sm"
                :disabled="isSubmitting"
              />
            </div>
            
            <div>
              <label for="confirm-email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                确认邮箱地址
              </label>
              <input
                v-model="confirmEmail"
                type="email"
                id="confirm-email"
                name="confirm-email"
                autocomplete="email"
                placeholder="请再次输入邮箱地址"
                class="w-full px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition text-sm"
                :disabled="isSubmitting"
              />
            </div>
            
            <div class="flex gap-3">
              <button
                type="button"
                @click="handleCancelChangeEmail"
                :disabled="isSubmitting"
                class="flex-1 py-2.5 px-4 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition disabled:opacity-50"
              >
                取消
              </button>
              <button
                type="submit"
                :disabled="isSubmitting"
                class="flex-1 py-2.5 px-4 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <div v-if="isSubmitting" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                {{ isSubmitting ? '发送中...' : '发送验证邮件' }}
              </button>
            </div>
          </form>
        </div>
        
        <div v-else class="space-y-4">
          <div class="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
            <p class="text-sm text-gray-600 dark:text-gray-400">
              您尚未设置邮箱地址，请提供您的邮箱以完成账户设置。
            </p>
          </div>
          
          <form @submit.prevent="handleSubmitNewEmail" class="space-y-4">
            <div>
              <label for="setup-email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                邮箱地址
              </label>
              <input
                v-model="newEmail"
                type="email"
                id="setup-email"
                name="email"
                autocomplete="email"
                placeholder="请输入您的邮箱地址"
                class="w-full px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition text-sm"
                :disabled="isSubmitting"
              />
            </div>
            
            <div>
              <label for="setup-confirm-email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                确认邮箱地址
              </label>
              <input
                v-model="confirmEmail"
                type="email"
                id="setup-confirm-email"
                name="confirm-email"
                autocomplete="email"
                placeholder="请再次输入邮箱地址"
                class="w-full px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition text-sm"
                :disabled="isSubmitting"
              />
            </div>
            
            <button
              type="submit"
              :disabled="isSubmitting"
              class="w-full py-3 px-4 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <div v-if="isSubmitting" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              {{ isSubmitting ? '发送中...' : '发送验证邮件' }}
            </button>
          </form>
        </div>
        
        <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h3 class="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">
            没有收到邮件？
          </h3>
          <ul class="text-sm text-blue-700 dark:text-blue-300 space-y-1">
            <li>• 检查您的垃圾邮件/垃圾箱文件夹</li>
            <li>• 确认邮箱地址是否正确</li>
            <li>• 等待几分钟后再试</li>
            <li>• 尝试更换其他邮箱地址</li>
          </ul>
        </div>
        
        <div class="text-center">
          <router-link to="/login" class="text-sm text-gray-500 hover:text-primary transition">
            返回登录
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
