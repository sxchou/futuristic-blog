<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { commentApi } from '@/api'
import { notificationApi, type NotificationSettings } from '@/api/notifications'
import type { AdminComment, CommentAuditLog, PaginatedResponse } from '@/types'
import { useDialogStore, useUserProfileStore, useAuthStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { useDeletionConfirm } from '@/composables/useDeletionConfirm'
import DeletionConfirmDialog from '@/components/common/DeletionConfirmDialog.vue'
import { formatDateTime } from '@/utils/date'
import DateRangePicker from '@/components/common/DateRangePicker.vue'

const dialog = useDialogStore()
const commentDeletion = useDeletionConfirm()
const userProfileStore = useUserProfileStore()
const authStore = useAuthStore()
const { requirePermission, hasPermission } = useAdminCheck()

const comments = ref<AdminComment[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = ref(0)
const statusFilter = ref<string>('')
const contentFilter = ref<string>('')
const articleTitleFilter = ref<string>('')
const authorNameFilter = ref<string>('')
const startDateFilter = ref<string>('')
const endDateFilter = ref<string>('')
const showFilters = ref(false)

const hasActiveFilters = computed(() => {
  return !!(statusFilter.value || contentFilter.value || articleTitleFilter.value || 
            authorNameFilter.value || startDateFilter.value || endDateFilter.value)
})
const selectedComments = ref<number[]>([])
const showAuditModal = ref(false)
const showLogsModal = ref(false)
const currentComment = ref<AdminComment | null>(null)
const auditStatus = ref<'pending' | 'approved' | 'rejected'>('approved')
const auditReason = ref('')
const auditLogs = ref<CommentAuditLog[]>([])
const showBatchAuditModal = ref(false)
const batchAuditStatus = ref<'pending' | 'approved' | 'rejected'>('approved')
const batchAuditReason = ref('')
const showBatchDeleteModal = ref(false)
const batchDeleteType = ref<'soft' | 'permanent'>('soft')

const auditSettings = ref<NotificationSettings | null>(null)
const requireCommentAudit = ref(false)
const isSavingSettings = ref(false)
const canEditSettings = computed(() => hasPermission('comment.audit'))
const canViewComments = computed(() => hasPermission('comment.view') || hasPermission('comment.audit') || hasPermission('comment.delete'))

const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 'pending', label: '待审核' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已拒绝' }
]

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  approved: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  rejected: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
}

const statusLabels: Record<string, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝'
}

const pendingCount = computed(() => {
  return comments.value.filter(c => c.status === 'pending').length
})

const fetchComments = async () => {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    if (contentFilter.value) {
      params.content = contentFilter.value
    }
    if (articleTitleFilter.value) {
      params.article_title = articleTitleFilter.value
    }
    if (authorNameFilter.value) {
      params.author_name = authorNameFilter.value
    }
    if (startDateFilter.value) {
      params.start_date = startDateFilter.value
    }
    if (endDateFilter.value) {
      params.end_date = endDateFilter.value
    }
    const response: PaginatedResponse<AdminComment> = await commentApi.getAdminComments(params as Parameters<typeof commentApi.getAdminComments>[0])
    comments.value = response.items
    total.value = response.total
    totalPages.value = response.total_pages
  } catch (error: any) {
    if (error?.isCancel) {
      return
    }
    console.error('Failed to fetch comments:', error)
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchComments()
}

const handleStatusFilter = () => {
  currentPage.value = 1
  fetchComments()
}

const clearFilters = () => {
  statusFilter.value = ''
  contentFilter.value = ''
  articleTitleFilter.value = ''
  authorNameFilter.value = ''
  startDateFilter.value = ''
  endDateFilter.value = ''
  currentPage.value = 1
  fetchComments()
}

const toggleSelectAll = () => {
  if (selectedComments.value.length === comments.value.length) {
    selectedComments.value = []
  } else {
    selectedComments.value = comments.value.map(c => c.id)
  }
}

const toggleSelect = (id: number) => {
  const index = selectedComments.value.indexOf(id)
  if (index > -1) {
    selectedComments.value.splice(index, 1)
  } else {
    selectedComments.value.push(id)
  }
}

const openAuditModal = async (comment: AdminComment, status: 'pending' | 'approved' | 'rejected') => {
  if (!await requirePermission('comment.audit', '审核评论')) return
  currentComment.value = comment
  auditStatus.value = status
  auditReason.value = ''
  showAuditModal.value = true
}

const submitAudit = async () => {
  if (!currentComment.value) return
  try {
    await commentApi.auditComment(currentComment.value.id, {
      status: auditStatus.value,
      reason: auditReason.value || undefined
    })
    showAuditModal.value = false
    await dialog.showSuccess('审核状态已更新', '成功')
    fetchComments()
  } catch (error: any) {
    console.error('Failed to audit comment:', error)
    await dialog.showError(error.response?.data?.detail || '审核失败', '错误')
  }
}

const openLogsModal = async (comment: AdminComment) => {
  currentComment.value = comment
  try {
    auditLogs.value = await commentApi.getAuditLogs(comment.id)
    showLogsModal.value = true
  } catch (error) {
    console.error('Failed to fetch audit logs:', error)
  }
}

const openBatchAuditModal = async (status: 'pending' | 'approved' | 'rejected') => {
  if (!await requirePermission('comment.audit', '批量审核评论')) return
  batchAuditStatus.value = status
  batchAuditReason.value = ''
  showBatchAuditModal.value = true
}

const submitBatchAudit = async () => {
  if (selectedComments.value.length === 0) return
  try {
    const count = selectedComments.value.length
    const statusText = batchAuditStatus.value === 'approved' ? '通过' : batchAuditStatus.value === 'rejected' ? '拒绝' : '处理'
    await commentApi.batchAudit({
      comment_ids: selectedComments.value,
      status: batchAuditStatus.value,
      reason: batchAuditReason.value || undefined
    })
    showBatchAuditModal.value = false
    selectedComments.value = []
    await dialog.showSuccess(`已批量${statusText} ${count} 条评论`, '成功')
    fetchComments()
  } catch (error: any) {
    console.error('Failed to batch audit:', error)
    await dialog.showError(error.response?.data?.detail || '批量审核失败', '错误')
  }
}

const showDeleteModal = ref(false)
const deleteTargetComment = ref<AdminComment | null>(null)
const deleteType = ref<'soft' | 'permanent'>('soft')

const openDeleteModal = async (comment: AdminComment) => {
  if (!await requirePermission('comment.delete', '删除评论')) return
  deleteTargetComment.value = comment
  deleteType.value = 'soft'
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!deleteTargetComment.value) return
  
  if (deleteType.value === 'permanent') {
    showDeleteModal.value = false
    const previewed = await commentDeletion.requestDeletion('comment', deleteTargetComment.value.id)
    if (!previewed) return
    return
  }
  
  showDeleteModal.value = false
  try {
    const keepRecord = deleteType.value === 'soft'
    const result = await commentApi.adminDelete(deleteTargetComment.value.id, keepRecord)
    if (result.type === 'soft') {
      await dialog.showSuccess('评论已标记为删除，记录已保留', '成功')
    } else {
      await dialog.showSuccess('评论已彻底删除', '成功')
    }
    fetchComments()
  } catch (error: any) {
    console.error('Failed to delete comment:', error)
    await dialog.showError(error.response?.data?.detail || '删除评论失败', '错误')
  }
}

const commentDeletionLoading = ref(false)
const executeCommentDeletion = async () => {
  try {
    commentDeletionLoading.value = true
    await commentApi.adminDelete(commentDeletion.currentItemId.value, false)
    commentDeletion.confirmDeletion()
    await dialog.showSuccess('评论已彻底删除', '成功')
    fetchComments()
  } catch (error: any) {
    console.error('Failed to delete comment:', error)
    commentDeletion.cancelDeletion()
  } finally {
    commentDeletionLoading.value = false
  }
}

const openBatchDeleteModal = async () => {
  if (!await requirePermission('comment.delete', '批量删除评论')) return
  batchDeleteType.value = 'soft'
  showBatchDeleteModal.value = true
}

const confirmBatchDelete = async () => {
  if (selectedComments.value.length === 0) return
  showBatchDeleteModal.value = false
  try {
    const permanent = batchDeleteType.value === 'permanent'
    const result = await commentApi.batchDelete(selectedComments.value, permanent)
    selectedComments.value = []
    if (result.type === 'soft') {
      await dialog.showSuccess(`已批量删除 ${result.deleted_count} 条评论，记录已保留`, '成功')
    } else {
      await dialog.showSuccess(`已彻底删除 ${result.deleted_count} 条评论`, '成功')
    }
    fetchComments()
  } catch (error: any) {
    console.error('Failed to batch delete comments:', error)
    await dialog.showError(error.response?.data?.detail || '批量删除失败', '错误')
  }
}

const loadAuditSettings = async () => {
  try {
    const data = await notificationApi.getSettings()
    auditSettings.value = data
    requireCommentAudit.value = data.require_comment_audit
  } catch (error) {
    console.error('Failed to load audit settings:', error)
  }
}

const toggleCommentAudit = async () => {
  if (!await requirePermission('comment.audit', '修改评论审核设置')) return
  
  const newValue = !requireCommentAudit.value
  requireCommentAudit.value = newValue
  isSavingSettings.value = true
  
  try {
    const data = await notificationApi.updateSettings({
      ...auditSettings.value,
      require_comment_audit: newValue
    })
    auditSettings.value = data
    dialog.showSuccess(`评论审核已${newValue ? '启用' : '关闭'}`)
  } catch (error) {
    console.error('Failed to save audit settings:', error)
    requireCommentAudit.value = !newValue
    dialog.showError('保存失败，请重试')
  } finally {
    isSavingSettings.value = false
  }
}

const formatDate = (dateStr: string) => formatDateTime(dateStr)

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'ArrowLeft' && currentPage.value > 1) {
    event.preventDefault()
    handlePageChange(currentPage.value - 1)
  } else if (event.key === 'ArrowRight' && currentPage.value < totalPages.value) {
    event.preventDefault()
    handlePageChange(currentPage.value + 1)
  } else if (event.key === 'Delete') {
    event.preventDefault()
    clearFilters()
  }
}

onMounted(async () => {
  await authStore.waitForInit()
  if (!canViewComments.value) return
  fetchComments()
  loadAuditSettings()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

watch(() => userProfileStore.avatarUpdatedAt, () => {
  if (!loading.value) {
    fetchComments()
  }
})
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between gap-2">
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
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          评论管理
        </h1>
      </div>
      <div class="flex items-center gap-2 sm:gap-4">
        <span
          v-if="pendingCount > 0 && canViewComments"
          class="px-2 sm:px-3 py-1 bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400 rounded-full text-xs sm:text-sm font-medium whitespace-nowrap"
        >
          {{ pendingCount }} 条待审核
        </span>
      </div>
    </div>

    <div
      v-if="!canViewComments"
      class="glass-card p-8 text-center"
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
        无评论管理访问权限，请联系管理员
      </p>
    </div>

    <template v-else>
      <div class="glass-card p-4">
        <div class="flex items-center justify-between">
          <div class="flex-1">
            <h3 class="text-sm font-medium text-gray-900 dark:text-white">
              评论审核
            </h3>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              开启后，新发表的评论需要审核通过后才能显示
            </p>
          </div>
          <button
            :class="[
              'relative inline-flex h-6 w-11 flex-shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
              canEditSettings ? 'cursor-pointer' : 'cursor-not-allowed opacity-50',
              requireCommentAudit ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'
            ]"
            role="switch"
            :aria-checked="requireCommentAudit"
            @click="toggleCommentAudit"
          >
            <span
              :class="[
                'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                requireCommentAudit ? 'translate-x-5' : 'translate-x-0'
              ]"
            />
          </button>
        </div>
        <div
          v-if="requireCommentAudit"
          class="mt-3 p-2.5 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800/30"
        >
          <div class="flex items-start gap-2">
            <svg
              class="w-4 h-4 text-blue-500 mt-0.5"
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
            <p class="text-xs text-blue-700 dark:text-blue-300">
              评论审核已启用，新评论将不会立即显示，请在此页面进行审核操作。
            </p>
          </div>
        </div>
      </div>

      <div class="glass-card overflow-hidden">
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
            <span v-if="contentFilter" class="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full">{{ contentFilter }}</span>
            <span v-if="articleTitleFilter" class="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full">{{ articleTitleFilter }}</span>
            <span v-if="authorNameFilter" class="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full">{{ authorNameFilter }}</span>
            <span v-if="statusFilter" class="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full">{{ statusFilter === 'approved' ? '已通过' : statusFilter === 'rejected' ? '已拒绝' : '待审核' }}</span>
          </div>
        </div>
        <form 
          class="flex flex-wrap items-center gap-2"
          :class="{ 'hidden md:flex': !showFilters, 'md:flex': true }"
          @submit.prevent="handleStatusFilter"
        >
          <input
            v-model="contentFilter"
            type="text"
            placeholder="内容"
            class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-36"
            @keyup.enter="handleStatusFilter"
          >
          <input
            v-model="articleTitleFilter"
            type="text"
            placeholder="文章"
            class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-28"
            @keyup.enter="handleStatusFilter"
          >
          <input
            v-model="authorNameFilter"
            type="text"
            placeholder="评论人"
            class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-28"
            @keyup.enter="handleStatusFilter"
          >
          <select id="select-statusFilter"
            v-model="statusFilter"
            class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
            @change="handleStatusFilter"
          >
            <option
              v-for="option in statusOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
          <DateRangePicker
            v-model:start-date="startDateFilter"
            v-model:end-date="endDateFilter"
          />
          <button
            type="button"
            class="px-2.5 py-1 text-xs bg-red-500/10 text-red-500 dark:text-red-400 border border-red-500/20 dark:border-red-400/20 rounded-lg hover:bg-red-500/20 dark:hover:bg-red-400/20 transition-colors flex items-center gap-1"
            @click="clearFilters"
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
            type="button"
            class="btn-primary text-xs px-3 py-1 flex items-center gap-1"
            @click="handleStatusFilter"
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
        </form>

        <div
          v-if="selectedComments.length > 0"
          class="flex items-center gap-2"
        >
          <span class="text-sm text-gray-500 dark:text-gray-400">
            已选择 {{ selectedComments.length }} 条
          </span>
          <button
            class="px-3 py-1.5 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 transition-colors"
            @click="openBatchAuditModal('approved')"
          >
            批量通过
          </button>
          <button
            class="px-3 py-1.5 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 transition-colors"
            @click="openBatchAuditModal('rejected')"
          >
            批量拒绝
          </button>
          <button
            class="px-3 py-1.5 bg-gray-600 text-white rounded-lg text-sm hover:bg-gray-700 transition-colors"
            @click="openBatchDeleteModal"
          >
            批量删除
          </button>
        </div>
      </div>

      <div
        v-if="loading"
        class="p-8 text-center"
      >
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto" />
      </div>

      <div
        v-else-if="comments.length === 0"
        class="p-8 text-center text-gray-500 dark:text-gray-400"
      >
        暂无评论
      </div>

      <div
        v-else
        class="overflow-x-auto"
      >
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-dark-100">
            <tr>
              <th class="px-4 py-3 text-left">
                <input id="comment-search-input"
                  type="checkbox"
                  :checked="selectedComments.length === comments.length && comments.length > 0"
                  class="rounded border-gray-300 dark:border-white/20"
                  @change="toggleSelectAll"
                >
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                ID
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                内容
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                文章
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                评论人
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                状态
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                时间
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                操作
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-white/10">
            <tr
              v-for="comment in comments"
              :key="comment.id"
              class="hover:bg-gray-50 dark:hover:bg-dark-100/50"
            >
              <td class="px-4 py-3">
                <input id="comment-author-search"
                  type="checkbox"
                  :checked="selectedComments.includes(comment.id)"
                  class="rounded border-gray-300 dark:border-white/20"
                  @change="toggleSelect(comment.id)"
                >
              </td>
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">
                {{ comment.id }}
              </td>
              <td class="px-4 py-3">
                <router-link
                  v-if="comment.article_slug"
                  :to="`/article/${comment.article_slug}#comment-${comment.id}`"
                  class="text-sm text-primary hover:underline block max-w-xs line-clamp-2"
                  title="点击查看评论"
                >
                  <span v-if="comment.reply_to_user_name" class="text-gray-500 dark:text-gray-400">@{{ comment.reply_to_user_name }} </span>{{ comment.content }}
                </router-link>
                <div
                  v-else
                  class="text-sm text-gray-900 dark:text-white max-w-xs line-clamp-2"
                >
                  <span v-if="comment.reply_to_user_name" class="text-gray-500 dark:text-gray-400">@{{ comment.reply_to_user_name }} </span>{{ comment.content }}
                </div>
              </td>
              <td class="px-4 py-3 text-sm">
                <router-link
                  v-if="comment.article_slug"
                  :to="`/article/${comment.article_slug}`"
                  class="text-primary hover:underline"
                >
                  {{ comment.article_title || `文章 #${comment.article_id}` }}
                </router-link>
                <span
                  v-else
                  class="text-gray-500"
                >
                  {{ comment.article_title || `文章 #${comment.article_id}` }}
                </span>
              </td>
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">
                {{ comment.author_name || '匿名用户' }}
              </td>
              <td class="px-4 py-3">
                <span
                  :class="[
                    'px-2 py-1 rounded-full text-xs font-medium',
                    statusColors[comment.status]
                  ]"
                >
                  {{ statusLabels[comment.status] }}
                </span>
              </td>
              <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                {{ formatDate(comment.created_at) }}
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <button
                    v-if="comment.status !== 'approved'"
                    class="px-2 py-1 text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors"
                    @click="openAuditModal(comment, 'approved')"
                  >
                    通过
                  </button>
                  <button
                    v-if="comment.status !== 'rejected'"
                    class="px-2 py-1 text-xs bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 rounded hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
                    @click="openAuditModal(comment, 'rejected')"
                  >
                    拒绝
                  </button>
                  <button
                    class="px-2 py-1 text-xs bg-gray-100 text-gray-700 dark:bg-dark-100 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-dark-50 transition-colors"
                    @click="openLogsModal(comment)"
                  >
                    日志
                  </button>
                  <button
                    class="px-2 py-1 text-xs bg-gray-100 text-red-600 dark:bg-dark-100 dark:text-red-400 rounded hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                    @click="openDeleteModal(comment)"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div
        v-if="totalPages > 1"
        class="p-4 border-t border-gray-200 dark:border-white/10 flex items-center justify-between"
      >
        <div class="text-sm text-gray-500 dark:text-gray-400">
          共 {{ total }} 条评论
        </div>
        <div class="flex items-center gap-2">
          <button
            :disabled="currentPage === 1"
            class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-dark-50 transition-colors"
            @click="handlePageChange(currentPage - 1)"
          >
            上一页
          </button>
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ currentPage }} / {{ totalPages }}
          </span>
          <button
            :disabled="currentPage === totalPages"
            class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-dark-50 transition-colors"
            @click="handlePageChange(currentPage + 1)"
          >
            下一页
          </button>
        </div>
      </div>
      </div>
    </template>

    <div
      v-if="showAuditModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    >
      <div class="glass-card p-6 w-full max-w-md mx-4">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-4">
          审核评论
        </h3>
        <form class="space-y-4" @submit.prevent="submitAudit">
          <div>
            <label
              for="comment-audit-status"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >状态</label>
            <select
              id="comment-audit-status"
              v-model="auditStatus"
              name="audit-status"
              class="w-full px-3 py-2 bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:outline-none focus:border-gray-300 dark:focus:border-white/20"
            >
              <option value="pending">
                待审核
              </option>
              <option value="approved">
                已通过
              </option>
              <option value="rejected">
                已拒绝
              </option>
            </select>
          </div>
          <div>
            <label
              for="comment-audit-reason"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >原因（可选）</label>
            <textarea
              id="comment-audit-reason"
              v-model="auditReason"
              name="audit-reason"
              rows="3"
              class="w-full px-3 py-2 bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:outline-none focus:border-gray-300 dark:focus:border-white/20"
              placeholder="请输入审核原因..."
            />
          </div>
        </form>
        <div class="flex justify-end gap-3 mt-6">
          <button
            class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-100 rounded-lg transition-colors"
            @click="showAuditModal = false"
          >
            取消
          </button>
          <button
            class="btn-primary text-sm px-4 py-1.5"
            @click="submitAudit"
          >
            确认
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showBatchAuditModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    >
      <div class="glass-card p-6 w-full max-w-md mx-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          批量审核
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          将对 {{ selectedComments.length }} 条评论进行批量操作
        </p>
        <form class="space-y-4" @submit.prevent="submitBatchAudit">
          <div>
            <label
              for="batch-audit-status"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >状态</label>
            <select
              id="batch-audit-status"
              v-model="batchAuditStatus"
              name="batch-audit-status"
              class="w-full px-3 py-2 bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:outline-none focus:border-gray-300 dark:focus:border-white/20"
            >
              <option value="pending">
                待审核
              </option>
              <option value="approved">
                已通过
              </option>
              <option value="rejected">
                已拒绝
              </option>
            </select>
          </div>
          <div>
            <label
              for="batch-audit-reason"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >原因（可选）</label>
            <textarea
              id="batch-audit-reason"
              v-model="batchAuditReason"
              name="batch-audit-reason"
              rows="3"
              class="w-full px-3 py-2 bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:outline-none focus:border-gray-300 dark:focus:border-white/20"
              placeholder="请输入审核原因..."
            />
          </div>
        </form>
        <div class="flex justify-end gap-3 mt-6">
          <button
            class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-100 rounded-lg transition-colors"
            @click="showBatchAuditModal = false"
          >
            取消
          </button>
          <button
            class="btn-primary text-sm px-4 py-1.5"
            @click="submitBatchAudit"
          >
            确认
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showLogsModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    >
      <div class="glass-card p-6 w-full max-w-lg mx-4 max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
            审核日志
          </h3>
          <button
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
            @click="showLogsModal = false"
          >
            <svg
              class="w-5 h-5"
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
        <div
          v-if="auditLogs.length === 0"
          class="text-center text-gray-500 dark:text-gray-400 py-8"
        >
          暂无审核记录
        </div>
        <div
          v-else
          class="space-y-4"
        >
          <div
            v-for="log in auditLogs"
            :key="log.id"
            class="p-4 bg-gray-50 dark:bg-dark-100 rounded-lg"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-gray-900 dark:text-white">
                {{ log.operator_name || '系统' }}
              </span>
              <span class="text-xs text-gray-500 dark:text-gray-400">
                {{ formatDate(log.created_at) }}
              </span>
            </div>
            <div class="flex items-center gap-2 text-sm">
              <span
                v-if="log.old_status"
                :class="['px-2 py-0.5 rounded text-xs', statusColors[log.old_status]]"
              >
                {{ statusLabels[log.old_status] }}
              </span>
              <span
                v-if="log.old_status"
                class="text-gray-400"
              >→</span>
              <span :class="['px-2 py-0.5 rounded text-xs', statusColors[log.new_status]]">
                {{ statusLabels[log.new_status] }}
              </span>
            </div>
            <p
              v-if="log.reason"
              class="mt-2 text-sm text-gray-600 dark:text-gray-400"
            >
              原因：{{ log.reason }}
            </p>
          </div>
        </div>
        <div class="flex justify-end mt-6">
          <button
            class="px-4 py-2 text-sm bg-gray-100 dark:bg-dark-100 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-50 transition-colors"
            @click="showLogsModal = false"
          >
            关闭
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showDeleteModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    >
      <div class="glass-card p-6 w-full max-w-md mx-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          删除评论
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          请选择删除方式：
        </p>
        <div class="space-y-3 mb-6">
          <label
            class="flex items-start gap-3 p-3 border border-gray-200 dark:border-white/10 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-dark-100 transition-colors"
            :class="{ 'border-primary bg-primary/5 dark:bg-primary/10': deleteType === 'soft' }"
          >
            <input id="input-deleteType-soft"
              v-model="deleteType"
              type="radio"
              value="soft"
              class="mt-1"
            >
            <div>
              <div class="font-medium text-gray-900 dark:text-white">保留记录（推荐）</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">评论将显示为"此评论已被管理员删除"，保留嵌套结构和审核日志</div>
            </div>
          </label>
          <label
            class="flex items-start gap-3 p-3 border border-gray-200 dark:border-white/10 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-dark-100 transition-colors"
            :class="{ 'border-red-500 bg-red-50 dark:bg-red-900/20': deleteType === 'permanent' }"
          >
            <input id="input-deleteType-permanent"
              v-model="deleteType"
              type="radio"
              value="permanent"
              class="mt-1"
            >
            <div>
              <div class="font-medium text-gray-900 dark:text-white">彻底删除</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">永久删除评论及所有相关记录，包括审核日志，此操作不可恢复</div>
            </div>
          </label>
        </div>
        <div class="flex justify-end gap-3">
          <button
            class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-100 rounded-lg transition-colors"
            @click="showDeleteModal = false"
          >
            取消
          </button>
          <button
            :class="[
              'px-4 py-2 text-sm text-white rounded-lg transition-colors',
              deleteType === 'permanent' 
                ? 'bg-red-500 hover:bg-red-600' 
                : 'bg-primary hover:bg-primary/90'
            ]"
            @click="confirmDelete"
          >
            {{ deleteType === 'permanent' ? '彻底删除' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showBatchDeleteModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    >
      <div class="glass-card p-6 w-full max-w-md mx-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          批量删除评论
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          将删除 <span class="font-medium text-red-500">{{ selectedComments.length }}</span> 条评论，请选择删除方式：
        </p>
        <div class="space-y-3 mb-6">
          <label
            class="flex items-start gap-3 p-3 border border-gray-200 dark:border-white/10 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-dark-100 transition-colors"
            :class="{ 'border-primary bg-primary/5 dark:bg-primary/10': batchDeleteType === 'soft' }"
          >
            <input id="input-batchDeleteType-soft"
              v-model="batchDeleteType"
              type="radio"
              value="soft"
              class="mt-1"
            >
            <div>
              <div class="font-medium text-gray-900 dark:text-white">保留记录（推荐）</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">评论将显示为"此评论已被管理员删除"，保留嵌套结构和审核日志</div>
            </div>
          </label>
          <label
            class="flex items-start gap-3 p-3 border border-gray-200 dark:border-white/10 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-dark-100 transition-colors"
            :class="{ 'border-red-500 bg-red-50 dark:bg-red-900/20': batchDeleteType === 'permanent' }"
          >
            <input id="input-batchDeleteType-permanent"
              v-model="batchDeleteType"
              type="radio"
              value="permanent"
              class="mt-1"
            >
            <div>
              <div class="font-medium text-gray-900 dark:text-white">彻底删除</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">永久删除评论及所有相关记录，包括审核日志，此操作不可恢复</div>
            </div>
          </label>
        </div>
        <div class="flex justify-end gap-3">
          <button
            class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-100 rounded-lg transition-colors"
            @click="showBatchDeleteModal = false"
          >
            取消
          </button>
          <button
            :class="[
              'px-4 py-2 text-sm text-white rounded-lg transition-colors',
              batchDeleteType === 'permanent' 
                ? 'bg-red-500 hover:bg-red-600' 
                : 'bg-primary hover:bg-primary/90'
            ]"
            @click="confirmBatchDelete"
          >
            {{ batchDeleteType === 'permanent' ? '彻底删除' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>

    <DeletionConfirmDialog
      :visible="commentDeletion.showDeletionDialog.value"
      :preview="commentDeletion.deletionPreview.value"
      :loading="commentDeletionLoading"
      @confirm="executeCommentDeletion"
      @cancel="commentDeletion.cancelDeletion()"
    />
  </div>
</template>
