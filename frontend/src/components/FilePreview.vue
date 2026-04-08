<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { fileApi, type ArchiveContent } from '@/api'
import type { ArticleFile } from '@/types'

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
const archiveContent = ref<ArchiveContent | null>(null)
const archiveLoading = ref(false)
const expandedDirs = ref<Set<string>>(new Set())
const searchQuery = ref('')
const sortField = ref<'name' | 'size' | 'type'>('name')
const sortDirection = ref<'asc' | 'desc'>('asc')

const imageScale = ref(1)
const imageTranslateX = ref(0)
const imageTranslateY = ref(0)
const isDragging = ref(false)
const dragStartX = ref(0)
const dragStartY = ref(0)
const lastTranslateX = ref(0)
const lastTranslateY = ref(0)

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

const directUrl = computed(() => {
  if (props.file.file_path && props.file.file_path.startsWith('http')) {
    return props.file.file_path
  }
  return null
})

const fileUrl = computed(() => {
  return directUrl.value || ''
})

const downloadUrl = computed(() => {
  return directUrl.value || ''
})

const isLocalhost = computed(() => {
  const hostname = window.location.hostname
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.')
})

const officePreviewUrl = computed(() => {
  if (isLocalhost.value) return ''
  
  let url = fileUrl.value
  
  if (url.startsWith('/api/storage?')) {
    url = `${window.location.origin}${url}`
  }
  
  const encodedUrl = encodeURIComponent(url)
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
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
        <rect x="3" y="3" width="26" height="26" rx="3" fill="rgba(255,255,255,0.2)"/>
        <circle cx="11" cy="11" r="3" fill="white"/>
        <path d="M29 20l-7-7L7 29" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
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
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
        <path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/>
        <path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/>
        <path d="M9 16h14M9 21h10" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
      </svg>`
    }
  }
  
  if (isAudioFile.value) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-purple-500 to-purple-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
        <path d="M12 24V6l16-3v18" fill="rgba(255,255,255,0.5)"/>
        <circle cx="8" cy="24" r="4" fill="white"/>
        <circle cx="24" cy="21" r="4" fill="white"/>
      </svg>`
    }
  }
  
  if (isVideoFile.value) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-pink-500 to-pink-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
        <rect x="2" y="5" width="28" height="22" rx="3" fill="rgba(255,255,255,0.3)"/>
        <polygon points="13,10 22,16 13,22" fill="white"/>
      </svg>`
    }
  }
  
  if (isArchiveFile.value) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-amber-500 to-amber-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
        <path d="M28 10v18H4V10" fill="rgba(255,255,255,0.3)"/>
        <path d="M30 4H2v6h28V4z" fill="rgba(255,255,255,0.5)"/>
        <rect x="13" y="14" width="6" height="5" fill="white" rx="1"/>
        <rect x="13" y="21" width="6" height="4" fill="rgba(255,255,255,0.5)" rx="1"/>
      </svg>`
    }
  }
  
  return {
    color: 'text-white',
    bg: 'bg-gradient-to-br from-gray-400 to-gray-600',
    svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
      <path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/>
      <path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/>
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

const fetchArchiveContent = async () => {
  if (previewType.value !== 'archive') return
  
  archiveLoading.value = true
  error.value = ''
  
  try {
    archiveContent.value = await fileApi.getArchiveContent(props.file.id)
  } catch (err: any) {
    console.error('Failed to load archive content:', err)
    error.value = err.response?.data?.detail || '无法加载压缩包内容'
  } finally {
    archiveLoading.value = false
  }
}

const toggleDir = (path: string) => {
  if (expandedDirs.value.has(path)) {
    expandedDirs.value.delete(path)
  } else {
    expandedDirs.value.add(path)
  }
}

const isExpanded = (path: string) => expandedDirs.value.has(path)

const highlightText = (text: string, query: string): string => {
  if (!query) return text
  
  if (query.includes('*') || query.includes('?')) {
    try {
      const pattern = query
        .replace(/[.+^${}()|[\]\\]/g, '\\$&')
        .replace(/\*/g, '.*')
        .replace(/\?/g, '.')
      
      const regex = new RegExp(`(${pattern})`, 'gi')
      return text.replace(regex, '<mark class="bg-yellow-400/40 text-yellow-100 rounded px-0.5">$1</mark>')
    } catch (e) {
      return text
    }
  }
  
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return text.replace(regex, '<mark class="bg-yellow-400/40 text-yellow-100 rounded px-0.5">$1</mark>')
}

const getFileIcon = (name: string, isDir: boolean): string => {
  if (isDir) {
    return `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
    </svg>`
  }
  
  const ext = name.split('.').pop()?.toLowerCase() || ''
  const iconColors: Record<string, string> = {
    'jpg': 'text-green-400', 'jpeg': 'text-green-400', 'png': 'text-green-400', 'gif': 'text-green-400', 'webp': 'text-green-400', 'svg': 'text-green-400',
    'pdf': 'text-red-400',
    'doc': 'text-blue-400', 'docx': 'text-blue-400',
    'xls': 'text-emerald-400', 'xlsx': 'text-emerald-400',
    'ppt': 'text-orange-400', 'pptx': 'text-orange-400',
    'zip': 'text-amber-400', 'rar': 'text-amber-400', '7z': 'text-amber-400',
    'mp3': 'text-purple-400', 'wav': 'text-purple-400', 'flac': 'text-purple-400',
    'mp4': 'text-pink-400', 'avi': 'text-pink-400', 'mkv': 'text-pink-400',
    'txt': 'text-gray-400', 'md': 'text-gray-400',
    'js': 'text-yellow-400', 'ts': 'text-blue-300',
    'html': 'text-orange-400', 'css': 'text-blue-400',
    'json': 'text-yellow-400', 'xml': 'text-orange-400'
  }
  
  const color = iconColors[ext] || 'text-gray-400'
  
  return `<svg class="w-4 h-4 ${color}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>`
}

const filteredEntries = computed(() => {
  if (!archiveContent.value || !searchQuery.value) return null
  
  const query = searchQuery.value
  
  if (query.includes('*') || query.includes('?')) {
    try {
      const pattern = query
        .replace(/[.+^${}()|[\]\\]/g, '\\$&')
        .replace(/\*/g, '.*')
        .replace(/\?/g, '.')
      
      const regex = new RegExp(pattern, 'i')
      
      return archiveContent.value.entries.filter(entry => 
        regex.test(entry.name) || regex.test(entry.path)
      )
    } catch (e) {
      return archiveContent.value.entries.filter(entry => 
        entry.name.toLowerCase().includes(query.toLowerCase()) || 
        entry.path.toLowerCase().includes(query.toLowerCase())
      )
    }
  }
  
  return archiveContent.value.entries.filter(entry => 
    entry.name.toLowerCase().includes(query.toLowerCase()) || 
    entry.path.toLowerCase().includes(query.toLowerCase())
  )
})

const renderTree = (node: any, depth: number = 0): any[] => {
  if (!node.children) return []
  
  const result: any[] = []
  let children = Object.values(node.children) as any[]
  
  children = children.sort((a, b) => {
    if (a.is_dir !== b.is_dir) {
      return a.is_dir ? -1 : 1
    }
    
    let comparison = 0
    if (sortField.value === 'name') {
      comparison = a.name.localeCompare(b.name, 'zh-CN')
    } else if (sortField.value === 'size') {
      comparison = (a.size || 0) - (b.size || 0)
    } else if (sortField.value === 'type') {
      const extA = a.name.split('.').pop()?.toLowerCase() || ''
      const extB = b.name.split('.').pop()?.toLowerCase() || ''
      comparison = extA.localeCompare(extB)
    }
    
    return sortDirection.value === 'asc' ? comparison : -comparison
  })
  
  for (const child of children) {
    if (searchQuery.value && filteredEntries.value) {
      const matches = filteredEntries.value.some(e => e.path.startsWith(child.path))
      if (!matches) continue
    }
    
    result.push({
      ...child,
      depth
    })
    
    if (child.is_dir && isExpanded(child.path)) {
      result.push(...renderTree(child, depth + 1))
    }
  }
  
  return result
}

const flattenTree = computed(() => {
  if (!archiveContent.value) return []
  return renderTree(archiveContent.value.tree)
})

const toggleSort = (field: 'name' | 'size' | 'type') => {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
}

const fetchTextContent = async () => {
  if (previewType.value !== 'text') return
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await fetch(fileUrl.value)
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
  if (accessMode.value === 'direct' && cfProxyUrl.value) {
    const prevMode = accessMode.value
    handleLoadError()
    if (accessMode.value !== prevMode) {
      return
    }
  }
  loading.value = false
  error.value = '图片加载失败'
}

const zoomIn = () => {
  if (imageScale.value < 5) {
    imageScale.value = Math.min(5, imageScale.value + 0.25)
  }
}

const zoomOut = () => {
  if (imageScale.value > 0.25) {
    imageScale.value = Math.max(0.25, imageScale.value - 0.25)
  }
}

const resetZoom = () => {
  imageScale.value = 1
  imageTranslateX.value = 0
  imageTranslateY.value = 0
}

const handleWheel = (e: WheelEvent) => {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  const newScale = Math.max(0.25, Math.min(5, imageScale.value + delta))
  imageScale.value = newScale
}

const handleMouseDown = (e: MouseEvent) => {
  if (e.button !== 0) return
  isDragging.value = true
  dragStartX.value = e.clientX
  dragStartY.value = e.clientY
  lastTranslateX.value = imageTranslateX.value
  lastTranslateY.value = imageTranslateY.value
  e.preventDefault()
}

const handleMouseMove = (e: MouseEvent) => {
  if (!isDragging.value) return
  
  const deltaX = e.clientX - dragStartX.value
  const deltaY = e.clientY - dragStartY.value
  
  imageTranslateX.value = lastTranslateX.value + deltaX
  imageTranslateY.value = lastTranslateY.value + deltaY
}

const handleMouseUp = () => {
  isDragging.value = false
}

const handleIframeLoad = () => {
  loading.value = false
}

const handleIframeError = () => {
  if (accessMode.value === 'direct' && cfProxyUrl.value) {
    const prevMode = accessMode.value
    handleLoadError()
    if (accessMode.value !== prevMode) {
      return
    }
  }
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
  archiveContent.value = null
  expandedDirs.value.clear()
  searchQuery.value = ''
  imageScale.value = 1
  imageTranslateX.value = 0
  imageTranslateY.value = 0
  isDragging.value = false
  
  if (previewType.value === 'text') {
    fetchTextContent()
  } else if (previewType.value === 'archive') {
    loading.value = false
    fetchArchiveContent()
  } else if (previewType.value === 'audio' || previewType.value === 'video' || previewType.value === 'unsupported') {
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
      <div class="relative w-full h-full max-w-7xl max-h-[95vh] m-4 flex flex-col bg-white dark:bg-dark-300 rounded-xl overflow-hidden shadow-2xl border border-gray-200 dark:border-white/10">
        <div class="flex items-center justify-between px-3 py-1 border-b border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-gray-800/50">
          <div class="flex items-center gap-2 min-w-0 flex-1">
            <span 
              class="w-6 h-6 flex-shrink-0 flex items-center justify-center rounded"
              :class="[getFileIconComponent.bg, getFileIconComponent.color]"
              v-html="getFileIconComponent.svg"
            ></span>
            <h3 class="text-xs font-medium text-gray-900 dark:text-white break-all leading-tight m-0">
              {{ file.original_filename }}
            </h3>
            <span class="text-[10px] text-gray-500 dark:text-gray-400 flex-shrink-0">
              {{ formatFileSize(file.file_size) }}
            </span>
          </div>
          <div class="flex items-center gap-1 flex-shrink-0 ml-2">
            <button
              @click="handleDownload"
              title="下载"
              class="p-1.5 text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-700/50 rounded transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </button>
            <button
              @click="emit('close')"
              class="p-1.5 text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700/50 rounded transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-auto relative">
          <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-900 z-10">
            <div class="flex flex-col items-center gap-4">
              <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
              <p class="text-gray-500 dark:text-gray-400">加载中...</p>
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

          <div v-if="previewType === 'image'" class="relative h-full flex flex-col">
            <div class="absolute top-2 left-1/2 -translate-x-1/2 z-10 flex items-center gap-2 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg px-3 py-2 shadow-lg border border-gray-200 dark:border-gray-700">
              <button
                @click="zoomOut"
                :disabled="imageScale <= 0.25"
                class="p-1.5 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="缩小"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
                </svg>
              </button>
              <div class="flex items-center gap-2 px-2">
                <span class="text-sm text-gray-700 dark:text-gray-300 min-w-[60px] text-center">{{ Math.round(imageScale * 100) }}%</span>
                <button
                  @click="resetZoom"
                  class="p-1 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                  title="重置"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
              </div>
              <button
                @click="zoomIn"
                :disabled="imageScale >= 5"
                class="p-1.5 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="放大"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
                </svg>
              </button>
            </div>
            
            <div 
              class="flex-1 overflow-hidden cursor-move relative"
              @wheel="handleWheel"
              @mousedown="handleMouseDown"
              @mousemove="handleMouseMove"
              @mouseup="handleMouseUp"
              @mouseleave="handleMouseUp"
            >
              <img
                :src="fileUrl"
                :alt="file.original_filename"
                class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 rounded-lg shadow-lg transition-transform duration-75"
                :style="{
                  transform: `translate(calc(-50% + ${imageTranslateX}px), calc(-50% + ${imageTranslateY}px)) scale(${imageScale})`,
                  cursor: isDragging ? 'grabbing' : 'grab'
                }"
                @load="handleImageLoad"
                @error="handleImageError"
                draggable="false"
              />
            </div>
          </div>

          <div v-else-if="previewType === 'pdf'" class="h-full">
            <iframe
              :src="fileUrl"
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
                <h4 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">{{ file.original_filename }}</h4>
                <div class="bg-gray-100 dark:bg-dark-400 rounded-lg p-6 mt-4">
                  <div class="flex items-center justify-between mb-3">
                    <span class="text-gray-500 dark:text-gray-400">类型:</span>
                    <span class="text-gray-900 dark:text-white font-medium">{{ officeFileType }} 文档</span>
                  </div>
                  <div class="flex items-center justify-between mb-3">
                    <span class="text-gray-500 dark:text-gray-400">大小:</span>
                    <span class="text-gray-900 dark:text-white font-medium">{{ formatFileSize(file.file_size) }}</span>
                  </div>
                </div>
                <p class="text-amber-600 dark:text-yellow-400 mt-4 text-sm">
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
            <pre class="h-full overflow-auto p-4 bg-gray-100 dark:bg-dark-400 rounded-lg text-gray-800 dark:text-gray-100 text-sm font-mono whitespace-pre-wrap break-words border border-gray-200 dark:border-white/10">{{ textContent }}</pre>
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
              <h4 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">{{ file.original_filename }}</h4>
              <audio
                :src="fileUrl"
                controls
                class="w-full max-w-md"
              >
                您的浏览器不支持音频播放
              </audio>
            </div>
          </div>

          <div v-else-if="previewType === 'video'" class="flex items-center justify-center h-full p-4">
            <video
              :src="fileUrl"
              controls
              class="max-w-full max-h-full rounded-lg shadow-lg"
            >
              您的浏览器不支持视频播放
            </video>
          </div>

          <div v-else-if="previewType === 'archive'" class="h-full flex flex-col">
            <div v-if="archiveLoading" class="flex-1 flex items-center justify-center">
              <div class="flex flex-col items-center gap-4">
                <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
                <p class="text-gray-500 dark:text-gray-400">正在解析压缩包...</p>
              </div>
            </div>
            
            <div v-else-if="error && !archiveContent" class="flex-1 flex items-center justify-center p-8">
              <div class="text-center">
                <p class="text-red-500 dark:text-red-400 mb-4">{{ error }}</p>
                <button
                  @click="fetchArchiveContent"
                  class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/80 transition-colors"
                >
                  重试
                </button>
              </div>
            </div>
            
            <div v-else-if="archiveContent" class="flex-1 flex flex-col overflow-hidden">
              <div class="px-3 py-2 border-b border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-gray-800/50 flex-shrink-0">
                <div class="flex flex-col gap-1.5 mb-2">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="px-1.5 py-0.5 text-[10px] font-medium bg-amber-500/20 text-amber-600 dark:text-amber-400 rounded">
                      {{ archiveContent.format }}
                    </span>
                    <span class="text-[10px] text-gray-500 dark:text-gray-400">
                      {{ archiveContent.total_files }} 个文件, {{ archiveContent.total_dirs }} 个文件夹
                    </span>
                  </div>
                  <div class="text-[10px] text-gray-500 dark:text-gray-400 break-all">
                    原始大小: {{ formatFileSize(archiveContent.total_size) }} | 
                    压缩后: {{ formatFileSize(archiveContent.compressed_size) }}
                    <span v-if="archiveContent.total_size > 0" class="text-green-600 dark:text-green-400 ml-1">
                      ({{ Math.round((1 - archiveContent.compressed_size / archiveContent.total_size) * 100) }}% 压缩率)
                    </span>
                  </div>
                </div>
                <div class="relative">
                  <input
                    v-model="searchQuery"
                    type="text"
                    placeholder="搜索文件（支持 * 和 ? 通配符）..."
                    class="w-full px-2 py-1 text-xs bg-white dark:bg-dark-400 border border-gray-300 dark:border-white/10 rounded text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary focus:outline-none"
                  />
                  <svg class="w-3 h-3 absolute right-2 top-1/2 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                
                <div class="flex items-center gap-1 mt-1.5 flex-wrap">
                  <span class="text-[10px] text-gray-500 dark:text-gray-400">排序:</span>
                  <button
                    @click="toggleSort('name')"
                    class="px-1.5 py-0.5 text-[10px] rounded transition-colors flex items-center gap-0.5"
                    :class="sortField === 'name' ? 'bg-primary/20 text-primary' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'"
                  >
                    名称
                    <svg v-if="sortField === 'name'" class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path v-if="sortDirection === 'asc'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                      <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  <button
                    @click="toggleSort('size')"
                    class="px-1.5 py-0.5 text-[10px] rounded transition-colors flex items-center gap-0.5"
                    :class="sortField === 'size' ? 'bg-primary/20 text-primary' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'"
                  >
                    大小
                    <svg v-if="sortField === 'size'" class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path v-if="sortDirection === 'asc'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                      <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  <button
                    @click="toggleSort('type')"
                    class="px-1.5 py-0.5 text-[10px] rounded transition-colors flex items-center gap-0.5"
                    :class="sortField === 'type' ? 'bg-primary/20 text-primary' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'"
                  >
                    类型
                    <svg v-if="sortField === 'type'" class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path v-if="sortDirection === 'asc'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                      <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                </div>
              </div>
              
              <div class="flex-1 overflow-auto p-2">
                <div class="space-y-0.5">
                  <div
                    v-for="item in flattenTree"
                    :key="item.path"
                    class="flex items-center gap-1.5 px-1.5 py-1 rounded hover:bg-gray-100 dark:hover:bg-white/5 cursor-default group"
                    :class="{ 'cursor-pointer': item.is_dir }"
                    :style="{ paddingLeft: `${item.depth * 12 + 6}px` }"
                    @click="item.is_dir && toggleDir(item.path)"
                  >
                    <span
                      v-if="item.is_dir"
                      class="w-3 h-3 flex items-center justify-center text-gray-500 dark:text-gray-400"
                    >
                      <svg 
                        class="w-2.5 h-2.5 transition-transform" 
                        :class="{ 'rotate-90': isExpanded(item.path) }"
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                      </svg>
                    </span>
                    <span v-else class="w-3"></span>
                    
                    <span 
                      class="flex-shrink-0"
                      :class="item.is_dir ? 'text-amber-600 dark:text-amber-400' : ''"
                      v-html="getFileIcon(item.name, item.is_dir)"
                    ></span>
                    
                    <span 
                      class="flex-1 text-xs break-all"
                      :class="item.is_dir ? 'text-gray-900 dark:text-gray-200 font-medium' : 'text-gray-700 dark:text-gray-300'"
                      v-html="highlightText(item.name, searchQuery)"
                    ></span>
                    
                    <span v-if="!item.is_dir" class="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                      {{ formatFileSize(item.size) }}
                    </span>
                  </div>
                </div>
                
                <div v-if="flattenTree.length === 0 && searchQuery" class="text-center py-8 text-gray-500 dark:text-gray-400">
                  未找到匹配的文件
                </div>
              </div>
            </div>
            
            <div v-else class="flex-1 flex items-center justify-center p-8">
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
                <h4 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">{{ file.original_filename }}</h4>
                <div class="bg-gray-100 dark:bg-dark-400 rounded-lg p-6 mt-4">
                  <div class="flex items-center justify-between mb-3">
                    <span class="text-gray-500 dark:text-gray-400">类型:</span>
                    <span class="text-gray-900 dark:text-white font-medium">{{ getArchiveInfo().type }}</span>
                  </div>
                  <div class="flex items-center justify-between mb-3">
                    <span class="text-gray-500 dark:text-gray-400">大小:</span>
                    <span class="text-gray-900 dark:text-white font-medium">{{ formatFileSize(file.file_size) }}</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-500 dark:text-gray-400">描述:</span>
                    <span class="text-gray-900 dark:text-white font-medium">{{ getArchiveInfo().description }}</span>
                  </div>
                </div>
                <button
                  @click="fetchArchiveContent"
                  class="mt-6 px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/80 transition-colors"
                >
                  查看内容
                </button>
              </div>
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
              <h4 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">{{ file.original_filename }}</h4>
              <p class="text-gray-500 dark:text-gray-400 mb-6">
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
  background: transparent;
  border-radius: 4px;
}

.dark pre::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

pre::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

.dark pre::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
}

pre::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.15);
}

.dark pre::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
