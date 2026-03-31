<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fileApi, type StorageInfo, type StorageFileInfo } from '@/api/files'
import { useAdminCheck } from '@/composables/useAdminCheck'

const { requireAdmin } = useAdminCheck()

const loading = ref(true)
const storageInfo = ref<StorageInfo | null>(null)
const expandedDirs = ref<Set<string>>(new Set())
const showOrphanFiles = ref(false)

const fetchStorageInfo = async () => {
  if (!await requireAdmin('查看存储信息')) return
  
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

onMounted(fetchStorageInfo)
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">存储管理</h1>
      <button
        @click="fetchStorageInfo"
        class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 11-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/>
          <path d="M21 3v5h-5"/>
        </svg>
        刷新
      </button>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>

    <div v-else-if="storageInfo" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="glass-card p-4 rounded-xl">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2">
                <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
              </svg>
            </div>
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400">上传目录</p>
              <p class="text-sm font-medium text-gray-900 dark:text-white truncate" :title="storageInfo.upload_dir">
                {{ storageInfo.upload_dir }}
              </p>
            </div>
          </div>
        </div>

        <div class="glass-card p-4 rounded-xl">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12,6 12,12 16,14"/>
              </svg>
            </div>
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400">总存储大小</p>
              <p class="text-lg font-bold text-gray-900 dark:text-white">
                {{ storageInfo.total_size_formatted }}
              </p>
            </div>
          </div>
        </div>

        <div class="glass-card p-4 rounded-xl">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#a855f7" stroke-width="2">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
              </svg>
            </div>
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400">磁盘文件数</p>
              <p class="text-lg font-bold text-gray-900 dark:text-white">
                {{ storageInfo.total_files }}
              </p>
            </div>
          </div>
        </div>

        <div class="glass-card p-4 rounded-xl">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f97316" stroke-width="2">
                <ellipse cx="12" cy="5" rx="9" ry="3"/>
                <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
              </svg>
            </div>
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400">数据库记录数</p>
              <p class="text-lg font-bold text-gray-900 dark:text-white">
                {{ storageInfo.db_files_count }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="storageInfo.orphan_count > 0" class="glass-card p-4 rounded-xl border-l-4 border-yellow-500">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#eab308" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white">
                发现 {{ storageInfo.orphan_count }} 个孤立文件
              </p>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                这些文件在磁盘上存在，但数据库中没有记录
              </p>
            </div>
          </div>
          <button
            @click="showOrphanFiles = !showOrphanFiles"
            class="px-3 py-1.5 text-xs bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 rounded-lg hover:bg-yellow-500/30 transition-colors"
          >
            {{ showOrphanFiles ? '隐藏' : '查看详情' }}
          </button>
        </div>
        
        <div v-if="showOrphanFiles" class="mt-4 space-y-2 max-h-60 overflow-y-auto">
          <div
            v-for="file in storageInfo.orphan_files"
            :key="file.path"
            class="flex items-center justify-between p-2 bg-yellow-500/10 rounded-lg"
          >
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ file.name }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ file.path }}</p>
            </div>
            <div class="text-right flex-shrink-0 ml-2">
              <p class="text-sm text-gray-900 dark:text-white">{{ file.size_formatted }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ formatDate(file.modified) }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="glass-card rounded-xl overflow-hidden">
        <div class="p-4 border-b border-gray-200 dark:border-white/10">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">目录结构</h2>
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
                  <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
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
                  <polyline points="6,9 12,15 18,9"/>
                </svg>
              </div>
            </div>
            
            <div v-if="expandedDirs.has(dirName)" class="mt-3 ml-8 space-y-2">
              <div
                v-for="file in dir.files"
                :key="file.path"
                class="flex items-center justify-between p-2 bg-gray-50 dark:bg-white/5 rounded-lg"
              >
                <div class="flex items-center gap-2 min-w-0 flex-1">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-gray-400 flex-shrink-0">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                    <polyline points="14,2 14,8 20,8"/>
                  </svg>
                  <span class="text-sm text-gray-900 dark:text-white truncate">{{ file.name }}</span>
                </div>
                <div class="text-right flex-shrink-0 ml-2">
                  <span class="text-xs text-gray-500 dark:text-gray-400">{{ file.size_formatted }}</span>
                </div>
              </div>
              <p v-if="dir.file_count > 20" class="text-xs text-gray-500 dark:text-gray-400 text-center py-2">
                仅显示前 20 个文件，共 {{ dir.file_count }} 个
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-12 text-gray-500 dark:text-gray-400">
      无法获取存储信息
    </div>
  </div>
</template>
