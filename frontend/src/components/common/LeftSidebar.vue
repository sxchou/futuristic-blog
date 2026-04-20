<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useAuthStore, useUserProfileStore, useDialogStore, useSiteConfigStore } from '@/stores'
import { userProfileApi } from '@/api/userProfile'
import UserAvatar from './UserAvatar.vue'
import AvatarCropper from './AvatarCropper.vue'

const authStore = useAuthStore()
const userProfileStore = useUserProfileStore()
const dialogStore = useDialogStore()
const siteConfigStore = useSiteConfigStore()

const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
const uploadProgress = ref(0)
const showCropper = ref(false)
const selectedImageSrc = ref('')

const showGithubSection = computed(() => {
  return siteConfigStore.showGithubStats && siteConfigStore.githubStats?.enabled
})

const formatCount = (count: number) => {
  if (count >= 1000) {
    return (count / 1000).toFixed(1) + 'k'
  }
  return count.toString()
}

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    dialogStore.showError('仅支持 JPG、PNG、WebP 格式的图片')
    return
  }
  
  if (file.size > 10 * 1024 * 1024) {
    dialogStore.showError('文件大小不能超过 10MB')
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    selectedImageSrc.value = e.target?.result as string
    showCropper.value = true
  }
  reader.readAsDataURL(file)
  
  if (target) {
    target.value = ''
  }
}

const handleCropConfirm = async (blob: Blob) => {
  isUploading.value = true
  uploadProgress.value = 0
  
  try {
    const formData = new FormData()
    formData.append('file', blob, 'avatar.jpg')
    
    const interval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 100)
    
    await userProfileApi.uploadAvatar(formData)
    
    clearInterval(interval)
    uploadProgress.value = 100
    
    await userProfileStore.refreshProfile()
    
    dialogStore.showSuccess('头像上传成功')
    
    setTimeout(() => {
      isUploading.value = false
      uploadProgress.value = 0
    }, 500)
  } catch (error: any) {
    isUploading.value = false
    uploadProgress.value = 0
    dialogStore.showError(error.response?.data?.detail || '头像上传失败')
  }
}

watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated) {
    userProfileStore.fetchProfile()
  } else {
    userProfileStore.clearProfile()
  }
})

watch(() => siteConfigStore.showGithubStats, (show) => {
  if (show && !siteConfigStore.githubStats) {
    siteConfigStore.fetchGithubStats()
  }
}, { immediate: true })

watch(() => siteConfigStore.githubRepoUrl, () => {
  if (siteConfigStore.showGithubStats) {
    siteConfigStore.fetchGithubStats()
  }
})

onMounted(() => {
  if (authStore.isAuthenticated && !userProfileStore.profile) {
    userProfileStore.fetchProfile()
  }
})
</script>

<template>
  <aside class="blog-sidebar">
    <div class="sidebar-widget sidebar-widget-compact">
      <template v-if="authStore.isAuthenticated && authStore.user">
        <div class="p-4 bg-gray-50/50 dark:bg-white/[0.02] rounded-xl">
          <div class="flex flex-col items-center">
            <div class="relative mb-3 group">
              <div class="absolute inset-0 bg-primary/10 dark:bg-primary/20 rounded-full blur-xl opacity-60" />
              <div class="relative">
                <button
                  class="relative cursor-pointer rounded-full overflow-hidden transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-primary/50"
                  :disabled="isUploading"
                  @click="triggerUpload"
                >
                  <UserAvatar
                    :profile="userProfileStore.profile"
                    size="lg"
                    :show-dropdown="false"
                  />
                  
                  <div
                    v-if="!isUploading"
                    class="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all duration-200 flex items-center justify-center opacity-0 group-hover:opacity-100"
                  >
                    <svg
                      class="w-6 h-6 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                      />
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                    </svg>
                  </div>
                  
                  <div
                    v-if="isUploading"
                    class="absolute inset-0 bg-black/60 flex items-center justify-center"
                  >
                    <div class="relative">
                      <svg
                        class="w-8 h-8 text-white animate-spin"
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
                      <div class="absolute inset-0 flex items-center justify-center">
                        <span class="text-xs font-bold text-white">{{ uploadProgress }}%</span>
                      </div>
                    </div>
                  </div>
                </button>
                
                <span
                  v-if="authStore.user.is_verified"
                  class="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-emerald-500 rounded-full flex items-center justify-center ring-2 ring-white dark:ring-dark-200"
                >
                  <svg
                    class="w-2.5 h-2.5 text-white"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </span>
              </div>
            </div>
            
            <div class="text-center mb-3">
              <div class="flex items-center justify-center gap-2 mb-2">
                <h4 class="text-base font-bold text-gray-900 dark:text-white m-0">
                  {{ userProfileStore.profile?.username || authStore.user.username }}
                </h4>
                <span
                  v-if="authStore.user.is_admin"
                  class="inline-flex items-center px-2 py-0.5 bg-primary/10 dark:bg-primary/20 text-primary text-xs font-semibold rounded-full border border-primary/30"
                >
                  管理员
                </span>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                {{ authStore.user.email }}
              </p>
            </div>
            
            <div class="w-full pt-3 border-t border-gray-200/50 dark:border-white/5 flex items-center justify-between text-xs">
              <span class="text-gray-400 dark:text-gray-500">ID: {{ authStore.user.id }}</span>
              <router-link
                to="/profile"
                class="flex items-center gap-1 text-gray-400 dark:text-gray-500 hover:text-gray-500 dark:hover:text-gray-400 transition-colors font-medium"
              >
                <svg
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7zM12 11a4 4 0 100-8 4 4 0 000 8z"
                  />
                </svg>
                个人中心
              </router-link>
            </div>
          </div>
        </div>
      </template>
      <template v-else>
        <div class="p-4 bg-gray-50/50 dark:bg-white/[0.02] rounded-xl">
          <div class="flex flex-col items-center">
            <div class="w-14 h-14 rounded-full bg-gray-200 dark:bg-dark-400 flex items-center justify-center mb-3">
              <svg
                class="w-7 h-7 text-gray-400 dark:text-gray-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
            </div>
            
            <div class="text-center mb-3">
              <h4 class="text-base font-bold text-gray-900 dark:text-white mb-1">
                欢迎访问
              </h4>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                登录以获取更多功能
              </p>
            </div>
            
            <div class="w-full flex gap-2">
              <router-link
                to="/login"
                class="flex-1 py-2 text-center text-xs font-medium text-primary bg-primary/10 border border-primary/30 rounded-lg hover:bg-primary/20 hover:border-primary/50 transition-colors"
              >
                登录
              </router-link>
              <router-link
                to="/register"
                class="flex-1 py-2 text-center text-xs font-medium text-white bg-primary rounded-lg hover:bg-primary/90 transition-colors shadow-sm"
              >
                注册
              </router-link>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div
      v-if="showGithubSection"
      class="sidebar-widget sidebar-widget-compact"
    >
      <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
        <svg
          class="w-4 h-4 text-primary"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
        </svg>
        GitHub
      </h3>
      
      <a
        :href="siteConfigStore.githubRepoUrl"
        target="_blank"
        rel="noopener noreferrer"
        class="block group"
      >
        <div class="flex flex-col gap-3">
          <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg hover:bg-gray-100 dark:hover:bg-white/[0.05] transition-colors">
            <div class="flex items-center gap-2">
              <svg
                class="w-4 h-4 text-amber-500"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
              <span class="text-xs text-gray-600 dark:text-gray-400">Stars</span>
            </div>
            <span class="text-sm font-semibold text-gray-900 dark:text-white group-hover:text-primary transition-colors">
              {{ formatCount(siteConfigStore.githubStats?.stars || 0) }}
            </span>
          </div>
          
          <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg hover:bg-gray-100 dark:hover:bg-white/[0.05] transition-colors">
            <div class="flex items-center gap-2">
              <svg
                class="w-4 h-4 text-blue-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                />
              </svg>
              <span class="text-xs text-gray-600 dark:text-gray-400">Forks</span>
            </div>
            <span class="text-sm font-semibold text-gray-900 dark:text-white group-hover:text-primary transition-colors">
              {{ formatCount(siteConfigStore.githubStats?.forks || 0) }}
            </span>
          </div>
          
          <div class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-white/[0.02] rounded-lg hover:bg-gray-100 dark:hover:bg-white/[0.05] transition-colors">
            <div class="flex items-center gap-2">
              <svg
                class="w-4 h-4 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
              <span class="text-xs text-gray-600 dark:text-gray-400">Watchers</span>
            </div>
            <span class="text-sm font-semibold text-gray-900 dark:text-white group-hover:text-primary transition-colors">
              {{ formatCount(siteConfigStore.githubStats?.watchers || 0) }}
            </span>
          </div>
          
          <div class="mt-2 p-3 bg-gray-50 dark:bg-white/[0.02] rounded-lg border border-gray-200/60 dark:border-white/5">
            <div class="flex items-center gap-2 mb-1.5">
              <svg
                class="w-3.5 h-3.5 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              <span class="text-xs font-medium text-gray-700 dark:text-gray-300">欢迎 Fork 本项目</span>
            </div>
            <p class="text-xs text-gray-500 dark:text-gray-400 leading-relaxed flex items-center gap-1 flex-wrap">
              欢迎Star ⭐ 和
              <svg
                class="w-3.5 h-3.5 text-blue-500 inline-block"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                />
              </svg>
              Fork 支持
            </p>
          </div>
        </div>
      </a>
    </div>
    
    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png,image/webp"
      class="hidden"
      @change="handleFileChange"
    >
    
    <AvatarCropper
      v-model="showCropper"
      :image-src="selectedImageSrc"
      @confirm="handleCropConfirm"
    />
  </aside>
</template>
