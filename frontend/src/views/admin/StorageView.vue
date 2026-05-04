<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fileApi, type StorageInfo, type StorageFileInfo } from '@/api/files'
import { useDialogStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'

const dialog = useDialogStore()
const { requirePermission } = useAdminCheck()

const loading = ref(true)
const storageInfo = ref<StorageInfo | null>(null)
const expandedDirs = ref<Set<string>>(new Set())
const showOrphanFiles = ref(false)
const deletingOrphans = ref(false)
const copySuccess = ref(false)

const getAvatarUrl = (file: StorageFileInfo): string => {
  if (!file.is_avatar) return ''
  const filename = file.name
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
  const staticBase = apiUrl.replace('/api/v1', '').replace(/\/$/, '')
  return `${staticBase}/uploads/avatars/${filename}`
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    copySuccess.value = true
    setTimeout(() => {
      copySuccess.value = false
    }, 2000)
    dialog.showSuccess('已复制到剪贴板')
  } catch (error) {
    console.error('Failed to copy:', error)
    dialog.showError('复制失败')
  }
}

const fetchStorageInfo = async () => {
  loading.value = true
  try {
    storageInfo.value = await fileApi.getStorageInfo()
  } catch (error) {
    console.error('Failed to fetch storage info:', error)
  } finally {
    loading.value = false
  }
}

const toggleDir = (dirName: string) => {
  if (expandedDirs.value.has(dirName)) {
    expandedDirs.value.delete(dirName)
  } else {
    expandedDirs.value.add(dirName)
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getFileIconInfo = (file: StorageFileInfo): { bg: string; svg: string } => {
  if (file.is_avatar) {
    return {
      bg: '',
      svg: ''
    }
  }
  
  const ext = file.display_name.split('.').pop()?.toLowerCase() || ''
  
  const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico']
  const docExts = ['doc', 'docx', 'rtf']
  const xlsExts = ['xls', 'xlsx', 'csv']
  const pptExts = ['ppt', 'pptx']
  const archiveExts = ['zip', 'rar', '7z', 'tar', 'gz']
  const audioExts = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a']
  const videoExts = ['mp4', 'webm', 'avi', 'mov', 'mkv']
  
  if (imageExts.includes(ext)) {
    return {
      bg: 'bg-gradient-to-br from-green-400 to-green-600',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="24" height="24"><rect x="3" y="3" width="26" height="26" rx="3" fill="rgba(255,255,255,0.2)"/><circle cx="11" cy="11" r="3" fill="white"/><path d="M29 20l-7-7L7 29" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
    }
  }
  if (ext === 'pdf') {
    return {
      bg: 'bg-gradient-to-br from-red-500 to-red-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="24" height="24"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/><foreignObject x="4" y="16" width="24" height="12"><div xmlns="http://www.w3.org/1999/xhtml" style="color: white; font-size: 9px; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; line-height: 12px;">PDF</div></foreignObject></svg>`
    }
  }
  if (docExts.includes(ext)) {
    return {
      bg: 'bg-gradient-to-br from-blue-500 to-blue-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="24" height="24"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/><foreignObject x="4" y="16" width="24" height="16"><div xmlns="http://www.w3.org/1999/xhtml" style="color: white; font-size: 14px; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; line-height: 16px;">W</div></foreignObject></svg>`
    }
  }
  if (xlsExts.includes(ext)) {
    return {
      bg: 'bg-gradient-to-br from-emerald-500 to-emerald-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="24" height="24"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/><foreignObject x="4" y="16" width="24" height="16"><div xmlns="http://www.w3.org/1999/xhtml" style="color: white; font-size: 14px; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; line-height: 16px;">X</div></foreignObject></svg>`
    }
  }
  if (pptExts.includes(ext)) {
    return {
      bg: 'bg-gradient-to-br from-orange-500 to-orange-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="24" height="24"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/><foreignObject x="4" y="16" width="24" height="16"><div xmlns="http://www.w3.org/1999/xhtml" style="color: white; font-size: 14px; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; line-height: 16px;">P</div></foreignObject></svg>`
    }
  }
  if (archiveExts.includes(ext)) {
    return {
      bg: 'bg-gradient-to-br from-amber-500 to-amber-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="24" height="24"><path d="M28 10v18H4V10" fill="rgba(255,255,255,0.3)"/><path d="M30 4H2v6h28V4z" fill="rgba(255,255,255,0.5)"/><rect x="13" y="14" width="6" height="5" fill="white" rx="1"/><rect x="13" y="21" width="6" height="4" fill="rgba(255,255,255,0.5)" rx="1"/></svg>`
    }
  }
  if (audioExts.includes(ext)) {
    return {
      bg: 'bg-gradient-to-br from-purple-500 to-purple-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="24" height="24"><path d="M12 24V6l16-3v18" fill="rgba(255,255,255,0.5)"/><circle cx="8" cy="24" r="4" fill="white"/><circle cx="24" cy="21" r="4" fill="white"/></svg>`
    }
  }
  if (videoExts.includes(ext)) {
    return {
      bg: 'bg-gradient-to-br from-pink-500 to-pink-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="24" height="24"><rect x="2" y="5" width="28" height="22" rx="3" fill="rgba(255,255,255,0.3)"/><polygon points="13,10 22,16 13,22" fill="white"/></svg>`
    }
  }
  return {
    bg: 'bg-gradient-to-br from-gray-400 to-gray-600',
    svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="24" height="24"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/></svg>`
  }
}

const handleDeleteOrphanFiles = async () => {
  if (!storageInfo.value || storageInfo.value.orphan_count === 0) return
  
  if (!await requirePermission('storage.delete', '删除孤立文件')) return
  
  const confirmed = await dialog.showConfirm({
    message: `确定要删除 ${storageInfo.value.orphan_count} 个孤立文件吗？`,
    title: '此操作不可恢复'
  })
  if (!confirmed) return
  
  deletingOrphans.value = true
  try {
    const result = await fileApi.deleteOrphanFiles()
    if (result.errors.length > 0) {
      dialog.showWarning(
        `成功删除 ${result.deleted_count} 个文件，释放空间 ${result.deleted_size_formatted}`,
        `${result.errors.length} 个文件删除失败`
      )
    } else {
      dialog.showSuccess(`成功删除 ${result.deleted_count} 个文件，释放空间 ${result.deleted_size_formatted}`)
    }
    await fetchStorageInfo()
  } catch (error: any) {
    console.error('Failed to delete orphan files:', error)
    const errorMsg = error.response?.data?.detail || '删除失败，请稍后重试'
    dialog.showError(errorMsg)
  } finally {
    deletingOrphans.value = false
  }
}

onMounted(fetchStorageInfo)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-5">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
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
              d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          文件存储
        </h1>
      </div>
      <button
        class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2"
        @click="fetchStorageInfo"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M21 12a9 9 0 11-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
          <path d="M21 3v5h-5" />
        </svg>
        刷新
      </button>
    </div>

    <div class="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
      <div class="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle
            cx="12"
            cy="12"
            r="10"
          />
          <line
            x1="12"
            y1="16"
            x2="12"
            y2="12"
          />
          <line
            x1="12"
            y1="8"
            x2="12.01"
            y2="8"
          />
        </svg>
        <span>头像目录、网站Logo目录和图片目录 显示但受保护，不会被清理孤立文件时删除</span>
      </div>
    </div>

    <div
      v-if="loading"
      class="flex items-center justify-center py-12"
    >
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>

    <div
      v-else-if="storageInfo"
      class="space-y-6"
    >
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="glass-card p-4 rounded-xl">
          <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#3b82f6"
                  stroke-width="2"
                >
                  <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  上传目录
                </p>
                <div class="flex items-center gap-2">
                  <p
                    class="text-sm font-medium text-gray-900 dark:text-white truncate flex-1"
                    :title="storageInfo.upload_dir"
                  >
                    {{ storageInfo.upload_dir }}
                  </p>
                  <button
                    type="button"
                    class="flex-shrink-0 p-1 rounded hover:bg-gray-100 dark:hover:bg-white/10 transition-colors group"
                    title="复制路径"
                    @click="copyToClipboard(storageInfo.upload_dir)"
                  >
                    <svg
                      v-if="!copySuccess"
                      class="w-4 h-4 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <rect
                        x="9"
                        y="9"
                        width="13"
                        height="13"
                        rx="2"
                        ry="2"
                      />
                      <path
                        d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"
                      />
                    </svg>
                    <svg
                      v-else
                      class="w-4 h-4 text-green-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <polyline points="20,6 9,17 4,12" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="glass-card p-4 rounded-xl">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#22c55e"
                  stroke-width="2"
                >
                  <circle
                    cx="12"
                    cy="12"
                    r="10"
                  />
                  <polyline points="12,6 12,12 16,14" />
                </svg>
              </div>
              <div>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  总存储大小
                </p>
                <p class="text-lg font-bold text-gray-900 dark:text-white">
                  {{ storageInfo.total_size_formatted }}
                </p>
              </div>
            </div>
          </div>

          <div class="glass-card p-4 rounded-xl">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#a855f7"
                  stroke-width="2"
                >
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                  <polyline points="14,2 14,8 20,8" />
                </svg>
              </div>
              <div>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  磁盘文件数
                </p>
                <p class="text-lg font-bold text-gray-900 dark:text-white">
                  {{ storageInfo.total_files }}
                </p>
              </div>
            </div>
          </div>

          <div class="glass-card p-4 rounded-xl">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#f97316"
                  stroke-width="2"
                >
                  <ellipse
                    cx="12"
                    cy="5"
                    rx="9"
                    ry="3"
                  />
                  <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                  <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
                </svg>
              </div>
              <div>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  数据库记录数
                </p>
                <p class="text-lg font-bold text-gray-900 dark:text-white">
                  {{ storageInfo.db_files_count }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="storageInfo.orphan_count > 0"
          class="glass-card p-4 rounded-xl border-l-4 border-yellow-500"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#eab308"
                  stroke-width="2"
                >
                  <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                  <line
                    x1="12"
                    y1="9"
                    x2="12"
                    y2="13"
                  />
                  <line
                    x1="12"
                    y1="17"
                    x2="12.01"
                    y2="17"
                  />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-900 dark:text-white">
                  发现 {{ storageInfo.orphan_count }} 个孤立文件
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  这些文件在磁盘上存在，但数据库中没有记录，不会被网站使用
                </p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button
                class="px-3 py-1.5 text-xs bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 rounded-lg hover:bg-yellow-500/30 transition-colors"
                @click="showOrphanFiles = !showOrphanFiles"
              >
                {{ showOrphanFiles ? '隐藏' : '查看详情' }}
              </button>
              <button
                :disabled="deletingOrphans"
                class="px-3 py-1.5 text-xs bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                @click="handleDeleteOrphanFiles"
              >
                <svg
                  v-if="deletingOrphans"
                  class="animate-spin w-3 h-3"
                  xmlns="http://www.w3.org/2000/svg"
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
                {{ deletingOrphans ? '删除中...' : '全部删除' }}
              </button>
            </div>
          </div>
        
          <div
            v-if="showOrphanFiles"
            class="mt-4 space-y-2 max-h-60 overflow-y-auto"
          >
            <div
              v-for="file in storageInfo.orphan_files"
              :key="file.path"
              class="flex items-center justify-between p-2 bg-yellow-500/10 rounded-lg"
            >
              <div class="flex items-center gap-2 min-w-0 flex-1">
                <img 
                  v-if="file.is_avatar"
                  :src="getAvatarUrl(file)"
                  :alt="file.display_name"
                  class="w-7 h-7 rounded-full object-cover flex-shrink-0"
                >
                <span 
                  v-else
                  class="w-7 h-7 flex items-center justify-center rounded flex-shrink-0"
                  :class="getFileIconInfo(file).bg"
                  v-html="getFileIconInfo(file).svg"
                />
                <div class="min-w-0">
                  <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {{ file.display_name }}
                  </p>
                  <p class="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {{ file.path }}
                  </p>
                </div>
              </div>
              <div class="text-right flex-shrink-0 ml-2">
                <p class="text-sm text-gray-900 dark:text-white">
                  {{ file.size_formatted }}
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ formatDate(file.modified) }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div class="glass-card rounded-xl overflow-hidden">
          <div class="p-4 border-b border-gray-200 dark:border-white/10">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              目录结构
            </h2>
          </div>
          <div class="divide-y divide-gray-200 dark:divide-white/10">
            <div
              v-for="(dir, dirName) in storageInfo.directories"
              :key="dirName"
              class="p-4"
            >
              <div
                class="flex items-center justify-between cursor-pointer hover:bg-gray-50 dark:hover:bg-white/5 -mx-4 px-4 py-2 rounded-lg transition-colors"
                @click="toggleDir(dirName)"
              >
                <div class="flex items-center gap-3">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    class="text-yellow-500 transition-transform"
                    :class="{ 'rotate-90': expandedDirs.has(dirName) }"
                  >
                    <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
                  </svg>
                  <span class="font-medium text-gray-900 dark:text-white">{{ dirName }}</span>
                  <span class="text-xs text-gray-500 dark:text-gray-400">
                    ({{ dir.file_count }} 个文件)
                  </span>
                </div>
                <div class="flex items-center gap-4">
                  <span class="text-sm font-medium text-gray-900 dark:text-white">
                    {{ dir.size_formatted }}
                  </span>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    class="text-gray-400 transition-transform"
                    :class="{ 'rotate-180': expandedDirs.has(dirName) }"
                  >
                    <polyline points="6,9 12,15 18,9" />
                  </svg>
                </div>
              </div>
            
              <div
                v-if="expandedDirs.has(dirName)"
                class="mt-3 ml-8 space-y-2"
              >
                <div
                  v-for="file in dir.files"
                  :key="file.path"
                  class="flex items-center justify-between p-2 bg-gray-50 dark:bg-white/5 rounded-lg"
                >
                  <div class="flex items-center gap-2 min-w-0 flex-1">
                    <img 
                      v-if="file.is_avatar"
                      :src="getAvatarUrl(file)"
                      :alt="file.display_name"
                      class="w-6 h-6 rounded-full object-cover flex-shrink-0"
                    >
                    <span 
                      v-else
                      class="w-6 h-6 flex items-center justify-center rounded flex-shrink-0"
                      :class="getFileIconInfo(file).bg"
                      v-html="getFileIconInfo(file).svg"
                    />
                    <span class="text-sm text-gray-900 dark:text-white truncate">{{ file.display_name }}</span>
                  </div>
                  <div class="text-right flex-shrink-0 ml-2">
                    <span class="text-xs text-gray-500 dark:text-gray-400">{{ file.size_formatted }}</span>
                  </div>
                </div>
                <p
                  v-if="dir.file_count > 20"
                  class="text-xs text-gray-500 dark:text-gray-400 text-center py-2"
                >
                  仅显示前 20 个文件，共 {{ dir.file_count }} 个
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-else
        class="text-center py-12 text-gray-500 dark:text-gray-400"
      >
        无法获取存储信息
      </div>
  </div>
</template>
