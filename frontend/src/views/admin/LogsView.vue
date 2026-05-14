<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { logsApi } from '@/api'
import { useDialogStore, useUserProfileStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { formatDateTime } from '@/utils/date'
import DateRangePicker from '@/components/common/DateRangePicker.vue'

const dialog = useDialogStore()
const userProfileStore = useUserProfileStore()
const { hasPermission } = useAdminCheck()

const canClearLogs = computed(() => hasPermission('log.clear'))

interface LogStats {
  total_operations: number
  total_logins: number
  total_access: number
  today_operations: number
  today_logins: number
  failed_logins: number
}

const activeTab = ref('operations')
const stats = ref<LogStats>({
  total_operations: 0,
  total_logins: 0,
  total_access: 0,
  today_operations: 0,
  today_logins: 0,
  failed_logins: 0
})

const operationLogs = ref<any[]>([])
const loginLogs = ref<any[]>([])
const accessLogs = ref<any[]>([])

const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const filters = ref({
  module: '',
  action: '',
  description: '',
  status: '',
  username: '',
  login_type: '',
  ip_address: '',
  request_method: '',
  path: '',
  start_date: '',
  end_date: ''
})

const showFilters = ref(false)

const hasActiveFilters = computed(() => {
  const f = filters.value
  return !!(f.module || f.action || f.description || f.status || f.username || 
            f.login_type || f.ip_address || f.request_method || f.path || 
            f.start_date || f.end_date)
})

const tabs = [
  { key: 'operations', label: '操作日志', icon: 'operation' },
  { key: 'logins', label: '登录日志', icon: 'login' },
  { key: 'access', label: '访问日志', icon: 'access' }
]

const fetchStats = async () => {
  try {
    const response = await logsApi.getStats()
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

const fetchLogs = async () => {
  loading.value = true
  try {
    let response: any
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize.value
    }
    
    Object.keys(filters.value).forEach(key => {
      const value = filters.value[key as keyof typeof filters.value]
      if (value) {
        params[key] = value
      }
    })
    
    switch (activeTab.value) {
      case 'operations':
        response = await logsApi.getOperations(params)
        operationLogs.value = response.data.items
        break
      case 'logins':
        response = await logsApi.getLogins(params)
        loginLogs.value = response.data.items
        break
      case 'access':
        response = await logsApi.getAccess(params)
        accessLogs.value = response.data.items
        break
    }
    if (response) {
      total.value = response.data.total
    }
  } catch (error: any) {
    if (error?.isCancel) {
      return
    }
    console.error('Failed to fetch logs:', error)
  } finally {
    loading.value = false
  }
}

const handleTabChange = (tab: string) => {
  activeTab.value = tab
  page.value = 1
  resetFilters()
  fetchLogs()
}

const resetFilters = () => {
  filters.value = {
    module: '',
    action: '',
    description: '',
    status: '',
    username: '',
    login_type: '',
    ip_address: '',
    request_method: '',
    path: '',
    start_date: '',
    end_date: ''
  }
}

const handleSearch = () => {
  page.value = 1
  fetchLogs()
}

const handleClearFilters = () => {
  resetFilters()
  page.value = 1
  fetchLogs()
}

const handleClearLogs = async () => {
  if (!canClearLogs.value) {
    dialog.showWarning('无清理日志权限，请联系管理员', '权限不足')
    return
  }
  
  const confirmed = await dialog.showConfirm({
    message: '确定要清理30天前的日志吗？',
    title: '确认清理'
  })
  if (!confirmed) return
  
  try {
    switch (activeTab.value) {
      case 'operations':
        await logsApi.clearOperations()
        break
      case 'logins':
        await logsApi.clearLogins()
        break
      case 'access':
        await logsApi.clearAccess()
        break
    }
    await dialog.showSuccess('日志清理成功', '成功')
    fetchLogs()
    fetchStats()
  } catch (error) {
    console.error('Failed to clear logs:', error)
    await dialog.showError('日志清理失败', '错误')
  }
}

interface ExportState {
  isExporting: boolean
  progress: number
  total: number
  status: string
  abortController: AbortController | null
}

const exportStates = ref<Record<string, ExportState>>({
  operations: {
    isExporting: false,
    progress: 0,
    total: 0,
    status: '',
    abortController: null
  },
  logins: {
    isExporting: false,
    progress: 0,
    total: 0,
    status: '',
    abortController: null
  },
  access: {
    isExporting: false,
    progress: 0,
    total: 0,
    status: '',
    abortController: null
  }
})

const handleExport = async (logType: string) => {
  const state = exportStates.value[logType]
  state.isExporting = true
  state.progress = 0
  state.total = 0
  state.status = '准备导出...'
  state.abortController = new AbortController()
  
  try {
    const params: Record<string, any> = {}
    Object.keys(filters.value).forEach(key => {
      const value = filters.value[key as keyof typeof filters.value]
      if (value) {
        params[key] = value
      }
    })
    
    state.status = '正在查询数据总数...'
    state.progress = 5
    
    let countResponse: any
    switch (logType) {
      case 'operations':
        countResponse = await logsApi.getExportOperationsCount(params)
        break
      case 'logins':
        countResponse = await logsApi.getExportLoginsCount(params)
        break
      case 'access':
        countResponse = await logsApi.getExportAccessCount(params)
        break
      default:
        throw new Error('Unknown log type')
    }
    
    const totalCount = countResponse.data.total
    state.total = totalCount
    
    if (totalCount === 0) {
      state.status = '没有符合条件的记录'
      await dialog.showWarning('没有找到符合条件的日志记录', '导出提示')
      return
    }
    
    state.status = `准备导出 ${totalCount.toLocaleString()} 条记录...`
    state.progress = 10
    
    await new Promise(resolve => setTimeout(resolve, 300))
    
    if (state.abortController?.signal.aborted) {
      return
    }
    
    let response: any
    let filename: string
    
    state.status = `正在生成Excel（0/${totalCount.toLocaleString()}）...`
    state.progress = 15
    
    const config = {
      signal: state.abortController?.signal,
      responseType: 'blob' as const,
      onDownloadProgress: (progressEvent: any) => {
        if (progressEvent.lengthComputable && totalCount > 0) {
          const percentCompleted = Math.round((progressEvent.loaded / progressEvent.total) * 100)
          const progressRange = 85
          const baseProgress = 15
          const currentProgress = baseProgress + (percentCompleted * progressRange / 100)
          state.progress = Math.min(currentProgress, 99)
          state.status = `正在下载文件（${state.progress.toFixed(0)}%）...`
        }
      }
    }
    
    switch (logType) {
      case 'operations':
        response = await logsApi.exportOperations(params, config)
        filename = '操作日志'
        break
      case 'logins':
        response = await logsApi.exportLogins(params, config)
        filename = '登录日志'
        break
      case 'access':
        response = await logsApi.exportAccess(params, config)
        filename = '访问日志'
        break
      default:
        throw new Error('Unknown log type')
    }
    
    state.status = '正在处理文件...'
    state.progress = 95
    
    const contentDisposition = response.headers['content-disposition']
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/)
      if (filenameMatch) {
        filename = decodeURIComponent(filenameMatch[1])
      }
    }
    
    if (!filename.endsWith('.xlsx')) {
      const timestamp = new Date().toISOString().replace(/[\-:T]/g, '').slice(0, 15)
      filename = `${filename}_${timestamp}.xlsx`
    }
    
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    state.progress = 100
    state.status = '导出完成'
    
    await dialog.showSuccess(`成功导出 ${filename}（共 ${totalCount.toLocaleString()} 条记录）`, '导出成功')
  } catch (error: any) {
    if (error.name === 'AbortError' || error.code === 'ERR_CANCELED') {
      state.status = '导出已取消'
      await dialog.showWarning('导出操作已取消', '已取消')
      return
    }
    console.error('Export failed:', error)
    const errorMsg = error?.response?.data?.message || error?.message || '导出失败，请重试'
    await dialog.showError(errorMsg, '导出失败')
  } finally {
    state.isExporting = false
    setTimeout(() => {
      state.progress = 0
      state.total = 0
      state.status = ''
      state.abortController = null
    }, 2000)
  }
}

const cancelExport = (logType: string) => {
  const state = exportStates.value[logType]
  if (state.abortController) {
    state.abortController.abort()
    state.isExporting = false
    state.status = '正在取消...'
  }
}

const formatDate = (date: string) => formatDateTime(date)

const getStatusClass = (status: string) => {
  return status === 'success' 
    ? 'bg-green-500/20 text-green-400' 
    : 'bg-red-500/20 text-red-400'
}

const formatLoginType = (loginType: string) => {
  if (loginType === 'login') return '登录'
  if (loginType === 'logout') return '登出'
  if (loginType.startsWith('oauth_')) {
    const provider = loginType.replace('oauth_', '')
    const providerNames: Record<string, string> = {
      google: 'Google',
      github: 'GitHub',
      twitter: 'Twitter',
      x: 'X',
      wechat: '微信',
      qq: 'QQ'
    }
    return `${providerNames[provider] || provider} 登录`
  }
  return loginType
}

const getLoginLogAvatarStyle = (log: any) => {
  if (log.avatar_type === 'custom' && log.avatar_url) {
    return {
      backgroundImage: `url(${log.avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (log.oauth_avatar_url) {
    return {
      backgroundImage: `url(${log.oauth_avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (log.avatar_gradient && log.avatar_gradient.length >= 1) {
    return {
      backgroundColor: log.avatar_gradient[0]
    }
  }
  
  return {
    backgroundColor: '#667eea'
  }
}

const getOperationLogAvatarStyle = (log: any) => {
  if (log.avatar_type === 'custom' && log.avatar_url) {
    return {
      backgroundImage: `url(${log.avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (log.oauth_avatar_url) {
    return {
      backgroundImage: `url(${log.oauth_avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (log.avatar_gradient && log.avatar_gradient.length >= 1) {
    return {
      backgroundColor: log.avatar_gradient[0]
    }
  }
  
  return {
    backgroundColor: '#667eea'
  }
}

const getAccessLogAvatarStyle = (log: any) => {
  if (log.username && log.avatar_type === 'custom' && log.avatar_url) {
    return {
      backgroundImage: `url(${log.avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (log.username && log.oauth_avatar_url) {
    return {
      backgroundImage: `url(${log.oauth_avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (log.username && log.avatar_gradient && log.avatar_gradient.length >= 1) {
    return {
      backgroundColor: log.avatar_gradient[0]
    }
  }
  
  if (!log.username) {
    return {
      backgroundColor: '#9ca3af'
    }
  }
  
  return {
    backgroundColor: '#667eea'
  }
}

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'ArrowLeft' && page.value > 1) {
    event.preventDefault()
    page.value--
    fetchLogs()
  } else if (event.key === 'ArrowRight' && page.value < totalPages.value) {
    event.preventDefault()
    page.value++
    fetchLogs()
  } else if (event.key === 'Delete') {
    event.preventDefault()
    handleClearFilters()
  }
}

onMounted(() => {
  fetchStats()
  fetchLogs()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

watch(() => userProfileStore.avatarUpdatedAt, () => {
  if (!loading.value) {
    fetchLogs()
  }
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-5 gap-2">
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
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          系统日志
        </h1>
      </div>
      <button
        class="px-2 sm:px-3 py-1.5 text-xs sm:text-sm bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors whitespace-nowrap"
        @click="handleClearLogs"
      >
        清理30天前日志
      </button>
    </div>

    <div class="grid grid-cols-3 gap-3 mb-6">
        <div class="glass-card p-3">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
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
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
            </div>
            <div>
              <p class="text-gray-500 dark:text-gray-400 text-xs">
                操作日志
              </p>
              <p class="text-lg font-bold text-gray-900 dark:text-white">
                {{ stats.total_operations }}
              </p>
            </div>
          </div>
        </div>
      
        <div class="glass-card p-3">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-secondary/20 flex items-center justify-center">
              <svg
                class="w-4 h-4 text-secondary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
                />
              </svg>
            </div>
            <div>
              <p class="text-gray-500 dark:text-gray-400 text-xs">
                登录日志
              </p>
              <p class="text-lg font-bold text-gray-900 dark:text-white">
                {{ stats.total_logins }}
              </p>
            </div>
          </div>
        </div>
      
        <div class="glass-card p-3">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
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
            </div>
            <div>
              <p class="text-gray-500 dark:text-gray-400 text-xs">
                访问日志
              </p>
              <p class="text-lg font-bold text-gray-900 dark:text-white">
                {{ stats.total_access }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="glass-card">
        <div class="flex border-b border-gray-200 dark:border-white/10">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="[
              'px-4 py-2 text-sm font-medium transition-colors',
              activeTab === tab.key
                ? 'text-primary border-b-2 border-primary'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            ]"
            @click="handleTabChange(tab.key)"
          >
            {{ tab.label }}
          </button>
        </div>

        <div class="p-3 border-b border-gray-200 dark:border-white/10">
          <div class="flex items-center justify-between md:hidden mb-2">
            <button
              type="button"
              class="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-200 transition-colors"
              @click="showFilters = !showFilters"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              筛选
              <svg class="w-3 h-3 transition-transform" :class="{ 'rotate-180': showFilters }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <div v-if="hasActiveFilters" class="flex items-center gap-1 flex-wrap">
              <span v-if="filters.username" class="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full">{{ filters.username }}</span>
              <span v-if="filters.module" class="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full">{{ filters.module }}</span>
              <span v-if="filters.action" class="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full">{{ filters.action }}</span>
              <span v-if="filters.ip_address" class="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full">{{ filters.ip_address }}</span>
              <span v-if="filters.path" class="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full">{{ filters.path }}</span>
            </div>
          </div>
          <form 
            v-if="activeTab === 'operations'" 
            class="flex flex-wrap items-center gap-2"
            :class="{ 'hidden md:flex': !showFilters, 'md:flex': true }"
            @submit.prevent="handleSearch"
          >
              <input id="input-ops-filters-username"
                v-model="filters.username"
                type="text"
                name="ops-username"
                placeholder="用户名"
                class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-28"
                @keyup.enter="handleSearch"
              >
              <input id="input-ops-filters-module"
                v-model="filters.module"
                type="text"
                name="ops-module"
                placeholder="模块"
                class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-24"
                @keyup.enter="handleSearch"
              >
              <input id="input-ops-filters-action"
                v-model="filters.action"
                type="text"
                name="ops-action"
                placeholder="操作"
                class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-24"
                @keyup.enter="handleSearch"
              >
              <input id="input-ops-filters-description"
                v-model="filters.description"
                type="text"
                name="ops-description"
                placeholder="描述"
                class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-40"
                @keyup.enter="handleSearch"
              >
              <select id="select-ops-filters-status"
                v-model="filters.status"
                name="ops-status"
                class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
                @change="handleSearch"
              >
                <option value="">
                  全部状态
                </option>
                <option value="success">
                  成功
                </option>
                <option value="failed">
                  失败
                </option>
              </select>
              <DateRangePicker
                v-model:start-date="filters.start_date"
                v-model:end-date="filters.end_date"
              />
              <button
                type="button"
                class="px-2.5 py-1 text-xs bg-red-500/10 text-red-500 dark:text-red-400 border border-red-500/20 dark:border-red-400/20 rounded-lg hover:bg-red-500/20 dark:hover:bg-red-400/20 transition-colors flex items-center gap-1"
                @click="handleClearFilters"
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
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
                清除
              </button>
              <button
                class="btn-primary text-xs px-3 py-1 flex items-center gap-1"
                @click="handleSearch"
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
                    d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                  />
                </svg>
                筛选
              </button>
              <button
                type="button"
                :disabled="exportStates.operations.isExporting"
                :class="[
                  'px-2.5 py-1 text-xs border rounded-lg transition-colors flex items-center gap-1',
                  exportStates.operations.isExporting 
                    ? 'bg-gray-100 dark:bg-dark-100 text-gray-400 dark:text-gray-500 border-gray-200 dark:border-white/10 cursor-not-allowed'
                    : 'bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20 dark:border-green-400/20 hover:bg-green-500/20 dark:hover:bg-green-400/20'
                ]"
                @click="handleExport('operations')"
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
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                {{ exportStates.operations.isExporting ? '导出中...' : '导出' }}
              </button>
              
              <div
                v-if="exportStates.operations.isExporting && exportStates.operations.status"
                class="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg"
              >
                <div class="flex-1 min-w-[200px]">
                  <div class="flex items-center justify-between mb-1">
                    <span class="text-xs text-blue-600 dark:text-blue-400">{{ exportStates.operations.status }}</span>
                    <span class="text-xs text-blue-600 dark:text-blue-400">{{ exportStates.operations.progress }}%</span>
                  </div>
                  <div class="w-full bg-blue-500/20 rounded-full h-1.5">
                    <div
                      class="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                      :style="{ width: `${exportStates.operations.progress}%` }"
                    ></div>
                  </div>
                </div>
                <button
                  type="button"
                  class="px-2 py-1 text-xs bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 rounded hover:bg-red-500/20"
                  @click="cancelExport('operations')"
                >
                  取消
                </button>
              </div>
            </form>

            <form 
              v-if="activeTab === 'logins'" 
              class="flex flex-wrap items-center gap-2"
              :class="{ 'hidden md:flex': !showFilters, 'md:flex': true }"
              @submit.prevent="handleSearch"
            >
              <input id="input-logins-filters-username"
                v-model="filters.username"
                type="text"
                name="logins-username"
                placeholder="用户名"
                class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-28"
              >
              <input id="input-logins-filters-ip_address"
                v-model="filters.ip_address"
                type="text"
                name="logins-ip-address"
                placeholder="IP地址"
                class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-32"
              >
              <select id="select-logins-filters-status"
                v-model="filters.status"
                name="logins-status"
                class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
                @change="handleSearch"
              >
                <option value="">
                  全部状态
                </option>
                <option value="success">
                  成功
                </option>
                <option value="failed">
                  失败
                </option>
              </select>
              <DateRangePicker
                v-model:start-date="filters.start_date"
                v-model:end-date="filters.end_date"
              />
              <button
                type="button"
                class="px-2.5 py-1 text-xs bg-red-500/10 text-red-500 dark:text-red-400 border border-red-500/20 dark:border-red-400/20 rounded-lg hover:bg-red-500/20 dark:hover:bg-red-400/20 transition-colors flex items-center gap-1"
                @click="handleClearFilters"
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
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
                清除
              </button>
              <button
                class="btn-primary text-xs px-3 py-1 flex items-center gap-1"
                @click="handleSearch"
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
                    d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                  />
                </svg>
                筛选
              </button>
              <button
                type="button"
                :disabled="exportStates.logins.isExporting"
                :class="[
                  'px-2.5 py-1 text-xs border rounded-lg transition-colors flex items-center gap-1',
                  exportStates.logins.isExporting 
                    ? 'bg-gray-100 dark:bg-dark-100 text-gray-400 dark:text-gray-500 border-gray-200 dark:border-white/10 cursor-not-allowed'
                    : 'bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20 dark:border-green-400/20 hover:bg-green-500/20 dark:hover:bg-green-400/20'
                ]"
                @click="handleExport('logins')"
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
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                {{ exportStates.logins.isExporting ? '导出中...' : '导出' }}
              </button>
              
              <div
                v-if="exportStates.logins.isExporting && exportStates.logins.status"
                class="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg"
              >
                <div class="flex-1 min-w-[200px]">
                  <div class="flex items-center justify-between mb-1">
                    <span class="text-xs text-blue-600 dark:text-blue-400">{{ exportStates.logins.status }}</span>
                    <span class="text-xs text-blue-600 dark:text-blue-400">{{ exportStates.logins.progress }}%</span>
                  </div>
                  <div class="w-full bg-blue-500/20 rounded-full h-1.5">
                    <div
                      class="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                      :style="{ width: `${exportStates.logins.progress}%` }"
                    ></div>
                  </div>
                </div>
                <button
                  type="button"
                  class="px-2 py-1 text-xs bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 rounded hover:bg-red-500/20"
                  @click="cancelExport('logins')"
                >
                  取消
                </button>
              </div>
            </form>

            <form 
              v-if="activeTab === 'access'" 
              class="flex flex-wrap items-center gap-2"
              :class="{ 'hidden md:flex': !showFilters, 'md:flex': true }"
              @submit.prevent="handleSearch"
            >
              <input id="input-access-filters-username"
                v-model="filters.username"
                type="text"
                name="access-username"
                placeholder="用户名"
                class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-28"
                @keyup.enter="handleSearch"
              >
              <select id="select-filters-request_method"
                v-model="filters.request_method"
                name="access-request-method"
                class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
                @change="handleSearch"
              >
                <option value="">
                  全部方法
                </option>
                <option value="GET">
                  GET
                </option>
                <option value="POST">
                  POST
                </option>
                <option value="PUT">
                  PUT
                </option>
                <option value="DELETE">
                  DELETE
                </option>
              </select>
              <input id="input-access-filters-path"
                v-model="filters.path"
                type="text"
                name="access-path"
                placeholder="请求路径"
                class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-40"
                @keyup.enter="handleSearch"
              >
              <input id="input-access-filters-ip_address"
                v-model="filters.ip_address"
                type="text"
                name="access-ip-address"
                placeholder="IP地址"
                class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-32"
                @keyup.enter="handleSearch"
              >
              <DateRangePicker
                v-model:start-date="filters.start_date"
                v-model:end-date="filters.end_date"
              />
              <button
                type="button"
                class="px-2.5 py-1 text-xs bg-red-500/10 text-red-500 dark:text-red-400 border border-red-500/20 dark:border-red-400/20 rounded-lg hover:bg-red-500/20 dark:hover:bg-red-400/20 transition-colors flex items-center gap-1"
                @click="handleClearFilters"
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
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
                清除
              </button>
              <button
                class="btn-primary text-xs px-3 py-1 flex items-center gap-1"
                @click="handleSearch"
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
                    d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                  />
                </svg>
                筛选
              </button>
              <button
                type="button"
                :disabled="exportStates.access.isExporting"
                :class="[
                  'px-2.5 py-1 text-xs border rounded-lg transition-colors flex items-center gap-1',
                  exportStates.access.isExporting 
                    ? 'bg-gray-100 dark:bg-dark-100 text-gray-400 dark:text-gray-500 border-gray-200 dark:border-white/10 cursor-not-allowed'
                    : 'bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20 dark:border-green-400/20 hover:bg-green-500/20 dark:hover:bg-green-400/20'
                ]"
                @click="handleExport('access')"
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
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                {{ exportStates.access.isExporting ? '导出中...' : '导出' }}
              </button>
              
              <div
                v-if="exportStates.access.isExporting && exportStates.access.status"
                class="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg"
              >
                <div class="flex-1 min-w-[200px]">
                  <div class="flex items-center justify-between mb-1">
                    <span class="text-xs text-blue-600 dark:text-blue-400">{{ exportStates.access.status }}</span>
                    <span class="text-xs text-blue-600 dark:text-blue-400">{{ exportStates.access.progress }}%</span>
                  </div>
                  <div class="w-full bg-blue-500/20 rounded-full h-1.5">
                    <div
                      class="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                      :style="{ width: `${exportStates.access.progress}%` }"
                    ></div>
                  </div>
                </div>
                <button
                  type="button"
                  class="px-2 py-1 text-xs bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 rounded hover:bg-red-500/20"
                  @click="cancelExport('access')"
                >
                  取消
                </button>
              </div>
            </form>
        </div>

        <div class="overflow-x-auto" v-if="activeTab === 'operations'">
          <table class="w-full text-sm table-fixed">
            <thead>
              <tr class="border-b border-gray-200 dark:border-white/10">
                <th class="w-32 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  用户
                </th>
                <th class="w-24 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  模块
                </th>
                <th class="w-24 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  操作
                </th>
                <th class="w-32 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  描述
                </th>
                <th class="w-24 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  IP
                </th>
                <th class="w-20 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  状态
                </th>
                <th class="w-36 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  时间
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="log in operationLogs"
                :key="log.id"
                class="border-b border-gray-200 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/5"
              >
                <td class="py-2 px-3">
                  <div class="flex items-center gap-2">
                    <div
                      class="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-medium overflow-hidden flex-shrink-0"
                      :style="getOperationLogAvatarStyle(log)"
                    >
                      <span v-if="(!log.avatar_type || log.avatar_type === 'default') && !log.oauth_avatar_url">
                        {{ (log.username || '?').charAt(0).toUpperCase() }}
                      </span>
                    </div>
                    <span class="text-gray-900 dark:text-white truncate">{{ log.username || '-' }}</span>
                  </div>
                </td>
                <td class="py-2 px-3 text-gray-600 dark:text-gray-300 truncate">
                  {{ log.module }}
                </td>
                <td class="py-2 px-3 text-gray-600 dark:text-gray-300 truncate">
                  {{ log.action }}
                </td>
                <td class="py-2 px-3 text-gray-600 dark:text-gray-300 truncate">
                  {{ log.description || '-' }}
                </td>
                <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs truncate">
                  {{ log.ip_address || '-' }}
                </td>
                <td class="py-2 px-3">
                  <span :class="['px-2 py-0.5 rounded text-xs', getStatusClass(log.status)]">
                    {{ log.status === 'success' ? '成功' : '失败' }}
                  </span>
                </td>
                <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs">
                  {{ formatDate(log.created_at) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="overflow-x-auto" v-if="activeTab === 'logins'">
          <table class="w-full text-sm table-fixed">
            <thead>
              <tr class="border-b border-gray-200 dark:border-white/10">
                <th class="w-32 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  用户
                </th>
                <th class="w-24 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  类型
                </th>
                <th class="w-24 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  浏览器
                </th>
                <th class="w-32 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  系统
                </th>
                <th class="w-24 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  IP
                </th>
                <th class="w-20 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  状态
                </th>
                <th class="w-36 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  时间
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="log in loginLogs"
                :key="log.id"
                class="border-b border-gray-200 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/5"
              >
                <td class="py-2 px-3">
                  <div class="flex items-center gap-2">
                    <div
                      class="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-medium overflow-hidden flex-shrink-0"
                      :style="getLoginLogAvatarStyle(log)"
                    >
                      <span v-if="(!log.avatar_type || log.avatar_type === 'default') && !log.oauth_avatar_url">
                        {{ (log.username || '?').charAt(0).toUpperCase() }}
                      </span>
                    </div>
                    <span class="text-gray-900 dark:text-white truncate">{{ log.username || '-' }}</span>
                  </div>
                </td>
                <td class="py-2 px-3 text-gray-600 dark:text-gray-300 truncate">
                  {{ formatLoginType(log.login_type) }}
                </td>
                <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs truncate">
                  {{ log.browser || '-' }}
                </td>
                <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs truncate">
                  {{ log.os || '-' }}
                </td>
                <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs truncate">
                  {{ log.ip_address || '-' }}
                </td>
                <td class="py-2 px-3">
                  <span :class="['px-2 py-0.5 rounded text-xs', getStatusClass(log.status)]">
                    {{ log.status === 'success' ? '成功' : '失败' }}
                  </span>
                </td>
                <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs">
                  {{ formatDate(log.created_at) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="overflow-x-auto" v-if="activeTab === 'access'">
          <table class="w-full text-sm table-fixed">
            <thead>
              <tr class="border-b border-gray-200 dark:border-white/10">
                <th class="w-32 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  用户
                </th>
                <th class="w-24 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  方法
                </th>
                <th class="w-24 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  响应时间
                </th>
                <th class="w-32 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  路径
                </th>
                <th class="w-24 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  IP
                </th>
                <th class="w-20 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  状态码
                </th>
                <th class="w-36 text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">
                  时间
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="log in accessLogs"
                :key="log.id"
                class="border-b border-gray-200 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/5"
              >
                <td class="py-2 px-3">
                  <div class="flex items-center gap-2">
                    <div
                      class="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-medium overflow-hidden flex-shrink-0"
                      :style="getAccessLogAvatarStyle(log)"
                    >
                      <span v-if="(!log.avatar_type || log.avatar_type === 'default') && !log.oauth_avatar_url">
                        {{ log.username ? (log.username || '?').charAt(0).toUpperCase() : '游' }}
                      </span>
                    </div>
                    <span class="text-gray-900 dark:text-white truncate">{{ log.username || '游客' }}</span>
                  </div>
                </td>
                <td class="py-2 px-3">
                  <span
                    :class="[
                      'px-2 py-0.5 rounded text-xs',
                      log.request_method === 'GET' ? 'bg-blue-500/20 text-blue-400' :
                      log.request_method === 'POST' ? 'bg-green-500/20 text-green-400' :
                      log.request_method === 'PUT' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-red-500/20 text-red-400'
                    ]"
                  >
                    {{ log.request_method }}
                  </span>
                </td>
                <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs">
                  {{ log.response_time ? log.response_time.toFixed(2) + 'ms' : '-' }}
                </td>
                <td class="py-2 px-3 text-gray-600 dark:text-gray-300 truncate">
                  {{ log.request_path }}
                </td>
                <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs truncate">
                  {{ log.ip_address || '-' }}
                </td>
                <td class="py-2 px-3">
                  <span
                    :class="[
                      'px-2 py-0.5 rounded text-xs',
                      log.response_status < 400 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    ]"
                  >
                    {{ log.response_status }}
                  </span>
                </td>
                <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs">
                  {{ formatDate(log.created_at) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div
          v-if="totalPages > 1"
          class="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-white/10"
        >
            <p class="text-sm text-gray-500 dark:text-gray-400">
              共 {{ total }} 条记录
            </p>
            <div class="flex gap-2">
              <button
                :disabled="page === 1"
                class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                @click="page--; fetchLogs()"
              >
                上一页
              </button>
              <span class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-300">
                {{ page }} / {{ totalPages }}
              </span>
              <button
                :disabled="page === totalPages"
                class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                @click="page++; fetchLogs()"
              >
                下一页
              </button>
            </div>
          </div>
      </div>
    </div>
</template>
