<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { oauthApi } from '@/api/oauth'
import type { OAuthProviderResponse, OAuthProviderDetail, OAuthProviderUpdate } from '@/api/oauth'
import { useDialogStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'

const dialog = useDialogStore()
const { requirePermission, hasPermission } = useAdminCheck()
const canEdit = computed(() => hasPermission('oauth.edit'))
const currentScopeOptions = computed(() => {
  if (!editingProvider.value) return []
  return scopeOptions[editingProvider.value.name] || []
})
const providers = ref<OAuthProviderResponse[]>([])
const isLoading = ref(true)
const savingId = ref<number | null>(null)
const editingProvider = ref<OAuthProviderDetail | null>(null)
const isEditing = ref(false)
const isSaving = ref(false)

const form = ref<OAuthProviderUpdate>({
  display_name: '',
  client_id: '',
  client_secret: '',
  redirect_uri: '',
  authorize_url: '',
  token_url: '',
  userinfo_url: '',
  scope: '',
  is_enabled: false,
  show_on_login: true
})

const defaultConfigs: Record<string, { authorize_url: string; token_url: string; userinfo_url: string; scope: string }> = {
  google: {
    authorize_url: 'https://accounts.google.com/o/oauth2/v2/auth',
    token_url: 'https://oauth2.googleapis.com/token',
    userinfo_url: 'https://www.googleapis.com/oauth2/v2/userinfo',
    scope: 'openid profile'
  },
  github: {
    authorize_url: 'https://github.com/login/oauth/authorize',
    token_url: 'https://github.com/login/oauth/access_token',
    userinfo_url: 'https://api.github.com/user',
    scope: 'read:user user:email'
  },
  x: {
    authorize_url: 'https://twitter.com/i/oauth2/authorize',
    token_url: 'https://api.twitter.com/2/oauth2/token',
    userinfo_url: 'https://api.twitter.com/2/users/me',
    scope: 'users.read tweet.read offline.access'
  },
  wechat: {
    authorize_url: 'https://open.weixin.qq.com/connect/qrconnect',
    token_url: 'https://api.weixin.qq.com/sns/oauth2/access_token',
    userinfo_url: 'https://api.weixin.qq.com/sns/userinfo',
    scope: 'snsapi_userinfo'
  },
  qq: {
    authorize_url: 'https://graph.qq.com/oauth2.0/authorize',
    token_url: 'https://graph.qq.com/oauth2.0/token',
    userinfo_url: 'https://graph.qq.com/user/get_user_info',
    scope: 'get_user_info'
  }
}

const scopeOptions: Record<string, { label: string; value: string }[]> = {
  google: [
    { label: 'openid profile（默认）', value: 'openid profile' },
    { label: 'openid email profile', value: 'openid email profile' },
    { label: 'openid email', value: 'openid email' },
  ],
  github: [
    { label: 'read:user user:email（默认）', value: 'read:user user:email' },
    { label: 'read:user', value: 'read:user' },
    { label: 'user:email', value: 'user:email' },
  ],
  x: [
    { label: 'users.read tweet.read offline.access（默认）', value: 'users.read tweet.read offline.access' },
    { label: 'tweet.read users.read', value: 'tweet.read users.read' },
    { label: 'users.read offline.access', value: 'users.read offline.access' },
  ],
  wechat: [
    { label: 'snsapi_userinfo（默认）', value: 'snsapi_userinfo' },
    { label: 'snsapi_login', value: 'snsapi_login' },
  ],
  qq: [
    { label: 'get_user_info（默认）', value: 'get_user_info' },
  ],
}

const fetchProviders = async () => {
  isLoading.value = true
  try {
    providers.value = await oauthApi.getProviders()
  } catch (error) {
    console.error('Failed to fetch OAuth providers:', error)
  } finally {
    isLoading.value = false
  }
}

const openEditModal = async (provider: OAuthProviderResponse) => {
  if (!await requirePermission('oauth.edit', '编辑OAuth配置')) return
  
  try {
    const detail = await oauthApi.getProvider(provider.id)
    editingProvider.value = detail
    form.value = {
      display_name: detail.display_name,
      client_id: detail.client_id || '',
      client_secret: '',
      redirect_uri: detail.redirect_uri || '',
      authorize_url: detail.authorize_url || '',
      token_url: detail.token_url || '',
      userinfo_url: detail.userinfo_url || '',
      scope: detail.scope || '',
      is_enabled: detail.is_enabled,
      show_on_login: detail.show_on_login
    }
    isEditing.value = true
  } catch (error) {
    console.error('Failed to fetch provider details:', error)
    await dialog.showError('获取配置详情失败', '错误')
  }
}

const closeEditModal = () => {
  isEditing.value = false
  editingProvider.value = null
  form.value = {
    display_name: '',
    client_id: '',
    client_secret: '',
    redirect_uri: '',
    authorize_url: '',
    token_url: '',
    userinfo_url: '',
    scope: '',
    is_enabled: false,
    show_on_login: true
  }
  formErrors.value = {
    display_name: '',
    client_id: '',
    redirect_uri: '',
    authorize_url: '',
    token_url: '',
    userinfo_url: '',
    scope: ''
  }
}

const applyDefaultConfig = () => {
  if (!editingProvider.value) return
  const defaults = defaultConfigs[editingProvider.value.name]
  if (defaults) {
    form.value.authorize_url = defaults.authorize_url
    form.value.token_url = defaults.token_url
    form.value.userinfo_url = defaults.userinfo_url
    form.value.scope = defaults.scope
  }
}

const formErrors = ref({
  display_name: '',
  client_id: '',
  redirect_uri: '',
  authorize_url: '',
  token_url: '',
  userinfo_url: '',
  scope: ''
})

const validateForm = (): boolean => {
  formErrors.value = {
    display_name: '',
    client_id: '',
    redirect_uri: '',
    authorize_url: '',
    token_url: '',
    userinfo_url: '',
    scope: ''
  }
  
  let isValid = true
  
  if (!form.value.display_name?.trim()) {
    formErrors.value.display_name = '请输入显示名称'
    isValid = false
  }
  
  if (!form.value.client_id?.trim()) {
    formErrors.value.client_id = '请输入客户端ID'
    isValid = false
  }
  
  if (!form.value.redirect_uri?.trim()) {
    formErrors.value.redirect_uri = '请输入回调地址'
    isValid = false
  } else if (!form.value.redirect_uri.startsWith('http')) {
    formErrors.value.redirect_uri = '回调地址必须以 http 或 https 开头'
    isValid = false
  }
  
  if (!form.value.authorize_url?.trim()) {
    formErrors.value.authorize_url = '请输入授权地址'
    isValid = false
  } else if (!form.value.authorize_url.startsWith('http')) {
    formErrors.value.authorize_url = '授权地址必须以 http 或 https 开头'
    isValid = false
  }
  
  if (!form.value.token_url?.trim()) {
    formErrors.value.token_url = '请输入令牌地址'
    isValid = false
  } else if (!form.value.token_url.startsWith('http')) {
    formErrors.value.token_url = '令牌地址必须以 http 或 https 开头'
    isValid = false
  }
  
  if (!form.value.userinfo_url?.trim()) {
    formErrors.value.userinfo_url = '请输入用户信息地址'
    isValid = false
  } else if (!form.value.userinfo_url.startsWith('http')) {
    formErrors.value.userinfo_url = '用户信息地址必须以 http 或 https 开头'
    isValid = false
  }
  
  if (!form.value.scope) {
    formErrors.value.scope = '请选择授权范围'
    isValid = false
  }
  
  return isValid
}

const saveConfig = async () => {
  if (!await requirePermission('oauth.edit', '保存OAuth配置')) return
  
  if (!editingProvider.value) return
  
  if (!validateForm()) return
  
  isSaving.value = true
  try {
    const updateData: OAuthProviderUpdate = { ...form.value }
    if (!updateData.client_secret) {
      delete updateData.client_secret
    }
    await oauthApi.updateProvider(editingProvider.value.id, updateData)
    await dialog.showSuccess('配置保存成功', '成功')
    await fetchProviders()
    closeEditModal()
  } catch (error: any) {
    console.error('Failed to save config:', error)
    const errorMessage = error.response?.data?.detail || '保存配置失败'
    await dialog.showError(errorMessage, '错误')
  } finally {
    isSaving.value = false
  }
}

const toggleShowOnLogin = async (provider: OAuthProviderResponse) => {
  if (!await requirePermission('oauth.edit', '修改登录页显示设置')) return
  
  if (savingId.value) return
  savingId.value = provider.id
  try {
    await oauthApi.updateProvider(provider.id, { show_on_login: !provider.show_on_login })
    provider.show_on_login = !provider.show_on_login
  } catch (error) {
    console.error('Failed to toggle show on login:', error)
  } finally {
    savingId.value = null
  }
}

const toggleEnabled = async (provider: OAuthProviderResponse) => {
  if (!await requirePermission('oauth.edit', '启用/禁用OAuth提供商')) return
  
  if (savingId.value) return
  savingId.value = provider.id
  try {
    await oauthApi.updateProvider(provider.id, { is_enabled: !provider.is_enabled })
    provider.is_enabled = !provider.is_enabled
  } catch (error) {
    console.error('Failed to toggle enabled:', error)
  } finally {
    savingId.value = null
  }
}

const getProviderIcon = (icon: string | null) => {
  const icons: Record<string, string> = {
    google: `<path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>`,
    github: `<path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>`,
    twitter: `<path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>`,
    x: `<path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>`,
    wechat: `<path d="M8.5 3.5C4.36 3.5 1 6.19 1 9.5c0 1.84 1.06 3.48 2.71 4.57-.12.42-.44 1.52-.5 1.76-.08.31.11.31.24.22.1-.07 1.47-.96 2.07-1.35.62.12 1.27.19 1.98.19.26 0 .51-.01.76-.03-.16-.48-.25-.99-.25-1.52 0-2.85 2.77-5.16 6.19-5.16.26 0 .52.02.77.04C14.54 5.21 11.83 3.5 8.5 3.5zm-2.25 3c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm4.5 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1z"/><path d="M23 14.5c0-2.76-2.69-5-6-5s-6 2.24-6 5 2.69 5 6 5c.55 0 1.08-.06 1.58-.17.48.32 1.58 1.03 1.67 1.09.11.07.26.07.19-.18-.05-.19-.31-1.07-.4-1.41C21.89 17.99 23 16.38 23 14.5zm-8-.75c-.41 0-.75-.34-.75-.75s.34-.75.75-.75.75.34.75.75-.34.75-.75.75zm4 0c-.41 0-.75-.34-.75-.75s.34-.75.75-.75.75.34.75.75-.34.75-.75.75z"/>`,
    qq: `<path d="M12.003 2c-2.265 0-6.29 1.364-6.29 7.325v1.195S3.55 14.96 3.55 17.474c0 .665.17 1.025.281 1.025.114 0 .902-.484 1.748-2.072 0 0-.18 2.197 1.904 3.967 0 0-1.77.495-1.77 1.182 0 .686 4.078.43 6.29.43 2.212 0 6.29.256 6.29-.43 0-.687-1.77-1.182-1.77-1.182 2.085-1.77 1.905-3.967 1.905-3.967.845 1.588 1.634 2.072 1.746 2.072.111 0 .283-.36.283-1.025 0-2.514-2.166-6.954-2.166-6.954V9.325C18.29 3.364 14.268 2 12.003 2z"/>`
  }
  
  if (!icon) {
    return `<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>`
  }
  
  const lowerIcon = icon.toLowerCase()
  if (icons[lowerIcon]) {
    return icons[lowerIcon]
  }
  
  if (/^[MmLlHhVvCcSsQqTtAaZz]/.test(icon.trim())) {
    return `<path d="${icon}"/>`
  }
  
  return `<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>`
}

const getProviderBgColor = (name: string) => {
  switch (name) {
    case 'google':
      return 'bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10'
    case 'github':
      return 'bg-gray-900 dark:bg-gray-800'
    case 'x':
    case 'twitter':
      return 'bg-black dark:bg-dark-100'
    case 'wechat':
      return 'bg-[#07C160]'
    case 'qq':
      return 'bg-[#12B7F5]'
    default:
      return 'bg-gray-100 dark:bg-dark-100'
  }
}

onMounted(fetchProviders)
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
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          OAuth授权
        </h1>
      </div>
    </div>

    <div
      v-if="isLoading"
      class="flex justify-center py-8"
    >
      <div class="w-6 h-6 border-3 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <div
      v-else
      class="bg-white dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10 overflow-hidden"
    >
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-200 dark:border-white/10 bg-gray-50/50 dark:bg-dark-100/50">
              <th class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5 w-48">
                平台
              </th>
              <th class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5">
                状态
              </th>
              <th class="text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5 w-28">
                登录页显示
              </th>
              <th class="text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5 w-24">
                启用
              </th>
              <th class="text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider px-4 py-2.5 w-20">
                操作
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-white/5">
            <tr
              v-for="provider in providers"
              :key="provider.id"
              class="hover:bg-gray-50/50 dark:hover:bg-dark-200/30 transition-colors"
            >
              <td class="px-4 py-3">
                <div class="flex items-center gap-2.5">
                  <div
                    class="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0"
                    :class="getProviderBgColor(provider.name)"
                  >
                    <svg
                      class="w-5 h-5"
                      :class="provider.name === 'google' ? '' : 'text-white'"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                      v-html="getProviderIcon(provider.icon)"
                    />
                  </div>
                  <div>
                    <div class="font-medium text-gray-900 dark:text-white text-sm">
                      {{ provider.display_name }}
                    </div>
                    <div class="text-xs text-gray-400 dark:text-gray-500">
                      {{ provider.name }}
                    </div>
                  </div>
                </div>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <span
                    :class="[
                      'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                      provider.is_configured
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'
                    ]"
                  >
                    {{ provider.is_configured ? '已配置' : '未配置' }}
                  </span>
                  <span
                    v-if="!provider.is_configured && provider.show_on_login"
                    class="text-xs text-yellow-600 dark:text-yellow-400"
                  >
                    需配置
                  </span>
                </div>
              </td>
              <td class="px-4 py-3 text-center">
                <button
                  :disabled="savingId === provider.id"
                  :class="[
                    'relative inline-flex h-4 w-7 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30',
                    provider.show_on_login ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'
                  ]"
                  @click="toggleShowOnLogin(provider)"
                >
                  <span
                    :class="[
                      'inline-block h-3 w-3 transform rounded-full bg-white shadow-sm transition-transform',
                      provider.show_on_login ? 'translate-x-3.5' : 'translate-x-0.5'
                    ]"
                  />
                </button>
              </td>
              <td class="px-4 py-3 text-center">
                <button
                  :disabled="savingId === provider.id"
                  :class="[
                    'relative inline-flex h-4 w-7 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30',
                    provider.is_enabled ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'
                  ]"
                  @click="toggleEnabled(provider)"
                >
                  <span
                    :class="[
                      'inline-block h-3 w-3 transform rounded-full bg-white shadow-sm transition-transform',
                      provider.is_enabled ? 'translate-x-3.5' : 'translate-x-0.5'
                    ]"
                  />
                </button>
              </td>
              <td class="px-4 py-3 text-right">
                <button
                  class="text-sm text-primary hover:text-primary/80 transition-colors font-medium"
                  @click="openEditModal(provider)"
                >
                  配置
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="isEditing"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      >
        <div
          class="bg-white dark:bg-dark-100 rounded-xl shadow-2xl w-full max-w-xl max-h-[85vh] overflow-hidden"
          @click.stop
        >
          <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-white/10">
            <div class="flex items-center gap-2.5">
              <div
                class="w-7 h-7 rounded-md flex items-center justify-center"
                :class="getProviderBgColor(editingProvider?.name || '')"
              >
                <svg
                  class="w-4 h-4"
                  :class="editingProvider?.name === 'google' ? '' : 'text-white'"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  v-html="getProviderIcon(editingProvider?.icon || null)"
                />
              </div>
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
                配置 {{ editingProvider?.display_name }}
              </h2>
            </div>
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
              <div class="p-2.5 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800/50">
                <p class="text-xs text-blue-700 dark:text-blue-400">
                  前往 {{ editingProvider?.display_name }} 开发者平台创建 OAuth 应用获取凭证
                </p>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label
                    for="oauth-display-name"
                    class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1"
                  >显示名称 <span class="text-red-500">*</span></label>
                  <input
                    id="oauth-display-name"
                    v-model="form.display_name"
                    type="text"
                    name="display-name"
                    autocomplete="off"
                    :disabled="!canEdit"
                    :class="['w-full px-2.5 py-1.5 text-sm rounded-md border bg-white dark:bg-dark-100 text-gray-900 dark:text-white focus:ring-1 focus:ring-primary/50 focus:border-primary outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed', formErrors.display_name ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-white/10']"
                  >
                  <p v-if="formErrors.display_name" class="mt-1 text-xs text-red-500">{{ formErrors.display_name }}</p>
                </div>
                <div>
                  <label
                    for="oauth-scope"
                    class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1"
                  >授权范围 <span class="text-red-500">*</span></label>
                  <select
                    id="oauth-scope"
                    v-model="form.scope"
                    name="scope"
                    :disabled="!canEdit"
                    :class="['w-full px-2.5 py-1.5 text-sm rounded-md border bg-white dark:bg-dark-100 text-gray-900 dark:text-white focus:ring-1 focus:ring-primary/50 focus:border-primary outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed', formErrors.scope ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-white/10']"
                  >
                    <option value="" disabled>请选择授权范围</option>
                    <option v-for="opt in currentScopeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                  </select>
                  <p v-if="formErrors.scope" class="mt-1 text-xs text-red-500">{{ formErrors.scope }}</p>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label
                    for="oauth-client-id"
                    class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1"
                  >
                    Client ID <span class="text-red-500">*</span>
                  </label>
                  <input
                    id="oauth-client-id"
                    v-model="form.client_id"
                    type="text"
                    name="client-id"
                    autocomplete="off"
                    :disabled="!canEdit"
                    :class="['w-full px-2.5 py-1.5 text-sm rounded-md border bg-white dark:bg-dark-100 text-gray-900 dark:text-white focus:ring-1 focus:ring-primary/50 focus:border-primary outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed', formErrors.client_id ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-white/10']"
                  >
                  <p v-if="formErrors.client_id" class="mt-1 text-xs text-red-500">{{ formErrors.client_id }}</p>
                </div>
                <div>
                  <label
                    for="oauth-client-secret"
                    class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1"
                  >
                    Client Secret
                  </label>
                  <input
                    id="oauth-client-secret"
                    v-model="form.client_secret"
                    type="password"
                    name="client-secret"
                    autocomplete="new-password"
                    :disabled="!canEdit"
                    class="w-full px-2.5 py-1.5 text-sm rounded-md border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white focus:ring-1 focus:ring-primary/50 focus:border-primary outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    placeholder="留空保持原值"
                  >
                </div>
              </div>

              <div>
                <label
                  for="oauth-redirect-uri"
                  class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1"
                >
                  回调地址 <span class="text-red-500">*</span>
                </label>
                <input
                    id="oauth-redirect-uri"
                    v-model="form.redirect_uri"
                    type="text"
                    name="redirect-uri"
                    autocomplete="url"
                  :disabled="!canEdit"
                  :class="['w-full px-2.5 py-1.5 text-sm rounded-md border bg-white dark:bg-dark-100 text-gray-900 dark:text-white focus:ring-1 focus:ring-primary/50 focus:border-primary outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed', formErrors.redirect_uri ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-white/10']"
                  placeholder="http://localhost:3001/oauth/callback/{provider}"
                >
                <p v-if="formErrors.redirect_uri" class="mt-1 text-xs text-red-500">{{ formErrors.redirect_uri }}</p>
              </div>

              <div class="border-t border-gray-200 dark:border-white/10 pt-3">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs font-medium text-gray-600 dark:text-gray-400">高级配置</span>
                  <button
                    v-if="defaultConfigs[editingProvider?.name || '']"
                    type="button"
                    class="text-xs text-primary hover:text-primary/80 transition-colors"
                    @click="applyDefaultConfig"
                  >
                    应用默认值
                  </button>
                </div>
                <div class="space-y-2">
                  <div class="grid grid-cols-3 gap-2">
                    <div>
                      <label
                        for="oauth-authorize-url"
                        class="block text-xs text-gray-500 dark:text-gray-500 mb-0.5"
                      >授权端点 <span class="text-red-500">*</span></label>
                      <input
                        id="oauth-authorize-url"
                        v-model="form.authorize_url"
                        type="text"
                        name="authorize-url"
                        autocomplete="url"
                        :disabled="!canEdit"
                        :class="['w-full px-2 py-1 text-xs rounded border bg-white dark:bg-dark-100 text-gray-900 dark:text-white focus:ring-1 focus:ring-primary/50 focus:border-primary outline-none disabled:opacity-50 disabled:cursor-not-allowed', formErrors.authorize_url ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-white/10']"
                      >
                      <p v-if="formErrors.authorize_url" class="mt-0.5 text-xs text-red-500">{{ formErrors.authorize_url }}</p>
                    </div>
                    <div>
                      <label
                        for="oauth-token-url"
                        class="block text-xs text-gray-500 dark:text-gray-500 mb-0.5"
                      >令牌端点 <span class="text-red-500">*</span></label>
                      <input
                        id="oauth-token-url"
                        v-model="form.token_url"
                        type="text"
                        name="token-url"
                        autocomplete="url"
                        :disabled="!canEdit"
                        :class="['w-full px-2 py-1 text-xs rounded border bg-white dark:bg-dark-100 text-gray-900 dark:text-white focus:ring-1 focus:ring-primary/50 focus:border-primary outline-none disabled:opacity-50 disabled:cursor-not-allowed', formErrors.token_url ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-white/10']"
                      >
                      <p v-if="formErrors.token_url" class="mt-0.5 text-xs text-red-500">{{ formErrors.token_url }}</p>
                    </div>
                    <div>
                      <label
                        for="oauth-userinfo-url"
                        class="block text-xs text-gray-500 dark:text-gray-500 mb-0.5"
                      >用户信息端点 <span class="text-red-500">*</span></label>
                      <input
                        id="oauth-userinfo-url"
                        v-model="form.userinfo_url"
                        type="text"
                        name="userinfo-url"
                        autocomplete="url"
                        :disabled="!canEdit"
                        :class="['w-full px-2 py-1 text-xs rounded border bg-white dark:bg-dark-100 text-gray-900 dark:text-white focus:ring-1 focus:ring-primary/50 focus:border-primary outline-none disabled:opacity-50 disabled:cursor-not-allowed', formErrors.userinfo_url ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-white/10']"
                      >
                      <p v-if="formErrors.userinfo_url" class="mt-0.5 text-xs text-red-500">{{ formErrors.userinfo_url }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div class="flex items-center gap-5 pt-1">
                <label :class="['flex items-center gap-1.5', canEdit ? 'cursor-pointer' : 'cursor-not-allowed opacity-50']">
                  <input id="input-form-show_on_login"
                    v-model="form.show_on_login"
                    type="checkbox"
                    :disabled="!canEdit"
                    class="w-3.5 h-3.5 rounded border-gray-300 text-primary focus:ring-primary"
                  >
                  <span class="text-xs text-gray-600 dark:text-gray-400">登录页显示</span>
                </label>
                <label :class="['flex items-center gap-1.5', canEdit ? 'cursor-pointer' : 'cursor-not-allowed opacity-50']">
                  <input id="input-form-is_enabled"
                    v-model="form.is_enabled"
                    type="checkbox"
                    :disabled="!canEdit"
                    class="w-3.5 h-3.5 rounded border-gray-300 text-primary focus:ring-primary"
                  >
                  <span class="text-xs text-gray-600 dark:text-gray-400">启用</span>
                </label>
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
              :disabled="isSaving || !canEdit"
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
