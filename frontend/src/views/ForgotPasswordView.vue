<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api'
import { useSiteConfigStore, useDialogStore } from '@/stores'
import { checkServerHealth } from '@/api/client'

const router = useRouter()
const siteConfigStore = useSiteConfigStore()
const dialog = useDialogStore()

const step = ref(1)
const email = ref('')
const code = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

const isLoading = ref(false)
const isSendingCode = ref(false)
const countdown = ref(0)
const emailError = ref('')
const codeError = ref('')
const passwordError = ref('')
const confirmError = ref('')

let countdownTimer: ReturnType<typeof setInterval> | null = null

const scrollToField = async (fieldId: string) => {
  await nextTick()
  const element = document.getElementById(fieldId)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    element.focus({ preventScroll: true })
  }
}

const isEmailValid = computed(() => {
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  return emailRegex.test(email.value)
})

const isPasswordValid = computed(() => {
  return newPassword.value.length >= 6
})

const isCodeValid = computed(() => {
  return /^\d{6}$/.test(code.value)
})

const canSubmit = computed(() => {
  if (step.value === 1) {
    return isEmailValid.value && !isSendingCode.value
  }
  return isEmailValid.value && isCodeValid.value && isPasswordValid.value && newPassword.value === confirmPassword.value
})

const formatCountdown = computed(() => {
  const minutes = Math.floor(countdown.value / 60)
  const seconds = countdown.value % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
})

const validateEmail = () => {
  emailError.value = ''
  if (!email.value) {
    emailError.value = '请输入邮箱地址'
    return false
  }
  if (!isEmailValid.value) {
    emailError.value = '请输入有效的邮箱地址'
    return false
  }
  return true
}

const validateCode = () => {
  codeError.value = ''
  if (!code.value) {
    codeError.value = '请输入验证码'
    return false
  }
  if (!isCodeValid.value) {
    codeError.value = '请输入6位数字验证码'
    return false
  }
  return true
}

const validatePassword = () => {
  passwordError.value = ''
  confirmError.value = ''
  
  if (!newPassword.value) {
    passwordError.value = '请输入新密码'
    return false
  }
  if (!isPasswordValid.value) {
    passwordError.value = '密码长度至少6位'
    return false
  }
  if (!confirmPassword.value) {
    confirmError.value = '请确认新密码'
    return false
  }
  if (newPassword.value !== confirmPassword.value) {
    confirmError.value = '两次输入的密码不一致'
    return false
  }
  return true
}

const startCountdown = (seconds: number) => {
  countdown.value = seconds
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer!)
      countdownTimer = null
    }
  }, 1000)
}

const handleSendCode = async () => {
  if (!validateEmail()) return
  
  isSendingCode.value = true
  try {
    const isHealthy = await checkServerHealth()
    if (!isHealthy) {
      emailError.value = '服务暂时不可用，请稍后重试'
      isSendingCode.value = false
      return
    }

    const result = await authApi.requestPasswordReset(email.value)
    step.value = 2
    startCountdown(result.expires_in)
    await dialog.showSuccess(result.message, '成功')
  } catch (error: any) {
    const detail = error.response?.data?.detail
    if (error.response?.status === 404) {
      emailError.value = detail || '该邮箱未注册'
    } else if (error.response?.status === 429) {
      await dialog.showError(detail || '请求次数过多，请稍后再试', '提示')
    } else {
      await dialog.showError(detail || '发送验证码失败', '错误')
    }
  } finally {
    isSendingCode.value = false
  }
}

const handleResendCode = async () => {
  if (countdown.value > 0) return
  
  isSendingCode.value = true
  try {
    const result = await authApi.requestPasswordReset(email.value)
    startCountdown(result.expires_in)
    await dialog.showSuccess('验证码已重新发送', '成功')
  } catch (error: any) {
    const detail = error.response?.data?.detail
    await dialog.showError(detail || '发送验证码失败', '错误')
  } finally {
    isSendingCode.value = false
  }
}

const handleResetPassword = async () => {
  const emailValid = validateEmail()
  const codeValid = validateCode()
  const passwordValid = validatePassword()
  
  if (!emailValid || !codeValid || !passwordValid) {
    if (emailError.value) {
      await scrollToField('forgot-email')
    } else if (codeError.value) {
      await scrollToField('forgot-code')
    } else if (passwordError.value) {
      await scrollToField('forgot-new-password')
    } else if (confirmError.value) {
      await scrollToField('forgot-confirm-password')
    }
    return
  }
  
  isLoading.value = true
  try {
    const isHealthy = await checkServerHealth()
    if (!isHealthy) {
      await dialog.showError('服务暂时不可用，请稍后重试', '错误')
      isLoading.value = false
      return
    }

    await authApi.verifyPasswordReset({
      email: email.value,
      code: code.value,
      new_password: newPassword.value,
      confirm_password: confirmPassword.value
    })
    
    await dialog.showSuccess('密码已重置，请使用新密码登录', '成功')
    router.push('/login')
  } catch (error: any) {
    const detail = error.response?.data?.detail
    if (detail?.includes('验证码')) {
      codeError.value = detail
    } else {
      await dialog.showError(detail || '密码重置失败', '错误')
    }
  } finally {
    isLoading.value = false
  }
}

const goBack = () => {
  if (step.value === 2) {
    step.value = 1
    code.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    codeError.value = ''
    passwordError.value = ''
    confirmError.value = ''
    if (countdownTimer) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  } else {
    router.push('/login')
  }
}
</script>

<template>
  <div class="flex items-center justify-center px-4 pb-32">
    <div class="w-full max-w-sm">
      <div class="glass-card p-6">
        <div class="text-center mb-6">
          <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-white dark:bg-gray-800 flex items-center justify-center overflow-hidden shadow-sm">
            <img
              v-if="siteConfigStore.siteLogoUrl"
              :src="siteConfigStore.siteLogoUrl"
              :alt="siteConfigStore.siteName"
              class="w-full h-full object-cover"
            >
            <div
              v-else
              class="w-full h-full bg-black flex items-center justify-center"
            >
              <svg
                viewBox="0 0 100 100"
                class="w-8 h-8"
              >
                <defs>
                  <linearGradient
                    id="forgot-logo-grad"
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="100%"
                  >
                    <stop
                      offset="0%"
                      style="stop-color:#00d4ff;stop-opacity:1"
                    />
                    <stop
                      offset="100%"
                      style="stop-color:#7c3aed;stop-opacity:1"
                    />
                  </linearGradient>
                </defs>
                <text
                  x="50"
                  y="68"
                  font-family="monospace"
                  font-size="55"
                  font-weight="bold"
                  fill="url(#forgot-logo-grad)"
                  text-anchor="middle"
                >F</text>
                <circle
                  cx="75"
                  cy="25"
                  r="8"
                  fill="#00d4ff"
                  opacity="0.8"
                />
                <circle
                  cx="85"
                  cy="35"
                  r="4"
                  fill="#7c3aed"
                  opacity="0.6"
                />
              </svg>
            </div>
          </div>
          <h1 class="text-lg font-bold gradient-text">
            忘记密码
          </h1>
          <p class="text-gray-500 dark:text-gray-400 mt-1 text-sm">
            {{ step === 1 ? '输入您的邮箱地址' : '验证身份并设置新密码' }}
          </p>
        </div>

        <div class="flex items-center justify-center mb-6">
          <div class="flex items-center">
            <div 
              :class="[
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors',
                step >= 1 ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-dark-100 text-gray-500'
              ]"
            >
              1
            </div>
            <div 
              :class="[
                'w-12 h-0.5 transition-colors',
                step >= 2 ? 'bg-primary' : 'bg-gray-200 dark:bg-dark-100'
              ]"
            />
            <div 
              :class="[
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors',
                step >= 2 ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-dark-100 text-gray-500'
              ]"
            >
              2
            </div>
          </div>
        </div>

        <form
          class="space-y-4"
          @submit.prevent="step === 1 ? handleSendCode() : handleResetPassword()"
        >
          <div>
            <label
              for="forgot-email"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >邮箱地址</label>
            <input
              id="forgot-email"
              v-model="email"
              type="email"
              name="email"
              autocomplete="email"
              :disabled="step === 2"
              :class="[
                'w-full px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none transition-colors text-sm',
                emailError ? 'border-red-500 focus:border-red-500' : 'border-gray-200 dark:border-white/10 focus:border-primary',
                step === 2 ? 'opacity-60 cursor-not-allowed' : ''
              ]"
              placeholder="请输入注册时使用的邮箱"
              @blur="validateEmail"
            >
            <p
              v-if="emailError"
              class="mt-1 text-xs text-red-400"
            >
              {{ emailError }}
            </p>
          </div>

          <template v-if="step === 2">
            <div>
              <label
                for="forgot-code"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >验证码</label>
              <div class="flex gap-2">
                <input
                  id="forgot-code"
                  v-model="code"
                  type="text"
                  name="code"
                  maxlength="6"
                  :class="[
                    'flex-1 px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none transition-colors text-sm tracking-widest text-center',
                    codeError ? 'border-red-500 focus:border-red-500' : 'border-gray-200 dark:border-white/10 focus:border-primary'
                  ]"
                  placeholder="请输入6位验证码"
                  @input="codeError = ''"
                >
                <button
                  type="button"
                  :disabled="countdown > 0 || isSendingCode"
                  class="px-3 py-2.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-200 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap transition-colors"
                  @click="handleResendCode"
                >
                  {{ countdown > 0 ? formatCountdown : (isSendingCode ? '发送中...' : '重新发送') }}
                </button>
              </div>
              <p
                v-if="codeError"
                class="mt-1 text-xs text-red-400"
              >
                {{ codeError }}
              </p>
            </div>

            <div>
              <label
                for="forgot-new-password"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >新密码</label>
              <input
                id="forgot-new-password"
                v-model="newPassword"
                type="password"
                name="new-password"
                autocomplete="new-password"
                :class="[
                  'w-full px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none transition-colors text-sm',
                  passwordError ? 'border-red-500 focus:border-red-500' : 'border-gray-200 dark:border-white/10 focus:border-primary'
                ]"
                placeholder="请输入新密码（至少6位）"
                @input="passwordError = ''"
              >
              <p
                v-if="passwordError"
                class="mt-1 text-xs text-red-400"
              >
                {{ passwordError }}
              </p>
            </div>

            <div>
              <label
                for="forgot-confirm-password"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >确认新密码</label>
              <input
                id="forgot-confirm-password"
                v-model="confirmPassword"
                type="password"
                name="confirm-password"
                autocomplete="new-password"
                :class="[
                  'w-full px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none transition-colors text-sm',
                  confirmError ? 'border-red-500 focus:border-red-500' : 'border-gray-200 dark:border-white/10 focus:border-primary'
                ]"
                placeholder="请再次输入新密码"
                @input="confirmError = ''"
              >
              <p
                v-if="confirmError"
                class="mt-1 text-xs text-red-400"
              >
                {{ confirmError }}
              </p>
            </div>
          </template>

          <button
            type="submit"
            :disabled="!canSubmit || isLoading || isSendingCode"
            class="w-full py-2.5 bg-primary text-white font-semibold rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 text-sm"
          >
            <span
              v-if="isLoading || isSendingCode"
              class="flex items-center justify-center gap-2"
            >
              <svg
                class="animate-spin w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              {{ step === 1 ? '发送中...' : '重置中...' }}
            </span>
            <span v-else>{{ step === 1 ? '获取验证码' : '重置密码' }}</span>
          </button>

          <button
            type="button"
            class="w-full py-2.5 text-gray-500 dark:text-gray-400 hover:text-primary transition-colors text-sm"
            @click="goBack"
          >
            {{ step === 2 ? '返回上一步' : '返回登录' }}
          </button>
        </form>

        <div class="mt-4 text-center">
          <p class="text-gray-500 dark:text-gray-400 text-sm">
            还没有账户？
            <router-link
              to="/register"
              class="text-primary hover:underline"
            >
              立即注册
            </router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
