<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { emailApi, type EmailConfig, type EmailLog, type EmailStats, type EmailProvider } from '@/api/email'

const activeTab = ref<'config' | 'logs'>('config')

const configs = ref<EmailConfig[]>([])
const activeConfig = ref<EmailConfig | null>(null)
const providers = ref<EmailProvider[]>([])
const isLoading = ref(false)
const isSaving = ref(false)
const isTesting = ref(false)
const showAddForm = ref(false)
const editingConfig = ref<EmailConfig | null>(null)

const configForm = ref({
  provider: 'qq' as 'qq' | 'gmail',
  smtp_user: '',
  smtp_password: '',
  from_email: '',
  from_name: 'Futuristic Blog'
})

const testEmail = ref('')

const logs = ref<EmailLog[]>([])
const logsPage = ref(1)
const logsTotal = ref(0)
const logsPageSize = ref(10)
const logsFilter = ref({
  email_type: '',
  status: ''
})

const stats = ref<EmailStats>({
  total_sent: 0,
  total_failed: 0,
  total_verified: 0,
  total_pending: 0,
  verification_rate: 0
})

const totalPages = computed(() => Math.ceil(logsTotal.value / logsPageSize.value))

const providerInfo = computed(() => {
  const info: Record<string, { name: string; color: string }> = {
    qq: { name: 'QQ邮箱', color: 'text-blue-400' },
    gmail: { name: 'Gmail', color: 'text-red-400' }
  }
  return info
})

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-500/20 text-yellow-400',
  sent: 'bg-green-500/20 text-green-400',
  failed: 'bg-red-500/20 text-red-400'
}

const statusLabels: Record<string, string> = {
  pending: '待发送',
  sent: '已发送',
  failed: '发送失败'
}

const emailTypeLabels: Record<string, string> = {
  verification: '邮箱验证',
  test: '测试邮件'
}

onMounted(async () => {
  await loadProviders()
  await loadConfigs()
  await loadStats()
})

async function loadProviders() {
  try {
    const data = await emailApi.getProviders()
    providers.value = data.providers
  } catch (error) {
    console.error('Failed to load providers:', error)
  }
}

async function loadConfigs() {
  isLoading.value = true
  try {
    const [configsData, activeData] = await Promise.all([
      emailApi.getConfigs(),
      emailApi.getActiveConfig()
    ])
    configs.value = configsData
    activeConfig.value = activeData
  } catch (error) {
    console.error('Failed to load configs:', error)
  } finally {
    isLoading.value = false
  }
}

async function loadLogs() {
  isLoading.value = true
  try {
    const data = await emailApi.getLogs({
      page: logsPage.value,
      page_size: logsPageSize.value,
      email_type: logsFilter.value.email_type || undefined,
      status: logsFilter.value.status || undefined
    })
    logs.value = data.items
    logsTotal.value = data.total
  } catch (error) {
    console.error('Failed to load logs:', error)
  } finally {
    isLoading.value = false
  }
}

async function loadStats() {
  try {
    stats.value = await emailApi.getStats()
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

function resetForm() {
  configForm.value = {
    provider: 'qq',
    smtp_user: '',
    smtp_password: '',
    from_email: '',
    from_name: 'Futuristic Blog'
  }
  editingConfig.value = null
  showAddForm.value = false
}

function startAddConfig() {
  resetForm()
  showAddForm.value = true
}

function startEditConfig(config: EmailConfig) {
  editingConfig.value = config
  configForm.value = {
    provider: config.provider,
    smtp_user: config.smtp_user || '',
    smtp_password: '',
    from_email: config.from_email || '',
    from_name: config.from_name
  }
  showAddForm.value = true
}

async function saveConfig() {
  if (!configForm.value.smtp_user || !configForm.value.smtp_password || !configForm.value.from_email) {
    alert('请填写所有必填字段')
    return
  }

  isSaving.value = true
  try {
    if (editingConfig.value) {
      await emailApi.updateConfig(editingConfig.value.id, configForm.value)
    } else {
      await emailApi.createConfig(configForm.value)
    }
    alert('保存成功！')
    resetForm()
    await loadConfigs()
  } catch (error: any) {
    alert(error.response?.data?.detail || '保存失败')
  } finally {
    isSaving.value = false
  }
}

async function activateConfig(config: EmailConfig) {
  if (!confirm(`确定要激活配置 "${config.smtp_user}" 吗？`)) return
  
  try {
    await emailApi.activateConfig(config.id)
    alert('激活成功！')
    await loadConfigs()
  } catch (error: any) {
    alert(error.response?.data?.detail || '激活失败')
  }
}

async function deleteConfig(config: EmailConfig) {
  if (!confirm(`确定要删除配置 "${config.smtp_user}" 吗？`)) return

  try {
    const result = await emailApi.deleteConfig(config.id)
    alert('删除成功')
    if (result.was_active) {
      activeConfig.value = null
    }
    await loadConfigs()
  } catch (error: any) {
    alert(error.response?.data?.detail || '删除失败')
  }
}

async function sendTestEmail() {
  if (!testEmail.value) {
    alert('请输入测试邮箱地址')
    return
  }

  if (!activeConfig.value) {
    alert('请先激活一个邮箱配置')
    return
  }

  isTesting.value = true
  try {
    await emailApi.testEmail(testEmail.value)
    alert('测试邮件发送成功，请查收')
    testEmail.value = ''
    await loadStats()
  } catch (error: any) {
    alert(error.response?.data?.detail || '发送失败')
  } finally {
    isTesting.value = false
  }
}

function switchToLogs() {
  activeTab.value = 'logs'
  loadLogs()
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function changePage(page: number) {
  logsPage.value = page
  loadLogs()
}

function getProviderName(provider: string): string {
  return providerInfo.value[provider]?.name || provider
}

function getProviderColor(provider: string): string {
  return providerInfo.value[provider]?.color || 'text-gray-400'
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">邮件管理</h1>
      <div class="flex gap-2">
        <button
          @click="activeTab = 'config'"
          :class="[
            'px-4 py-2 rounded-lg font-medium transition-colors',
            activeTab === 'config'
              ? 'bg-primary text-white'
              : 'bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-200'
          ]"
        >
          邮箱配置
        </button>
        <button
          @click="switchToLogs"
          :class="[
            'px-4 py-2 rounded-lg font-medium transition-colors',
            activeTab === 'logs'
              ? 'bg-primary text-white'
              : 'bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-200'
          ]"
        >
          发送记录
        </button>
      </div>
    </div>

    <div v-if="activeTab === 'config'" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="glass-card p-4">
          <div class="text-sm text-gray-500 dark:text-gray-400">已发送</div>
          <div class="text-2xl font-bold text-green-400">{{ stats.total_sent }}</div>
        </div>
        <div class="glass-card p-4">
          <div class="text-sm text-gray-500 dark:text-gray-400">发送失败</div>
          <div class="text-2xl font-bold text-red-400">{{ stats.total_failed }}</div>
        </div>
        <div class="glass-card p-4">
          <div class="text-sm text-gray-500 dark:text-gray-400">已验证</div>
          <div class="text-2xl font-bold text-primary">{{ stats.total_verified }}</div>
        </div>
        <div class="glass-card p-4">
          <div class="text-sm text-gray-500 dark:text-gray-400">验证率</div>
          <div class="text-2xl font-bold text-accent">{{ stats.verification_rate }}%</div>
        </div>
      </div>

      <div class="glass-card p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">邮箱配置列表</h2>
          <button
            @click="startAddConfig"
            class="btn-primary flex items-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            添加配置
          </button>
        </div>

        <div v-if="isLoading" class="text-center py-8 text-gray-500">
          加载中...
        </div>

        <div v-else-if="configs.length === 0" class="text-center py-8 text-gray-500">
          暂无配置，请添加邮箱配置
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="config in configs"
            :key="config.id"
            :class="[
              'p-4 rounded-lg border transition-all',
              config.is_active
                ? 'border-primary bg-primary/5'
                : 'border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-dark-100'
            ]"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                  <span :class="['font-semibold', getProviderColor(config.provider)]">
                    {{ getProviderName(config.provider) }}
                  </span>
                  <span class="text-gray-700 dark:text-gray-300">{{ config.smtp_user }}</span>
                  <span
                    v-if="config.is_active"
                    class="px-2 py-0.5 text-xs rounded-full bg-green-500/20 text-green-400"
                  >
                    当前使用
                  </span>
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400 space-y-1">
                  <div>发件人: {{ config.from_name }} &lt;{{ config.from_email }}&gt;</div>
                  <div>SMTP: {{ config.smtp_host }}:{{ config.smtp_port }}</div>
                  <div>创建时间: {{ formatDate(config.created_at) }}</div>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button
                  v-if="!config.is_active"
                  @click="activateConfig(config)"
                  class="px-3 py-1.5 text-sm bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors"
                >
                  激活
                </button>
                <button
                  @click="startEditConfig(config)"
                  class="px-3 py-1.5 text-sm bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
                >
                  编辑
                </button>
                <button
                  @click="deleteConfig(config)"
                  class="px-3 py-1.5 text-sm bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="showAddForm" class="glass-card p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ editingConfig ? '编辑配置' : '添加新配置' }}
          </h2>
          <button
            @click="resetForm"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              邮箱服务商 <span class="text-red-400">*</span>
            </label>
            <div class="grid grid-cols-2 gap-4">
              <label
                v-for="provider in providers"
                :key="provider.id"
                :class="[
                  'flex items-center gap-3 p-4 rounded-lg border cursor-pointer transition-all',
                  configForm.provider === provider.id
                    ? 'border-primary bg-primary/5'
                    : 'border-gray-200 dark:border-white/10 hover:border-primary/50'
                ]"
              >
                <input
                  type="radio"
                  v-model="configForm.provider"
                  :value="provider.id"
                  class="w-4 h-4 text-primary"
                  :disabled="!!editingConfig"
                />
                <div>
                  <div :class="['font-medium', getProviderColor(provider.id)]">{{ provider.name }}</div>
                  <div class="text-xs text-gray-500">{{ provider.host }}:{{ provider.port }}</div>
                </div>
              </label>
            </div>
          </div>

          <div class="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <div class="flex items-start gap-2">
              <svg class="w-5 h-5 text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div class="text-sm text-blue-300">
                <div v-if="configForm.provider === 'qq'" class="space-y-1">
                  <p class="font-medium">QQ邮箱授权码获取方式：</p>
                  <ol class="list-decimal list-inside space-y-0.5 text-blue-200">
                    <li>登录QQ邮箱 → 设置 → 账户</li>
                    <li>找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"</li>
                    <li>开启"POP3/SMTP服务"</li>
                    <li>按提示生成授权码（16位字符）</li>
                  </ol>
                </div>
                <div v-else class="space-y-1">
                  <p class="font-medium">Gmail应用密码获取方式：</p>
                  <ol class="list-decimal list-inside space-y-0.5 text-blue-200">
                    <li>登录Google账户 → 安全性</li>
                    <li>开启两步验证</li>
                    <li>搜索"应用专用密码"或访问 myaccount.google.com/apppasswords</li>
                    <li>生成新的应用专用密码（16位字符）</li>
                  </ol>
                </div>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                邮箱账号 <span class="text-red-400">*</span>
              </label>
              <input
                v-model="configForm.smtp_user"
                type="text"
                :placeholder="configForm.provider === 'qq' ? '您的QQ邮箱@qq.com' : '您的Gmail@gmail.com'"
                class="w-full px-4 py-3 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary focus:outline-none"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {{ configForm.provider === 'qq' ? '授权码' : '应用密码' }} <span class="text-red-400">*</span>
              </label>
              <input
                v-model="configForm.smtp_password"
                type="password"
                :placeholder="editingConfig ? '留空则保持原密码不变' : (configForm.provider === 'qq' ? '16位授权码' : '16位应用密码')"
                class="w-full px-4 py-3 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary focus:outline-none"
              />
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                发件人邮箱 <span class="text-red-400">*</span>
              </label>
              <input
                v-model="configForm.from_email"
                type="email"
                placeholder="用于发送邮件的邮箱地址"
                class="w-full px-4 py-3 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary focus:outline-none"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                发件人名称
              </label>
              <input
                v-model="configForm.from_name"
                type="text"
                placeholder="显示的发件人名称"
                class="w-full px-4 py-3 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary focus:outline-none"
              />
            </div>
          </div>

          <div class="flex items-center gap-4 pt-4 border-t border-gray-200 dark:border-white/10">
            <button
              @click="saveConfig"
              :disabled="isSaving"
              class="btn-primary"
            >
              {{ isSaving ? '保存中...' : (editingConfig ? '更新配置' : '保存配置') }}
            </button>
            <button
              @click="resetForm"
              class="px-4 py-2 bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-200 transition-colors"
            >
              取消
            </button>
          </div>
        </div>
      </div>

      <div class="glass-card p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">发送测试邮件</h2>
        <div class="flex gap-4">
          <input
            v-model="testEmail"
            type="email"
            placeholder="输入测试邮箱地址"
            class="flex-1 px-4 py-3 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary focus:outline-none"
          />
          <button
            @click="sendTestEmail"
            :disabled="isTesting || !activeConfig"
            class="btn-secondary whitespace-nowrap"
          >
            {{ isTesting ? '发送中...' : '发送测试' }}
          </button>
        </div>
        <p v-if="!activeConfig" class="mt-2 text-sm text-yellow-400">
          请先激活一个邮箱配置后再发送测试邮件
        </p>
        <p v-else class="mt-2 text-sm text-green-400">
          当前使用: {{ getProviderName(activeConfig.provider) }} - {{ activeConfig.smtp_user }}
        </p>
      </div>
    </div>

    <div v-else class="space-y-6">
      <div class="glass-card p-4">
        <div class="flex flex-wrap gap-4 items-center">
          <select
            v-model="logsFilter.email_type"
            @change="loadLogs"
            class="px-4 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white"
          >
            <option value="">所有类型</option>
            <option value="verification">邮箱验证</option>
            <option value="test">测试邮件</option>
          </select>

          <select
            v-model="logsFilter.status"
            @change="loadLogs"
            class="px-4 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white"
          >
            <option value="">所有状态</option>
            <option value="sent">已发送</option>
            <option value="failed">发送失败</option>
            <option value="pending">待发送</option>
          </select>
        </div>
      </div>

      <div class="glass-card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 dark:bg-dark-100">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">类型</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">收件人</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">主题</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">状态</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">已验证</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">发送时间</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">错误信息</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-white/10">
              <tr v-if="isLoading">
                <td colspan="7" class="px-4 py-8 text-center text-gray-500">加载中...</td>
              </tr>
              <tr v-else-if="logs.length === 0">
                <td colspan="7" class="px-4 py-8 text-center text-gray-500">暂无记录</td>
              </tr>
              <tr
                v-else
                v-for="log in logs"
                :key="log.id"
                class="hover:bg-gray-50 dark:hover:bg-dark-100"
              >
                <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">
                  {{ emailTypeLabels[log.email_type] || log.email_type }}
                </td>
                <td class="px-4 py-3">
                  <div class="text-sm text-gray-900 dark:text-white">{{ log.recipient_email }}</div>
                  <div v-if="log.recipient_name" class="text-xs text-gray-500">{{ log.recipient_name }}</div>
                </td>
                <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 max-w-xs truncate">
                  {{ log.subject || '-' }}
                </td>
                <td class="px-4 py-3">
                  <span :class="['px-2 py-1 text-xs rounded-full', statusColors[log.status]]">
                    {{ statusLabels[log.status] }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <span
                    v-if="log.email_type === 'verification'"
                    :class="[
                      'px-2 py-1 text-xs rounded-full',
                      log.is_verified
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-gray-500/20 text-gray-400'
                    ]"
                  >
                    {{ log.is_verified ? '已验证' : '未验证' }}
                  </span>
                  <span v-else class="text-gray-500">-</span>
                </td>
                <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                  {{ formatDate(log.sent_at) }}
                </td>
                <td class="px-4 py-3 text-sm text-red-400 max-w-xs truncate">
                  {{ log.error_message || '-' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="totalPages > 1" class="px-4 py-3 border-t border-gray-200 dark:border-white/10 flex items-center justify-between">
          <div class="text-sm text-gray-500 dark:text-gray-400">
            共 {{ logsTotal }} 条记录
          </div>
          <div class="flex gap-2">
            <button
              @click="changePage(logsPage - 1)"
              :disabled="logsPage === 1"
              class="px-3 py-1 rounded-lg bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-400 disabled:opacity-50"
            >
              上一页
            </button>
            <button
              v-for="p in totalPages"
              :key="p"
              @click="changePage(p)"
              :class="[
                'px-3 py-1 rounded-lg',
                p === logsPage
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-400'
              ]"
            >
              {{ p }}
            </button>
            <button
              @click="changePage(logsPage + 1)"
              :disabled="logsPage === totalPages"
              class="px-3 py-1 rounded-lg bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-400 disabled:opacity-50"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
