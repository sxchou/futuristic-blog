<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, useDialogStore, useUserProfileStore } from '@/stores'
import { userProfileApi } from '@/api/userProfile'
import type { UserProfile } from '@/api/userProfile'
import AvatarCropper from './AvatarCropper.vue'

const props = defineProps<{
  size?: 'sm' | 'md' | 'lg'
  showDropdown?: boolean
  profile?: UserProfile | null
}>()

const emit = defineEmits<{
  (e: 'upload'): void
  (e: 'reset'): void
}>()

const router = useRouter()
const authStore = useAuthStore()
const dialogStore = useDialogStore()
const userProfileStore = useUserProfileStore()

const isDropdownOpen = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const fileInput = ref<HTMLInputElement | null>(null)
const showCropper = ref(false)
const selectedImageSrc = ref('')

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'w-8 h-8 text-sm'
    case 'lg':
      return 'w-16 h-16 text-2xl'
    default:
      return 'w-10 h-10 text-base'
  }
})

const avatarStyle = computed(() => {
  if (!props.profile) return {}
  
  if (props.profile.avatar_type === 'custom' && props.profile.avatar_url) {
    return {
      backgroundImage: `url(${props.profile.avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (props.profile.oauth_avatar_url) {
    return {
      backgroundImage: `url(${props.profile.oauth_avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (props.profile.default_avatar_gradient && props.profile.default_avatar_gradient.length >= 2) {
    const colors = props.profile.default_avatar_gradient
    return {
      background: `linear-gradient(135deg, ${colors[0]}, ${colors[1]})`
    }
  }
  
  return {
    background: 'linear-gradient(135deg, #667eea, #764ba2)'
  }
})

const showInitial = computed(() => {
  if (!props.profile) return true
  if (props.profile.avatar_type === 'custom' && props.profile.avatar_url) return false
  if (props.profile.oauth_avatar_url) return false
  return true
})

const initial = computed(() => {
  if (props.profile?.username) {
    return props.profile.username.charAt(0).toUpperCase()
  }
  if (authStore.user?.username) {
    return authStore.user.username.charAt(0).toUpperCase()
  }
  return 'U'
})

const toggleDropdown = () => {
  if (props.showDropdown) {
    isDropdownOpen.value = !isDropdownOpen.value
  }
}

const closeDropdown = () => {
  isDropdownOpen.value = false
}

const triggerUpload = () => {
  fileInput.value?.click()
  closeDropdown()
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
    emit('upload')
    
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

const handleReset = async () => {
  const confirmed = await dialogStore.showConfirm({ message: '确定要恢复默认头像吗？' })
  if (!confirmed) return
  
  try {
    await userProfileApi.resetAvatar()
    
    await userProfileStore.refreshProfile()
    
    dialogStore.showSuccess('已恢复默认头像')
    emit('reset')
    closeDropdown()
  } catch (error: any) {
    dialogStore.showError(error.response?.data?.detail || '操作失败')
  }
}

const handleUseOAuthAvatar = async () => {
  const confirmed = await dialogStore.showConfirm({ message: '确定要使用OAuth头像吗？' })
  if (!confirmed) return
  
  try {
    await userProfileApi.useOAuthAvatar()
    
    await userProfileStore.refreshProfile()
    
    dialogStore.showSuccess('已切换到OAuth头像')
    emit('reset')
    closeDropdown()
  } catch (error: any) {
    dialogStore.showError(error.response?.data?.detail || '操作失败')
  }
}

const goToProfile = () => {
  router.push('/admin/my-profile')
  closeDropdown()
}

const handleLogout = () => {
  authStore.logout()
  router.push('/')
  closeDropdown()
}

watch(isDropdownOpen, (isOpen) => {
  if (isOpen) {
    document.addEventListener('click', handleClickOutside)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.avatar-container')) {
    closeDropdown()
  }
}
</script>

<template>
  <div class="avatar-container relative" @click.stop>
    <button
      class="avatar-btn rounded-full flex items-center justify-center font-bold text-white shadow-lg transition-all duration-200 hover:scale-105 hover:shadow-xl cursor-pointer overflow-hidden"
      :class="[sizeClasses, { 'ring-2 ring-primary/50': showDropdown && isDropdownOpen }]"
      :style="avatarStyle"
      @click="toggleDropdown"
    >
      <span v-if="showInitial">{{ initial }}</span>
    </button>
    
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95 -translate-y-2"
      enter-to-class="opacity-100 scale-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100 translate-y-0"
      leave-to-class="opacity-0 scale-95 -translate-y-2"
    >
      <div
        v-if="showDropdown && isDropdownOpen"
        class="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden z-50"
      >
        <div class="p-3 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center gap-3">
            <div
              class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-sm overflow-hidden"
              :style="avatarStyle"
            >
              <span v-if="showInitial">{{ initial }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-medium text-gray-900 dark:text-white truncate">
                {{ profile?.username || authStore.user?.username || '用户' }}
              </p>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                {{ authStore.user?.is_admin ? '管理员' : '用户' }}
              </p>
            </div>
          </div>
        </div>
        
        <div class="p-2">
          <button
            @click="goToProfile"
            class="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            个人资料
          </button>
          
          <button
            @click="triggerUpload"
            class="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
            :disabled="isUploading"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span v-if="isUploading">上传中 {{ uploadProgress }}%</span>
            <span v-else>更换头像</span>
          </button>
          
          <button
            v-if="profile?.oauth_avatar_url && profile?.avatar_type !== 'oauth'"
            @click="handleUseOAuthAvatar"
            class="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            使用OAuth头像
          </button>
          
          <button
            v-if="profile?.avatar_type === 'custom' && !profile?.oauth_avatar_url"
            @click="handleReset"
            class="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            使用默认头像
          </button>
        </div>
        
        <div class="p-2 border-t border-gray-200 dark:border-gray-700">
          <router-link
            to="/admin"
            class="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
            @click="closeDropdown"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            管理后台
          </router-link>
          
          <button
            @click="handleLogout"
            class="w-full px-3 py-2 text-left text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            退出登录
          </button>
        </div>
      </div>
    </transition>
    
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
    
    <div
      v-if="isUploading"
      class="absolute inset-0 bg-black/50 rounded-full flex items-center justify-center"
    >
      <svg class="w-5 h-5 text-white animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
    </div>
  </div>
</template>

<style scoped>
.avatar-btn {
  user-select: none;
}

.avatar-btn:hover {
  transform: scale(1.05);
}
</style>
