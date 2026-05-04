<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { notificationApi, type NotificationSettings } from '@/api/notifications'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { useDialogStore } from '@/stores'

const { requirePermission } = useAdminCheck()
const dialog = useDialogStore()

const settings = ref<NotificationSettings | null>(null)
const isLoading = ref(false)
const isSaving = ref(false)

const settingsForm = ref({
  notify_on_register: true,
  notify_on_comment: true,
  notify_on_like: true,
  notify_on_reply: true
})

const settingLabels: Record<string, string> = {
  notify_on_register: '新用户注册通知',
  notify_on_comment: '新评论通知',
  notify_on_like: '新点赞通知',
  notify_on_reply: '评论回复通知'
}

const notificationOptions = [
  { 
    key: 'notify_on_register' as const, 
    label: '新用户注册', 
    description: '当有新用户注册时，发送邮件通知管理员',
    icon: 'M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z'
  },
  { 
    key: 'notify_on_comment' as const, 
    label: '新评论', 
    description: '当用户发表评论时，发送邮件通知文章作者和管理员',
    icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z'
  },
  { 
    key: 'notify_on_like' as const, 
    label: '新点赞', 
    description: '当用户点赞文章时，发送邮件通知文章作者',
    icon: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z'
  },
  { 
    key: 'notify_on_reply' as const, 
    label: '评论回复', 
    description: '当用户回复其他用户的评论时，发送邮件通知被回复的用户',
    icon: 'M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6'
  }
]

onMounted(() => {
  loadSettings()
})

async function loadSettings() {
  isLoading.value = true
  try {
    const data = await notificationApi.getSettings()
    settings.value = data
    settingsForm.value = {
      notify_on_register: data.notify_on_register,
      notify_on_comment: data.notify_on_comment,
      notify_on_like: data.notify_on_like,
      notify_on_reply: data.notify_on_reply
    }
  } catch (error) {
    console.error('Failed to load notification settings:', error)
  } finally {
    isLoading.value = false
  }
}

async function toggleSetting(key: keyof typeof settingsForm.value) {
  if (!await requirePermission('notification.edit', '修改通知设置')) return
  
  const newValue = !settingsForm.value[key]
  settingsForm.value[key] = newValue
  isSaving.value = true
  
  try {
    const data = await notificationApi.updateSettings({
      ...settings.value,
      [key]: newValue
    })
    settings.value = data
    const label = settingLabels[key]
    dialog.showSuccess(`${label}已${newValue ? '启用' : '关闭'}`)
  } catch (error) {
    console.error('Failed to save notification settings:', error)
    settingsForm.value[key] = !newValue
    dialog.showError('保存失败，请重试')
  } finally {
    isSaving.value = false
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
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          通知设置
        </h1>
      </div>
    </div>

    <div
      v-if="isLoading"
      class="flex justify-center py-12"
    >
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>

    <div
      v-else
      class="space-y-4"
    >
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div
          v-for="option in notificationOptions"
          :key="option.key"
          class="bg-white dark:bg-dark-100 rounded-xl border border-gray-200 dark:border-white/10 hover:border-gray-300 dark:hover:border-white/20 transition-colors overflow-hidden"
        >
          <div class="p-4">
            <div class="flex items-start gap-3">
              <div class="w-10 h-10 rounded-xl bg-primary/10 dark:bg-primary/20 flex items-center justify-center flex-shrink-0">
                <svg
                  class="w-5 h-5 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    :d="option.icon"
                  />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-2">
                  <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
                    {{ option.label }}
                  </h3>
                  <button
                    type="button"
                    :class="[
                      'relative inline-flex h-5 w-9 flex-shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 dark:focus:ring-offset-dark-100',
                      'cursor-pointer',
                      settingsForm[option.key] ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'
                    ]"
                    role="switch"
                    :aria-checked="settingsForm[option.key]"
                    @click="toggleSetting(option.key)"
                  >
                    <span
                      :class="[
                        'pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                        settingsForm[option.key] ? 'translate-x-4' : 'translate-x-0'
                      ]"
                    />
                  </button>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {{ option.description }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl border border-amber-200 dark:border-amber-800/30 p-4">
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center flex-shrink-0">
            <svg
              class="w-4 h-4 text-amber-600 dark:text-amber-400"
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
          </div>
          <div class="flex-1">
            <h4 class="text-sm font-medium text-amber-800 dark:text-amber-300">
              配置提醒
            </h4>
            <p class="text-xs text-amber-700 dark:text-amber-400 mt-1">
              所有邮件通知都依赖于正确的邮箱配置。请确保已在「邮件服务」中正确配置邮箱服务，否则通知将无法正常发送。
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
