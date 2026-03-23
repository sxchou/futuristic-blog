<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { userApi } from '@/api'
import type { User } from '@/types'
import { useDialogStore, useUserProfileStore, useAuthStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { formatDateTime } from '@/utils/date'

const dialog = useDialogStore()
const userProfileStore = useUserProfileStore()
const authStore = useAuthStore()
const { requireAdmin, isAdmin } = useAdminCheck()

const users = ref<User[]>([])
const isLoading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 10

const showEditor = ref(false)
const editingUser = ref<User | null>(null)
const showPasswordModal = ref(false)
const newPassword = ref('')

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

const handleEdit = async (user: User) => {
  if (!await requireAdmin('编辑用户信息')) return
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
  if (!await requireAdmin('删除用户')) return
  
  const confirmed = await dialog.showConfirm({
    title: '确认删除',
    message: `确定要删除用户"${user.username}"吗？此操作不可恢复。`
  })
  if (!confirmed) return
  
  try {
    await userApi.deleteUser(user.id)
    await fetchUsers()
    await dialog.showSuccess('用户已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete user:', error)
    await dialog.showError(error.response?.data?.detail || '删除失败', '错误')
  }
}

const handleSubmit = async () => {
  if (!await requireAdmin('保存用户信息')) return
  
  try {
    if (editingUser.value) {
      await userApi.updateUser(editingUser.value.id, form.value)
    }
    showEditor.value = false
    editingUser.value = null
    await fetchUsers()
    await dialog.showSuccess('用户信息已更新', '成功')
  } catch (error: any) {
    console.error('Failed to save user:', error)
    await dialog.showError(error.response?.data?.detail || '保存失败', '错误')
  }
}

const handleResetPassword = async () => {
  if (!await requireAdmin('重置用户密码')) return
  if (!editingUser.value || !newPassword.value) return
  
  try {
    await userApi.resetPassword(editingUser.value.id, newPassword.value)
    showPasswordModal.value = false
    newPassword.value = ''
    await dialog.showSuccess('密码重置成功', '成功')
  } catch (error: any) {
    console.error('Failed to reset password:', error)
    await dialog.showError(error.response?.data?.detail || '密码重置失败', '错误')
  }
}

const openPasswordModal = async (user: User) => {
  if (!await requireAdmin('重置用户密码')) return
  editingUser.value = user
  newPassword.value = ''
  showPasswordModal.value = true
}

const formatDate = (date: string) => formatDateTime(date)

const getUserAvatarStyle = (user: User) => {
  if (user.avatar_type === 'custom' && user.avatar_url) {
    return {
      backgroundImage: `url(${user.avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (user.avatar_type === 'oauth' && user.oauth_avatar_url) {
    return {
      backgroundImage: `url(${user.oauth_avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (user.avatar_gradient && user.avatar_gradient.length >= 2) {
    return {
      background: `linear-gradient(135deg, ${user.avatar_gradient[0]}, ${user.avatar_gradient[1]})`
    }
  }
  
  return {
    background: 'linear-gradient(135deg, #667eea, #764ba2)'
  }
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

onMounted(async () => {
  await authStore.waitForInit()
  if (!isAdmin.value) return
  fetchUsers()
})

watch(() => userProfileStore.avatarUpdatedAt, () => {
  if (!isLoading.value) {
    fetchUsers()
  }
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">用户管理</h1>
    </div>

    <div v-if="!isAdmin" class="glass-card p-8 text-center">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
        <svg class="w-8 h-8 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">权限不足</h2>
      <p class="text-gray-500 dark:text-gray-400">您没有权限访问此页面，请联系管理员</p>
    </div>

    <div v-else-if="isLoading" class="flex justify-center py-16">
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
                  class="w-8 h-8 rounded-full flex items-center justify-center text-white font-medium overflow-hidden flex-shrink-0"
                  :style="getUserAvatarStyle(user)"
                >
                  <span v-if="user.avatar_type === 'default' || (user.avatar_type === 'custom' && !user.avatar_url) || (user.avatar_type === 'oauth' && !user.oauth_avatar_url)">
                    {{ user.username.charAt(0).toUpperCase() }}
                  </span>
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
            <label for="user-username" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">用户名</label>
            <input
              v-model="form.username"
              type="text"
              id="user-username"
              name="username"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="用户名"
            />
          </div>

          <div>
            <label for="user-email" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">邮箱</label>
            <input
              v-model="form.email"
              type="email"
              id="user-email"
              name="email"
              autocomplete="email"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="邮箱地址"
            />
          </div>

          <div>
            <label for="user-bio" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">简介</label>
            <textarea
              v-model="form.bio"
              id="user-bio"
              name="bio"
              rows="3"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="个人简介"
            />
          </div>

          <div>
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                v-model="form.is_admin"
                id="user-is-admin"
                name="is_admin"
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
            <label for="user-new-password" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">新密码</label>
            <input
              v-model="newPassword"
              type="password"
              id="user-new-password"
              name="new-password"
              autocomplete="new-password"
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
  </div>
</template>
