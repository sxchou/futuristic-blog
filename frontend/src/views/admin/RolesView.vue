<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { roleApi, permissionApi } from '@/api'
import type { Role, Permission, PermissionTree } from '@/api'
import { useDialogStore, usePermissionStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { useDeletionConfirm } from '@/composables/useDeletionConfirm'
import DeletionConfirmDialog from '@/components/common/DeletionConfirmDialog.vue'

const dialog = useDialogStore()
const permissionStore = usePermissionStore()
const { requirePermission } = useAdminCheck()
const deletion = useDeletionConfirm()

const roles = ref<Role[]>([])
const permissionTree = ref<PermissionTree | null>(null)
const isLoading = ref(false)
const showEditor = ref(false)
const showPermissionEditor = ref(false)
const editingRole = ref<Role | null>(null)
const isCreating = ref(false)
const isViewOnly = ref(false)
const activeModule = ref('')
const permissionContentRef = ref<HTMLElement | null>(null)

const form = ref({
  name: '',
  code: '',
  description: '',
  priority: 0,
  permission_ids: [] as number[]
})

const fetchRoles = async () => {
  isLoading.value = true
  try {
    roles.value = await roleApi.getRoles()
  } catch (error) {
    console.error('Failed to fetch roles:', error)
  } finally {
    isLoading.value = false
  }
}

const fetchPermissionTree = async () => {
  try {
    permissionTree.value = await permissionApi.getPermissionTree()
  } catch (error) {
    console.error('Failed to fetch permission tree:', error)
  }
}

const openCreateDialog = async () => {
  if (!await requirePermission('role.create', '创建角色')) return
  isCreating.value = true
  editingRole.value = null
  form.value = {
    name: '',
    code: '',
    description: '',
    priority: 0,
    permission_ids: []
  }
  showEditor.value = true
}

const openEditDialog = async (role: Role) => {
  if (!await requirePermission('role.edit', '编辑角色')) return
  if (role.is_system) {
    dialog.showWarning('系统角色不可编辑', '提示')
    return
  }
  isCreating.value = false
  editingRole.value = role
  form.value = {
    name: role.name,
    code: role.code,
    description: role.description || '',
    priority: role.priority,
    permission_ids: role.permissions.map(p => p.id)
  }
  showEditor.value = true
}

const openPermissionEditor = async (role: Role) => {
  if (role.code === 'super_admin') {
    isViewOnly.value = true
  } else {
    isViewOnly.value = false
    if (!await requirePermission('role.edit', '编辑角色权限')) return
  }
  editingRole.value = role
  form.value = {
    name: role.name,
    code: role.code,
    description: role.description || '',
    priority: role.priority,
    permission_ids: role.permissions.map(p => p.id)
  }
  activeModule.value = permissionTree.value?.modules[0]?.module || ''
  showPermissionEditor.value = true
}

const scrollToModule = (moduleCode: string) => {
  activeModule.value = moduleCode
  const element = permissionContentRef.value?.querySelector(`[data-module="${moduleCode}"]`)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const handleSave = async () => {
  if (!form.value.name.trim()) {
    dialog.showError('请输入角色名称')
    return
  }
  if (!form.value.code.trim()) {
    dialog.showError('请输入角色代码')
    return
  }

  try {
    if (isCreating.value) {
      await roleApi.createRole({
        name: form.value.name,
        code: form.value.code,
        description: form.value.description,
        priority: form.value.priority,
        permission_ids: form.value.permission_ids
      })
      dialog.showSuccess('角色创建成功')
    } else if (editingRole.value) {
      await roleApi.updateRole(editingRole.value.id, {
        name: form.value.name,
        description: form.value.description,
        priority: form.value.priority,
        permission_ids: form.value.permission_ids
      })
      dialog.showSuccess('角色更新成功')
    }
    showEditor.value = false
    await fetchRoles()
  } catch (error: any) {
    console.error('Failed to save role:', error)
    dialog.showError(error.response?.data?.detail || '操作失败')
  }
}

const handleSavePermissions = async () => {
  if (!editingRole.value) return

  try {
    await roleApi.updateRolePermissions(editingRole.value.id, form.value.permission_ids)
    dialog.showSuccess('权限更新成功')
    showPermissionEditor.value = false
    await fetchRoles()
  } catch (error: any) {
    console.error('Failed to update permissions:', error)
    dialog.showError(error.response?.data?.detail || '操作失败')
  }
}

const handleResetPermissions = async () => {
  if (!editingRole.value) return

  const confirmed = await dialog.showConfirm({
    title: '确认初始化',
    message: '确定要将当前角色权限恢复至默认状态吗？此操作不可撤销。'
  })
  if (!confirmed) return

  try {
    const result = await roleApi.resetRolePermissions(editingRole.value.id)
    dialog.showSuccess(`权限初始化成功，已恢复 ${result.permission_count} 个权限`)
    showPermissionEditor.value = false
    await fetchRoles()
  } catch (error: any) {
    console.error('Failed to reset permissions:', error)
    dialog.showError(error.response?.data?.detail || '权限初始化失败')
  }
}

const handleDelete = async (role: Role) => {
  if (!await requirePermission('role.delete', '删除角色')) return
  if (role.is_system) {
    dialog.showError('系统角色不能删除')
    return
  }

  const previewed = await deletion.requestDeletion('role', role.id, role.name)
  if (!previewed) return
}

const deletionLoading = ref(false)
const executeDeletion = async () => {
  try {
    deletionLoading.value = true
    await roleApi.deleteRole(deletion.currentItemId.value)
    deletion.confirmDeletion()
    dialog.showSuccess('角色已删除')
    await fetchRoles()
  } catch (error: any) {
    console.error('Failed to delete role:', error)
    deletion.cancelDeletion()
    dialog.showError(error.response?.data?.detail || '删除失败')
  }
}

const toggleModulePermissions = (_module: string, permissions: Permission[]) => {
  const modulePermIds = permissions.map(p => p.id)
  const allSelected = modulePermIds.every(id => form.value.permission_ids.includes(id))

  if (allSelected) {
    form.value.permission_ids = form.value.permission_ids.filter(id => !modulePermIds.includes(id))
  } else {
    for (const id of modulePermIds) {
      if (!form.value.permission_ids.includes(id)) {
        form.value.permission_ids.push(id)
      }
    }
  }
}

const isModuleFullySelected = (permissions: Permission[]) => {
  return permissions.every(p => form.value.permission_ids.includes(p.id))
}

const isModulePartiallySelected = (permissions: Permission[]) => {
  const selectedCount = permissions.filter(p => form.value.permission_ids.includes(p.id)).length
  return selectedCount > 0 && selectedCount < permissions.length
}

const getRoleIcon = (code: string) => {
  const icons: Record<string, string> = {
    super_admin: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
    admin: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
    editor: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
    author: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    guest: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z'
  }
  return icons[code] || 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z'
}

const getRoleGradient = (code: string) => {
  const gradients: Record<string, string> = {
    super_admin: 'from-amber-500 to-orange-600',
    admin: 'from-blue-500 to-indigo-600',
    editor: 'from-purple-500 to-pink-600',
    author: 'from-green-500 to-teal-600',
    guest: 'from-gray-500 to-slate-600'
  }
  return gradients[code] || 'from-primary to-blue-600'
}

onMounted(() => {
  fetchRoles()
  fetchPermissionTree()
})
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
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          角色管理
        </h1>
      </div>
      <button
        class="px-3 py-1.5 text-sm bg-primary text-white rounded-md hover:bg-primary/90 transition-colors flex items-center gap-1.5"
        @click="openCreateDialog"
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
        创建角色
      </button>
    </div>

    <div
      v-if="isLoading"
      class="flex justify-center py-12"
    >
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>

    <div
      v-else
      class="grid grid-cols-1 md:grid-cols-2 gap-3"
    >
      <div
        v-for="role in roles"
        :key="role.id"
        class="group bg-white dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10 overflow-hidden hover:border-primary/30 transition-colors"
      >
        <div class="p-4">
          <div class="flex items-start gap-3">
            <div
              class="w-10 h-10 rounded-lg bg-gradient-to-br flex items-center justify-center shrink-0"
              :class="getRoleGradient(role.code)"
            >
              <svg
                class="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  :d="getRoleIcon(role.code)"
                />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
                  {{ role.name }}
                </h3>
                <span
                  v-if="role.is_system"
                  class="px-1.5 py-0.5 text-xs font-medium rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400"
                >
                  系统
                </span>
              </div>
              <div class="flex items-center gap-2 mt-1">
                <code class="text-xs px-1.5 py-0.5 bg-gray-100 dark:bg-dark-200 rounded text-gray-600 dark:text-gray-400">
                  {{ role.code }}
                </code>
                <span class="text-xs text-gray-400 dark:text-gray-500">
                  {{ role.permissions.length }} 个权限
                </span>
              </div>
            </div>
          </div>

          <p
            v-if="role.description"
            class="text-xs text-gray-500 dark:text-gray-400 mt-2 line-clamp-1"
          >
            {{ role.description }}
          </p>

          <div class="flex items-center justify-between mt-3 pt-3 border-t border-gray-100 dark:border-white/5">
            <div class="flex flex-wrap gap-1">
              <span
                v-for="perm in role.permissions.slice(0, 3)"
                :key="perm.id"
                class="px-1.5 py-0.5 text-xs bg-gray-50 dark:bg-dark-200 text-gray-600 dark:text-gray-400 rounded"
              >
                {{ perm.name }}
              </span>
              <span
                v-if="role.permissions.length > 3"
                class="px-1.5 py-0.5 text-xs bg-primary/10 text-primary rounded"
              >
                +{{ role.permissions.length - 3 }}
              </span>
            </div>
            <div class="flex items-center gap-1">
              <button
                class="p-1.5 text-primary hover:bg-primary/10 rounded transition-colors"
                :title="role.code === 'super_admin' && !permissionStore.isSuperAdmin ? '超级管理员权限仅超级管理员可编辑' : '配置权限'"
                @click="openPermissionEditor(role)"
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
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
              </button>
              <button
                :class="['p-1.5 rounded transition-colors', role.is_system ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-dark-200']"
                :title="role.is_system ? '系统角色不可编辑' : '编辑角色'"
                @click="openEditDialog(role)"
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
                :class="['p-1.5 rounded transition-colors', role.is_system ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed' : 'text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20']"
                :title="role.is_system ? '系统角色不可删除' : '删除角色'"
                @click="handleDelete(role)"
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
    </div>

    <div
      v-if="showEditor"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
    >
      <div class="glass-card w-full max-w-md m-4 p-6 max-h-[90vh] overflow-y-auto animate-fade-in">
        <div class="flex items-center justify-between mb-5">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">
            {{ isCreating ? '创建角色' : '编辑角色' }}
          </h2>
          <button
            class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-200 rounded-lg transition-colors"
            @click="showEditor = false"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form class="space-y-4" @submit.prevent="handleSave">
          <div>
            <label for="input-form-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              角色名称 <span class="text-red-500">*</span>
            </label>
            <input id="input-form-name"
              v-model="form.name"
              type="text"
              name="role-name"
              class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-200 border border-gray-200 dark:border-dark-300 rounded-lg focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none transition-all text-gray-900 dark:text-white"
              placeholder="请输入角色名称"
            />
          </div>

          <div>
            <label for="input-form-code" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              角色代码 <span class="text-red-500">*</span>
            </label>
            <input id="input-form-code"
              v-model="form.code"
              type="text"
              name="role-code"
              :disabled="!isCreating"
              class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-200 border border-gray-200 dark:border-dark-300 rounded-lg focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none transition-all text-gray-900 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              placeholder="请输入角色代码（英文）"
            />
          </div>

          <div>
            <label for="textarea-form-description" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              描述
            </label>
            <textarea id="textarea-form-description"
              v-model="form.description"
              rows="3"
              name="role-description"
              class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-200 border border-gray-200 dark:border-dark-300 rounded-lg focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none transition-all text-gray-900 dark:text-white resize-none"
              placeholder="请输入角色描述"
            ></textarea>
          </div>

          <div>
            <label for="role-is-default" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              优先级
            </label>
            <input id="role-is-default"
              v-model.number="form.priority"
              type="number"
              class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-200 border border-gray-200 dark:border-dark-300 rounded-lg focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none transition-all text-gray-900 dark:text-white"
              placeholder="数字越大优先级越高"
            />
          </div>
        </form>

        <div class="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200 dark:border-dark-300">
          <button
            class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-200 rounded-lg transition-colors"
            @click="showEditor = false"
          >
            取消
          </button>
          <button
            class="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors shadow-lg shadow-primary/25"
            @click="handleSave"
          >
            保存
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showPermissionEditor"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
    >
      <div class="glass-card w-full max-w-3xl m-2 sm:m-4 flex flex-col animate-fade-in permission-dialog">
        <div class="flex items-center justify-between p-3 sm:p-4 border-b border-gray-200 dark:border-dark-300 shrink-0">
          <div class="flex items-center gap-2 sm:gap-3">
            <div
              class="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-gradient-to-br flex items-center justify-center"
              :class="getRoleGradient(editingRole?.code || '')"
            >
              <svg class="w-4 h-4 sm:w-5 sm:h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getRoleIcon(editingRole?.code || '')" />
              </svg>
            </div>
            <div>
              <h2 class="text-sm sm:text-base font-bold text-gray-900 dark:text-white">
                {{ isViewOnly ? '查看权限' : '权限配置' }}
              </h2>
              <p class="text-xs sm:text-sm text-gray-500 dark:text-gray-400">{{ editingRole?.name }}</p>
            </div>
          </div>
          <div class="flex items-center gap-1 sm:gap-2">
            <span
              v-if="isViewOnly && editingRole?.code === 'super_admin'"
              class="text-xs text-amber-600 dark:text-amber-400 px-2 py-1 bg-amber-50 dark:bg-amber-900/20 rounded"
            >
              超级管理员权限不可修改
            </span>
            <button
                v-if="!isViewOnly && editingRole?.code && ['admin', 'editor', 'author', 'guest'].includes(editingRole.code)"
                class="px-2 sm:px-3 py-1 sm:py-1.5 text-xs text-orange-600 dark:text-orange-400 border border-orange-300 dark:border-orange-700 rounded-lg hover:bg-orange-50 dark:hover:bg-orange-900/20 transition-colors"
                @click="handleResetPermissions"
              >
                恢复默认权限
              </button>
            <button
              class="p-1 sm:p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-200 rounded-lg transition-colors"
              @click="showPermissionEditor = false"
            >
              <svg class="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div v-if="permissionTree" class="flex-1 flex overflow-hidden">
          <div class="w-32 shrink-0 border-r border-gray-200 dark:border-dark-300 bg-gray-50/50 dark:bg-dark-200/50 overflow-y-auto">
            <div class="p-1 space-y-0.5">
              <button
                v-for="module in permissionTree.modules"
                :key="module.module"
                :class="[
                  'w-full flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-left transition-colors',
                  activeModule === module.module
                    ? 'bg-primary/10 text-primary dark:bg-primary/20'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-300'
                ]"
                @click="scrollToModule(module.module)"
              >
                <div
                  class="w-3 h-3 rounded border-2 flex items-center justify-center transition-colors shrink-0"
                  :class="[
                    isModuleFullySelected(module.permissions)
                      ? 'bg-primary border-primary'
                      : isModulePartiallySelected(module.permissions)
                      ? 'bg-primary/50 border-primary'
                      : 'border-gray-300 dark:border-gray-600'
                  ]"
                >
                  <svg
                    v-if="isModuleFullySelected(module.permissions)"
                    class="w-1.5 h-1.5 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span class="text-xs sm:text-sm font-medium truncate">{{ module.module_name }}</span>
              </button>
            </div>
          </div>

          <div ref="permissionContentRef" class="flex-1 overflow-y-auto p-3 sm:p-4 space-y-2 sm:space-y-3">
            <div
              v-for="module in permissionTree.modules"
              :key="module.module"
              :data-module="module.module"
              class="border border-gray-200 dark:border-dark-300 rounded-lg sm:rounded-xl overflow-hidden"
            >
              <div
                class="flex items-center gap-2 sm:gap-3 px-3 sm:px-4 py-2 sm:py-3 bg-gray-50 dark:bg-dark-200 transition-colors"
                :class="isViewOnly ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:bg-gray-100 dark:hover:bg-dark-300'"
                @click="!isViewOnly && toggleModulePermissions(module.module, module.permissions)"
              >
                <div
                  class="w-4 h-4 sm:w-5 sm:h-5 rounded border-2 flex items-center justify-center transition-colors shrink-0"
                  :class="[
                    isModuleFullySelected(module.permissions)
                      ? 'bg-primary border-primary'
                      : isModulePartiallySelected(module.permissions)
                      ? 'bg-primary/50 border-primary'
                      : 'border-gray-300 dark:border-gray-600'
                  ]"
                >
                  <svg
                    v-if="isModuleFullySelected(module.permissions)"
                    class="w-2.5 h-2.5 sm:w-3 sm:h-3 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span class="text-xs sm:text-sm font-medium text-gray-900 dark:text-white">
                  {{ module.module_name }}
                </span>
                <span class="text-xs text-gray-400 dark:text-gray-500 ml-auto">
                  {{ module.permissions.filter(p => form.permission_ids.includes(p.id)).length }}/{{ module.permissions.length }}
                </span>
              </div>
              <div class="p-2 sm:p-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1 sm:gap-2">
                <label
                  v-for="permission in module.permissions"
                  :key="permission.id"
                  class="flex items-center gap-2 px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg transition-colors"
                  :class="isViewOnly ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50 dark:hover:bg-dark-200 cursor-pointer'"
                >
                  <input :id="`permission-${permission.id}`"
                    v-model="form.permission_ids"
                    type="checkbox"
                    :value="permission.id"
                    :disabled="isViewOnly"
                    class="w-3.5 h-3.5 sm:w-4 sm:h-4 rounded border-gray-300 dark:border-gray-600 text-primary focus:ring-primary shrink-0 disabled:opacity-50"
                  />
                  <span :class="['text-xs sm:text-sm', isViewOnly ? 'text-gray-400 dark:text-gray-500' : 'text-gray-700 dark:text-gray-300']">
                    {{ permission.name }}
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-2 sm:gap-3 p-3 sm:p-4 border-t border-gray-200 dark:border-dark-300 shrink-0">
          <button
            class="px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-200 rounded-lg transition-colors"
            @click="showPermissionEditor = false"
          >
            {{ isViewOnly ? '关闭' : '取消' }}
          </button>
          <button
            v-if="!isViewOnly"
            class="px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors shadow-lg shadow-primary/25"
            @click="handleSavePermissions"
          >
            保存权限
          </button>
        </div>
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

<style scoped>
.permission-dialog {
  max-height: 95vh;
  max-height: 95dvh;
}

@media (min-width: 640px) {
  .permission-dialog {
    max-height: 90vh;
    max-height: 90dvh;
  }
}

@supports (max-height: 95dvh) {
  .permission-dialog {
    max-height: calc(95dvh - env(safe-area-inset-top, 0px) - env(safe-area-inset-bottom, 0px));
  }
  @media (min-width: 640px) {
    .permission-dialog {
      max-height: calc(90dvh - env(safe-area-inset-top, 0px) - env(safe-area-inset-bottom, 0px));
    }
  }
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-clamp: 2;
  overflow: hidden;
}

.animate-fade-in {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
