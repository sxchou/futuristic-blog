<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore, useUserProfileStore, useDialogStore } from '@/stores'
import { userProfileApi } from '@/api/userProfile'
import AvatarCropper from '@/components/common/AvatarCropper.vue'

const authStore = useAuthStore()
const userProfileStore = useUserProfileStore()
const dialogStore = useDialogStore()

const isLoading = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const fileInput = ref<HTMLInputElement | null>(null)
const showCropper = ref(false)
const selectedImageSrc = ref('')

const user = computed(() => authStore.user)
const profile = computed(() => userProfileStore.profile)

const avatarStyle = computed(() => {
  if (!profile.value) return {}
  
  if (profile.value.avatar_type === 'custom' && profile.value.avatar_url) {
    return {
      backgroundImage: `url(${profile.value.avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (profile.value.oauth_avatar_url) {
    return {
      backgroundImage: `url(${profile.value.oauth_avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (profile.value.default_avatar_gradient && profile.value.default_avatar_gradient.length >= 2) {
    const colors = profile.value.default_avatar_gradient
    return {
      background: `linear-gradient(135deg, ${colors[0]}, ${colors[1]})`
    }
  }
  
  return {
    background: 'linear-gradient(135deg, #667eea, #764ba2)'
  }
})

const showInitial = computed(() => {
  if (!profile.value) return true
  if (profile.value.avatar_type === 'custom' && profile.value.avatar_url) return false
  if (profile.value.oauth_avatar_url) return false
  return true
})

const initial = computed(() => {
  if (profile.value?.username) {
    return profile.value.username.charAt(0).toUpperCase()
  }
  if (user.value?.username) {
    return user.value.username.charAt(0).toUpperCase()
  }
  return 'U'
})

const fetchProfile = async () => {
  isLoading.value = true
  try {
    await userProfileStore.fetchProfile()
  } catch (error) {
    console.error('Failed to fetch profile:', error)
  } finally {
    isLoading.value = false
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
    
    dialogStore.showSuccess('头像上传成功')
    await userProfileStore.refreshProfile()
    
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

const handleResetAvatar = async () => {
  const confirmed = await dialogStore.showConfirm({ message: '确定要恢复默认头像吗？' })
  if (!confirmed) return
  
  try {
    await userProfileApi.resetAvatar()
    dialogStore.showSuccess('已恢复默认头像')
    await userProfileStore.refreshProfile()
  } catch (error: any) {
    dialogStore.showError(error.response?.data?.detail || '操作失败')
  }
}

const handleUseOAuthAvatar = async () => {
  const confirmed = await dialogStore.showConfirm({ message: '确定要使用OAuth头像吗？' })
  if (!confirmed) return
  
  try {
    await userProfileApi.useOAuthAvatar()
    dialogStore.showSuccess('已切换到OAuth头像')
    await userProfileStore.refreshProfile()
  } catch (error: any) {
    dialogStore.showError(error.response?.data?.detail || '操作失败')
  }
}

onMounted(fetchProfile)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">我的资料</h1>
    </div>

    <div v-if="isLoading" class="flex justify-center py-16">
      <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <div v-else class="space-y-6">
      <div class="glass-card p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">头像设置</h2>
        
        <div class="flex items-center gap-6">
          <div class="relative">
            <div
              class="w-24 h-24 rounded-full flex items-center justify-center font-bold text-white text-3xl shadow-lg overflow-hidden cursor-pointer transition-transform hover:scale-105"
              :style="avatarStyle"
              @click="triggerUpload"
            >
              <span v-if="showInitial">{{ initial }}</span>
            </div>
            
            <div
              v-if="isUploading"
              class="absolute inset-0 bg-black/50 rounded-full flex items-center justify-center"
            >
              <div class="text-white text-sm">{{ uploadProgress }}%</div>
            </div>
          </div>
          
          <div class="flex-1">
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
              点击头像更换图片，支持 JPG、PNG、WebP 格式，最大 10MB
            </p>
            <div class="flex gap-3 flex-wrap">
              <button
                @click="triggerUpload"
                class="px-4 py-2 bg-primary text-white text-sm rounded-lg hover:opacity-90 transition-opacity"
                :disabled="isUploading"
              >
                {{ isUploading ? '上传中...' : '上传头像' }}
              </button>
              <button
                v-if="profile?.oauth_avatar_url && profile?.avatar_type !== 'oauth'"
                @click="handleUseOAuthAvatar"
                class="px-4 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors"
                :disabled="isUploading"
              >
                使用OAuth头像
              </button>
              <button
                v-if="profile?.avatar_type === 'custom' && !profile?.oauth_avatar_url"
                @click="handleResetAvatar"
                class="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                恢复默认
              </button>
            </div>
          </div>
        </div>
        
        <input
          ref="fileInput"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          class="hidden"
          @change="handleFileChange"
        />
        
        <AvatarCropper
          v-model="showCropper"
          :image-src="selectedImageSrc"
          @confirm="handleCropConfirm"
        />
      </div>

      <div class="glass-card p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">账户信息</h2>
        
        <div class="space-y-4">
          <div class="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700">
            <span class="text-sm text-gray-600 dark:text-gray-400">用户名</span>
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ user?.username }}</span>
          </div>
          
          <div class="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700">
            <span class="text-sm text-gray-600 dark:text-gray-400">邮箱</span>
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ user?.email }}</span>
          </div>
          
          <div class="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700">
            <span class="text-sm text-gray-600 dark:text-gray-400">账户类型</span>
            <span 
              class="text-sm font-medium px-2 py-0.5 rounded"
              :class="user?.is_admin ? 'bg-primary/10 text-primary' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'"
            >
              {{ user?.is_admin ? '管理员' : '普通用户' }}
            </span>
          </div>
          
          <div class="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700">
            <span class="text-sm text-gray-600 dark:text-gray-400">邮箱验证</span>
            <span 
              class="text-sm font-medium px-2 py-0.5 rounded"
              :class="user?.is_verified ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400'"
            >
              {{ user?.is_verified ? '已验证' : '未验证' }}
            </span>
          </div>
          
          <div class="flex items-center justify-between py-3">
            <span class="text-sm text-gray-600 dark:text-gray-400">注册时间</span>
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ user?.created_at || '-' }}</span>
          </div>
        </div>
      </div>

      <div v-if="user?.is_admin" class="glass-card p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">管理功能</h2>
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
          作为管理员，您可以编辑网站所有者的公开资料信息（显示在"关于我"页面）。
        </p>
        <router-link
          to="/admin/profile"
          class="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary to-accent text-white text-sm rounded-lg hover:opacity-90 transition-opacity"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          编辑网站资料
        </router-link>
      </div>
    </div>
  </div>
</template>
