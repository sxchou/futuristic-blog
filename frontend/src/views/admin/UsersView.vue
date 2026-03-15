<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userApi } from '@/api'
import type { User } from '@/types'
import ModalDialog from '@/components/common/ModalDialog.vue'

const users = ref<User[]>([])
const isLoading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 10

const showEditor = ref(false)
const editingUser = ref<User | null>(null)
const showPasswordModal = ref(false)
const newPassword = ref('')

const dialogVisible = ref(false)
const dialogOptions = ref({
  title: '',
  message: '',
  type: 'alert' as 'confirm' | 'alert' | 'success' | 'error'
})
let dialogResolve: ((value: boolean) => void) | null = null

const showDialog = (options: { title?: string; message: string; type?: 'confirm' | 'alert' | 'success' | 'error' }): Promise<boolean> => {
  dialogOptions.value = { title: '', message: '', type: 'alert', ...options }
  dialogVisible.value = true
  return new Promise((resolve) => {
    dialogResolve = resolve
  })
}

const onDialogConfirm = () => {
  dialogVisible.value = false
  if (dialogResolve) {
    dialogResolve(true)
    dialogResolve = null
  }
}

const onDialogCancel = () => {
  dialogVisible.value = false
  if (dialogResolve) {
    dialogResolve(false)
    dialogResolve = null
  }
}

const form = ref({
  username: '',
  email: '',
  bio: '',
  is_admin: false
})

const fetchUsers = async () => {
  isLoading.value = true
  try {
    const response = await userApi.getUsers(currentPage.value, pageSize)
    users.value = response.items
    totalPages.value = response.total_pages
  } catch (error) {
    console.error('Failed to fetch users:', error)
  } finally {
    isLoading.value = false
  }
}

const handleEdit = (user: User) => {
  editingUser.value = user
  form.value = {
    username: user.username,
    email: user.email,
    bio: user.bio || '',
    is_admin: user.is_admin
  }
  showEditor.value = true
}

const handleDelete = async (user: User) => {
  const confirmed = await showDialog({
    title: '确认删除',
    message: `确定要删除用户"${user.username}"吗？`,
    type: 'confirm'
  })
  if (!confirmed) return
  
  try {
    await userApi.deleteUser(user.id)
    await fetchUsers()
    await showDialog({ title: '成功', message: '用户已删除', type: 'success' })
  } catch (error: any) {
    console.error('Failed to delete user:', error)
    await showDialog({ title: '错误', message: error.response?.data?.detail || '删除失败', type: 'error' })
  }
}

const handleSubmit = async () => {
  try {
    if (editingUser.value) {
      await userApi.updateUser(editingUser.value.id, form.value)
    }
    showEditor.value = false
    editingUser.value = null
    await fetchUsers()
    await showDialog({ title: '成功', message: '用户信息已更新', type: 'success' })
  } catch (error: any) {
    console.error('Failed to save user:', error)
    await showDialog({ title: '错误', message: error.response?.data?.detail || '保存失败', type: 'error' })
  }
}

const handleResetPassword = async () => {
  if (!editingUser.value || !newPassword.value) return
  
  try {
    await userApi.resetPassword(editingUser.value.id, newPassword.value)
    showPasswordModal.value = false
    newPassword.value = ''
    await showDialog({ title: '成功', message: '密码重置成功', type: 'success' })
  } catch (error: any) {
    console.error('Failed to reset password:', error)
    if (error.response?.status === 403) {
      await showDialog({ title: '权限不足', message: '无权限重置密码', type: 'error' })
    } else {
      await showDialog({ title: '错误', message: error.response?.data?.detail || '密码重置失败', type: 'error' })
    }
  }
}

const openPasswordModal = (user: User) => {
  editingUser.value = user
  newPassword.value = ''
  showPasswordModal.value = true
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    fetchUsers()
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    fetchUsers()
  }
}

onMounted(fetchUsers)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold text-gray-900 dark:text-white">用户管理</h1>
    </div>

    <div v-if="isLoading" class="flex justify-center py-16">
      <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <div v-else class="glass-card overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-100 dark:bg-dark-100">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">用户</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">邮箱</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">角色</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">状态</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">注册时间</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-white/5">
          <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50 dark:hover:bg-white/5">
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <div
                  class="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-medium"
                >
                  {{ user.username.charAt(0).toUpperCase() }}
                </div>
                <div>
                  <p class="text-gray-900 dark:text-white font-medium">{{ user.username }}</p>
                  <p class="text-gray-500 text-xs">{{ user.bio || '暂无简介' }}</p>
                </div>
              </div>
            </td>
            <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{{ user.email }}</td>
            <td class="px-4 py-3">
              <span
                :class="[
                  'px-2 py-1 text-xs rounded',
                  user.is_admin
                    ? 'bg-accent/20 text-accent'
                    : 'bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-400'
                ]"
              >
                {{ user.is_admin ? '管理员' : '普通用户' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <span
                :class="[
                  'px-2 py-1 text-xs rounded',
                  user.is_verified
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-yellow-500/20 text-yellow-400'
                ]"
              >
                {{ user.is_verified ? '已验证' : '未验证' }}
              </span>
            </td>
            <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{{ formatDate(user.created_at) }}</td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-2">
                <button
                  @click="handleEdit(user)"
                  class="text-primary hover:text-primary/80 text-xs"
                >
                  编辑
                </button>
                <button
                  @click="openPasswordModal(user)"
                  class="text-accent hover:text-accent/80 text-xs"
                >
                  重置密码
                </button>
                <button
                  @click="handleDelete(user)"
                  class="text-red-400 hover:text-red-300 text-xs"
                >
                  删除
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="totalPages > 1" class="flex items-center justify-center gap-4 mt-4">
        <button
          @click="prevPage"
          :disabled="currentPage === 1"
          class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-dark-200 transition-colors"
        >
          上一页
        </button>
        <span class="text-sm text-gray-500">
          {{ currentPage }} / {{ totalPages }}
        </span>
        <button
          @click="nextPage"
          :disabled="currentPage === totalPages"
          class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-dark-200 transition-colors"
        >
          下一页
        </button>
      </div>
    </div>

    <div
      v-if="showEditor"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    >
      <div class="glass-card w-full max-w-md m-4 p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-bold text-gray-900 dark:text-white">编辑用户</h2>
          <button
            @click="showEditor = false"
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">用户名</label>
            <input
              v-model="form.username"
              type="text"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="用户名"
            />
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">邮箱</label>
            <input
              v-model="form.email"
              type="email"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="邮箱地址"
            />
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">简介</label>
            <textarea
              v-model="form.bio"
              rows="2"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="个人简介"
            />
          </div>

          <div>
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                v-model="form.is_admin"
                class="rounded border-gray-300 dark:border-white/20 bg-white dark:bg-dark-200 text-primary focus:ring-primary"
              />
              <span class="text-gray-700 dark:text-gray-300 text-sm">管理员权限</span>
            </label>
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              @click="showEditor = false"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              class="btn-primary text-sm px-4 py-1.5"
            >
              保存
            </button>
          </div>
        </form>
      </div>
    </div>

    <div
      v-if="showPasswordModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    >
      <div class="glass-card w-full max-w-sm m-4 p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-bold text-gray-900 dark:text-white">重置密码</h2>
          <button
            @click="showPasswordModal = false"
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="handleResetPassword" class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">新密码</label>
            <input
              v-model="newPassword"
              type="password"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="请输入新密码"
            />
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              @click="showPasswordModal = false"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              class="btn-primary text-sm px-4 py-1.5"
            >
              确认重置
            </button>
          </div>
        </form>
      </div>
    </div>

    <ModalDialog
      v-model="dialogVisible"
      :title="dialogOptions.title"
      :message="dialogOptions.message"
      :type="dialogOptions.type"
      @confirm="onDialogConfirm"
      @cancel="onDialogCancel"
    />
  </div>
</template>
