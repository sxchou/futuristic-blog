<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { announcementApi, type Announcement } from '@/api'
import { useAuthStore, useUserProfileStore, useDialogStore } from '@/stores'
import { userProfileApi } from '@/api/userProfile'
import UserAvatar from './UserAvatar.vue'
import AvatarCropper from './AvatarCropper.vue'

const authStore = useAuthStore()
const userProfileStore = useUserProfileStore()
const dialogStore = useDialogStore()

const announcements = ref<Announcement[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
const uploadProgress = ref(0)
const showCropper = ref(false)
const selectedImageSrc = ref('')

const fetchAnnouncements = async () => {
  try {
    announcements.value = await announcementApi.getAnnouncements(true)
  } catch (error) {
    console.error('Failed to fetch announcements:', error)
  }
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

onMounted(() => {
  if (authStore.isAuthenticated && !userProfileStore.profile) {
    userProfileStore.fetchProfile()
  }
  fetchAnnouncements()
})

const getTypeIcon = (type: string) => {
  const icons = {
    info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
    success: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    error: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
  }
  return icons[type as keyof typeof icons] || icons.info
}

const getTypeColor = (type: string) => {
  const colors = {
    info: 'text-blue-500',
    warning: 'text-amber-500',
    success: 'text-emerald-500',
    error: 'text-red-500'
  }
  return colors[type as keyof typeof colors] || colors.info
}

const formatDate = (date: string) => {
  if (!date) return ''
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
</script>

<template>
  <aside class="blog-sidebar">
    <div class="sidebar-widget sidebar-widget-compact">
      <template v-if="authStore.isAuthenticated && authStore.user">
        <div class="p-4 bg-gray-50/50 dark:bg-white/[0.02] rounded-xl">
          <div class="flex flex-col items-center">
            <div class="relative mb-3 group">
              <div class="absolute inset-0 bg-gradient-to-br from-primary/20 to-accent/20 rounded-full blur-xl opacity-60" />
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
                  class="inline-flex items-center px-2 py-0.5 bg-gradient-to-r from-primary/20 to-accent/20 text-primary text-xs font-semibold rounded-full border border-primary/30"
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
                class="flex items-center gap-1 text-primary hover:text-primary/80 transition-colors font-medium"
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
            <div class="w-14 h-14 rounded-full bg-gradient-to-br from-gray-200 to-gray-300 dark:from-dark-400 dark:to-dark-500 flex items-center justify-center mb-3">
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
                class="flex-1 py-2 text-center text-xs font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-300 border border-gray-200 dark:border-white/10 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-400 transition-colors"
              >
                登录
              </router-link>
              <router-link
                to="/register"
                class="flex-1 py-2 text-center text-xs font-medium text-white bg-gradient-to-r from-primary to-accent rounded-lg hover:opacity-90 transition-opacity shadow-sm"
              >
                注册
              </router-link>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div
      v-if="announcements.length > 0"
      class="sidebar-widget sidebar-widget-compact"
    >
      <h3 class="sidebar-widget-title sidebar-widget-title-compact flex items-center gap-2">
        <svg
          class="w-4 h-4 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"
          />
        </svg>
        公告
      </h3>
      
      <div class="space-y-3">
        <div
          v-for="announcement in announcements"
          :key="announcement.id"
          class="group"
        >
          <div class="flex items-start gap-2">
            <svg
              :class="['w-4 h-4 mt-0.5 flex-shrink-0', getTypeColor(announcement.type)]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                :d="getTypeIcon(announcement.type)"
              />
            </svg>
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-semibold text-gray-900 dark:text-white group-hover:text-primary transition-colors">
                {{ announcement.title }}
              </h4>
              <p class="text-xs text-gray-600 dark:text-gray-400 mt-1 leading-relaxed">
                {{ announcement.content }}
              </p>
              <p class="text-xs text-gray-400 dark:text-gray-500 mt-1.5">
                {{ formatDate(announcement.updated_at || announcement.created_at) }}
              </p>
            </div>
          </div>
        </div>
      </div>
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
