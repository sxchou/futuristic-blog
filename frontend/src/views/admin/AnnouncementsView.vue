<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { announcementApi, type Announcement, type AnnouncementCreate, type AnnouncementUpdate } from '@/api'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { useDialogStore } from '@/stores'
import { useDeletionConfirm } from '@/composables/useDeletionConfirm'
import DeletionConfirmDialog from '@/components/common/DeletionConfirmDialog.vue'

const { requirePermission, hasPermission } = useAdminCheck()
const dialog = useDialogStore()
const deletion = useDeletionConfirm()
const canEdit = computed(() => hasPermission('announcement.edit') || hasPermission('announcement.create'))

const announcements = ref<Announcement[]>([])
const isLoading = ref(false)
const isSaving = ref(false)
const showEditor = ref(false)
const editingId = ref<number | null>(null)

const formData = ref<AnnouncementCreate>({
  title: '',
  content: '',
  type: 'info',
  is_active: true,
  order: 0
})

const typeOptions = [
  { value: 'info', label: '信息', color: 'blue', icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
  { value: 'warning', label: '警告', color: 'amber', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' },
  { value: 'success', label: '成功', color: 'green', icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' },
  { value: 'error', label: '错误', color: 'red', icon: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z' }
]

const stats = computed(() => {
  const total = announcements.value.length
  const active = announcements.value.filter(a => a.is_active).length
  const inactive = total - active
  return { total, active, inactive }
})

onMounted(() => {
  fetchAnnouncements()
})

const fetchAnnouncements = async () => {
  isLoading.value = true
  try {
    announcements.value = await announcementApi.getAnnouncements()
  } catch (error: any) {
    await dialog.showError(error.response?.data?.detail || '获取公告失败', '获取失败')
  } finally {
    isLoading.value = false
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const openEditor = async (announcement?: Announcement) => {
  const permission = announcement ? 'announcement.edit' : 'announcement.create'
  if (!await requirePermission(permission, announcement ? '编辑公告' : '创建公告')) return
  
  if (announcement) {
    editingId.value = announcement.id
    formData.value = {
      title: announcement.title,
      content: announcement.content,
      type: announcement.type,
      is_active: announcement.is_active,
      order: announcement.order
    }
  } else {
    editingId.value = null
    formData.value = {
      title: '',
      content: '',
      type: 'info',
      is_active: true,
      order: 0
    }
  }
  showEditor.value = true
}

const closeEditor = () => {
  showEditor.value = false
  editingId.value = null
  validationErrors.value = []
}

interface ValidationError {
  field: string
  message: string
}

const validationErrors = ref<ValidationError[]>([])

const scrollToField = async (fieldId: string) => {
  await nextTick()
  const element = document.getElementById(fieldId)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    element.focus({ preventScroll: true })
  }
}

const hasError = (field: string): boolean => {
  return validationErrors.value.some(e => e.field === field)
}

const getErrorMessage = (field: string): string => {
  const error = validationErrors.value.find(e => e.field === field)
  return error?.message || ''
}

const clearValidationError = (field: string) => {
  validationErrors.value = validationErrors.value.filter(e => e.field !== field)
}

const handleSave = async () => {
  validationErrors.value = []
  
  if (!formData.value.title.trim()) {
    validationErrors.value.push({ field: 'title', message: '请输入公告标题' })
  }
  
  if (!formData.value.content.trim()) {
    validationErrors.value.push({ field: 'content', message: '请输入公告内容' })
  }
  
  if (validationErrors.value.length > 0) {
    const firstError = validationErrors.value[0]
    const fieldIdMap: Record<string, string> = { title: 'announcement-title', content: 'announcement-content' }
    await scrollToField(fieldIdMap[firstError.field] || firstError.field)
    return
  }
  
  isSaving.value = true
  
  try {
    if (editingId.value) {
      await announcementApi.updateAnnouncement(editingId.value, formData.value as AnnouncementUpdate)
      await dialog.showSuccess('公告更新成功', '成功')
    } else {
      await announcementApi.createAnnouncement(formData.value)
      await dialog.showSuccess('公告创建成功', '成功')
    }
    
    closeEditor()
    fetchAnnouncements()
  } catch (error: any) {
    console.error('Failed to save announcement:', error)
  } finally {
    isSaving.value = false
  }
}

const handleDelete = async (id: number) => {
  if (!await requirePermission('announcement.delete', '删除公告')) return
  
  const previewed = await deletion.requestDeletion('announcement', id)
  if (!previewed) return
}

const deletionLoading = ref(false)
const executeDeletion = async () => {
  try {
    deletionLoading.value = true
    await announcementApi.deleteAnnouncement(deletion.currentItemId.value)
    deletion.confirmDeletion()
    await dialog.showSuccess('公告删除成功', '成功')
    fetchAnnouncements()
  } catch (error: any) {
    console.error('Failed to delete announcement:', error)
    deletion.cancelDeletion()
  } finally {
    deletionLoading.value = false
  }
}

const toggleActive = async (announcement: Announcement) => {
  if (!await requirePermission('announcement.edit', '修改公告状态')) return

  const previousState = announcement.is_active
  announcement.is_active = !previousState

  try {
    await announcementApi.updateAnnouncement(announcement.id, {
      is_active: !previousState
    })
    dialog.showSuccess(previousState ? '公告已禁用' : '公告已启用', '成功')
  } catch (error: any) {
    announcement.is_active = previousState
    await dialog.showError(error.response?.data?.detail || '操作失败', '操作失败')
  }
}

const getTypeStyles = (type: string) => {
  const styles = {
    info: {
      bg: 'bg-blue-500/10 dark:bg-blue-500/20',
      border: 'border-blue-500/30 dark:border-blue-500/40',
      text: 'text-blue-600 dark:text-blue-400',
      icon: 'text-blue-500'
    },
    warning: {
      bg: 'bg-amber-500/10 dark:bg-amber-500/20',
      border: 'border-amber-500/30 dark:border-amber-500/40',
      text: 'text-amber-600 dark:text-amber-400',
      icon: 'text-amber-500'
    },
    success: {
      bg: 'bg-emerald-500/10 dark:bg-emerald-500/20',
      border: 'border-emerald-500/30 dark:border-emerald-500/40',
      text: 'text-emerald-600 dark:text-emerald-400',
      icon: 'text-emerald-500'
    },
    error: {
      bg: 'bg-red-500/10 dark:bg-red-500/20',
      border: 'border-red-500/30 dark:border-red-500/40',
      text: 'text-red-600 dark:text-red-400',
      icon: 'text-red-500'
    }
  }
  return styles[type as keyof typeof styles] || styles.info
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
              d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          公告中心
        </h1>
      </div>
      <button
        type="button"
        class="inline-flex items-center gap-2 px-4 py-2.5 bg-primary text-white text-sm font-medium rounded-xl hover:bg-primary/90 transition-all shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 hover:-translate-y-0.5"
        @click="openEditor()"
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
            d="M12 4v16m8-8H4"
          />
        </svg>
        新建公告
      </button>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div class="glass-card p-3 group hover:shadow-lg transition-all">
        <div class="flex items-center gap-2.5">
          <div class="w-9 h-9 rounded-lg bg-blue-500/10 dark:bg-blue-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
            <svg
              class="w-4 h-4 text-blue-500"
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
            <p class="text-xs text-gray-500 dark:text-gray-400">总公告数</p>
            <p class="text-xl font-bold text-gray-900 dark:text-white">{{ stats.total }}</p>
          </div>
        </div>
      </div>

      <div class="glass-card p-3 group hover:shadow-lg transition-all">
        <div class="flex items-center gap-2.5">
          <div class="w-9 h-9 rounded-lg bg-emerald-500/10 dark:bg-emerald-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
            <svg
              class="w-4 h-4 text-emerald-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div>
            <p class="text-xs text-gray-500 dark:text-gray-400">已启用</p>
            <p class="text-xl font-bold text-emerald-600 dark:text-emerald-400">{{ stats.active }}</p>
          </div>
        </div>
      </div>

      <div class="glass-card p-3 group hover:shadow-lg transition-all">
        <div class="flex items-center gap-2.5">
          <div class="w-9 h-9 rounded-lg bg-gray-500/10 dark:bg-gray-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
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
                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div>
            <p class="text-xs text-gray-500 dark:text-gray-400">已禁用</p>
            <p class="text-xl font-bold text-gray-600 dark:text-gray-400">{{ stats.inactive }}</p>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="showEditor"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
    >
      <transition
        enter-active-class="transition ease-out duration-300"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition ease-in duration-200"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div
          v-if="showEditor"
          class="bg-white dark:bg-dark-100 rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden"
        >
          <div class="px-4 py-3 border-b border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-dark-200">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
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
                      d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"
                    />
                  </svg>
                </div>
                <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
                  {{ editingId ? '编辑公告' : '新建公告' }}
                </h2>
              </div>
              <button
                type="button"
                class="p-2 hover:bg-gray-100 dark:hover:bg-white/5 rounded-lg transition-colors"
                @click="closeEditor"
              >
                <svg
                  class="w-5 h-5 text-gray-500"
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
          </div>

          <form class="p-4 space-y-3 overflow-y-auto max-h-[calc(90vh-120px)]" @submit.prevent="handleSave">
            <div>
              <label for="announcement-title" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                公告标题 <span class="text-red-500">*</span>
              </label>
              <input id="announcement-title"
                v-model="formData.title"
                type="text"
                :disabled="!canEdit"
                class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-200 border rounded-xl text-gray-900 dark:text-white outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                :class="hasError('title') ? 'border-red-500 dark:border-red-500' : 'border-gray-200 dark:border-white/10'"
                placeholder="请输入公告标题"
                @input="clearValidationError('title')"
              >
              <p
                v-if="hasError('title')"
                class="mt-1 text-xs text-red-500"
              >
                {{ getErrorMessage('title') }}
              </p>
            </div>

            <div>
              <label for="announcement-content" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                公告内容 <span class="text-red-500">*</span>
              </label>
              <textarea id="announcement-content"
                v-model="formData.content"
                rows="4"
                :disabled="!canEdit"
                class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-200 border rounded-xl text-gray-900 dark:text-white outline-none transition-all resize-none disabled:opacity-50 disabled:cursor-not-allowed"
                :class="hasError('content') ? 'border-red-500 dark:border-red-500' : 'border-gray-200 dark:border-white/10'"
                placeholder="请输入公告内容"
                @input="clearValidationError('content')"
              />
              <p
                v-if="hasError('content')"
                class="mt-1 text-xs text-red-500"
              >
                {{ getErrorMessage('content') }}
              </p>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label for="announcement-type-helper" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  公告类型
                </label>
                <input id="announcement-type-helper" type="text" class="sr-only" :value="formData.type" tabindex="-1" readonly autocomplete="off">
                <div class="grid grid-cols-2 gap-1.5">
                  <button
                    v-for="option in typeOptions"
                    :key="option.value"
                    type="button"
                    :class="[
                      'relative flex flex-col items-center gap-1 p-2 rounded-lg border-2 transition-all',
                      formData.type === option.value
                        ? `border-${option.color}-500 bg-${option.color}-500/10`
                        : 'border-gray-200 dark:border-white/10 hover:border-gray-300 dark:hover:border-white/20'
                    ]"
                    @click="formData.type = option.value as any"
                  >
                    <svg
                      class="w-4 h-4"
                      :class="formData.type === option.value ? `text-${option.color}-500` : 'text-gray-400'"
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
                    <span
                      :class="[
                        'text-xs font-medium',
                        formData.type === option.value ? `text-${option.color}-600 dark:text-${option.color}-400` : 'text-gray-600 dark:text-gray-400'
                      ]"
                    >
                      {{ option.label }}
                    </span>
                  </button>
                </div>
              </div>

              <div>
                <label for="announcement-is-active" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  排序权重
                </label>
                <input id="announcement-is-active"
                  v-model.number="formData.order"
                  type="number"
                  min="0"
                  :disabled="!canEdit"
                  class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-200 border border-gray-200 dark:border-white/10 rounded-xl text-gray-900 dark:text-white outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  placeholder="数字越小越靠前"
                >
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  数值越小，显示顺序越靠前
                </p>
              </div>
            </div>

            <div class="flex items-center gap-2 p-3 bg-gray-50 dark:bg-dark-200 rounded-xl">
              <input
                id="announcement-active"
                v-model="formData.is_active"
                type="checkbox"
                :disabled="!canEdit"
                class="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
              <label
                for="announcement-active"
                :class="['flex-1', canEdit ? '' : 'opacity-50']"
              >
                <div class="text-sm font-medium text-gray-900 dark:text-white">启用此公告</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">启用后将在前端展示该公告</div>
              </label>
            </div>
          </form>

          <div class="px-4 py-3 border-t border-gray-200 dark:border-white/10 flex justify-end gap-2 bg-gray-50/50 dark:bg-white/[0.02]">
            <button
              type="button"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              @click="closeEditor"
            >
              取消
            </button>
            <button
              type="button"
              :disabled="isSaving || !canEdit"
              class="btn-primary text-sm px-4 py-1.5"
              @click="handleSave"
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
      </transition>
    </div>

    <div
      v-if="isLoading"
      class="flex items-center justify-center py-20"
    >
      <div class="flex flex-col items-center gap-3">
        <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        <p class="text-sm text-gray-500 dark:text-gray-400">加载中...</p>
      </div>
    </div>

    <div
      v-else-if="announcements.length === 0"
      class="glass-card p-16 text-center"
    >
      <div class="flex flex-col items-center gap-4">
        <div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700 flex items-center justify-center">
          <svg
            class="w-10 h-10 text-gray-400 dark:text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
        </div>
        <div>
          <p class="text-base font-medium text-gray-900 dark:text-white mb-1">
            暂无公告
          </p>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            点击右上角"新建公告"按钮创建第一条公告
          </p>
        </div>
      </div>
    </div>

    <div
      v-else
      class="grid grid-cols-1 lg:grid-cols-2 gap-4"
    >
      <transition-group
        enter-active-class="transition ease-out duration-300"
        enter-from-class="opacity-0 translate-y-2"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition ease-in duration-200"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 translate-y-2"
      >
        <div
          v-for="announcement in announcements"
          :key="announcement.id"
          class="glass-card overflow-hidden hover:shadow-xl transition-all group"
        >
          <div class="p-4">
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-2">
                  <div
                    :class="[
                      'px-2 py-0.5 rounded-lg border flex items-center gap-1',
                      getTypeStyles(announcement.type).bg,
                      getTypeStyles(announcement.type).border
                    ]"
                  >
                    <svg
                      class="w-3 h-3"
                      :class="getTypeStyles(announcement.type).icon"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        :d="typeOptions.find(t => t.value === announcement.type)?.icon"
                      />
                    </svg>
                    <span
                      :class="[
                        'text-xs font-medium',
                        getTypeStyles(announcement.type).text
                      ]"
                    >
                      {{ typeOptions.find(t => t.value === announcement.type)?.label || '信息' }}
                    </span>
                  </div>
                  
                  <span
                    v-if="announcement.is_active"
                    class="px-2 py-0.5 text-xs font-medium rounded-lg bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/30"
                  >
                    已启用
                  </span>
                  <span
                    v-else
                    class="px-2 py-0.5 text-xs font-medium rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700"
                  >
                    已禁用
                  </span>
                </div>
                
                <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-1 group-hover:text-primary transition-colors">
                  {{ announcement.title }}
                </h3>
                <p class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed line-clamp-2">
                  {{ announcement.content }}
                </p>
                
                <div class="flex items-center gap-3 mt-2 text-xs text-gray-500 dark:text-gray-400">
                  <span class="flex items-center gap-1">
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
                        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                    {{ formatDate(announcement.updated_at || announcement.created_at) }}
                  </span>
                  <span class="flex items-center gap-1">
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
                        d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"
                      />
                    </svg>
                    排序: {{ announcement.order }}
                  </span>
                </div>
              </div>
              
              <div class="flex flex-col gap-1.5">
                <button
                  type="button"
                  :class="[
                    'p-2 rounded-lg transition-all',
                    announcement.is_active
                      ? 'text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-500/10'
                      : 'text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5'
                  ]"
                  :title="announcement.is_active ? '点击禁用' : '点击启用'"
                  @click="toggleActive(announcement)"
                >
                  <svg
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      v-if="announcement.is_active"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                    <path
                      v-else
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </button>
                <button
                  type="button"
                  class="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 rounded-lg transition-all"
                  title="编辑"
                  @click="openEditor(announcement)"
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
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                  </svg>
                </button>
                <button
                  type="button"
                  class="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-all"
                  title="删除"
                  @click="handleDelete(announcement.id)"
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
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </transition-group>
    </div>

    <DeletionConfirmDialog
      :visible="deletion.showDeletionDialog.value"
      :preview="deletion.deletionPreview.value"
      :loading="deletionLoading"
      @confirm="executeDeletion"
      @cancel="deletion.cancelDeletion()"
    />
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-clamp: 2;
  overflow: hidden;
}
</style>
