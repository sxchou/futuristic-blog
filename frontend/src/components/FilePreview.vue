<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { fileApi } from '@/api'

interface ArticleFile {
  id: number
  filename: string
  original_filename: string
  file_size: number
  file_type: string
  mime_type: string
  is_image: boolean
  download_count: number
  created_at: string
}

const props = defineProps<{
  file: ArticleFile
}>()

const emit = defineEmits<{
  close: []
}>()

const loading = ref(true)
const error = ref('')
const textContent = ref('')
const imageLoaded = ref(false)

const getFileExtension = (filename: string): string => {
  return filename.split('.').pop()?.toLowerCase() || ''
}

const fileExtension = computed(() => getFileExtension(props.file.original_filename))

const isOfficeFile = computed(() => {
  const officeExtensions = ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']
  return officeExtensions.includes(fileExtension.value)
})

const isTextFile = computed(() => {
  const textExtensions = ['txt', 'md', 'csv', 'json', 'xml', 'html', 'css', 'js', 'ts', 'py', 'java', 'c', 'cpp', 'h', 'hpp', 'sql', 'yaml', 'yml', 'ini', 'conf', 'log', 'sh', 'bat']
  const textMimeTypes = ['text/plain', 'text/markdown', 'text/csv', 'application/json', 'text/xml', 'text/html', 'text/css', 'text/javascript']
  return textExtensions.includes(fileExtension.value) || textMimeTypes.includes(props.file.mime_type)
})

const isPdfFile = computed(() => {
  return fileExtension.value === 'pdf' || props.file.mime_type === 'application/pdf'
})

const isImageFile = computed(() => {
  return props.file.is_image || ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico'].includes(fileExtension.value)
})

const isArchiveFile = computed(() => {
  const archiveExtensions = ['zip', 'rar', '7z', 'tar', 'gz']
  return archiveExtensions.includes(fileExtension.value)
})

const isAudioFile = computed(() => {
  const audioExtensions = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma']
  return audioExtensions.includes(fileExtension.value) || props.file.mime_type.startsWith('audio/')
})

const isVideoFile = computed(() => {
  const videoExtensions = ['mp4', 'webm', 'avi', 'mov', 'wmv', 'flv', 'mkv']
  return videoExtensions.includes(fileExtension.value) || props.file.mime_type.startsWith('video/')
})

const previewType = computed(() => {
  if (isImageFile.value) return 'image'
  if (isPdfFile.value) return 'pdf'
  if (isOfficeFile.value) return 'office'
  if (isTextFile.value) return 'text'
  if (isAudioFile.value) return 'audio'
  if (isVideoFile.value) return 'video'
  if (isArchiveFile.value) return 'archive'
  return 'unsupported'
})

const downloadUrl = computed(() => {
  return fileApi.getDownloadUrl(props.file.id)
})

const isLocalhost = computed(() => {
  const hostname = window.location.hostname
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.')
})

const officePreviewUrl = computed(() => {
  if (isLocalhost.value) return ''
  const encodedUrl = encodeURIComponent(window.location.origin + downloadUrl.value)
  return `https://view.officeapps.live.com/op/embed.aspx?src=${encodedUrl}`
})

const officeFileType = computed(() => {
  const ext = fileExtension.value
  if (['doc', 'docx'].includes(ext)) return 'Word'
  if (['xls', 'xlsx'].includes(ext)) return 'Excel'
  if (['ppt', 'pptx'].includes(ext)) return 'PowerPoint'
  return 'Office'
})

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const getFileIconComponent = computed(() => {
  const ext = fileExtension.value
  
  if (isImageFile.value) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-green-400 to-green-600',
      svg: `<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.5">
        <rect x="3" y="3" width="26" height="26" rx="3" fill="currentColor" fill-opacity="0.2"/>
        <circle cx="11" cy="11" r="3" fill="currentColor"/>
        <path d="M29 20l-7-7L7 29" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>`
    }
  }
  
  if (isPdfFile.value) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-red-500 to-red-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
        <path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/>
        <path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/>
        <foreignObject x="4" y="16" width="24" height="12">
          <div xmlns="http://www.w3.org/1999/xhtml" style="color: white; font-size: 9px; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; line-height: 12px;">PDF</div>
        </foreignObject>
      </svg>`
    }
  }
  
  if (['doc', 'docx'].includes(ext)) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-blue-500 to-blue-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
        <path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/>
        <path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/>
        <foreignObject x="4" y="16" width="24" height="16">
          <div xmlns="http://www.w3.org/1999/xhtml" style="color: white; font-size: 14px; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; line-height: 16px;">W</div>
        </foreignObject>
      </svg>`
    }
  }
  
  if (['xls', 'xlsx'].includes(ext)) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-emerald-500 to-emerald-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
        <path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/>
        <path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/>
        <foreignObject x="4" y="16" width="24" height="16">
          <div xmlns="http://www.w3.org/1999/xhtml" style="color: white; font-size: 14px; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; line-height: 16px;">X</div>
        </foreignObject>
      </svg>`
    }
  }
  
  if (['ppt', 'pptx'].includes(ext)) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-orange-500 to-orange-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
        <path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/>
        <path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/>
        <foreignObject x="4" y="16" width="24" height="16">
          <div xmlns="http://www.w3.org/1999/xhtml" style="color: white; font-size: 14px; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; line-height: 16px;">P</div>
        </foreignObject>
      </svg>`
    }
  }
  
  if (isTextFile.value) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-slate-500 to-slate-700',
      svg: `<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="currentColor" fill-opacity="0.3"/>
        <path d="M18 2v8h8"/>
        <path d="M9 16h14M9 21h10" stroke-width="2.5" stroke-linecap="round"/>
      </svg>`
    }
  }
  
  if (isAudioFile.value) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-purple-500 to-purple-700',
      svg: `<svg viewBox="0 0 32 32" fill="currentColor">
        <path d="M12 24V6l16-3v18"/>
        <circle cx="8" cy="24" r="4"/>
        <circle cx="24" cy="21" r="4"/>
      </svg>`
    }
  }
  
  if (isVideoFile.value) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-pink-500 to-pink-700',
      svg: `<svg viewBox="0 0 32 32" fill="currentColor">
        <rect x="2" y="5" width="28" height="22" rx="3" fill-opacity="0.3"/>
        <polygon points="13,10 22,16 13,22"/>
      </svg>`
    }
  }
  
  if (isArchiveFile.value) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-amber-500 to-amber-700',
      svg: `<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M28 10v18H4V10" fill="currentColor" fill-opacity="0.3"/>
        <path d="M30 4H2v6h28V4z" fill="currentColor" fill-opacity="0.5"/>
        <rect x="13" y="14" width="6" height="5" fill="currentColor" rx="1"/>
        <rect x="13" y="21" width="6" height="4" fill="currentColor" fill-opacity="0.5" rx="1"/>
      </svg>`
    }
  }
  
  return {
    color: 'text-white',
    bg: 'bg-gradient-to-br from-gray-400 to-gray-600',
    svg: `<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="currentColor" fill-opacity="0.3"/>
      <path d="M18 2v8h8"/>
    </svg>`
  }
})

const getArchiveInfo = (): { type: string; description: string } => {
  const archiveTypes: Record<string, { type: string; description: string }> = {
    zip: { type: 'ZIP', description: '标准压缩格式' },
    rar: { type: 'RAR', description: '高压缩率格式' },
    '7z': { type: '7-Zip', description: '高压缩率开源格式' },
    tar: { type: 'TAR', description: 'Unix归档格式' },
    gz: { type: 'GZIP', description: 'GNU压缩格式' }
  }
  return archiveTypes[fileExtension.value] || { type: '压缩包', description: '压缩文件' }
}

const fetchTextContent = async () => {
  if (previewType.value !== 'text') return
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await fetch(downloadUrl.value)
    if (!response.ok) throw new Error('加载失败')
    
    const text = await response.text()
    
    if (text.length > 100000) {
      textContent.value = text.substring(0, 100000) + '\n\n... (文件过大，仅显示前100KB内容)'
    } else {
      textContent.value = text
    }
  } catch (err) {
    error.value = '无法加载文件内容'
    console.error('Failed to load text content:', err)
  } finally {
    loading.value = false
  }
}

const handleImageLoad = () => {
  imageLoaded.value = true
  loading.value = false
}

const handleImageError = () => {
  loading.value = false
  error.value = '图片加载失败'
}

const handleIframeLoad = () => {
  loading.value = false
}

const handleIframeError = () => {
  loading.value = false
  error.value = '预览加载失败'
}

const handleDownload = () => {
  window.open(downloadUrl.value, '_blank')
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    emit('close')
  }
}

watch(() => props.file, () => {
  loading.value = true
  error.value = ''
  textContent.value = ''
  imageLoaded.value = false
  
  if (previewType.value === 'text') {
    fetchTextContent()
  } else if (previewType.value === 'audio' || previewType.value === 'video' || previewType.value === 'archive' || previewType.value === 'unsupported') {
    loading.value = false
  } else if (previewType.value === 'office' && isLocalhost.value) {
    loading.value = false
  }
}, { immediate: true })

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.body.style.overflow = 'hidden'
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm"
      @click.self="emit('close')"
    >
      <div class="relative w-full h-full max-w-7xl max-h-[95vh] m-4 flex flex-col bg-gray-900 dark:bg-dark-300 rounded-xl overflow-hidden shadow-2xl">
        <div class="flex items-center justify-between px-3 py-1 border-b border-gray-700 dark:border-white/10 bg-gray-800/50">
          <div class="flex items-center gap-2 min-w-0 flex-1">
            <span 
              class="w-6 h-6 flex-shrink-0 flex items-center justify-center rounded"
              :class="[getFileIconComponent.bg, getFileIconComponent.color]"
              v-html="getFileIconComponent.svg"
            ></span>
            <h3 class="text-xs font-medium text-white break-all leading-tight m-0">
              {{ file.original_filename }}
            </h3>
            <span class="text-[10px] text-gray-500 flex-shrink-0">
              {{ formatFileSize(file.file_size) }}
            </span>
          </div>
          <div class="flex items-center gap-1 flex-shrink-0 ml-2">
            <button
              @click="handleDownload"
              title="下载"
              class="p-1.5 text-gray-400 hover:text-primary hover:bg-gray-700/50 rounded transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </button>
            <button
              @click="emit('close')"
              class="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-auto relative">
          <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-gray-900 z-10">
            <div class="flex flex-col items-center gap-4">
              <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
              <p class="text-gray-400">加载中...</p>
            </div>
          </div>

          <div v-if="error && !loading" class="flex items-center justify-center h-full">
            <div class="text-center">
              <p class="text-red-400 text-lg mb-4">{{ error }}</p>
              <button
                @click="handleDownload"
                class="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/80 transition-colors"
              >
                直接下载
              </button>
            </div>
          </div>

          <div v-if="previewType === 'image'" class="flex items-center justify-center h-full p-4">
            <img
              :src="downloadUrl"
              :alt="file.original_filename"
              class="max-w-full max-h-full object-contain rounded-lg shadow-lg"
              @load="handleImageLoad"
              @error="handleImageError"
            />
          </div>

          <div v-else-if="previewType === 'pdf'" class="h-full">
            <iframe
              :src="downloadUrl"
              class="w-full h-full border-0"
              @load="handleIframeLoad"
              @error="handleIframeError"
            />
          </div>

          <div v-else-if="previewType === 'office'" class="h-full">
            <iframe
              v-if="!isLocalhost"
              :src="officePreviewUrl"
              class="w-full h-full border-0"
              @load="handleIframeLoad"
              @error="handleIframeError"
            />
            <div v-else class="flex items-center justify-center h-full p-8">
              <div class="text-center max-w-md">
                <div 
                  class="w-20 h-20 mx-auto mb-6 flex items-center justify-center rounded-xl"
                  :class="[getFileIconComponent.bg]"
                >
                  <span 
                    class="w-12 h-12"
                    :class="getFileIconComponent.color"
                    v-html="getFileIconComponent.svg"
                  ></span>
                </div>
                <h4 class="text-xl font-semibold text-white mb-2">{{ file.original_filename }}</h4>
                <div class="bg-gray-800 dark:bg-dark-400 rounded-lg p-6 mt-4">
                  <div class="flex items-center justify-between mb-3">
                    <span class="text-gray-400">类型:</span>
                    <span class="text-white font-medium">{{ officeFileType }} 文档</span>
                  </div>
                  <div class="flex items-center justify-between mb-3">
                    <span class="text-gray-400">大小:</span>
                    <span class="text-white font-medium">{{ formatFileSize(file.file_size) }}</span>
                  </div>
                </div>
                <p class="text-yellow-400 mt-4 text-sm">
                  ⚠️ Office 文件预览需要在线环境，本地开发环境暂不支持
                </p>
                <button
                  @click="handleDownload"
                  class="mt-6 px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/80 transition-colors"
                >
                  下载文件
                </button>
              </div>
            </div>
          </div>

          <div v-else-if="previewType === 'text'" class="h-full p-6">
            <pre class="h-full overflow-auto p-4 bg-gray-800 dark:bg-dark-400 rounded-lg text-gray-100 text-sm font-mono whitespace-pre-wrap break-words">{{ textContent }}</pre>
          </div>

          <div v-else-if="previewType === 'audio'" class="flex items-center justify-center h-full p-8">
            <div class="text-center">
              <div 
                class="w-20 h-20 mx-auto mb-6 flex items-center justify-center rounded-xl"
                :class="[getFileIconComponent.bg]"
              >
                <span 
                  class="w-12 h-12"
                  :class="getFileIconComponent.color"
                  v-html="getFileIconComponent.svg"
                ></span>
              </div>
              <h4 class="text-xl font-semibold text-white mb-4">{{ file.original_filename }}</h4>
              <audio
                :src="downloadUrl"
                controls
                class="w-full max-w-md"
              >
                您的浏览器不支持音频播放
              </audio>
            </div>
          </div>

          <div v-else-if="previewType === 'video'" class="flex items-center justify-center h-full p-4">
            <video
              :src="downloadUrl"
              controls
              class="max-w-full max-h-full rounded-lg shadow-lg"
            >
              您的浏览器不支持视频播放
            </video>
          </div>

          <div v-else-if="previewType === 'archive'" class="flex items-center justify-center h-full p-8">
            <div class="text-center max-w-md">
              <div 
                class="w-20 h-20 mx-auto mb-6 flex items-center justify-center rounded-xl"
                :class="[getFileIconComponent.bg]"
              >
                <span 
                  class="w-12 h-12"
                  :class="getFileIconComponent.color"
                  v-html="getFileIconComponent.svg"
                ></span>
              </div>
              <h4 class="text-xl font-semibold text-white mb-2">{{ file.original_filename }}</h4>
              <div class="bg-gray-800 dark:bg-dark-400 rounded-lg p-6 mt-4">
                <div class="flex items-center justify-between mb-3">
                  <span class="text-gray-400">类型:</span>
                  <span class="text-white font-medium">{{ getArchiveInfo().type }}</span>
                </div>
                <div class="flex items-center justify-between mb-3">
                  <span class="text-gray-400">大小:</span>
                  <span class="text-white font-medium">{{ formatFileSize(file.file_size) }}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-gray-400">描述:</span>
                  <span class="text-white font-medium">{{ getArchiveInfo().description }}</span>
                </div>
              </div>
              <p class="text-gray-400 mt-4 text-sm">
                压缩包文件需要下载后解压查看
              </p>
              <button
                @click="handleDownload"
                class="mt-6 px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/80 transition-colors"
              >
                下载文件
              </button>
            </div>
          </div>

          <div v-else-if="previewType === 'unsupported'" class="flex items-center justify-center h-full p-8">
            <div class="text-center">
              <div 
                class="w-20 h-20 mx-auto mb-6 flex items-center justify-center rounded-xl"
                :class="[getFileIconComponent.bg]"
              >
                <span 
                  class="w-12 h-12"
                  :class="getFileIconComponent.color"
                  v-html="getFileIconComponent.svg"
                ></span>
              </div>
              <h4 class="text-xl font-semibold text-white mb-2">{{ file.original_filename }}</h4>
              <p class="text-gray-400 mb-6">
                此文件类型暂不支持在线预览
              </p>
              <button
                @click="handleDownload"
                class="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/80 transition-colors"
              >
                下载文件
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
pre::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

pre::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

pre::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
}

pre::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}
</style>
