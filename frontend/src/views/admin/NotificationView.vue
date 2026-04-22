<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { notificationApi, type NotificationSettings } from '@/api/notifications'
import { useAdminCheck } from '@/composables/useAdminCheck'

const { requireAdmin } = useAdminCheck()

const settings = ref<NotificationSettings | null>(null)
const isLoading = ref(false)
const isSaving = ref(false)
const message = ref('')

const settingsForm = ref({
  notify_on_register: true,
  notify_on_comment: true,
  notify_on_like: true,
  notify_on_reply: true,
  require_comment_audit: false
})

const notificationOptions = [
  { 
    key: 'notify_on_register' as const, 
    label: '新用户注册通知', 
    description: '当有新用户注册时，发送邮件通知管理员' 
  },
  { 
    key: 'notify_on_comment' as const, 
    label: '新评论通知', 
    description: '当用户发表评论时，发送邮件通知管理员' 
  },
  { 
    key: 'notify_on_like' as const, 
    label: '新点赞通知', 
    description: '当用户点赞文章时，发送邮件通知管理员' 
  },
  { 
    key: 'notify_on_reply' as const, 
    label: '评论回复通知', 
    description: '当用户回复其他用户的评论时，发送邮件通知被回复的用户' 
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
      notify_on_reply: data.notify_on_reply,
      require_comment_audit: data.require_comment_audit
    }
  } catch (error) {
    console.error('Failed to load notification settings:', error)
  } finally {
    isLoading.value = false
  }
}

async function saveSettings() {
  if (!await requireAdmin('保存通知设置')) return
  
  isSaving.value = true
  message.value = ''
  try {
    const data = await notificationApi.updateSettings(settingsForm.value)
    settings.value = data
    message.value = '保存成功'
    setTimeout(() => {
      message.value = ''
    }, 3000)
  } catch (error) {
    console.error('Failed to save notification settings:', error)
    message.value = '保存失败，请重试'
  } finally {
    isSaving.value = false
  }
}

async function toggleSetting(key: keyof typeof settingsForm.value) {
  if (!await requireAdmin('修改通知设置')) return
  settingsForm.value[key] = !settingsForm.value[key]
  saveSettings()
}
</script>

<template>
  <div class="space-y-5">
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
          通知管理
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
      class="space-y-6"
    >
      <div class="glass-card p-5">
        <div class="mb-5">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
            评论审核设置
          </h2>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            控制评论是否需要审核后才能显示
          </p>
        </div>

        <div class="flex items-center justify-between p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800/30">
          <div class="flex-1">
            <h3 class="text-sm font-medium text-gray-900 dark:text-white">
              启用评论审核
            </h3>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              开启后，新发表的评论将标记为"待审核"状态，需要管理员审核通过后才能在前台显示
            </p>
          </div>
          <button
            :class="[
              'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
              settingsForm.require_comment_audit ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'
            ]"
            role="switch"
            :aria-checked="settingsForm.require_comment_audit"
            @click="toggleSetting('require_comment_audit')"
          >
            <span
              :class="[
                'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                settingsForm.require_comment_audit ? 'translate-x-5' : 'translate-x-0'
              ]"
            />
          </button>
        </div>

        <div
          v-if="settingsForm.require_comment_audit"
          class="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800/30"
        >
          <div class="flex items-start gap-2">
            <svg
              class="w-5 h-5 text-blue-500 mt-0.5"
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
            <div class="text-xs text-blue-700 dark:text-blue-300">
              <p class="font-medium">
                评论审核已启用
              </p>
              <p class="mt-1">
                新评论将不会立即显示，请前往「评论管理」进行审核操作。
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="glass-card p-5">
        <div class="mb-5">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
            邮件通知设置
          </h2>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            配置系统在特定事件发生时是否发送邮件通知
          </p>
        </div>

        <div class="space-y-3">
          <div 
            v-for="option in notificationOptions" 
            :key="option.key"
            class="flex items-center justify-between p-3 bg-gray-50 dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10"
          >
            <div class="flex-1">
              <h3 class="text-sm font-medium text-gray-900 dark:text-white">
                {{ option.label }}
              </h3>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {{ option.description }}
              </p>
            </div>
            <button
              :class="[
                'relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
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
        </div>

        <div
          v-if="message"
          class="mt-4 p-2.5 rounded-lg text-sm"
          :class="message.includes('成功') ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'"
        >
          {{ message }}
        </div>

        <div class="mt-5 flex justify-end">
          <button
            :disabled="isSaving"
            class="px-5 py-2 text-sm bg-primary text-white font-medium rounded-lg hover:bg-primary/80 disabled:opacity-50 transition-colors"
            @click="saveSettings"
          >
            <span
              v-if="isSaving"
              class="flex items-center gap-2"
            >
              <svg
                class="animate-spin w-4 h-4"
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
              保存中...
            </span>
            <span v-else>保存设置</span>
          </button>
        </div>
      </div>

      <div class="glass-card p-5">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
          说明
        </h2>
        <div class="space-y-2 text-xs text-gray-500 dark:text-gray-400">
          <p>• <strong>启用评论审核</strong>：开启后，新评论需要管理员审核通过后才能在前台显示。</p>
          <p>• <strong>新用户注册通知</strong>：当有新用户注册账户时，系统会发送邮件通知所有管理员。</p>
          <p>• <strong>新评论通知</strong>：当用户在文章下发表评论时，系统会发送邮件通知所有管理员。</p>
          <p>• <strong>新点赞通知</strong>：当用户点赞文章时，系统会发送邮件通知所有管理员。</p>
          <p>• <strong>评论回复通知</strong>：当用户回复其他用户的评论时，系统会发送邮件通知被回复的用户。</p>
          <p class="mt-3 text-xs opacity-75">
            注意：所有邮件通知都依赖于正确的邮箱配置。请确保已在「邮件管理」中正确配置邮箱服务。
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
