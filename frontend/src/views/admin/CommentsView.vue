<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { commentApi } from '@/api'
import type { AdminComment, CommentAuditLog, PaginatedResponse } from '@/types'
import { useDialogStore, useUserProfileStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'

const dialog = useDialogStore()
const userProfileStore = useUserProfileStore()
const { requireAdmin, isAdmin } = useAdminCheck()

const comments = ref<AdminComment[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = ref(0)
const statusFilter = ref<string>('')
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
    const response: PaginatedResponse<AdminComment> = await commentApi.getAdminComments(params as Parameters<typeof commentApi.getAdminComments>[0])
    comments.value = response.items
    total.value = response.total
    totalPages.value = response.total_pages
  } catch (error) {
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
  if (!await requireAdmin('审核评论')) return
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
  if (!await requireAdmin('批量审核评论')) return
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
  if (!await requireAdmin('删除评论')) return
  deleteTargetComment.value = comment
  deleteType.value = 'soft'
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!deleteTargetComment.value) return
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

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

onMounted(() => {
  if (!isAdmin.value) return
  fetchComments()
})

watch(() => userProfileStore.avatarUpdatedAt, () => {
  if (!loading.value) {
    fetchComments()
  }
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">评论管理</h1>
      <div class="flex items-center gap-4">
        <span v-if="pendingCount > 0 && isAdmin" class="px-3 py-1 bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400 rounded-full text-sm font-medium">
          {{ pendingCount }} 条待审核
        </span>
      </div>
    </div>

    <div v-if="!isAdmin" class="bg-white dark:bg-dark-200 rounded-xl border border-gray-200 dark:border-white/10 p-8 text-center">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
        <svg class="w-8 h-8 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">权限不足</h2>
      <p class="text-gray-500 dark:text-gray-400">您没有权限访问此页面，请联系管理员</p>
    </div>

    <div v-else class="bg-white dark:bg-dark-200 rounded-xl border border-gray-200 dark:border-white/10 overflow-hidden">
      <div class="p-4 border-b border-gray-200 dark:border-white/10 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <select
            v-model="statusFilter"
            @change="handleStatusFilter"
            class="px-3 py-2 bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          >
            <option v-for="option in statusOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <div v-if="selectedComments.length > 0" class="flex items-center gap-2">
          <span class="text-sm text-gray-500 dark:text-gray-400">
            已选择 {{ selectedComments.length }} 条
          </span>
          <button
            @click="openBatchAuditModal('approved')"
            class="px-3 py-1.5 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 transition-colors"
          >
            批量通过
          </button>
          <button
            @click="openBatchAuditModal('rejected')"
            class="px-3 py-1.5 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 transition-colors"
          >
            批量拒绝
          </button>
        </div>
      </div>

      <div v-if="loading" class="p-8 text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
      </div>

      <div v-else-if="comments.length === 0" class="p-8 text-center text-gray-500 dark:text-gray-400">
        暂无评论
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-dark-100">
            <tr>
              <th class="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  :checked="selectedComments.length === comments.length && comments.length > 0"
                  @change="toggleSelectAll"
                  class="rounded border-gray-300 dark:border-white/20"
                />
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">ID</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">内容</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">文章</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">作者</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">状态</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">时间</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-white/10">
            <tr v-for="comment in comments" :key="comment.id" class="hover:bg-gray-50 dark:hover:bg-dark-100/50">
              <td class="px-4 py-3">
                <input
                  type="checkbox"
                  :checked="selectedComments.includes(comment.id)"
                  @change="toggleSelect(comment.id)"
                  class="rounded border-gray-300 dark:border-white/20"
                />
              </td>
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">{{ comment.id }}</td>
              <td class="px-4 py-3">
                <div class="max-w-xs truncate text-sm text-gray-900 dark:text-white">
                  {{ comment.content }}
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
                <span v-else class="text-gray-500">
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
                    @click="openAuditModal(comment, 'approved')"
                    class="px-2 py-1 text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors"
                  >
                    通过
                  </button>
                  <button
                    v-if="comment.status !== 'rejected'"
                    @click="openAuditModal(comment, 'rejected')"
                    class="px-2 py-1 text-xs bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 rounded hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
                  >
                    拒绝
                  </button>
                  <button
                    @click="openLogsModal(comment)"
                    class="px-2 py-1 text-xs bg-gray-100 text-gray-700 dark:bg-dark-100 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-dark-50 transition-colors"
                  >
                    日志
                  </button>
                  <button
                    @click="openDeleteModal(comment)"
                    class="px-2 py-1 text-xs bg-gray-100 text-red-600 dark:bg-dark-100 dark:text-red-400 rounded hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="totalPages > 1" class="p-4 border-t border-gray-200 dark:border-white/10 flex items-center justify-between">
        <div class="text-sm text-gray-500 dark:text-gray-400">
          共 {{ total }} 条评论
        </div>
        <div class="flex items-center gap-2">
          <button
            :disabled="currentPage === 1"
            @click="handlePageChange(currentPage - 1)"
            class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-dark-50 transition-colors"
          >
            上一页
          </button>
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ currentPage }} / {{ totalPages }}
          </span>
          <button
            :disabled="currentPage === totalPages"
            @click="handlePageChange(currentPage + 1)"
            class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-dark-50 transition-colors"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <div v-if="showAuditModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-200 rounded-xl p-6 w-full max-w-md mx-4">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-4">审核评论</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">状态</label>
            <select
              v-model="auditStatus"
              class="w-full px-3 py-2 bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="pending">待审核</option>
              <option value="approved">已通过</option>
              <option value="rejected">已拒绝</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">原因（可选）</label>
            <textarea
              v-model="auditReason"
              rows="3"
              class="w-full px-3 py-2 bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="请输入审核原因..."
            ></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button
            @click="showAuditModal = false"
            class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-100 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            @click="submitAudit"
            class="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            确认
          </button>
        </div>
      </div>
    </div>

    <div v-if="showBatchAuditModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-200 rounded-xl p-6 w-full max-w-md mx-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">批量审核</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          将对 {{ selectedComments.length }} 条评论进行批量操作
        </p>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">状态</label>
            <select
              v-model="batchAuditStatus"
              class="w-full px-3 py-2 bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="pending">待审核</option>
              <option value="approved">已通过</option>
              <option value="rejected">已拒绝</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">原因（可选）</label>
            <textarea
              v-model="batchAuditReason"
              rows="3"
              class="w-full px-3 py-2 bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="请输入审核原因..."
            ></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button
            @click="showBatchAuditModal = false"
            class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-100 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            @click="submitBatchAudit"
            class="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            确认
          </button>
        </div>
      </div>
    </div>

    <div v-if="showLogsModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-200 rounded-xl p-6 w-full max-w-lg mx-4 max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">审核日志</h3>
          <button
            @click="showLogsModal = false"
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div v-if="auditLogs.length === 0" class="text-center text-gray-500 dark:text-gray-400 py-8">
          暂无审核记录
        </div>
        <div v-else class="space-y-4">
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
              <span v-if="log.old_status" class="text-gray-400">→</span>
              <span :class="['px-2 py-0.5 rounded text-xs', statusColors[log.new_status]]">
                {{ statusLabels[log.new_status] }}
              </span>
            </div>
            <p v-if="log.reason" class="mt-2 text-sm text-gray-600 dark:text-gray-400">
              原因：{{ log.reason }}
            </p>
          </div>
        </div>
        <div class="flex justify-end mt-6">
          <button
            @click="showLogsModal = false"
            class="px-4 py-2 text-sm bg-gray-100 dark:bg-dark-100 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-50 transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    </div>

    <div v-if="showDeleteModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-200 rounded-xl p-6 w-full max-w-md mx-4">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-4">删除评论</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          请选择删除方式：
        </p>
        <div class="space-y-3 mb-6">
          <label class="flex items-start gap-3 p-3 border border-gray-200 dark:border-white/10 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-dark-100 transition-colors" :class="{ 'border-primary bg-primary/5 dark:bg-primary/10': deleteType === 'soft' }">
            <input type="radio" v-model="deleteType" value="soft" class="mt-1" />
            <div>
              <div class="font-medium text-gray-900 dark:text-white">保留记录（推荐）</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">评论将显示为"此评论已被管理员删除"，保留嵌套结构和审核日志</div>
            </div>
          </label>
          <label class="flex items-start gap-3 p-3 border border-gray-200 dark:border-white/10 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-dark-100 transition-colors" :class="{ 'border-red-500 bg-red-50 dark:bg-red-900/20': deleteType === 'permanent' }">
            <input type="radio" v-model="deleteType" value="permanent" class="mt-1" />
            <div>
              <div class="font-medium text-gray-900 dark:text-white">彻底删除</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">永久删除评论及所有相关记录，包括审核日志，此操作不可恢复</div>
            </div>
          </label>
        </div>
        <div class="flex justify-end gap-3">
          <button
            @click="showDeleteModal = false"
            class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-100 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            @click="confirmDelete"
            :class="[
              'px-4 py-2 text-sm text-white rounded-lg transition-colors',
              deleteType === 'permanent' 
                ? 'bg-red-500 hover:bg-red-600' 
                : 'bg-primary hover:bg-primary/90'
            ]"
          >
            {{ deleteType === 'permanent' ? '彻底删除' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
