<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fileApi } from '@/api/files'
import type { ArticleFile } from '@/types'

const route = useRoute()
const router = useRouter()

const file = ref<ArticleFile | null>(null)
const loading = ref(true)
const error = ref('')
const downloading = ref(false)

const fileId = computed(() => parseInt(route.params.id as string))

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getFileTypeLabel = (fileType: string): string => {
  const typeMap: Record<string, string> = {
    image: '图片',
    document: '文档',
    video: '视频',
    audio: '音频',
    archive: '压缩包',
    other: '其他'
  }
  return typeMap[fileType] || fileType
}

const getFileIcon = (fileType: string, mimeType: string): string => {
  if (fileType === 'image') {
    return `<svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>`
  }
  
  if (mimeType.includes('pdf')) {
    return `<svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>`
  }
  
  if (mimeType.includes('word') || mimeType.includes('document')) {
    return `<svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>`
  }
  
  if (mimeType.includes('sheet') || mimeType.includes('excel')) {
    return `<svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>`
  }
  
  if (fileType === 'video') {
    return `<svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>`
  }
  
  if (fileType === 'audio') {
    return `<svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
    </svg>`
  }
  
  if (fileType === 'archive') {
    return `<svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
    </svg>`
  }
  
  return `<svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
  </svg>`
}

const fetchFile = async () => {
  loading.value = true
  error.value = ''
  
  try {
    file.value = await fileApi.getFileInfo(fileId.value)
  } catch (err: any) {
    console.error('Failed to fetch file:', err)
    error.value = err.response?.data?.detail || '文件不存在或已被删除'
  } finally {
    loading.value = false
  }
}

const downloadFile = async () => {
  if (!file.value || downloading.value) return
  
  downloading.value = true
  
  try {
    const response = await fileApi.downloadFile(file.value.id)
    const url = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = file.value.original_filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Failed to download file:', err)
  } finally {
    downloading.value = false
  }
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  fetchFile()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-dark-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-3xl mx-auto">
      <button
        @click="goBack"
        class="mb-6 flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        <span>返回</span>
      </button>
      
      <div v-if="loading" class="flex justify-center items-center py-20">
        <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
      
      <div v-else-if="error" class="bg-white dark:bg-dark-100 rounded-lg shadow-lg p-8 text-center">
        <svg class="w-16 h-16 mx-auto text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">{{ error }}</h2>
        <p class="text-gray-600 dark:text-gray-400 mb-4">该文件可能已被删除或您没有访问权限</p>
        <button
          @click="goBack"
          class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
        >
          返回上一页
        </button>
      </div>
      
      <div v-else-if="file" class="bg-white dark:bg-dark-100 rounded-lg shadow-lg overflow-hidden">
        <div class="p-6 border-b border-gray-200 dark:border-white/10">
          <div class="flex items-start gap-4">
            <div 
              class="flex-shrink-0 w-20 h-20 flex items-center justify-center rounded-lg bg-gray-100 dark:bg-dark-200 text-gray-600 dark:text-gray-400"
              v-html="getFileIcon(file.file_type, file.mime_type)"
            />
            
            <div class="flex-1 min-w-0">
              <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2 break-all">
                {{ file.original_filename }}
              </h1>
              <div class="flex flex-wrap gap-2">
                <span class="px-2 py-1 text-xs font-medium rounded-full bg-primary/10 text-primary">
                  {{ getFileTypeLabel(file.file_type) }}
                </span>
                <span class="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 dark:bg-dark-200 text-gray-700 dark:text-gray-300">
                  {{ file.mime_type }}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="file.is_image" class="p-6 border-b border-gray-200 dark:border-white/10">
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">图片预览</div>
          <div class="flex justify-center bg-gray-50 dark:bg-dark-200 rounded-lg p-4">
            <img
              :src="fileApi.getDownloadUrl(file.id)"
              :alt="file.original_filename"
              class="max-w-full max-h-96 object-contain rounded"
            />
          </div>
        </div>
        
        <div class="p-6 border-b border-gray-200 dark:border-white/10">
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">文件信息</div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">文件大小</div>
              <div class="text-sm font-medium text-gray-900 dark:text-white">
                {{ formatFileSize(file.file_size) }}
              </div>
            </div>
            <div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">上传时间</div>
              <div class="text-sm font-medium text-gray-900 dark:text-white">
                {{ formatDate(file.created_at) }}
              </div>
            </div>
            <div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">下载次数</div>
              <div class="text-sm font-medium text-gray-900 dark:text-white">
                {{ file.download_count }} 次
              </div>
            </div>
            <div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">预览次数</div>
              <div class="text-sm font-medium text-gray-900 dark:text-white">
                {{ file.preview_count }} 次
              </div>
            </div>
          </div>
        </div>
        
        <div class="p-6 flex gap-3">
          <button
            @click="downloadFile"
            :disabled="downloading"
            class="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="downloading" class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            <span>{{ downloading ? '下载中...' : '下载文件' }}</span>
          </button>
          
          <button
            @click="goBack"
            class="px-6 py-3 bg-gray-100 dark:bg-dark-200 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-300 transition-colors"
          >
            返回
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
