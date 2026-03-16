<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, useSiteConfigStore } from '@/stores'

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
const showSuccess = ref(false)
const registeredEmail = ref('')

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
    await authStore.register({
      username: form.value.username,
      email: form.value.email,
      password: form.value.password
    })
    registeredEmail.value = form.value.email
    showSuccess.value = true
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
  <div class="min-h-screen flex items-center justify-center px-4 py-16">
    <div class="w-full max-w-sm">
      <div class="glass-card p-6">
        <div v-if="!showSuccess">
          <div class="text-center mb-6">
            <div class="w-12 h-12 mx-auto mb-3 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <span class="text-xl font-bold text-white">{{ siteConfigStore.siteLogo }}</span>
            </div>
            <h1 class="text-xl font-bold gradient-text">创建账户</h1>
            <p class="text-gray-500 dark:text-gray-400 mt-1 text-sm">加入我们的技术社区</p>
          </div>

          <form @submit.prevent="handleRegister" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">用户名</label>
              <input
                v-model="form.username"
                type="text"
                id="register-username"
                name="username"
                autocomplete="username"
                class="w-full px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
                placeholder="请输入用户名"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">邮箱</label>
              <input
                v-model="form.email"
                type="email"
                id="register-email"
                name="email"
                autocomplete="email"
                class="w-full px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
                placeholder="请输入邮箱"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">密码</label>
              <input
                v-model="form.password"
                type="password"
                id="register-password"
                name="new-password"
                autocomplete="new-password"
                class="w-full px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
                placeholder="请输入密码"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">确认密码</label>
              <input
                v-model="form.confirmPassword"
                type="password"
                id="register-confirm-password"
                name="confirm-password"
                autocomplete="new-password"
                class="w-full px-3 py-2.5 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none transition-colors text-sm"
                placeholder="请再次输入密码"
              />
            </div>

            <div v-if="errorMessage" class="p-2.5 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p class="text-red-400 text-xs">{{ errorMessage }}</p>
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
                注册中...
              </span>
              <span v-else>注册</span>
            </button>
          </form>

          <div class="mt-4 text-center">
            <p class="text-gray-500 dark:text-gray-400 text-sm">
              已有账户？
              <router-link to="/login" class="text-primary hover:underline">立即登录</router-link>
            </p>
          </div>
        </div>

        <div v-else class="text-center py-6">
          <div class="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-3">注册成功！</h2>
          <p class="text-gray-400 text-sm mb-1">我们已向您的邮箱发送了一封验证邮件</p>
          <p class="text-primary font-medium text-sm mb-4">{{ registeredEmail }}</p>
          <p class="text-xs text-gray-500 mb-4">
            请点击邮件中的链接验证您的邮箱地址，验证后即可登录。
          </p>
          <button @click="goToLogin" class="btn-primary w-full text-sm py-2.5">
            前往登录
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
