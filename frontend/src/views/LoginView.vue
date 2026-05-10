<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, useSiteConfigStore, useDialogStore } from '@/stores'
import { authApi } from '@/api'
import { oauthApi } from '@/api/oauth'
import type { OAuthProviderResponse } from '@/api/oauth'
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
const oauthProviders = ref<OAuthProviderResponse[]>([])
const oauthLoading = ref<string | null>(null)
const activeTooltip = ref<number | null>(null)

const OAUTH_CACHE_KEY = 'oauth_providers_cache'
const OAUTH_CACHE_EXPIRY = 24 * 60 * 60 * 1000 // 24小时

const showTooltip = (id: number) => {
  activeTooltip.value = id
}

const hideTooltip = () => {
  activeTooltip.value = null
}

const getCachedProviders = (): OAuthProviderResponse[] | null => {
  try {
    const cached = localStorage.getItem(OAUTH_CACHE_KEY)
    if (!cached) return null
    
    const { data, timestamp } = JSON.parse(cached)
    const now = Date.now()
    
    if (now - timestamp > OAUTH_CACHE_EXPIRY) {
      localStorage.removeItem(OAUTH_CACHE_KEY)
      return null
    }
    
    return data
  } catch (e) {
    return null
  }
}

const cacheProviders = (providers: OAuthProviderResponse[]) => {
  try {
    localStorage.setItem(OAUTH_CACHE_KEY, JSON.stringify({
      data: providers,
      timestamp: Date.now()
    }))
  } catch (e) {
    console.error('Failed to cache OAuth providers:', e)
  }
}

const fetchOAuthProviders = async () => {
  const cached = getCachedProviders()
  if (cached && cached.length > 0) {
    oauthProviders.value = cached
    return
  }
  
  oauthLoading.value = 'loading'
  try {
    const providers = await oauthApi.getLoginProviders()
    oauthProviders.value = providers
    if (providers.length > 0) {
      cacheProviders(providers)
    }
  } catch (error) {
    console.error('Failed to fetch OAuth providers:', error)
  } finally {
    oauthLoading.value = null
  }
}

const handleOAuthLogin = async (provider: OAuthProviderResponse) => {
  if (!provider.is_configured || !provider.is_enabled) return
  oauthLoading.value = provider.name
  try {
    const response = await oauthApi.getLoginUrl(provider.name)
    window.location.href = response.authorize_url
  } catch (error: any) {
    let errorMsg: string
    if (!error.response) {
      if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        errorMsg = '网络连接失败，请检查网络后重试'
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMsg = '请求超时，请稍后重试'
      } else {
        errorMsg = '服务暂时不可用，请稍后重试'
      }
    } else if (error.response.status >= 500) {
      errorMsg = '服务器繁忙，请稍后重试'
    } else {
      errorMsg = error.response?.data?.detail || '登录失败，请重试'
    }
    await dialog.showError(errorMsg, '错误')
  } finally {
    oauthLoading.value = null
  }
}

const getProviderIcon = (icon: string | null) => {
  const icons: Record<string, string> = {
    google: `<path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>`,
    github: `<path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>`,
    twitter: `<path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>`,
    x: `<path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>`,
    wechat: `<path d="M8.5 3.5C4.36 3.5 1 6.19 1 9.5c0 1.84 1.06 3.48 2.71 4.57-.12.42-.44 1.52-.5 1.76-.08.31.11.31.24.22.1-.07 1.47-.96 2.07-1.35.62.12 1.27.19 1.98.19.26 0 .51-.01.76-.03-.16-.48-.25-.99-.25-1.52 0-2.85 2.77-5.16 6.19-5.16.26 0 .52.02.77.04C14.54 5.21 11.83 3.5 8.5 3.5zm-2.25 3c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1zm4.5 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1z"/><path d="M23 14.5c0-2.76-2.69-5-6-5s-6 2.24-6 5 2.69 5 6 5c.55 0 1.08-.06 1.58-.17.48.32 1.58 1.03 1.67 1.09.11.07.26.07.19-.18-.05-.19-.31-1.07-.4-1.41C21.89 17.99 23 16.38 23 14.5zm-8-.75c-.41 0-.75-.34-.75-.75s.34-.75.75-.75.75.34.75.75-.34.75-.75.75zm4 0c-.41 0-.75-.34-.75-.75s.34-.75.75-.75.75.34.75.75-.34.75-.75.75z"/>`,
    qq: `<path d="M12.003 2c-2.265 0-6.29 1.364-6.29 7.325v1.195S3.55 14.96 3.55 17.474c0 .665.17 1.025.281 1.025.114 0 .902-.484 1.748-2.072 0 0-.18 2.197 1.904 3.967 0 0-1.77.495-1.77 1.182 0 .686 4.078.43 6.29.43 2.212 0 6.29.256 6.29-.43 0-.687-1.77-1.182-1.77-1.182 2.085-1.77 1.905-3.967 1.905-3.967.845 1.588 1.634 2.072 1.746 2.072.111 0 .283-.36.283-1.025 0-2.514-2.166-6.954-2.166-6.954V9.325C18.29 3.364 14.268 2 12.003 2z"/>`
  }
  
  if (!icon) {
    return `<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>`
  }
  
  const lowerIcon = icon.toLowerCase()
  if (icons[lowerIcon]) {
    return icons[lowerIcon]
  }
  
  if (/^[MmLlHhVvCcSsQqTtAaZz]/.test(icon.trim())) {
    return `<path d="${icon}"/>`
  }
  
  return `<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>`
}

const getProviderButtonClass = (provider: OAuthProviderResponse) => {
  const base = 'flex items-center justify-center w-9 h-9 rounded-full border transition-all duration-200'
  if (!provider.is_configured || !provider.is_enabled) {
    return `${base} bg-gray-100 dark:bg-dark-100 border-gray-200 dark:border-white/10 text-gray-400 dark:text-gray-500 cursor-not-allowed opacity-60`
  }
  switch (provider.name) {
    case 'google':
      return `${base} bg-white dark:bg-dark-100 border-gray-200 dark:border-white/20 hover:border-gray-300 dark:hover:border-white/30 hover:shadow-md`
    case 'github':
      return `${base} bg-gray-900 dark:bg-gray-800 border-gray-900 dark:border-gray-700 text-white hover:bg-gray-800 dark:hover:bg-gray-700 hover:shadow-md`
    case 'x':
    case 'twitter':
      return `${base} bg-black dark:bg-dark-100 border-black dark:border-white/20 text-white hover:bg-gray-900 dark:hover:bg-dark-200 hover:shadow-md`
    case 'wechat':
      return `${base} bg-[#07C160] border-[#07C160] text-white hover:bg-[#06AD56] hover:shadow-md`
    case 'qq':
      return `${base} bg-[#12B7F5] border-[#12B7F5] text-white hover:bg-[#0FA8E0] hover:shadow-md`
    default:
      return `${base} bg-gray-100 dark:bg-dark-100 border-gray-200 dark:border-white/20 hover:bg-gray-200 dark:hover:bg-dark-200 hover:shadow-md`
  }
}

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

const scrollToField = async (fieldId: string) => {
  await nextTick()
  const element = document.getElementById(fieldId)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    element.focus({ preventScroll: true })
  }
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

  if (hasError) {
    if (usernameError.value) {
      await scrollToField('login-username')
    } else if (passwordError.value) {
      await scrollToField('login-password')
    }
    return
  }

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
      router.push({
        path: '/pending-verification',
        query: {
          email: responseData.detail.email,
          username: responseData.detail.username,
          expires: responseData.detail.verification_token_expires,
          is_expired: responseData.detail.is_expired ? 'true' : 'false'
        }
      })
      return
    }
    
    let message: string
    
    if (!error.response) {
      if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        message = '网络连接失败，请检查网络后重试'
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        message = '请求超时，请稍后重试'
      } else {
        message = '服务暂时不可用，请稍后重试'
      }
      generalError.value = message
    } else {
      const status = error.response.status
      const detail = responseData?.detail
      message = typeof detail === 'string' ? detail : detail?.message || ''
      
      if (status >= 500) {
        generalError.value = '服务器繁忙，请稍后重试'
      } else if (status === 401) {
        if (message.includes('用户不存在')) {
          usernameError.value = '用户名/邮箱不存在'
        } else if (message.includes('密码错误')) {
          passwordError.value = '密码错误'
        } else {
          generalError.value = message || '用户名或密码错误'
        }
      } else if (message) {
        if (message.includes('用户不存在')) {
          usernameError.value = '用户名/邮箱不存在'
        } else if (message.includes('密码错误')) {
          passwordError.value = message
        } else {
          generalError.value = message
        }
      } else {
        generalError.value = '登录失败，请稍后重试'
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
  if (!resendEmail.value) return
  
  isResending.value = true
  try {
    await authApi.resendVerification(resendEmail.value)
    showResendOption.value = false
    generalError.value = ''
    await dialog.showSuccess('验证邮件已重新发送', '成功')
  } catch (error: any) {
    await dialog.showError(error.response?.data?.detail || '发送失败', '错误')
  } finally {
    isResending.value = false
  }
}

onMounted(fetchOAuthProviders)
</script>

<template>
  <div class="flex items-center justify-center px-4 pb-32">
    <div class="w-full max-w-[386px]">
      <div class="glass-card p-5">
        <div class="text-center mb-4">
          <div class="w-12 h-12 mx-auto mb-2 rounded-full bg-white dark:bg-gray-800 flex items-center justify-center overflow-hidden shadow-sm">
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
                    id="login-logo-grad"
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
                  fill="url(#login-logo-grad)"
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
            欢迎回来
          </h1>
          <p class="text-gray-500 dark:text-gray-400 mt-0.5 text-xs">
            登录您的账户
          </p>
        </div>

        <form
          class="space-y-3"
          @submit.prevent="handleLogin"
        >
          <div>
            <label
              for="login-username"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
            >用户名/邮箱</label>
            <input
              id="login-username"
              v-model="form.username"
              type="text"
              name="username"
              autocomplete="username"
              class="w-full px-3 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
              placeholder="请输入用户名或邮箱"
              @input="onUsernameInput"
            >
            <p
              v-if="usernameError"
              class="mt-1 text-xs text-red-400"
            >
              {{ usernameError }}
            </p>
          </div>

          <div>
            <label
              for="login-password"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
            >密码</label>
            <input
              id="login-password"
              v-model="form.password"
              type="password"
              name="password"
              autocomplete="current-password"
              class="w-full px-3 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
              placeholder="请输入密码"
              @input="onPasswordInput"
            >
            <p
              v-if="passwordError"
              class="mt-1 text-xs text-red-400"
            >
              {{ passwordError }}
            </p>
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <span class="block text-xs font-medium text-gray-700 dark:text-gray-300">验证</span>
              <router-link
                to="/forgot-password"
                class="text-xs text-gray-500 dark:text-gray-400 hover:text-primary transition-colors"
              >
                忘记密码？
              </router-link>
            </div>
            <SliderCaptcha 
              ref="captchaRef"
              @success="handleCaptchaSuccess" 
            />
          </div>

          <div
            v-if="generalError"
            class="p-2 bg-red-500/10 border border-red-500/20 rounded-lg"
          >
            <p class="text-red-400 text-xs">
              {{ generalError }}
            </p>
          </div>

          <div
            v-if="showResendOption"
            class="p-2 bg-primary/10 border border-primary/20 rounded-lg"
          >
            <p class="text-xs text-gray-300 mb-1.5">
              您的邮箱尚未验证
            </p>
            <div class="flex gap-2">
              <input
                id="resend-email"
                v-model="resendEmail"
                type="email"
                name="resend-email"
                autocomplete="email"
                class="flex-1 px-2 py-1.5 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white"
                placeholder="邮箱地址"
              >
              <button
                type="button"
                :disabled="isResending"
                class="px-2 py-1.5 text-xs bg-primary text-white rounded hover:bg-primary/80 disabled:opacity-50 whitespace-nowrap"
                @click="handleResend"
              >
                {{ isResending ? '发送中' : '重发' }}
              </button>
            </div>
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full py-2 bg-primary text-white font-medium rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 text-sm"
          >
            <span
              v-if="isLoading"
              class="flex items-center justify-center gap-1.5"
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
              登录中...
            </span>
            <span v-else>登录</span>
          </button>
        </form>

        <div class="mt-3 text-center">
          <p class="text-gray-500 dark:text-gray-400 text-xs">
            还没有账户？
            <router-link
              to="/register"
              class="text-primary hover:underline"
            >
              立即注册
            </router-link>
          </p>
        </div>

        <div class="mt-4 min-h-[88px]">
          <div
            v-if="oauthLoading === 'loading' && oauthProviders.length === 0"
            class="animate-pulse"
          >
            <div class="flex items-center gap-[1px]">
              <div class="flex-1 border-t border-gray-200 dark:border-white/10" />
              <span class="px-[1px] bg-white dark:bg-dark-200 text-xs text-gray-500 dark:text-gray-400">或</span>
              <div class="flex-1 border-t border-gray-200 dark:border-white/10" />
            </div>

            <div class="mt-3 flex items-center justify-center gap-2">
              <div class="w-9 h-9 rounded-full bg-gray-200 dark:bg-gray-700" />
              <div class="w-9 h-9 rounded-full bg-gray-200 dark:bg-gray-700" />
            </div>
          </div>

          <template v-else-if="oauthProviders.length > 0">
            <div class="flex items-center gap-[1px]">
              <div class="flex-1 border-t border-gray-200 dark:border-white/10" />
              <span class="px-[1px] bg-white dark:bg-dark-200 text-xs text-gray-500 dark:text-gray-400">或</span>
              <div class="flex-1 border-t border-gray-200 dark:border-white/10" />
            </div>

            <div class="mt-3 flex items-center justify-center gap-2 flex-wrap">
              <div
                v-for="provider in oauthProviders"
                :key="provider.id"
                class="relative"
                @mouseenter="showTooltip(provider.id)"
                @mouseleave="hideTooltip"
              >
                <button
                  type="button"
                  :disabled="oauthLoading === provider.name || (!provider.is_configured || !provider.is_enabled)"
                  :class="getProviderButtonClass(provider)"
                  :aria-label="`使用${provider.display_name}登录`"
                  @click="handleOAuthLogin(provider)"
                >
                  <svg
                    class="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    :aria-label="provider.display_name"
                    v-html="getProviderIcon(provider.icon)"
                  />
                </button>
                <span
                  v-if="activeTooltip === provider.id"
                  class="oauth-btn-tooltip"
                  role="tooltip"
                >
                  {{ provider.display_name }}{{ !provider.is_configured || !provider.is_enabled ? ' (当前不可用)' : '' }}
                </span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.oauth-btn-tooltip {
  position: absolute !important;
  bottom: calc(100% + 8px) !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  padding: 4px 8px !important;
  background: #ffffff !important;
  color: #1a1a2e !important;
  font-size: 12px !important;
  font-weight: normal !important;
  border-radius: 4px !important;
  white-space: nowrap !important;
  pointer-events: none !important;
  z-index: 9999 !important;
  opacity: 1 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
}

html.dark .oauth-btn-tooltip {
  background: #0f0f1a !important;
  color: #f1f5f9 !important;
}
</style>
