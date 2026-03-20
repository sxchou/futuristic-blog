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

const verifyEmail = async () => {
  const token = route.query.token as string
  const email = route.query.email as string

  if (!token || !email) {
    error.value = '无效的验证链接'
    isLoading.value = false
    return
  }

  try {
    const response = await oauthApi.verifyEmail(token, email)
    
    authStore.setTokens(
      response.access_token,
      response.refresh_token,
      response.expires_in
    )
    await authStore.fetchUser()
    
    await dialog.showSuccess('邮箱验证成功！', '欢迎加入我们')
    
    await router.push('/')
    window.location.reload()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '验证失败，请重试'
    isLoading.value = false
  }
}

onMounted(() => {
  verifyEmail()
})
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-dark flex items-center justify-center px-4">
    <div class="text-center">
      <div v-if="isLoading" class="space-y-4">
        <div class="w-12 h-12 mx-auto border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        <p class="text-gray-500 dark:text-gray-400">正在验证邮箱...</p>
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
