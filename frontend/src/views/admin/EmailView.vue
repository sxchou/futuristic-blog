<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { emailApi, type EmailConfig, type EmailLog, type EmailStats, type EmailProvider, type ProviderStatus } from '@/api/email'
import { useDialogStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { formatDateTime } from '@/utils/date'

const dialog = useDialogStore()
const { requireAdmin, isAdmin } = useAdminCheck()
const activeTab = ref<'config' | 'logs'>('config')

const configs = ref<EmailConfig[]>([])
const activeConfig = ref<EmailConfig | null>(null)
const providers = ref<EmailProvider[]>([])
const providerStatus = ref<ProviderStatus | null>(null)
const isLoading = ref(false)
const isSaving = ref(false)
const isTesting = ref(false)
const isTestingResend = ref(false)
const isEditing = ref(false)
const editingConfig = ref<EmailConfig | null>(null)
const switchingProvider = ref(false)

const configForm = ref({
  provider: 'qq',
  smtp_user: '',
  smtp_password: '',
  from_email: '',
  from_name: 'Futuristic Blog'
})

const testEmail = ref('')
const testResendEmail = ref('')

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

const smtpProviders = computed(() => {
  return providers.value.filter(p => !p.is_api)
})

const providerInfo = computed(() => {
  const info: Record<string, { name: string; color: string; isApi?: boolean }> = {
    resend: { name: 'Resend', color: 'text-purple-400', isApi: true },
    qq: { name: 'QQ邮箱', color: 'text-blue-400' },
    gmail: { name: 'Gmail', color: 'text-red-400' },
    '163': { name: '163邮箱', color: 'text-green-400' },
    outlook: { name: 'Outlook', color: 'text-blue-400' }
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
  await loadProviderStatus()
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

async function loadProviderStatus() {
  try {
    providerStatus.value = await emailApi.getProviderStatus()
  } catch (error) {
    console.error('Failed to load provider status:', error)
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
}

function closeEditModal() {
  isEditing.value = false
  resetForm()
}

async function openAddModal() {
  if (!await requireAdmin('添加邮箱配置')) return
  resetForm()
  isEditing.value = true
}

async function openEditModal(config: EmailConfig) {
  if (!await requireAdmin('编辑邮箱配置')) return
  editingConfig.value = config
  configForm.value = {
    provider: config.provider,
    smtp_user: config.smtp_user || '',
    smtp_password: '',
    from_email: config.from_email || '',
    from_name: config.from_name
  }
  isEditing.value = true
}

async function saveConfig() {
  if (!await requireAdmin('保存邮箱配置')) return
  
  if (!configForm.value.smtp_user || !configForm.value.from_email) {
    await dialog.showError('请填写所有必填字段', '提示')
    return
  }

  if (!editingConfig.value && !configForm.value.smtp_password) {
    await dialog.showError('请填写密码/授权码', '提示')
    return
  }

  isSaving.value = true
  try {
    if (editingConfig.value) {
      const updateData = { ...configForm.value }
      if (!updateData.smtp_password) {
        delete (updateData as any).smtp_password
      }
      await emailApi.updateConfig(editingConfig.value.id, updateData)
    } else {
      await emailApi.createConfig(configForm.value)
    }
    await dialog.showSuccess('保存成功！', '成功')
    closeEditModal()
    await loadConfigs()
  } catch (error: any) {
    await dialog.showError(error.response?.data?.detail || '保存失败', '错误')
  } finally {
    isSaving.value = false
  }
}

async function activateConfig(config: EmailConfig) {
  if (!await requireAdmin('激活邮箱配置')) return
  
  const confirmed = await dialog.showConfirm({
    message: `确定要激活配置 "${config.smtp_user}" 吗？`,
    title: '确认激活'
  })
  if (!confirmed) return
  
  try {
    await emailApi.activateConfig(config.id)
    await dialog.showSuccess('激活成功！', '成功')
    await loadConfigs()
    await loadProviderStatus()
  } catch (error: any) {
    await dialog.showError(error.response?.data?.detail || '激活失败', '错误')
  }
}

async function deleteConfig(config: EmailConfig) {
  if (!await requireAdmin('删除邮箱配置')) return
  
  const confirmed = await dialog.showConfirm({
    message: `确定要删除配置 "${config.smtp_user}" 吗？`,
    title: '确认删除'
  })
  if (!confirmed) return

  try {
    const result = await emailApi.deleteConfig(config.id)
    await dialog.showSuccess('删除成功', '成功')
    if (result.was_active) {
      activeConfig.value = null
    }
    await loadConfigs()
    await loadProviderStatus()
  } catch (error: any) {
    await dialog.showError(error.response?.data?.detail || '删除失败', '错误')
  }
}

async function sendTestEmail() {
  if (!await requireAdmin('发送测试邮件')) return
  
  if (!testEmail.value) {
    await dialog.showError('请输入测试邮箱地址', '提示')
    return
  }

  if (!activeConfig.value) {
    await dialog.showError('请先激活一个邮箱配置', '提示')
    return
  }

  isTesting.value = true
  try {
    await emailApi.testEmail(testEmail.value)
    await dialog.showSuccess('测试邮件发送成功，请查收', '成功')
    testEmail.value = ''
    await loadStats()
  } catch (error: any) {
    await dialog.showError(error.response?.data?.detail || '发送失败', '错误')
  } finally {
    isTesting.value = false
  }
}

async function sendResendTestEmail() {
  if (!await requireAdmin('发送Resend测试邮件')) return
  
  if (!testResendEmail.value) {
    await dialog.showError('请输入测试邮箱地址', '提示')
    return
  }

  isTestingResend.value = true
  try {
    const result = await emailApi.testResendEmail(testResendEmail.value)
    await dialog.showSuccess(`Resend测试邮件发送成功！\n消息ID: ${result.message_id || 'N/A'}`, '成功')
    testResendEmail.value = ''
    await loadStats()
  } catch (error: any) {
    await dialog.showError(error.response?.data?.detail || 'Resend发送失败', '错误')
  } finally {
    isTestingResend.value = false
  }
}

async function switchProvider(provider: string) {
  if (!await requireAdmin('切换邮件服务提供商')) return
  
  const confirmed = await dialog.showConfirm({
    message: `确定要切换到 ${getProviderName(provider)} 吗？`,
    title: '确认切换'
  })
  if (!confirmed) return
  
  switchingProvider.value = true
  try {
    await emailApi.switchProvider(provider)
    await dialog.showSuccess('切换成功！', '成功')
    await loadProviderStatus()
    await loadConfigs()
  } catch (error: any) {
    await dialog.showError(error.response?.data?.detail || '切换失败', '错误')
  } finally {
    switchingProvider.value = false
  }
}

function switchToLogs() {
  activeTab.value = 'logs'
  loadLogs()
}

function formatDate(dateStr: string | null) {
  return formatDateTime(dateStr)
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

function isProviderActive(providerId: string): boolean {
  return providerStatus.value?.current_provider === providerId
}

function getProviderBgColor(provider: string) {
  switch (provider) {
    case 'qq':
      return 'bg-[#12B7F5]'
    case 'gmail':
      return 'bg-red-500'
    case '163':
      return 'bg-green-500'
    case 'outlook':
      return 'bg-blue-500'
    case 'resend':
      return 'bg-purple-500'
    default:
      return 'bg-gray-500'
  }
}
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-5">
      <div>
        <h1 class="text-lg font-semibold text-gray-900 dark:text-white">
          邮件管理
        </h1>
        <p class="text-gray-500 dark:text-gray-400 text-xs mt-0.5">
          配置邮件服务提供商和邮箱账号
        </p>
      </div>
      <div class="flex gap-2">
        <button
          :class="[
            'px-3 py-1.5 text-sm rounded-md font-medium transition-colors',
            activeTab === 'config'
              ? 'bg-primary text-white'
              : 'bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-300'
          ]"
          @click="activeTab = 'config'"
        >
          配置
        </button>
        <button
          :class="[
            'px-3 py-1.5 text-sm rounded-md font-medium transition-colors',
            activeTab === 'logs'
              ? 'bg-primary text-white'
              : 'bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-300'
          ]"
          @click="switchToLogs"
        >
          日志
        </button>
      </div>
    </div>

    <div
      v-if="!isAdmin"
      class="bg-white dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10 p-8 text-center"
    >
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
        <svg
          class="w-8 h-8 text-yellow-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        权限不足
      </h2>
      <p class="text-gray-500 dark:text-gray-400">
        您没有权限访问此页面，请联系管理员
      </p>
    </div>

    <template v-else>
      <div
        v-if="activeTab === 'config'"
        class="space-y-5"
      >
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="bg-white dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10 p-3">
            <div class="text-xs text-gray-500 dark:text-gray-400">
              已发送
            </div>
            <div class="text-xl font-bold text-green-400">
              {{ stats.total_sent }}
            </div>
          </div>
          <div class="bg-white dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10 p-3">
            <div class="text-xs text-gray-500 dark:text-gray-400">
              发送失败
            </div>
            <div class="text-xl font-bold text-red-400">
              {{ stats.total_failed }}
            </div>
          </div>
          <div class="bg-white dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10 p-3">
            <div class="text-xs text-gray-500 dark:text-gray-400">
              已验证
            </div>
            <div class="text-xl font-bold text-primary">
              {{ stats.total_verified }}
            </div>
          </div>
          <div class="bg-white dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10 p-3">
            <div class="text-xs text-gray-500 dark:text-gray-400">
              验证率
            </div>
            <div class="text-xl font-bold text-accent">
              {{ stats.verification_rate }}%
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10 overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-200 dark:border-white/10">
            <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
              邮件服务提供商
            </h2>
          </div>
          <div class="p-4">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div
                v-for="provider in providers"
                :key="provider.id"
                :class="[
                  'p-3 rounded-lg border transition-all cursor-pointer',
                  isProviderActive(provider.id)
                    ? 'border-primary bg-primary/5'
                    : 'border-gray-200 dark:border-white/10 hover:border-primary/50'
                ]"
                @click="switchProvider(provider.id)"
              >
                <div class="flex items-center justify-between mb-1.5">
                  <div class="flex items-center gap-2">
                    <div
                      class="w-6 h-6 rounded flex items-center justify-center text-white text-xs font-bold"
                      :class="getProviderBgColor(provider.id)"
                    >
                      {{ provider.name.charAt(0) }}
                    </div>
                    <span :class="['font-medium text-sm', getProviderColor(provider.id)]">
                      {{ provider.name }}
                    </span>
                  </div>
                  <span
                    v-if="isProviderActive(provider.id)"
                    class="px-1.5 py-0.5 text-xs rounded bg-green-500/20 text-green-400"
                  >
                    当前
                  </span>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400 mb-1.5">
                  {{ provider.description }}
                </p>
                <div
                  v-if="provider.is_api"
                  class="flex items-center gap-2"
                >
                  <span
                    :class="[
                      'px-1.5 py-0.5 text-xs rounded',
                      providerStatus?.has_resend_api_key
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-red-500/20 text-red-400'
                    ]"
                  >
                    {{ providerStatus?.has_resend_api_key ? 'API已配置' : 'API未配置' }}
                  </span>
                </div>
                <div
                  v-else-if="provider.host"
                  class="text-xs text-gray-400"
                >
                  {{ provider.host }}:{{ provider.port }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="providerStatus?.current_provider === 'resend' && providerStatus?.has_resend_api_key"
          class="bg-white dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10 p-4"
        >
          <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-3">
            Resend 测试
          </h3>
          <div class="flex gap-2">
            <input
              v-model="testResendEmail"
              type="email"
              placeholder="输入测试邮箱地址"
              class="flex-1 px-3 py-2 text-sm bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-md text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary focus:outline-none"
            >
            <button
              :disabled="isTestingResend"
              class="px-3 py-2 text-sm bg-primary text-white rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
              @click="sendResendTestEmail"
            >
              {{ isTestingResend ? '发送中...' : '测试' }}
            </button>
          </div>
        </div>

        <div class="bg-white dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10 overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-200 dark:border-white/10 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
              邮箱配置列表
            </h2>
            <button
              class="px-3 py-1.5 text-xs bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
              @click="openAddModal"
            >
              添加配置
            </button>
          </div>

          <div
            v-if="isLoading"
            class="flex justify-center py-8"
          >
            <div class="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>

          <div
            v-else-if="configs.length === 0"
            class="text-center py-8 text-gray-500 text-sm"
          >
            暂无配置，请添加邮箱配置
          </div>

          <div
            v-else
            class="overflow-x-auto"
          >
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-200 dark:border-white/10 bg-gray-50/50 dark:bg-dark-100/50">
                  <th class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5">
                    服务商
                  </th>
                  <th class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5">
                    邮箱账号
                  </th>
                  <th class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5">
                    发件人
                  </th>
                  <th class="text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5 w-20">
                    状态
                  </th>
                  <th class="text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5 w-28">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-white/5">
                <tr
                  v-for="config in configs"
                  :key="config.id"
                  :class="[
                    'hover:bg-gray-50/50 dark:hover:bg-dark-200/30 transition-colors',
                    config.is_active ? 'bg-primary/5' : ''
                  ]"
                >
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                      <div
                        class="w-6 h-6 rounded flex items-center justify-center text-white text-xs font-bold"
                        :class="getProviderBgColor(config.provider)"
                      >
                        {{ getProviderName(config.provider).charAt(0) }}
                      </div>
                      <span :class="['font-medium text-sm', getProviderColor(config.provider)]">
                        {{ getProviderName(config.provider) }}
                      </span>
                    </div>
                  </td>
                  <td class="px-4 py-3">
                    <span class="text-sm text-gray-900 dark:text-white">{{ config.smtp_user }}</span>
                  </td>
                  <td class="px-4 py-3">
                    <div class="text-sm text-gray-900 dark:text-white">
                      {{ config.from_name }}
                    </div>
                    <div class="text-xs text-gray-500">
                      {{ config.from_email }}
                    </div>
                  </td>
                  <td class="px-4 py-3 text-center">
                    <span
                      v-if="config.is_active"
                      class="px-2 py-0.5 text-xs rounded-full bg-green-500/20 text-green-400"
                    >
                      已激活
                    </span>
                    <span
                      v-else
                      class="px-2 py-0.5 text-xs rounded-full bg-gray-500/20 text-gray-400"
                    >
                      未激活
                    </span>
                  </td>
                  <td class="px-4 py-3 text-right">
                    <div class="flex items-center justify-end gap-1">
                      <button
                        v-if="!config.is_active"
                        class="px-2 py-1 text-xs text-green-400 hover:bg-green-500/10 rounded transition-colors"
                        @click="activateConfig(config)"
                      >
                        激活
                      </button>
                      <button
                        class="px-2 py-1 text-xs text-primary hover:bg-primary/10 rounded transition-colors"
                        @click="openEditModal(config)"
                      >
                        编辑
                      </button>
                      <button
                        class="px-2 py-1 text-xs text-red-400 hover:bg-red-500/10 rounded transition-colors"
                        @click="deleteConfig(config)"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="bg-white dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10 p-4">
          <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-3">
            发送测试邮件
          </h3>
          <div class="flex gap-2">
            <input
              v-model="testEmail"
              type="email"
              placeholder="输入测试邮箱地址"
              class="flex-1 px-3 py-2 text-sm bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-md text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary focus:outline-none"
            >
            <button
              :disabled="isTesting || !activeConfig"
              class="px-3 py-2 text-sm bg-gray-600 dark:bg-gray-700 text-white rounded-md hover:bg-gray-700 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
              @click="sendTestEmail"
            >
              {{ isTesting ? '发送中...' : '测试' }}
            </button>
          </div>
          <p
            v-if="!activeConfig"
            class="mt-2 text-xs text-yellow-500"
          >
            请先激活一个邮箱配置
          </p>
        </div>
      </div>

      <div
        v-else-if="activeTab === 'logs'"
        class="bg-white dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10 overflow-hidden"
      >
        <div class="px-4 py-3 border-b border-gray-200 dark:border-white/10 flex items-center gap-4">
          <select
            v-model="logsFilter.email_type"
            class="px-2 py-1 text-sm bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-md text-gray-900 dark:text-white"
            @change="logsPage = 1; loadLogs()"
          >
            <option value="">
              全部类型
            </option>
            <option value="verification">
              邮箱验证
            </option>
            <option value="test">
              测试邮件
            </option>
          </select>
          <select
            v-model="logsFilter.status"
            class="px-2 py-1 text-sm bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-md text-gray-900 dark:text-white"
            @change="logsPage = 1; loadLogs()"
          >
            <option value="">
              全部状态
            </option>
            <option value="sent">
              已发送
            </option>
            <option value="failed">
              发送失败
            </option>
            <option value="pending">
              待发送
            </option>
          </select>
        </div>

        <div
          v-if="isLoading"
          class="flex justify-center py-8"
        >
          <div class="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
        </div>

        <div
          v-else
          class="overflow-x-auto"
        >
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-200 dark:border-white/10 bg-gray-50/50 dark:bg-dark-100/50">
                <th class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5">
                  收件人
                </th>
                <th class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5">
                  类型
                </th>
                <th class="text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5 w-24">
                  状态
                </th>
                <th class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5">
                  时间
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-white/5">
              <tr
                v-for="log in logs"
                :key="log.id"
                class="hover:bg-gray-50/50 dark:hover:bg-dark-200/30 transition-colors"
              >
                <td class="px-4 py-3">
                  <span class="text-sm text-gray-900 dark:text-white">{{ log.recipient_email }}</span>
                </td>
                <td class="px-4 py-3">
                  <span class="text-sm text-gray-600 dark:text-gray-400">
                    {{ emailTypeLabels[log.email_type] || log.email_type }}
                  </span>
                </td>
                <td class="px-4 py-3 text-center">
                  <span :class="['px-2 py-0.5 text-xs rounded-full', statusColors[log.status]]">
                    {{ statusLabels[log.status] }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <span class="text-sm text-gray-500">{{ formatDate(log.created_at) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div
          v-if="logs.length > 0"
          class="px-4 py-3 border-t border-gray-200 dark:border-white/10 flex items-center justify-between"
        >
          <span class="text-xs text-gray-500">
            共 {{ logsTotal }} 条记录
          </span>
          <div class="flex items-center gap-1">
            <button
              v-for="page in totalPages"
              :key="page"
              :class="[
                'px-2 py-1 text-xs rounded transition-colors',
                logsPage === page
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-300'
              ]"
              @click="changePage(page)"
            >
              {{ page }}
            </button>
          </div>
        </div>
      </div>
    </template>

    <Teleport to="body">
      <div
        v-if="isEditing"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      >
        <div
          class="bg-white dark:bg-dark-100 rounded-xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-hidden"
          @click.stop
        >
          <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-white/10">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ editingConfig ? '编辑配置' : '添加配置' }}
            </h2>
            <button
              class="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-dark-200 transition-colors"
              @click="closeEditModal"
            >
              <svg
                class="w-4 h-4 text-gray-500"
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
            </button>
          </div>

          <div class="px-4 py-3 overflow-y-auto max-h-[calc(85vh-120px)]">
            <div class="space-y-4">
              <div>
                <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">
                  邮箱服务商 <span class="text-red-500">*</span>
                </label>
                <div class="grid grid-cols-2 gap-2">
                  <label
                    v-for="provider in smtpProviders"
                    :key="provider.id"
                    :class="[
                      'flex items-center gap-2 p-2.5 rounded-lg border cursor-pointer transition-all',
                      configForm.provider === provider.id
                        ? 'border-primary bg-primary/5'
                        : 'border-gray-200 dark:border-white/10 hover:border-primary/50'
                    ]"
                  >
                    <input
                      v-model="configForm.provider"
                      type="radio"
                      :value="provider.id"
                      class="w-3.5 h-3.5 text-primary"
                      :disabled="!!editingConfig"
                    >
                    <div>
                      <div :class="['font-medium text-sm', getProviderColor(provider.id)]">{{ provider.name }}</div>
                      <div
                        v-if="provider.host"
                        class="text-xs text-gray-500"
                      >{{ provider.host }}:{{ provider.port }}</div>
                    </div>
                  </label>
                </div>
              </div>

              <div class="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800/50">
                <div class="flex items-start gap-2">
                  <svg
                    class="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <div class="text-xs text-blue-700 dark:text-blue-400">
                    <div
                      v-if="configForm.provider === 'qq'"
                      class="space-y-0.5"
                    >
                      <p class="font-medium">
                        QQ邮箱授权码获取：
                      </p>
                      <p class="text-blue-200">
                        设置 → 账户 → 开启POP3/SMTP → 生成授权码
                      </p>
                    </div>
                    <div
                      v-else-if="configForm.provider === '163'"
                      class="space-y-0.5"
                    >
                      <p class="font-medium">
                        163邮箱授权码获取：
                      </p>
                      <p class="text-blue-200">
                        设置 → POP3/SMTP/IMAP → 获取授权密码
                      </p>
                    </div>
                    <div
                      v-else-if="configForm.provider === 'gmail'"
                      class="space-y-0.5"
                    >
                      <p class="font-medium">
                        Gmail应用密码获取：
                      </p>
                      <p class="text-blue-200">
                        开启两步验证 → myaccount.google.com/apppasswords
                      </p>
                    </div>
                    <div
                      v-else
                      class="space-y-0.5"
                    >
                      <p class="font-medium">
                        SMTP配置说明：
                      </p>
                      <p class="text-blue-200">
                        请填写邮箱服务商提供的SMTP账号和密码
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label
                    for="email-smtp-user"
                    class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1"
                  >
                    邮箱账号 <span class="text-red-500">*</span>
                  </label>
                  <input
                    id="email-smtp-user"
                    v-model="configForm.smtp_user"
                    type="text"
                    name="smtp-user"
                    autocomplete="email"
                    :placeholder="configForm.provider === 'qq' ? 'QQ邮箱' : '邮箱地址'"
                    class="w-full px-2.5 py-1.5 text-sm rounded-md border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white focus:ring-1 focus:ring-primary/50 focus:border-primary outline-none"
                  >
                </div>
                <div>
                  <label
                    for="email-smtp-password"
                    class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1"
                  >
                    {{ configForm.provider === 'qq' ? '授权码' : '密码' }} <span
                      v-if="!editingConfig"
                      class="text-red-500"
                    >*</span>
                  </label>
                  <input
                    id="email-smtp-password"
                    v-model="configForm.smtp_password"
                    type="password"
                    name="smtp-password"
                    autocomplete="new-password"
                    :placeholder="editingConfig ? '留空保持原值' : '授权码/密码'"
                    class="w-full px-2.5 py-1.5 text-sm rounded-md border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white focus:ring-1 focus:ring-primary/50 focus:border-primary outline-none"
                  >
                </div>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label
                    for="email-from-email"
                    class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1"
                  >
                    发件人邮箱 <span class="text-red-500">*</span>
                  </label>
                  <input
                    id="email-from-email"
                    v-model="configForm.from_email"
                    type="email"
                    name="from-email"
                    autocomplete="email"
                    placeholder="发件人邮箱"
                    class="w-full px-2.5 py-1.5 text-sm rounded-md border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white focus:ring-1 focus:ring-primary/50 focus:border-primary outline-none"
                  >
                </div>
                <div>
                  <label
                    for="email-from-name"
                    class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1"
                  >
                    发件人名称
                  </label>
                  <input
                    id="email-from-name"
                    v-model="configForm.from_name"
                    type="text"
                    name="from-name"
                    placeholder="显示名称"
                    class="w-full px-2.5 py-1.5 text-sm rounded-md border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white focus:ring-1 focus:ring-primary/50 focus:border-primary outline-none"
                  >
                </div>
              </div>
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 px-4 py-3 border-t border-gray-200 dark:border-white/10 bg-gray-50/50 dark:bg-dark-100/30">
            <button
              type="button"
              class="px-3 py-1.5 text-sm rounded-md border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-200 transition-colors"
              @click="closeEditModal"
            >
              取消
            </button>
            <button
              :disabled="isSaving"
              class="px-3 py-1.5 text-sm rounded-md bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
              @click="saveConfig"
            >
              <div
                v-if="isSaving"
                class="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin"
              />
              {{ isSaving ? '保存中' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
