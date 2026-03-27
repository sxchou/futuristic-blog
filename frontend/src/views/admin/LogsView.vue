<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { logsApi } from '@/api'
import { useDialogStore, useUserProfileStore, useAuthStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { formatDateTime } from '@/utils/date'

const dialog = useDialogStore()
const userProfileStore = useUserProfileStore()
const authStore = useAuthStore()
const { requireAdmin, isAdmin } = useAdminCheck()

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
  status: '',
  username: '',
  login_type: '',
  ip_address: '',
  request_method: '',
  path: ''
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
  } catch (error) {
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
    status: '',
    username: '',
    login_type: '',
    ip_address: '',
    request_method: '',
    path: ''
  }
}

const handleSearch = () => {
  page.value = 1
  fetchLogs()
}

const handleClearLogs = async () => {
  if (!await requireAdmin('清理日志')) return
  
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

const formatDate = (date: string) => formatDateTime(date)

const getStatusClass = (status: string) => {
  return status === 'success' 
    ? 'bg-green-500/20 text-green-400' 
    : 'bg-red-500/20 text-red-400'
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

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

onMounted(async () => {
  await authStore.waitForInit()
  if (!isAdmin.value) return
  fetchStats()
  fetchLogs()
})

watch(() => userProfileStore.avatarUpdatedAt, () => {
  if (!loading.value) {
    fetchLogs()
  }
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">日志管理</h1>
      <button
        v-if="isAdmin"
        @click="handleClearLogs"
        class="px-3 py-1.5 text-sm bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
      >
        清理30天前日志
      </button>
    </div>

    <div v-if="!isAdmin" class="glass-card p-8 text-center">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
        <svg class="w-8 h-8 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">权限不足</h2>
      <p class="text-gray-500 dark:text-gray-400">您没有权限访问此页面，请联系管理员</p>
    </div>

    <template v-else>
    <div class="grid grid-cols-3 gap-3 mb-6">
      <div class="glass-card p-3">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
            <svg class="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div>
            <p class="text-gray-500 dark:text-gray-400 text-xs">操作日志</p>
            <p class="text-lg font-bold text-gray-900 dark:text-white">{{ stats.total_operations }}</p>
          </div>
        </div>
      </div>
      
      <div class="glass-card p-3">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-lg bg-secondary/20 flex items-center justify-center">
            <svg class="w-4 h-4 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
            </svg>
          </div>
          <div>
            <p class="text-gray-500 dark:text-gray-400 text-xs">登录日志</p>
            <p class="text-lg font-bold text-gray-900 dark:text-white">{{ stats.total_logins }}</p>
          </div>
        </div>
      </div>
      
      <div class="glass-card p-3">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
            <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </div>
          <div>
            <p class="text-gray-500 dark:text-gray-400 text-xs">访问日志</p>
            <p class="text-lg font-bold text-gray-900 dark:text-white">{{ stats.total_access }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="glass-card">
      <div class="flex border-b border-gray-200 dark:border-white/10">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="handleTabChange(tab.key)"
          :class="[
            'px-4 py-2 text-sm font-medium transition-colors',
            activeTab === tab.key
              ? 'text-primary border-b-2 border-primary'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          ]"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="p-4">
        <div v-if="activeTab === 'operations'" class="space-y-4">
          <div class="flex flex-wrap gap-2">
            <input
              v-model="filters.username"
              type="text"
              placeholder="用户名"
              class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
            />
            <input
              v-model="filters.module"
              type="text"
              placeholder="模块"
              class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
            />
            <input
              v-model="filters.action"
              type="text"
              placeholder="操作"
              class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
            />
            <select
              v-model="filters.status"
              class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
            >
              <option value="">全部状态</option>
              <option value="success">成功</option>
              <option value="failed">失败</option>
            </select>
            <button
              @click="handleSearch"
              class="px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary/80 transition-colors"
            >
              搜索
            </button>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-white/10">
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">用户</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">模块</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">操作</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">描述</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">IP</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">状态</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">时间</th>
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
                      <span class="text-gray-900 dark:text-white">{{ log.username || '-' }}</span>
                    </div>
                  </td>
                  <td class="py-2 px-3 text-gray-600 dark:text-gray-300">{{ log.module }}</td>
                  <td class="py-2 px-3 text-gray-600 dark:text-gray-300">{{ log.action }}</td>
                  <td class="py-2 px-3 text-gray-600 dark:text-gray-300 max-w-xs truncate">{{ log.description || '-' }}</td>
                  <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs">{{ log.ip_address || '-' }}</td>
                  <td class="py-2 px-3">
                    <span :class="['px-2 py-0.5 rounded text-xs', getStatusClass(log.status)]">
                      {{ log.status === 'success' ? '成功' : '失败' }}
                    </span>
                  </td>
                  <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs">{{ formatDate(log.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="activeTab === 'logins'" class="space-y-4">
          <div class="flex flex-wrap gap-2">
            <input
              v-model="filters.username"
              type="text"
              placeholder="用户名"
              class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
            />
            <input
              v-model="filters.ip_address"
              type="text"
              placeholder="IP地址"
              class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
            />
            <select
              v-model="filters.status"
              class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
            >
              <option value="">全部状态</option>
              <option value="success">成功</option>
              <option value="failed">失败</option>
            </select>
            <button
              @click="handleSearch"
              class="px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary/80 transition-colors"
            >
              搜索
            </button>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-white/10">
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">用户</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">类型</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">IP</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">浏览器</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">系统</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">状态</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">时间</th>
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
                      <span class="text-gray-900 dark:text-white">{{ log.username || '-' }}</span>
                    </div>
                  </td>
                  <td class="py-2 px-3 text-gray-600 dark:text-gray-300">{{ log.login_type === 'login' ? '登录' : '登出' }}</td>
                  <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs">{{ log.ip_address || '-' }}</td>
                  <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs">{{ log.browser || '-' }}</td>
                  <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs">{{ log.os || '-' }}</td>
                  <td class="py-2 px-3">
                    <span :class="['px-2 py-0.5 rounded text-xs', getStatusClass(log.status)]">
                      {{ log.status === 'success' ? '成功' : '失败' }}
                    </span>
                  </td>
                  <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs">{{ formatDate(log.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="activeTab === 'access'" class="space-y-4">
          <div class="flex flex-wrap gap-2">
            <input
              v-model="filters.username"
              type="text"
              placeholder="用户名"
              class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
            />
            <input
              v-model="filters.ip_address"
              type="text"
              placeholder="IP地址"
              class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
            />
            <input
              v-model="filters.path"
              type="text"
              placeholder="请求路径"
              class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
            />
            <select
              v-model="filters.request_method"
              class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
            >
              <option value="">全部方法</option>
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
            </select>
            <button
              @click="handleSearch"
              class="px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary/80 transition-colors"
            >
              搜索
            </button>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-white/10">
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">用户</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">方法</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">路径</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">状态码</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">响应时间</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">IP</th>
                  <th class="text-left py-2 px-3 text-gray-500 dark:text-gray-400 font-medium">时间</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="log in accessLogs"
                  :key="log.id"
                  class="border-b border-gray-200 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/5"
                >
                  <td class="py-2 px-3 text-gray-900 dark:text-white">{{ log.username || '-' }}</td>
                  <td class="py-2 px-3">
                    <span :class="[
                      'px-2 py-0.5 rounded text-xs',
                      log.request_method === 'GET' ? 'bg-blue-500/20 text-blue-400' :
                      log.request_method === 'POST' ? 'bg-green-500/20 text-green-400' :
                      log.request_method === 'PUT' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-red-500/20 text-red-400'
                    ]">
                      {{ log.request_method }}
                    </span>
                  </td>
                  <td class="py-2 px-3 text-gray-600 dark:text-gray-300 max-w-xs truncate">{{ log.request_path }}</td>
                  <td class="py-2 px-3">
                    <span :class="[
                      'px-2 py-0.5 rounded text-xs',
                      log.response_status < 400 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    ]">
                      {{ log.response_status }}
                    </span>
                  </td>
                  <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs">{{ log.response_time ? log.response_time.toFixed(2) + 'ms' : '-' }}</td>
                  <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs">{{ log.ip_address || '-' }}</td>
                  <td class="py-2 px-3 text-gray-500 dark:text-gray-400 text-xs">{{ formatDate(log.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="totalPages > 1" class="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-white/10">
          <p class="text-sm text-gray-500 dark:text-gray-400">
            共 {{ total }} 条记录
          </p>
          <div class="flex gap-2">
            <button
              @click="page--; fetchLogs()"
              :disabled="page === 1"
              class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              上一页
            </button>
            <span class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-300">
              {{ page }} / {{ totalPages }}
            </span>
            <button
              @click="page++; fetchLogs()"
              :disabled="page === totalPages"
              class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>
    </template>
  </div>
</template>
