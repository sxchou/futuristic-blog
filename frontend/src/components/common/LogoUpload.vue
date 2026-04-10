<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSiteConfigStore, useDialogStore } from '@/stores'
import { clearCacheByPattern } from '@/api/client'
import AvatarCropper from './AvatarCropper.vue'

const props = defineProps<{
  size?: 'sm' | 'md' | 'lg'
}>()

const emit = defineEmits<{
  (e: 'upload'): void
  (e: 'reset'): void
}>()

const siteConfigStore = useSiteConfigStore()
const dialogStore = useDialogStore()

const isUploading = ref(false)
const uploadProgress = ref(0)
const fileInput = ref<HTMLInputElement | null>(null)
const showCropper = ref(false)
const selectedImageSrc = ref('')

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'w-12 h-12 text-base'
    case 'lg':
      return 'w-24 h-24 text-3xl'
    default:
      return 'w-20 h-20 text-2xl'
  }
})

const getLogoUrl = (url: string) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  if (url.startsWith('/')) return url
  return `/${url}`
}

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/svg+xml', 'image/x-icon']
  if (!allowedTypes.includes(file.type)) {
    dialogStore.showError('仅支持 JPG、PNG、WebP、SVG、ICO 格式的图片')
    return
  }
  
  if (file.size > 2 * 1024 * 1024) {
    dialogStore.showError('文件大小不能超过 2MB')
    return
  }
  
  if (file.type === 'image/svg+xml' || file.type === 'image/x-icon') {
    await uploadDirectly(file)
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

const uploadDirectly = async (file: File) => {
  isUploading.value = true
  uploadProgress.value = 0
  
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const interval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 100)
    
    await siteConfigStore.updateSiteLogo(formData)
    clearCacheByPattern('/site-config')
    
    clearInterval(interval)
    uploadProgress.value = 100
    
    dialogStore.showSuccess('Logo上传成功')
    emit('upload')
    
    setTimeout(() => {
      isUploading.value = false
      uploadProgress.value = 0
    }, 500)
  } catch (error: any) {
    isUploading.value = false
    uploadProgress.value = 0
    dialogStore.showError(error.response?.data?.detail || 'Logo上传失败')
  }
}

const handleCropConfirm = async (blob: Blob) => {
  isUploading.value = true
  uploadProgress.value = 0
  
  try {
    const formData = new FormData()
    formData.append('file', blob, 'logo.jpg')
    
    const interval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 100)
    
    await siteConfigStore.updateSiteLogo(formData)
    clearCacheByPattern('/site-config')
    
    clearInterval(interval)
    uploadProgress.value = 100
    
    dialogStore.showSuccess('Logo上传成功')
    emit('upload')
    
    setTimeout(() => {
      isUploading.value = false
      uploadProgress.value = 0
    }, 500)
  } catch (error: any) {
    isUploading.value = false
    uploadProgress.value = 0
    dialogStore.showError(error.response?.data?.detail || 'Logo上传失败')
  }
}

const handleReset = async () => {
  const confirmed = await dialogStore.showConfirm({ message: '确定要恢复默认Logo吗？' })
  if (!confirmed) return
  
  try {
    await siteConfigStore.resetSiteLogo()
    clearCacheByPattern('/site-config')
    
    dialogStore.showSuccess('已恢复默认Logo')
    emit('reset')
  } catch (error: any) {
    dialogStore.showError(error.response?.data?.detail || '操作失败')
  }
}
</script>

<template>
  <div class="logo-upload-container">
    <div class="flex items-start gap-6">
      <div class="flex-shrink-0">
        <div
          v-if="siteConfigStore.siteLogoUrl"
          class="rounded-xl overflow-hidden bg-gray-100 dark:bg-dark-200 border border-gray-200 dark:border-white/10 flex items-center justify-center"
          :class="sizeClasses"
        >
          <img
            :src="getLogoUrl(siteConfigStore.siteLogoUrl)"
            alt="网站Logo"
            class="w-full h-full object-contain"
          >
        </div>
        <div
          v-else
          class="rounded-xl bg-black flex items-center justify-center relative overflow-hidden shadow-lg"
          :class="sizeClasses"
        >
          <svg
            viewBox="0 0 100 100"
            class="w-3/5 h-3/5"
          >
            <defs>
              <linearGradient
                id="logo-upload-grad"
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
              fill="url(#logo-upload-grad)"
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
      
      <div class="flex-1">
        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            :disabled="isUploading"
            class="px-4 py-2 bg-primary text-white text-sm rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2"
            @click="triggerUpload"
          >
            <svg
              v-if="isUploading"
              class="w-4 h-4 animate-spin"
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
            <span v-if="isUploading">上传中 {{ uploadProgress }}%</span>
            <span v-else>上传Logo</span>
          </button>
          <button
            v-if="siteConfigStore.siteLogoUrl"
            type="button"
            :disabled="isUploading"
            class="px-4 py-2 bg-gray-100 dark:bg-dark-200 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-200 dark:hover:bg-dark-300 transition-colors disabled:opacity-50"
            @click="handleReset"
          >
            恢复默认
          </button>
        </div>
        
        <p class="mt-2 text-xs text-gray-400 dark:text-gray-500">
          支持 JPG、PNG、WebP、SVG、ICO 格式，最大 2MB，建议尺寸 32x32 或 64x64
        </p>
      </div>
    </div>
    
    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png,image/webp,image/svg+xml,image/x-icon"
      class="hidden"
      @change="handleFileChange"
    >
    
    <AvatarCropper
      v-model="showCropper"
      :image-src="selectedImageSrc"
      :aspect-ratio="1"
      :output-width="64"
      :output-height="64"
      @confirm="handleCropConfirm"
    />
  </div>
</template>
