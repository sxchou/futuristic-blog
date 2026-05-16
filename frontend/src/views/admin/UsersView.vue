<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { userApi, roleApi } from '@/api'
import { clearCacheByPattern } from '@/api/client'
import type { User, Role } from '@/types'
import { useDialogStore, useUserProfileStore, useAuthStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { useRoleColor } from '@/composables/useRoleColor'
import { useDeletionConfirm } from '@/composables/useDeletionConfirm'
import DeletionConfirmDialog from '@/components/common/DeletionConfirmDialog.vue'
import DateRangePicker from '@/components/common/DateRangePicker.vue'
import { formatDateTime } from '@/utils/date'

const { getRoleColorClasses } = useRoleColor()

const dialog = useDialogStore()
const userProfileStore = useUserProfileStore()
const authStore = useAuthStore()
const { requirePermission, hasPermission } = useAdminCheck()
const deletion = useDeletionConfirm()

const users = ref<User[]>([])
const isLoading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 10

const usernameFilter = ref<string>('')
const emailFilter = ref<string>('')
const roleFilter = ref<string>('')
const statusFilter = ref<string>('')

const startDateFilter = ref<string>('')
const endDateFilter = ref<string>('')

const showEditor = ref(false)
const isSubmitting = ref(false)
const editingUser = ref<User | null>(null)
const showPasswordModal = ref(false)
const isResetting = ref(false)
const newPassword = ref('')
const passwordError = ref('')

const showRoleModal = ref(false)
const roleAssignUser = ref<User | null>(null)
const allRoles = ref<Role[]>([])
const selectedRoleIds = ref<number[]>([])
const roleError = ref('')

const form = ref({
  username: '',
  email: '',
  bio: ''
})

const showCreateModal = ref(false)
const isCreating = ref(false)
const createForm = ref({
  username: '',
  email: '',
  password: '',
  roleIds: [] as number[]
})

const usernameChecking = ref(false)
const emailChecking = ref(false)
const usernameExists = ref(false)
const emailExists = ref(false)

let usernameCheckTimer: ReturnType<typeof setTimeout> | null = null
let emailCheckTimer: ReturnType<typeof setTimeout> | null = null

const checkUsernameUnique = async (username: string) => {
  if (!username.trim()) {
    usernameExists.value = false
    return
  }
  
  usernameChecking.value = true
  try {
    const result = await userApi.checkUnique('username', username)
    usernameExists.value = result.exists
    if (result.exists) {
      createErrors.value = createErrors.value.filter(e => e.field !== 'username')
      createErrors.value.push({ field: 'username', message: '用户名已存在' })
    } else {
      createErrors.value = createErrors.value.filter(e => e.field !== 'username')
    }
  } catch (error) {
    console.error('Failed to check username uniqueness:', error)
  } finally {
    usernameChecking.value = false
  }
}

const checkEmailUnique = async (email: string) => {
  if (!email.trim()) {
    emailExists.value = false
    return
  }
  
  emailChecking.value = true
  try {
    const result = await userApi.checkUnique('email', email)
    emailExists.value = result.exists
    if (result.exists) {
      createErrors.value = createErrors.value.filter(e => e.field !== 'email')
      createErrors.value.push({ field: 'email', message: '邮箱已存在' })
    } else {
      createErrors.value = createErrors.value.filter(e => e.field !== 'email')
    }
  } catch (error) {
    console.error('Failed to check email uniqueness:', error)
  } finally {
    emailChecking.value = false
  }
}

watch(() => createForm.value.username, (newUsername) => {
  if (usernameCheckTimer) {
    clearTimeout(usernameCheckTimer)
  }
  usernameExists.value = false
  createErrors.value = createErrors.value.filter(e => e.field !== 'username')
  
  if (newUsername.trim()) {
    usernameCheckTimer = setTimeout(() => {
      checkUsernameUnique(newUsername)
    }, 800)
  }
})

watch(() => createForm.value.email, (newEmail) => {
  if (emailCheckTimer) {
    clearTimeout(emailCheckTimer)
  }
  emailExists.value = false
  createErrors.value = createErrors.value.filter(e => e.field !== 'email')
  
  if (newEmail.trim()) {
    emailCheckTimer = setTimeout(() => {
      checkEmailUnique(newEmail)
    }, 800)
  }
})

const fetchUsers = async () => {
  isLoading.value = true
  try {
    const params: Record<string, unknown> = {
      page: currentPage.value,
      page_size: pageSize
    }
    if (usernameFilter.value) {
      params.username = usernameFilter.value
    }
    if (emailFilter.value) {
      params.email = emailFilter.value
    }
    if (roleFilter.value) {
      params.role = roleFilter.value
    }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    if (startDateFilter.value) {
      params.start_date = startDateFilter.value
    }
    if (endDateFilter.value) {
      params.end_date = endDateFilter.value
    }
    const response = await userApi.getUsers(params)
    users.value = response.items
    totalPages.value = response.total_pages
  } catch (error) {
    console.error('Failed to fetch users:', error)
  } finally {
    isLoading.value = false
  }
}

const handleEdit = async (user: User) => {
  if (!await requirePermission('user.edit', '编辑用户信息')) return
  editingUser.value = user
  form.value = {
    username: user.username,
    email: user.email,
    bio: user.bio || ''
  }
  editErrors.value = []
  showEditor.value = true
}

const handleCreate = async () => {
  if (!await requirePermission('user.create', '创建用户')) return
  createForm.value = {
    username: '',
    email: '',
    password: '',
    roleIds: []
  }
  usernameExists.value = false
  emailExists.value = false
  usernameChecking.value = false
  emailChecking.value = false
  createErrors.value = []
  showCreateModal.value = true
}

const handleCreateSubmit = async () => {
  if (isCreating.value) return
  
  if (!requirePermission('user.create')) return
  
  createErrors.value = []
  
  if (!createForm.value.username) {
    createErrors.value.push({ field: 'username', message: '请输入用户名' })
  } else if (createForm.value.username.length < 3) {
    createErrors.value.push({ field: 'username', message: '用户名长度至少需要3个字符' })
  }
  
  if (!createForm.value.email) {
    createErrors.value.push({ field: 'email', message: '请输入邮箱地址' })
  } else {
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
    if (!emailPattern.test(createForm.value.email)) {
      createErrors.value.push({ field: 'email', message: '请输入正确的邮箱格式' })
    }
  }
  
  if (!createForm.value.password) {
    createErrors.value.push({ field: 'password', message: '请输入密码' })
  } else if (createForm.value.password.length < 6) {
    createErrors.value.push({ field: 'password', message: '密码长度至少需要6个字符' })
  }
  
  if (createForm.value.roleIds.length === 0) {
    createErrors.value.push({ field: 'roleIds', message: '请至少选择一个角色' })
  }
  
  if (usernameChecking.value || emailChecking.value) {
    await new Promise(resolve => setTimeout(resolve, 600))
  }
  
  if (usernameExists.value) {
    const existing = createErrors.value.find(e => e.field === 'username')
    if (!existing) createErrors.value.push({ field: 'username', message: '用户名已存在，请使用其他用户名' })
  }
  
  if (emailExists.value) {
    const existing = createErrors.value.find(e => e.field === 'email')
    if (!existing) createErrors.value.push({ field: 'email', message: '邮箱已存在，请使用其他邮箱' })
  }
  
  if (createErrors.value.length > 0) {
    const firstError = createErrors.value[0]
    const fieldIdMap: Record<string, string> = {
      username: 'create-username',
      email: 'create-email',
      password: 'create-password',
      roleIds: 'create-roles'
    }
    await scrollToField(fieldIdMap[firstError.field] || firstError.field)
    return
  }
  
  isCreating.value = true
  try {
    await userApi.createUser({
      username: createForm.value.username,
      email: createForm.value.email,
      password: createForm.value.password,
      role_ids: createForm.value.roleIds
    })
    clearCacheByPattern('/users')
    showCreateModal.value = false
    await fetchUsers()
    await dialog.showSuccess('用户创建成功', '成功')
  } catch (error: any) {
    console.error('Failed to create user:', error)
  } finally {
    isCreating.value = false
  }
}

const toggleCreateRole = (roleId: number) => {
  const index = createForm.value.roleIds.indexOf(roleId)
  if (index === -1) {
    createForm.value.roleIds.push(roleId)
  } else {
    createForm.value.roleIds.splice(index, 1)
  }
}

const canResetPassword = (user: User): boolean => {
  const currentUser = authStore.user
  if (!currentUser) return false
  if (!hasPermission('user.reset_password')) return false
  if (user.id === 1) return false
  if (currentUser.id !== 1 && user.is_admin) return false
  return true
}

const handleDelete = async (user: User) => {
  if (!await requirePermission('user.delete', '删除用户')) return
  
  const previewed = await deletion.requestDeletion('user', user.id, user.username)
  if (!previewed) return
}

const executeDeletion = async () => {
  try {
    deletionLoading.value = true
    await userApi.deleteUser(deletion.currentItemId.value)
    deletion.confirmDeletion()
    clearCacheByPattern('/users')
    clearCacheByPattern('/articles')
    clearCacheByPattern('/comments')
    await fetchUsers()
    await dialog.showSuccess('用户已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete user:', error)
    deletion.cancelDeletion()
  } finally {
    deletionLoading.value = false
  }
}

const deletionLoading = ref(false)

const handleSubmit = async () => {
  if (!await requirePermission('user.edit', '保存用户信息')) return
  
  editErrors.value = []
  
  if (!form.value.username.trim()) {
    editErrors.value.push({ field: 'username', message: '请输入用户名' })
  } else if (form.value.username.trim().length < 3) {
    editErrors.value.push({ field: 'username', message: '用户名长度至少需要3个字符' })
  }
  
  if (!form.value.email.trim()) {
    editErrors.value.push({ field: 'email', message: '请输入邮箱地址' })
  } else {
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
    if (!emailPattern.test(form.value.email)) {
      editErrors.value.push({ field: 'email', message: '请输入正确的邮箱格式' })
    }
  }
  
  if (editErrors.value.length > 0) {
    const firstError = editErrors.value[0]
    const fieldIdMap: Record<string, string> = { username: 'user-username', email: 'user-email' }
    await scrollToField(fieldIdMap[firstError.field] || firstError.field)
    return
  }
  
  isSubmitting.value = true
  try {
    if (editingUser.value) {
      await userApi.updateUser(editingUser.value.id, form.value)
    }
    clearCacheByPattern('/users')
    clearCacheByPattern('/articles')
    clearCacheByPattern('/comments')
    showEditor.value = false
    editingUser.value = null
    await fetchUsers()
    await dialog.showSuccess('用户信息已更新', '成功')
  } catch (error: any) {
    console.error('Failed to save user:', error)
    await dialog.showError(error.response?.data?.detail || '保存失败', '错误')
  } finally {
    isSubmitting.value = false
  }
}

const fetchRoles = async () => {
  try {
    allRoles.value = await roleApi.getRoles(true)
  } catch (error) {
    console.error('Failed to fetch roles:', error)
  }
}

const openRoleModal = async (user: User) => {
  if (!await requirePermission('role.assign', '分配角色')) return
  roleAssignUser.value = user
  selectedRoleIds.value = user.roles?.map(r => r.id) || []
  roleError.value = ''
  showRoleModal.value = true
}

const handleRoleAssign = async () => {
  if (!roleAssignUser.value) return
  
  roleError.value = ''
  
  if (selectedRoleIds.value.length === 0) {
    roleError.value = '请至少选择一个角色'
    return
  }
  
  try {
    const currentRoleIds = roleAssignUser.value.roles?.map(r => r.id) || []
    const toAdd = selectedRoleIds.value.filter(id => !currentRoleIds.includes(id))
    const toRemove = currentRoleIds.filter(id => !selectedRoleIds.value.includes(id))
    
    if (toAdd.length > 0) {
      await roleApi.assignRoles({
        user_ids: [roleAssignUser.value.id],
        role_ids: toAdd
      })
    }
    
    if (toRemove.length > 0) {
      await roleApi.removeRoles({
        user_ids: [roleAssignUser.value.id],
        role_ids: toRemove
      })
    }
    
    clearCacheByPattern('/users')
    showRoleModal.value = false
    roleAssignUser.value = null
    await fetchUsers()
    await dialog.showSuccess('角色分配成功', '成功')
  } catch (error: any) {
    console.error('Failed to assign roles:', error)
    await dialog.showError(error.response?.data?.detail || '角色分配失败', '错误')
  }
}

const toggleRole = (roleId: number) => {
  roleError.value = ''
  const index = selectedRoleIds.value.indexOf(roleId)
  if (index === -1) {
    selectedRoleIds.value.push(roleId)
  } else {
    selectedRoleIds.value.splice(index, 1)
  }
}

const handleResetPassword = async () => {
  if (!await requirePermission('user.reset_password', '重置用户密码')) return
  
  passwordError.value = ''
  
  if (!newPassword.value) {
    passwordError.value = '请输入新密码'
    return
  }
  
  if (newPassword.value.length < 6) {
    passwordError.value = '密码长度至少需要6个字符'
    return
  }
  
  if (!editingUser.value) return
  
  isResetting.value = true
  try {
    await userApi.resetPassword(editingUser.value.id, newPassword.value)
    showPasswordModal.value = false
    newPassword.value = ''
    await dialog.showSuccess('密码重置成功', '成功')
  } catch (error: any) {
    console.error('Failed to reset password:', error)
    await dialog.showError(error.response?.data?.detail || '密码重置失败', '错误')
  } finally {
    isResetting.value = false
  }
}

const openPasswordModal = async (user: User) => {
  if (!await requirePermission('user.reset_password', '重置用户密码')) return
  if (!canResetPassword(user)) {
    let reason = ''
    if (user.id === 1) {
      reason = '该用户为超级管理员'
    } else if (authStore.user && authStore.user.id !== 1 && user.is_admin) {
      reason = '您没有权限重置管理员的密码'
    } else {
      reason = '无法重置该用户的密码'
    }
    await dialog.showWarning(`无法重置 ${user.username} 的密码`, reason)
    return
  }
  editingUser.value = user
  newPassword.value = ''
  passwordError.value = ''
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
  
  if (user.avatar_gradient && user.avatar_gradient.length >= 1) {
    return {
      backgroundColor: user.avatar_gradient[0]
    }
  }
  
  return {
    backgroundColor: '#667eea'
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

const handleSearch = () => {
  currentPage.value = 1
  fetchUsers()
}

const clearFilters = () => {
  usernameFilter.value = ''
  emailFilter.value = ''
  roleFilter.value = ''
  statusFilter.value = ''
  startDateFilter.value = ''
  endDateFilter.value = ''
  currentPage.value = 1
  fetchUsers()
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Delete') {
    event.preventDefault()
    clearFilters()
  } else if (event.key === 'ArrowLeft' && currentPage.value > 1) {
    event.preventDefault()
    prevPage()
  } else if (event.key === 'ArrowRight' && currentPage.value < totalPages.value) {
    event.preventDefault()
    nextPage()
  }
}

onMounted(() => {
  fetchUsers()
  fetchRoles()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

watch(() => userProfileStore.avatarUpdatedAt, () => {
  if (!isLoading.value) {
    fetchUsers()
  }
})

interface ValidationError {
  field: string
  message: string
}

const createErrors = ref<ValidationError[]>([])
const editErrors = ref<ValidationError[]>([])

const scrollToField = async (fieldId: string) => {
  await nextTick()
  const element = document.getElementById(fieldId)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    element.focus({ preventScroll: true })
  }
}

const hasCreateError = (field: string): boolean => {
  return createErrors.value.some(e => e.field === field)
}

const getCreateErrorMessage = (field: string): string => {
  const error = createErrors.value.find(e => e.field === field)
  return error?.message || ''
}

const clearCreateError = (field: string) => {
  createErrors.value = createErrors.value.filter(e => e.field !== field)
}

const hasEditError = (field: string): boolean => {
  return editErrors.value.some(e => e.field === field)
}

const getEditErrorMessage = (field: string): string => {
  const error = editErrors.value.find(e => e.field === field)
  return error?.message || ''
}

const clearEditError = (field: string) => {
  editErrors.value = editErrors.value.filter(e => e.field !== field)
}
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
              d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          用户管理
        </h1>
      </div>
      <button
        class="btn-primary text-sm px-4 py-1.5 flex items-center gap-2"
        @click="handleCreate"
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
        创建用户
      </button>
    </div>

    <div
      v-if="isLoading"
      class="flex justify-center py-16"
    >
      <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <div
      v-else
      class="glass-card overflow-hidden"
    >
      <div class="p-3 border-b border-gray-200 dark:border-white/10">
        <form 
          class="flex flex-wrap items-center gap-2"
          @submit.prevent="handleSearch"
        >
          <input
            v-model="usernameFilter"
            type="text"
            placeholder="用户名"
            class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-32"
            @keyup.enter="handleSearch"
          >
          <input
            v-model="emailFilter"
            type="text"
            placeholder="邮箱"
            class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-40"
            @keyup.enter="handleSearch"
          >
          <input
            v-model="roleFilter"
            type="text"
            placeholder="角色"
            class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none w-28"
            @keyup.enter="handleSearch"
          >
          <select
            v-model="statusFilter"
            class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none"
            @change="handleSearch"
          >
            <option value="">
              全部状态
            </option>
            <option value="verified">
              已验证
            </option>
            <option value="unverified">
              未验证
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
            @click="handleSearch"
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
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm table-fixed">
          <thead class="bg-gray-100 dark:bg-dark-100">
            <tr>
              <th class="w-48 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                用户
              </th>
              <th class="w-48 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                邮箱
              </th>
              <th class="w-32 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                角色
              </th>
              <th class="w-20 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                状态
              </th>
              <th class="w-28 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                注册时间
              </th>
              <th class="w-44 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                操作
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-white/5">
            <tr
              v-for="user in users"
              :key="user.id"
              class="hover:bg-gray-50 dark:hover:bg-white/5"
            >
              <td class="px-4 py-3">
                <div class="flex items-center gap-3 min-w-0">
                  <div
                    class="w-8 h-8 rounded-full flex items-center justify-center text-white font-medium overflow-hidden flex-shrink-0"
                    :style="getUserAvatarStyle(user)"
                  >
                    <span v-if="user.avatar_type === 'default' || (user.avatar_type === 'custom' && !user.avatar_url) || (user.avatar_type === 'oauth' && !user.oauth_avatar_url)">
                      {{ user.username.charAt(0).toUpperCase() }}
                    </span>
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-gray-900 dark:text-white font-medium truncate">
                      {{ user.username }}
                    </p>
                    <p class="text-gray-500 text-xs truncate">
                      {{ user.bio || '暂无简介' }}
                    </p>
                  </div>
                </div>
              </td>
              <td class="px-4 py-3 text-gray-500 dark:text-gray-400">
                <span class="line-clamp-2">{{ user.email }}</span>
              </td>
              <td class="px-4 py-3">
                <div class="flex flex-wrap gap-1">
                  <span
                    v-if="user.roles && user.roles.length > 0"
                    v-for="role in user.roles"
                    :key="role.id"
                    :class="getRoleColorClasses(role.code, 'badge')"
                  >
                    {{ role.name }}
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center px-2 py-0.5 text-xs font-semibold rounded-full border bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-white/10"
                  >
                    未分配角色
                  </span>
                </div>
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
              <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                {{ formatDate(user.created_at) }}
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <button
                    class="text-primary hover:text-primary/80 text-xs"
                    @click="handleEdit(user)"
                  >
                    编辑
                  </button>
                  <button
                    class="text-blue-400 hover:text-blue-300 text-xs"
                    @click="openRoleModal(user)"
                  >
                    角色
                  </button>
                  <button
                    class="text-accent hover:text-accent/80 text-xs"
                    @click="openPasswordModal(user)"
                  >
                    重置密码
                  </button>
                  <button
                    class="text-red-400 hover:text-red-300 text-xs"
                    @click="handleDelete(user)"
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
        class="flex items-center justify-center gap-4 mt-4"
      >
        <button
          :disabled="currentPage === 1"
          class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-dark-200 transition-colors"
          @click="prevPage"
        >
          上一页
        </button>
        <span class="text-sm text-gray-500">
          {{ currentPage }} / {{ totalPages }}
        </span>
        <button
          :disabled="currentPage === totalPages"
          class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-dark-200 transition-colors"
          @click="nextPage"
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
          <h2 class="text-base font-bold text-gray-900 dark:text-white">
            编辑用户
          </h2>
          <button
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
            @click="showEditor = false"
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

        <form
          class="space-y-3"
          @submit.prevent="handleSubmit"
        >
          <div>
            <label
              for="user-username"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >用户名 <span class="text-red-500">*</span></label>
            <input
              id="user-username"
              v-model="form.username"
              type="text"
              name="username"
              autocomplete="username"
              :class="['w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none', hasEditError('username') ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-white/10']"
              placeholder="用户名"
              @input="clearEditError('username')"
            >
            <p v-if="hasEditError('username')" class="mt-1 text-xs text-red-500">{{ getEditErrorMessage('username') }}</p>
          </div>

          <div>
            <label
              for="user-email"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >邮箱 <span class="text-red-500">*</span></label>
            <input
              id="user-email"
              v-model="form.email"
              type="email"
              name="email"
              autocomplete="email"
              :class="['w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none', hasEditError('email') ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-white/10']"
              placeholder="邮箱地址"
              @input="clearEditError('email')"
            >
            <p v-if="hasEditError('email')" class="mt-1 text-xs text-red-500">{{ getEditErrorMessage('email') }}</p>
          </div>

          <div>
            <label
              for="user-bio"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >简介</label>
            <textarea
              id="user-bio"
              v-model="form.bio"
              name="bio"
              rows="3"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="个人简介"
            />
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              @click="showEditor = false"
            >
              取消
            </button>
            <button
              type="submit"
              class="btn-primary text-sm px-4 py-1.5"
              :disabled="isSubmitting"
            >
              <span v-if="isSubmitting" class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                保存中...
              </span>
              <span v-else>保存</span>
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
          <h2 class="text-base font-bold text-gray-900 dark:text-white">
            重置密码
          </h2>
          <button
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
            @click="showPasswordModal = false"
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
          v-if="editingUser"
          class="mb-4 p-3 bg-primary/5 dark:bg-primary/10 rounded-xl"
        >
          <div class="flex items-center gap-3">
            <div
              class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm"
              :style="getUserAvatarStyle(editingUser)"
            >
              {{ editingUser.username?.charAt(0).toUpperCase() }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {{ editingUser.username }}
                </span>
                <span
                  v-if="editingUser.is_admin"
                  class="px-1.5 py-0.5 text-xs font-medium rounded bg-primary/20 text-primary"
                >
                  管理员
                </span>
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                ID: {{ editingUser.id }} · {{ editingUser.email || '未绑定邮箱' }}
              </div>
            </div>
          </div>
        </div>

        <form
          class="space-y-3"
          @submit.prevent="handleResetPassword"
        >
          <div>
            <label for="reset-password-username" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              用户名
            </label>
            <input
              id="reset-password-username"
              type="text"
              name="username"
              :value="editingUser?.username"
              autocomplete="username"
              readonly
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 dark:text-gray-400 cursor-not-allowed"
            >
          </div>
          <div>
            <label
              for="user-new-password"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >新密码 <span class="text-red-500">*</span></label>
            <input
              id="user-new-password"
              v-model="newPassword"
              type="password"
              name="new-password"
              autocomplete="new-password"
              :class="['w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none', passwordError ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-white/10']"
              placeholder="请输入新密码（至少6位）"
              @input="passwordError = ''"
            >
            <p v-if="passwordError" class="mt-1 text-xs text-red-500">{{ passwordError }}</p>
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              @click="showPasswordModal = false"
            >
              取消
            </button>
            <button
              type="submit"
              class="btn-primary text-sm px-4 py-1.5"
              :disabled="isResetting"
            >
              <span v-if="isResetting" class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                重置中...
              </span>
              <span v-else>确认重置</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <div
      v-if="showRoleModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    >
      <div class="glass-card w-full max-w-md m-4 p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-bold text-gray-900 dark:text-white">
            分配角色
          </h2>
          <button
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
            @click="showRoleModal = false"
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
          v-if="roleAssignUser"
          class="mb-4 p-3 bg-primary/5 dark:bg-primary/10 rounded-xl"
        >
          <div class="flex items-center gap-3">
            <div
              class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm"
              :style="getUserAvatarStyle(roleAssignUser)"
            >
              {{ roleAssignUser.username?.charAt(0).toUpperCase() }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {{ roleAssignUser.username }}
                </span>
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {{ roleAssignUser.email || '未绑定邮箱' }}
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-2 max-h-60 overflow-y-auto">
          <p
            v-if="roleError"
            class="text-xs text-red-500 mb-2"
          >
            {{ roleError }}
          </p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="role in allRoles"
              :key="role.id"
              type="button"
              :class="[
                'px-3 py-1.5 text-xs rounded-full border transition-all',
                selectedRoleIds.includes(role.id)
                  ? getRoleColorClasses(role.code, 'badge')
                  : 'bg-gray-200 dark:bg-dark-300 text-gray-600 dark:text-gray-400 border-transparent hover:bg-gray-300 dark:hover:bg-dark-400'
              ]"
              @click="toggleRole(role.id)"
            >
              {{ role.name }}
            </button>
          </div>
        </div>

        <div class="flex justify-end gap-3 pt-4">
          <button
            type="button"
            class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            @click="showRoleModal = false"
          >
            取消
          </button>
          <button
            type="button"
            class="btn-primary text-sm px-4 py-1.5"
            @click="handleRoleAssign"
          >
            保存
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    >
      <div class="glass-card w-full max-w-md m-4 p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-bold text-gray-900 dark:text-white">
            创建用户
          </h2>
          <button
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
            @click="showCreateModal = false"
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

        <form
          class="space-y-3"
          @submit.prevent="handleCreateSubmit"
        >
          <div>
            <label
              for="create-username"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >用户名 <span class="text-red-500">*</span>
              <span v-if="usernameChecking" class="ml-2 text-gray-400">检查中...</span>
            </label>
            <input
              id="create-username"
              v-model="createForm.username"
              type="text"
              name="create-username"
              autocomplete="username"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              :class="hasCreateError('username') || usernameExists ? 'border-red-500 dark:border-red-500' : usernameChecking ? 'border-yellow-500 dark:border-yellow-500' : 'border-gray-200 dark:border-white/10'"
              placeholder="请输入用户名"
              @input="clearCreateError('username')"
            >
            <p
              v-if="hasCreateError('username')"
              class="mt-1 text-xs text-red-500"
            >
              {{ getCreateErrorMessage('username') }}
            </p>
          </div>

          <div>
            <label
              for="create-email"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >邮箱 <span class="text-red-500">*</span>
              <span v-if="emailChecking" class="ml-2 text-gray-400">检查中...</span>
            </label>
            <input
              id="create-email"
              v-model="createForm.email"
              type="email"
              name="create-email"
              autocomplete="email"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              :class="hasCreateError('email') || emailExists ? 'border-red-500 dark:border-red-500' : emailChecking ? 'border-yellow-500 dark:border-yellow-500' : 'border-gray-200 dark:border-white/10'"
              placeholder="请输入邮箱地址"
              @input="clearCreateError('email')"
            >
            <p
              v-if="hasCreateError('email')"
              class="mt-1 text-xs text-red-500"
            >
              {{ getCreateErrorMessage('email') }}
            </p>
          </div>

          <div>
            <label
              for="create-password"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >密码 <span class="text-red-500">*</span></label>
            <input
              id="create-password"
              v-model="createForm.password"
              type="password"
              name="create-password"
              autocomplete="new-password"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              :class="hasCreateError('password') ? 'border-red-500 dark:border-red-500' : 'border-gray-200 dark:border-white/10'"
              placeholder="请输入密码（至少6位）"
              @input="clearCreateError('password')"
            >
            <p
              v-if="hasCreateError('password')"
              class="mt-1 text-xs text-red-500"
            >
              {{ getCreateErrorMessage('password') }}
            </p>
          </div>

          <div>
            <label for="create-roles" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              角色 <span class="text-red-500">*</span>
            </label>
            <div id="create-roles" class="flex flex-wrap gap-2">
              <button
                v-for="role in allRoles"
                :key="role.id"
                type="button"
                :class="[
                  'px-3 py-1.5 text-xs rounded-full border transition-all',
                  createForm.roleIds.includes(role.id)
                    ? getRoleColorClasses(role.code, 'badge')
                    : 'bg-gray-200 dark:bg-dark-300 text-gray-600 dark:text-gray-400 border-transparent hover:bg-gray-300 dark:hover:bg-dark-400'
                ]"
                @click="toggleCreateRole(role.id); clearCreateError('roleIds')"
              >
                {{ role.name }}
              </button>
            </div>
            <p
              v-if="hasCreateError('roleIds')"
              class="mt-1 text-xs text-red-500"
            >
              {{ getCreateErrorMessage('roleIds') }}
            </p>
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              @click="showCreateModal = false"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="isCreating"
              class="btn-primary text-sm px-4 py-1.5"
            >
              <span v-if="isCreating" class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                创建中...
              </span>
              <span v-else>创建</span>
            </button>
          </div>
        </form>
      </div>
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
