<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { emailApi, type EmailConfig, type EmailLog, type EmailStats, type EmailProvider, type ProviderStatus } from '@/api/email'
import { useDialogStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { useDeletionConfirm } from '@/composables/useDeletionConfirm'
import DeletionConfirmDialog from '@/components/common/DeletionConfirmDialog.vue'
import { formatDateTime } from '@/utils/date'
import DateRangePicker from '@/components/common/DateRangePicker.vue'

const dialog = useDialogStore()
const { requirePermission, hasPermission } = useAdminCheck()
const deletion = useDeletionConfirm()
const activeTab = ref<'config' | 'logs'>('config')

const canTest = computed(() => hasPermission('email.test'))

const configs = ref<EmailConfig[]>([])
const activeConfig = ref<EmailConfig | null>(null)
const providers = ref<EmailProvider[]>([])
const providerStatus = ref<ProviderStatus | null>(null)
const isLoading = ref(false)
const isInitialLoading = ref(true)
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
const testEmailError = ref('')
const testResendEmailError = ref('')
const configFormErrors = ref<Record<string, string>>({})

const logs = ref<EmailLog[]>([])
const logsPage = ref(1)
const logsTotal = ref(0)
const logsPageSize = ref(10)
const logsFilter = ref({
  email_type: '',
  status: '',
  recipient_email: '',
  start_date: '',
  end_date: ''
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
  test: '测试邮件',
  new_comment: '新评论通知',
  new_like: '新点赞通知',
  new_register: '新用户注册通知',
  reply_notification: '评论回复通知',
  comment_approved: '评论审核通过',
  password_reset: '密码重置',
  email_change: '邮箱更改',
  oauth_verification: 'OAuth验证',
  error_log: '错误日志'
}

const expandedLogs = ref<Set<number>>(new Set())

function toggleLogExpand(logId: number) {
  if (expandedLogs.value.has(logId)) {
    expandedLogs.value.delete(logId)
  } else {
    expandedLogs.value.add(logId)
  }
}

function isLogExpanded(logId: number) {
  return expandedLogs.value.has(logId)
}

onMounted(async () => {
  try {
    await Promise.all([
      loadProviders(),
      loadConfigs(),
      loadStats(),
      loadProviderStatus()
    ])
    window.addEventListener('keydown', handleKeydown)
  } finally {
    isInitialLoading.value = false
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
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
      status: logsFilter.value.status || undefined,
      recipient_email: logsFilter.value.recipient_email || undefined,
      start_date: logsFilter.value.start_date || undefined,
      end_date: logsFilter.value.end_date || undefined
    })
    logs.value = data.items
    logsTotal.value = data.total
  } catch (error: any) {
    if (error?.isCancel) {
      return
    }
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
  configFormErrors.value = {}
}

function closeEditModal() {
  isEditing.value = false
  resetForm()
}

async function openAddModal() {
  if (!await requirePermission('email.create', '创建邮箱配置')) return
  resetForm()
  isEditing.value = true
}

async function openEditModal(config: EmailConfig) {
  if (!await requirePermission('email.edit', '编辑邮箱配置')) return
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
  if (editingConfig.value) {
    if (!await requirePermission('email.edit', '编辑邮箱配置')) return
  } else {
    if (!await requirePermission('email.create', '创建邮箱配置')) return
  }
  
  configFormErrors.value = {}
  
  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  
  if (!configForm.value.smtp_user) {
    configFormErrors.value.smtp_user = '请填写邮箱账号'
  } else if (!emailPattern.test(configForm.value.smtp_user)) {
    configFormErrors.value.smtp_user = '请输入正确的邮箱格式'
  }
  if (!configForm.value.from_email) {
    configFormErrors.value.from_email = '请填写发件人邮箱'
  } else if (!emailPattern.test(configForm.value.from_email)) {
    configFormErrors.value.from_email = '请输入正确的邮箱格式'
  }
  if (!editingConfig.value && !configForm.value.smtp_password) {
    configFormErrors.value.smtp_password = '请填写密码/授权码'
  }
  
  if (Object.keys(configFormErrors.value).length > 0) {
    const fieldIdMap: Record<string, string> = {
      smtp_user: 'email-smtp-user',
      smtp_password: 'email-smtp-password',
      from_email: 'email-from-email'
    }
    for (const [field, id] of Object.entries(fieldIdMap)) {
      if (configFormErrors.value[field]) {
        const el = document.getElementById(id)
        if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); el.focus({ preventScroll: true }) }
        break
      }
    }
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
  if (!await requirePermission('email.activate', '激活邮箱配置')) return
  
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
  if (!await requirePermission('email.delete', '删除邮箱配置')) return
  
  const previewed = await deletion.requestDeletion('email_config', config.id, `${config.provider} - ${config.smtp_user}`)
  if (!previewed) return
}

const deletionLoading = ref(false)
async function executeDeletion() {
  try {
    deletionLoading.value = true
    const result = await emailApi.deleteConfig(deletion.currentItemId.value)
    deletion.confirmDeletion()
    await dialog.showSuccess('删除成功', '成功')
    if (result.was_active) {
      activeConfig.value = null
    }
    await loadConfigs()
    await loadProviderStatus()
  } catch (error: any) {
    console.error('Failed to delete email config:', error)
    deletion.cancelDeletion()
  } finally {
    deletionLoading.value = false
  }
}

async function sendTestEmail() {
  if (!await requirePermission('email.test', '发送测试邮件')) return
  
  testEmailError.value = ''
  
  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  
  if (!testEmail.value) {
    testEmailError.value = '请输入测试邮箱地址'
    return
  }
  if (!emailPattern.test(testEmail.value)) {
    testEmailError.value = '请输入正确的邮箱格式'
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
  if (!await requirePermission('email.test', '发送Resend测试邮件')) return
  
  testResendEmailError.value = ''
  
  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  
  if (!testResendEmail.value) {
    testResendEmailError.value = '请输入测试邮箱地址'
    return
  }
  if (!emailPattern.test(testResendEmail.value)) {
    testResendEmailError.value = '请输入正确的邮箱格式'
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
  if (!await requirePermission('email.switch_provider', '切换邮件服务商')) return
  
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

async function switchToLogs() {
  if (!await requirePermission('email.view_logs', '查看邮件日志')) return
  activeTab.value = 'logs'
  loadLogs()
}

function clearLogsFilters() {
  logsFilter.value = {
    email_type: '',
    status: '',
    recipient_email: '',
    start_date: '',
    end_date: ''
  }
  logsPage.value = 1
  loadLogs()
}

function formatDate(dateStr: string | null) {
  return formatDateTime(dateStr)
}

function changePage(page: number) {
  logsPage.value = page
  loadLogs()
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'ArrowLeft' && logsPage.value > 1) {
    event.preventDefault()
    changePage(logsPage.value - 1)
  } else if (event.key === 'ArrowRight' && logsPage.value < totalPages.value) {
    event.preventDefault()
    changePage(logsPage.value + 1)
  } else if (event.key === 'Delete') {
    event.preventDefault()
    clearLogsFilters()
  }
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
  <div class="space-y-4">
    <div class="flex items-center justify-between">
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
              d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          邮件服务
        </h1>
      </div>
      <div class="flex items-center gap-3">
        <div
          v-if="!isInitialLoading"
          class="hidden sm:flex items-center gap-3 text-xs"
        >
          <span class="text-gray-500">已发送: <strong class="text-green-400">{{ stats.total_sent }}</strong></span>
          <span class="text-gray-500">失败: <strong class="text-red-400">{{ stats.total_failed }}</strong></span>
          <span class="text-gray-500">验证率: <strong class="text-primary">{{ stats.verification_rate }}%</strong></span>
        </div>
        <div class="flex gap-1.5">
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
    </div>

    <div
      v-if="isInitialLoading"
      class="flex justify-center py-12"
    >
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>

    <div
      v-else-if="activeTab === 'config'"
      class="space-y-4"
    >
      <div class="glass-card overflow-hidden">
        <div class="px-4 py-2.5 border-b border-gray-200 dark:border-white/10 flex items-center justify-between">
          <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
            服务提供商
          </h2>
          <span
            v-if="providerStatus?.current_provider"
            class="text-xs text-gray-500"
          >
            当前: {{ getProviderName(providerStatus.current_provider) }}
          </span>
        </div>
        <div class="p-3">
          <div class="flex flex-wrap gap-2">
            <button
              v-for="provider in providers"
              :key="provider.id"
              :class="[
                'flex items-center gap-2 px-3 py-2 rounded-lg border transition-all',
                isProviderActive(provider.id)
                  ? 'border-primary bg-primary/5 ring-1 ring-primary'
                  : 'border-gray-200 dark:border-white/10 hover:border-primary/50'
              ]"
              :disabled="switchingProvider"
              @click="switchProvider(provider.id)"
            >
              <div
                class="w-5 h-5 rounded flex items-center justify-center text-white text-xs font-bold"
                :class="getProviderBgColor(provider.id)"
              >
                {{ provider.name.charAt(0) }}
              </div>
              <span :class="['font-medium text-sm', getProviderColor(provider.id)]">
                {{ provider.name }}
              </span>
              <span
                v-if="isProviderActive(provider.id)"
                class="px-1.5 py-0.5 text-xs rounded bg-green-500/20 text-green-400"
              >
                当前
              </span>
              <span
                v-if="provider.is_api && !providerStatus?.has_resend_api_key"
                class="px-1.5 py-0.5 text-xs rounded bg-red-500/20 text-red-400"
              >
                未配置
              </span>
            </button>
          </div>
        </div>
      </div>

      <div class="glass-card overflow-hidden">
        <div class="px-4 py-2.5 border-b border-gray-200 dark:border-white/10 flex items-center justify-between">
          <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
            SMTP 配置
          </h2>
          <button
            class="px-2.5 py-1 text-xs bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
            @click="openAddModal"
          >
            添加
          </button>
        </div>

        <div
          v-if="isLoading"
          class="flex justify-center py-6"
        >
          <div class="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
        </div>

        <div
          v-else-if="configs.length === 0"
          class="text-center py-6 text-gray-500 text-sm"
        >
          暂无配置，请添加邮箱配置
        </div>

        <div
          v-else
          class="divide-y divide-gray-200 dark:divide-white/5"
        >
          <div
            v-for="config in configs"
            :key="config.id"
            :class="[
              'flex items-center justify-between px-4 py-2.5 hover:bg-gray-50/50 dark:hover:bg-dark-200/30 transition-colors',
              config.is_active ? 'bg-primary/5' : ''
            ]"
          >
            <div class="flex items-center gap-3 flex-1 min-w-0">
              <div
                class="w-6 h-6 rounded flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                :class="getProviderBgColor(config.provider)"
              >
                {{ getProviderName(config.provider).charAt(0) }}
              </div>
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ config.smtp_user }}</span>
                  <span
                    v-if="config.is_active"
                    class="px-1.5 py-0.5 text-xs rounded bg-green-500/20 text-green-400 flex-shrink-0"
                  >
                    已激活
                  </span>
                </div>
                <div class="text-xs text-gray-500 truncate">
                  {{ config.from_name }} &lt;{{ config.from_email }}&gt;
                </div>
              </div>
            </div>
            <div class="flex items-center gap-1 flex-shrink-0">
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
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-if="!(providerStatus?.current_provider === 'resend' && providerStatus?.has_resend_api_key)"
          class="glass-card p-3"
        >
          <h3 class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
            SMTP 测试
          </h3>
          <form class="flex gap-2" @submit.prevent="sendTestEmail">
            <input id="input-testEmail"
              v-model="testEmail"
              type="email"
              name="test-email"
              placeholder="输入测试邮箱"
              :disabled="!canTest"
              :class="['flex-1 px-2.5 py-1.5 text-sm bg-gray-50 dark:bg-dark-200 border rounded-md text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none disabled:opacity-50', testEmailError ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-white/10']"
              @input="testEmailError = ''"
            >
            <button
              type="button"
              :disabled="isTesting || !activeConfig"
              class="px-3 py-1.5 text-sm bg-primary text-white rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
              @click="sendTestEmail"
            >
              {{ isTesting ? '发送中' : '测试' }}
            </button>
          </form>
          <p v-if="testEmailError" class="mt-1.5 text-xs text-red-500">{{ testEmailError }}</p>
          <p
            v-else-if="!activeConfig"
            class="mt-1.5 text-xs text-yellow-500"
          >
            请先激活一个配置
          </p>
        </div>

        <div
          v-if="providerStatus?.current_provider === 'resend' && providerStatus?.has_resend_api_key"
          class="glass-card p-3"
        >
          <h3 class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
            Resend 测试
          </h3>
          <form class="flex gap-2" @submit.prevent="sendResendTestEmail">
            <input id="input-testResendEmail"
              v-model="testResendEmail"
              type="email"
              name="test-resend-email"
              placeholder="输入测试邮箱"
              :disabled="!canTest"
              :class="['flex-1 px-2.5 py-1.5 text-sm bg-gray-50 dark:bg-dark-200 border rounded-md text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none disabled:opacity-50', testResendEmailError ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-white/10']"
              @input="testResendEmailError = ''"
            >
            <button
              :disabled="isTestingResend"
              class="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50"
              @click="sendResendTestEmail"
            >
              {{ isTestingResend ? '发送中' : '测试' }}
            </button>
          </form>
          <p v-if="testResendEmailError" class="mt-1.5 text-xs text-red-500">{{ testResendEmailError }}</p>
        </div>
      </div>
    </div>

    <div
      v-else-if="activeTab === 'logs'"
      class="glass-card overflow-hidden"
    >
      <form class="px-4 py-2.5 border-b border-gray-200 dark:border-white/10 flex items-center gap-3" @submit.prevent>
        <input
          id="input-logsFilter-recipient_email"
          v-model="logsFilter.recipient_email"
          type="text"
          placeholder="邮箱账号"
          class="px-2 py-1 text-xs bg-gray-50 dark:bg-dark-200 border border-gray-200 dark:border-white/10 rounded-md text-gray-900 dark:text-white"
          @keyup.enter="logsPage = 1; loadLogs()"
        >
        <select id="select-logsFilter-email_type"
          v-model="logsFilter.email_type"
          class="px-2 py-1 text-xs bg-gray-50 dark:bg-dark-200 border border-gray-200 dark:border-white/10 rounded-md text-gray-900 dark:text-white"
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
          <option value="new_comment">
            新评论通知
          </option>
          <option value="new_like">
            新点赞通知
          </option>
          <option value="new_register">
            新用户注册通知
          </option>
          <option value="reply_notification">
            评论回复通知
          </option>
          <option value="comment_approved">
            评论审核通过
          </option>
          <option value="password_reset">
            密码重置
          </option>
          <option value="email_change">
            邮箱更改
          </option>
          <option value="oauth_verification">
            OAuth验证
          </option>
          <option value="error_log">
            错误日志
          </option>
        </select>
        <select id="select-logsFilter-status"
          v-model="logsFilter.status"
          class="px-2 py-1 text-xs bg-gray-50 dark:bg-dark-200 border border-gray-200 dark:border-white/10 rounded-md text-gray-900 dark:text-white"
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
        <DateRangePicker
          v-model:start-date="logsFilter.start_date"
          v-model:end-date="logsFilter.end_date"
        />
        <button
          type="button"
          class="px-3 py-1.5 text-sm bg-red-500/10 text-red-500 dark:text-red-400 border border-red-500/20 dark:border-red-400/20 rounded-lg hover:bg-red-500/20 dark:hover:bg-red-400/20 transition-colors flex items-center gap-1.5"
          @click="clearLogsFilters"
        >
          <svg
            class="w-4 h-4"
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
          清除筛选
        </button>
        <button
          type="button"
          class="btn-primary text-sm px-4 py-1.5 flex items-center gap-1.5"
          @click="logsPage = 1; loadLogs()"
        >
          <svg
            class="w-4 h-4"
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
      </form>

      <div
        v-if="isLoading"
        class="flex justify-center py-6"
      >
        <div class="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>

      <div
        v-else-if="logs.length === 0"
        class="text-center py-6 text-gray-500 text-sm"
      >
        暂无日志记录
      </div>

      <div
        v-else
        class="divide-y divide-gray-200 dark:divide-white/5"
      >
        <div
          v-for="log in logs"
          :key="log.id"
          class="hover:bg-gray-50/50 dark:hover:bg-dark-200/30 transition-colors"
        >
          <div
            class="flex items-start justify-between px-4 py-2.5 cursor-pointer"
            @click="toggleLogExpand(log.id)"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ log.recipient_email }}</span>
                <span :class="['px-1.5 py-0.5 text-xs rounded-full', statusColors[log.status]]">
                  {{ statusLabels[log.status] }}
                </span>
                <span class="px-1.5 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                  {{ emailTypeLabels[log.email_type] || log.email_type }}
                </span>
                <span
                  v-if="log.is_verified"
                  class="px-1.5 py-0.5 text-xs rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
                >
                  已验证
                </span>
              </div>
              <div
                v-if="log.subject"
                class="text-xs text-gray-600 dark:text-gray-400 mt-1 truncate"
              >
                {{ log.subject }}
              </div>
              <div class="text-xs text-gray-500 mt-1">
                {{ formatDate(log.created_at) }}
                <span v-if="log.sent_at"> · 发送于 {{ formatDate(log.sent_at) }}</span>
              </div>
            </div>
            <svg
              :class="[
                'w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ml-2 mt-1',
                isLogExpanded(log.id) ? 'rotate-180' : ''
              ]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </div>
          <div
            v-if="isLogExpanded(log.id)"
            class="px-4 pb-3 space-y-2"
          >
            <div
              v-if="log.error_message"
              class="p-2.5 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800/30"
            >
              <div class="flex items-start gap-2">
                <svg
                  class="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-medium text-red-700 dark:text-red-400">
                    错误信息
                  </p>
                  <p class="text-xs text-red-600 dark:text-red-300 mt-0.5 break-all">
                    {{ log.error_message }}
                  </p>
                </div>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div class="p-2 bg-gray-50 dark:bg-dark-200 rounded">
                <span class="text-gray-500">收件人名称：</span>
                <span class="text-gray-700 dark:text-gray-300">{{ log.recipient_name || '-' }}</span>
              </div>
              <div class="p-2 bg-gray-50 dark:bg-dark-200 rounded">
                <span class="text-gray-500">验证状态：</span>
                <span class="text-gray-700 dark:text-gray-300">{{ log.is_verified ? '已验证' : '未验证' }}</span>
              </div>
              <div
                v-if="log.verified_at"
                class="p-2 bg-gray-50 dark:bg-dark-200 rounded"
              >
                <span class="text-gray-500">验证时间：</span>
                <span class="text-gray-700 dark:text-gray-300">{{ formatDate(log.verified_at) }}</span>
              </div>
              <div
                v-if="log.user_id"
                class="p-2 bg-gray-50 dark:bg-dark-200 rounded"
              >
                <span class="text-gray-500">用户ID：</span>
                <span class="text-gray-700 dark:text-gray-300">{{ log.user_id }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="logs.length > 0"
        class="px-4 py-2.5 border-t border-gray-200 dark:border-white/10 flex items-center justify-between"
      >
        <span class="text-xs text-gray-500">
          共 {{ logsTotal }} 条
        </span>
        <div class="flex items-center gap-1">
          <button
            v-for="page in totalPages"
            :key="page"
            :class="[
              'px-2 py-1 text-xs rounded transition-colors',
              logsPage === page
                ? 'bg-primary text-white'
                : 'bg-gray-100 dark:bg-dark-200 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-300'
            ]"
            @click="changePage(page)"
          >
            {{ page }}
          </button>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="isEditing"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      >
        <div
          class="glass-card shadow-2xl w-full max-w-lg max-h-[85vh] overflow-hidden"
          @click.stop
        >
          <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-white/10">
            <h2 class="text-base font-semibold text-gray-900 dark:text-white">
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
            <form
              class="space-y-3"
              @submit.prevent="saveConfig"
            >
              <div>
                <label for="email-provider-helper" class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">
                  邮箱服务商 <span class="text-red-500">*</span>
                </label>
                <input id="email-provider-helper" type="text" class="sr-only" :value="configForm.provider" tabindex="-1" readonly autocomplete="off">
                <div class="grid grid-cols-2 gap-2">
                  <label
                    v-for="provider in smtpProviders"
                    :key="provider.id"
                    :class="[
                      'flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-all',
                      configForm.provider === provider.id
                        ? 'border-primary bg-primary/5'
                        : 'border-gray-200 dark:border-white/10 hover:border-primary/50'
                    ]"
                  >
                    <input :id="`smtp-provider-${provider.id}`"
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

              <div class="p-2.5 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800/50">
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
                    class="w-full px-2.5 py-1.5 text-sm rounded-md border bg-white dark:bg-dark-200 text-gray-900 dark:text-white outline-none"
                    :class="configFormErrors.smtp_user ? 'border-red-500 dark:border-red-500' : 'border-gray-200 dark:border-white/10'"
                    @input="delete configFormErrors.smtp_user"
                  >
                  <p
                    v-if="configFormErrors.smtp_user"
                    class="mt-1 text-xs text-red-500"
                  >
                    {{ configFormErrors.smtp_user }}
                  </p>
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
                    class="w-full px-2.5 py-1.5 text-sm rounded-md border bg-white dark:bg-dark-200 text-gray-900 dark:text-white outline-none"
                    :class="configFormErrors.smtp_password ? 'border-red-500 dark:border-red-500' : 'border-gray-200 dark:border-white/10'"
                    @input="delete configFormErrors.smtp_password"
                  >
                  <p
                    v-if="configFormErrors.smtp_password"
                    class="mt-1 text-xs text-red-500"
                  >
                    {{ configFormErrors.smtp_password }}
                  </p>
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
                    class="w-full px-2.5 py-1.5 text-sm rounded-md border bg-white dark:bg-dark-200 text-gray-900 dark:text-white outline-none"
                    :class="configFormErrors.from_email ? 'border-red-500 dark:border-red-500' : 'border-gray-200 dark:border-white/10'"
                    @input="delete configFormErrors.from_email"
                  >
                  <p
                    v-if="configFormErrors.from_email"
                    class="mt-1 text-xs text-red-500"
                  >
                    {{ configFormErrors.from_email }}
                  </p>
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
                    class="w-full px-2.5 py-1.5 text-sm rounded-md border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-200 text-gray-900 dark:text-white outline-none"
                  >
                </div>
              </div>
            </form>
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
              class="btn-primary text-sm px-4 py-1.5"
              @click="saveConfig"
            >
              <span v-if="isSaving" class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                保存中...
              </span>
              <span v-else>保存</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <DeletionConfirmDialog
      :visible="deletion.showDeletionDialog.value"
      :preview="deletion.deletionPreview.value"
      :loading="deletionLoading"
      @confirm="executeDeletion"
      @cancel="deletion.cancelDeletion()"
    />
  </div>
</template>
