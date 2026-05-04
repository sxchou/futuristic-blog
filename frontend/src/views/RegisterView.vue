<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, useSiteConfigStore } from '@/stores'
import { checkServerHealth } from '@/api/client'

const router = useRouter()
const authStore = useAuthStore()
const siteConfigStore = useSiteConfigStore()

const form = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const isLoading = ref(false)
const errorMessage = ref('')

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
    const isHealthy = await checkServerHealth()
    if (!isHealthy) {
      errorMessage.value = '服务暂时不可用，请稍后重试'
      isLoading.value = false
      return
    }

    const response = await authStore.register({
      username: form.value.username,
      email: form.value.email,
      password: form.value.password
    })
    
    router.push({
      path: '/pending-verification',
      query: {
        email: form.value.email,
        username: form.value.username,
        expires: response?.verification_token_expires || undefined,
        is_expired: 'false'
      }
    })
  } catch (error: any) {
    if (!error.response) {
      if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        errorMessage.value = '网络连接失败，请检查网络后重试'
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMessage.value = '请求超时，请稍后重试'
      } else {
        errorMessage.value = '服务暂时不可用，请稍后重试'
      }
    } else if (error.response.status >= 500) {
      errorMessage.value = '服务器繁忙，请稍后重试'
    } else {
      errorMessage.value = error.response?.data?.detail || '注册失败，请稍后重试'
    }
  } finally {
    isLoading.value = false
  }
}
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
                    id="register-logo-grad"
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
                  fill="url(#register-logo-grad)"
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
            创建账户
          </h1>
          <p class="text-gray-500 dark:text-gray-400 mt-0.5 text-xs">
            加入我们的技术社区
          </p>
        </div>

        <form
          class="space-y-3"
          @submit.prevent="handleRegister"
        >
          <div>
            <label
              for="register-username"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
            >用户名</label>
            <input
              id="register-username"
              v-model="form.username"
              type="text"
              name="username"
              autocomplete="username"
              class="w-full px-3 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
              placeholder="请输入用户名"
            >
          </div>

          <div>
            <label
              for="register-email"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
            >邮箱</label>
            <input
              id="register-email"
              v-model="form.email"
              type="email"
              name="email"
              autocomplete="email"
              class="w-full px-3 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
              placeholder="请输入邮箱"
            >
          </div>

          <div>
            <label
              for="register-password"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
            >密码</label>
            <input
              id="register-password"
              v-model="form.password"
              type="password"
              name="new-password"
              autocomplete="new-password"
              class="w-full px-3 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
              placeholder="请输入密码"
            >
          </div>

          <div>
            <label
              for="register-confirm-password"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
            >确认密码</label>
            <input
              id="register-confirm-password"
              v-model="form.confirmPassword"
              type="password"
              name="confirm-password"
              autocomplete="new-password"
              class="w-full px-3 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
              placeholder="请再次输入密码"
            >
          </div>

          <div
            v-if="errorMessage"
            class="p-2 bg-red-500/10 border border-red-500/20 rounded-lg"
          >
            <p class="text-red-400 text-xs">
              {{ errorMessage }}
            </p>
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
              注册中...
            </span>
            <span v-else>注册</span>
          </button>
        </form>

        <div class="mt-3 text-center">
          <p class="text-gray-500 dark:text-gray-400 text-xs">
            已有账户？
            <router-link
              to="/login"
              class="text-primary hover:underline"
            >
              立即登录
            </router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
