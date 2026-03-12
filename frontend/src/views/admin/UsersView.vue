<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userApi } from '@/api'
import type { User } from '@/types'

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
  if (!confirm(`确定要删除用户"${user.username}"吗？`)) return
  
  try {
    await userApi.deleteUser(user.id)
    await fetchUsers()
  } catch (error: any) {
    console.error('Failed to delete user:', error)
    alert(error.response?.data?.detail || '删除失败')
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
  } catch (error: any) {
    console.error('Failed to save user:', error)
    alert(error.response?.data?.detail || '保存失败')
  }
}

const handleResetPassword = async () => {
  if (!editingUser.value || !newPassword.value) return
  
  try {
    await userApi.resetPassword(editingUser.value.id, newPassword.value)
    showPasswordModal.value = false
    newPassword.value = ''
    alert('密码重置成功')
  } catch (error: any) {
    console.error('Failed to reset password:', error)
    if (error.response?.status === 403) {
      alert('无权限重置密码')
    } else {
      alert(error.response?.data?.detail || '密码重置失败')
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

    <div v-else>
      <div class="glass-card overflow-hidden">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-dark-100">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">用户</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">邮箱</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">角色</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">邮箱验证</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">注册时间</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-white/10">
            <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50 dark:hover:bg-white/5">
              <td class="px-4 py-3">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-full bg-gradient-to-r from-primary to-accent flex items-center justify-center text-white text-sm font-medium">
                    {{ user.username.charAt(0).toUpperCase() }}
                  </div>
                  <div>
                    <div class="text-sm font-medium text-gray-900 dark:text-white">{{ user.username }}</div>
                    <div v-if="user.bio" class="text-xs text-gray-500 truncate max-w-[200px]">{{ user.bio }}</div>
                  </div>
                </div>
              </td>
              <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{{ user.email }}</td>
              <td class="px-4 py-3">
                <span
                  :class="user.is_admin ? 'bg-primary/20 text-primary' : 'bg-gray-100 dark:bg-dark-100 text-gray-500 dark:text-gray-400'"
                  class="px-2 py-1 text-xs rounded-full"
                >
                  {{ user.is_admin ? '管理员' : '普通用户' }}
                </span>
              </td>
              <td class="px-4 py-3">
                <span
                  :class="user.is_verified ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'"
                  class="px-2 py-1 text-xs rounded-full"
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
      </div>

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
              placeholder="邮箱"
            />
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">简介</label>
            <textarea
              v-model="form.bio"
              rows="2"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="用户简介"
            />
          </div>

          <div class="flex items-center gap-2">
            <input
              v-model="form.is_admin"
              type="checkbox"
              id="is_admin"
              class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <label for="is_admin" class="text-sm text-gray-700 dark:text-gray-300">管理员权限</label>
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
      <div class="glass-card w-full max-w-md m-4 p-5">
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

        <div class="space-y-3">
          <p class="text-sm text-gray-500 dark:text-gray-400">
            为用户 <span class="text-primary font-medium">{{ editingUser?.username }}</span> 设置新密码
          </p>
          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">新密码</label>
            <input
              v-model="newPassword"
              type="text"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="输入新密码"
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
              @click="handleResetPassword"
              :disabled="!newPassword"
              class="btn-primary text-sm px-4 py-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              确认重置
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
