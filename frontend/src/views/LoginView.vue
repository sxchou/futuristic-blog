<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, useSiteConfigStore, useDialogStore } from '@/stores'
import { authApi } from '@/api'
import SliderCaptcha from '@/components/common/SliderCaptcha.vue'

const router = useRouter()
const authStore = useAuthStore()
const siteConfigStore = useSiteConfigStore()
const dialog = useDialogStore()

const form = ref({
  username: '',
  password: ''
})

const isLoading = ref(false)
const usernameError = ref('')
const passwordError = ref('')
const generalError = ref('')
const showResendOption = ref(false)
const resendEmail = ref('')
const isResending = ref(false)
const isCaptchaVerified = ref(false)
const captchaRef = ref<InstanceType<typeof SliderCaptcha> | null>(null)

const handleCaptchaSuccess = () => {
  isCaptchaVerified.value = true
  generalError.value = ''
}

const onUsernameInput = () => {
  usernameError.value = ''
}

const onPasswordInput = () => {
  passwordError.value = ''
}

const handleLogin = async () => {
  usernameError.value = ''
  passwordError.value = ''
  generalError.value = ''
  showResendOption.value = false

  let hasError = false

  if (!form.value.username) {
    usernameError.value = '请输入用户名或邮箱'
    hasError = true
  }

  if (!form.value.password) {
    passwordError.value = '请输入密码'
    hasError = true
  }

  if (!isCaptchaVerified.value) {
    generalError.value = '请先完成滑动验证'
    hasError = true
  }

  if (hasError) return

  isLoading.value = true

  try {
    await authStore.login({
      username: form.value.username,
      password: form.value.password
    })
    router.push('/')
  } catch (error: any) {
    const responseData = error.response?.data
    
    if (responseData?.detail?.need_verification) {
      showResendOption.value = true
      resendEmail.value = responseData.detail.email || ''
      generalError.value = responseData.detail.message
    } else {
      const detail = responseData?.detail || '登录失败，请检查用户名和密码'
      const message = typeof detail === 'string' ? detail : detail.message || '登录失败'
      
      if (message.includes('用户不存在')) {
        usernameError.value = '用户名/邮箱不存在'
      } else if (message.includes('密码错误')) {
        passwordError.value = message
      } else {
        generalError.value = message
      }
    }
    
    if (captchaRef.value) {
      captchaRef.value.reset()
      isCaptchaVerified.value = false
    }
  } finally {
    isLoading.value = false
  }
}

const handleResend = async () => {
  if (!resendEmail.value) {
    await dialog.showError('请输入您的邮箱地址', '提示')
    return
  }

  isResending.value = true
  try {
    await authApi.resendVerification(resendEmail.value)
    await dialog.showSuccess('验证邮件已发送，请查收', '成功')
    showResendOption.value = false
  } catch (error: any) {
    await dialog.showError(error.response?.data?.detail || '发送失败', '错误')
  } finally {
    isResending.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-dark flex items-center justify-center px-4 py-16">
    <div class="w-full max-w-sm">
      <div class="glass-card p-6">
        <div class="text-center mb-6">
          <div class="w-12 h-12 mx-auto mb-3 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
            <span class="text-xl font-bold text-white">{{ siteConfigStore.siteLogo }}</span>
          </div>
          <h1 class="text-xl font-bold gradient-text">欢迎回来</h1>
          <p class="text-gray-500 dark:text-gray-400 mt-1 text-sm">登录您的账户</p>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">用户名/邮箱</label>
            <input
              v-model="form.username"
              type="text"
              id="login-username"
              name="username"
              autocomplete="username"
              @input="onUsernameInput"
              :class="[
                'w-full px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none transition-colors text-sm',
                usernameError ? 'border-red-500 focus:border-red-500' : 'border-gray-200 dark:border-white/10 focus:border-primary'
              ]"
              placeholder="请输入用户名或邮箱"
            />
            <p v-if="usernameError" class="mt-1 text-xs text-red-400">{{ usernameError }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">密码</label>
            <input
              v-model="form.password"
              type="password"
              id="login-password"
              name="password"
              autocomplete="current-password"
              @input="onPasswordInput"
              :class="[
                'w-full px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none transition-colors text-sm',
                passwordError ? 'border-red-500 focus:border-red-500' : 'border-gray-200 dark:border-white/10 focus:border-primary'
              ]"
              placeholder="请输入密码"
            />
            <p v-if="passwordError" class="mt-1 text-xs text-red-400">{{ passwordError }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">人机验证</label>
            <SliderCaptcha 
              ref="captchaRef"
              @success="handleCaptchaSuccess" 
            />
          </div>

          <div v-if="generalError" class="p-2.5 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p class="text-red-400 text-xs">{{ generalError }}</p>
          </div>

          <div v-if="showResendOption" class="p-3 bg-primary/10 border border-primary/20 rounded-lg">
            <p class="text-xs text-gray-300 mb-2">您的邮箱尚未验证，点击按钮重新发送验证邮件：</p>
            <div class="flex gap-2">
              <input
                v-model="resendEmail"
                type="email"
                id="resend-email"
                name="email"
                autocomplete="email"
                placeholder="输入邮箱地址"
                class="flex-1 px-2.5 py-2 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary focus:outline-none"
              />
              <button
                type="button"
                @click="handleResend"
                :disabled="isResending"
                class="px-3 py-2 text-xs bg-primary text-white rounded-lg hover:bg-primary/80 disabled:opacity-50 whitespace-nowrap"
              >
                {{ isResending ? '发送中...' : '重新发送' }}
              </button>
            </div>
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full py-2.5 bg-gradient-to-r from-primary to-accent text-white font-semibold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 text-sm"
          >
            <span v-if="isLoading" class="flex items-center justify-center gap-2">
              <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              登录中...
            </span>
            <span v-else>登录</span>
          </button>
        </form>

        <div class="mt-4 text-center">
          <p class="text-gray-500 dark:text-gray-400 text-sm">
            还没有账户？
            <router-link to="/register" class="text-primary hover:underline">立即注册</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
