import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { permissionApi, roleApi } from '@/api'
import type { Permission, PermissionTree, Role } from '@/api'

export const usePermissionStore = defineStore('permission', () => {
  const permissions = ref<Permission[]>([])
  const permissionTree = ref<PermissionTree | null>(null)
  const roles = ref<Role[]>([])
  const myPermissions = ref<string[]>([])
  const myRoles = ref<{ id: number; name: string; code: string }[]>([])
  const isLoading = ref(false)

  const isSuperAdmin = computed(() => {
    return myRoles.value.some(r => r.code === 'super_admin')
  })

  const hasPermission = (code: string): boolean => {
    return myPermissions.value.includes(code)
  }

  const hasAnyPermission = (codes: string[]): boolean => {
    return codes.some(code => myPermissions.value.includes(code))
  }

  const hasAllPermissions = (codes: string[]): boolean => {
    return codes.every(code => myPermissions.value.includes(code))
  }

  const fetchPermissions = async (module?: string, isActive?: boolean) => {
    try {
      permissions.value = await permissionApi.getPermissions(module, isActive)
    } catch (error) {
      console.error('Failed to fetch permissions:', error)
    }
  }

  const fetchPermissionTree = async () => {
    try {
      permissionTree.value = await permissionApi.getPermissionTree()
    } catch (error) {
      console.error('Failed to fetch permission tree:', error)
    }
  }

  const fetchRoles = async (isActive?: boolean) => {
    try {
      roles.value = await roleApi.getRoles(isActive)
    } catch (error) {
      console.error('Failed to fetch roles:', error)
    }
  }

  const fetchMyPermissions = async () => {
    try {
      const result = await permissionApi.getMyPermissions()
      myPermissions.value = result.permissions
      myRoles.value = result.roles
    } catch (error) {
      console.error('Failed to fetch my permissions:', error)
    }
  }

  const createPermission = async (data: Parameters<typeof permissionApi.createPermission>[0]) => {
    const permission = await permissionApi.createPermission(data)
    permissions.value.push(permission)
    return permission
  }

  const updatePermission = async (id: number, data: Parameters<typeof permissionApi.updatePermission>[1]) => {
    const permission = await permissionApi.updatePermission(id, data)
    const index = permissions.value.findIndex(p => p.id === id)
    if (index !== -1) {
      permissions.value[index] = permission
    }
    return permission
  }

  const deletePermission = async (id: number) => {
    await permissionApi.deletePermission(id)
    permissions.value = permissions.value.filter(p => p.id !== id)
  }

  const createRole = async (data: Parameters<typeof roleApi.createRole>[0]) => {
    const role = await roleApi.createRole(data)
    roles.value.push(role)
    return role
  }

  const createRoleFromTemplate = async (data: Parameters<typeof roleApi.createRoleFromTemplate>[0]) => {
    const role = await roleApi.createRoleFromTemplate(data)
    roles.value.push(role)
    return role
  }

  const updateRole = async (id: number, data: Parameters<typeof roleApi.updateRole>[1]) => {
    const role = await roleApi.updateRole(id, data)
    const index = roles.value.findIndex(r => r.id === id)
    if (index !== -1) {
      roles.value[index] = role
    }
    return role
  }

  const updateRolePermissions = async (id: number, permissionIds: number[]) => {
    await roleApi.updateRolePermissions(id, permissionIds)
    const role = await roleApi.getRole(id)
    const index = roles.value.findIndex(r => r.id === id)
    if (index !== -1) {
      roles.value[index] = role
    }
    return role
  }

  const deleteRole = async (id: number) => {
    await roleApi.deleteRole(id)
    roles.value = roles.value.filter(r => r.id !== id)
  }

  const assignRoles = async (userIds: number[], roleIds: number[]) => {
    return await roleApi.assignRoles({ user_ids: userIds, role_ids: roleIds })
  }

  const removeRoles = async (userIds: number[], roleIds: number[]) => {
    return await roleApi.removeRoles({ user_ids: userIds, role_ids: roleIds })
  }

  return {
    permissions,
    permissionTree,
    roles,
    myPermissions,
    myRoles,
    isLoading,
    isSuperAdmin,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    fetchPermissions,
    fetchPermissionTree,
    fetchRoles,
    fetchMyPermissions,
    createPermission,
    updatePermission,
    deletePermission,
    createRole,
    createRoleFromTemplate,
    updateRole,
    updateRolePermissions,
    deleteRole,
    assignRoles,
    removeRoles,
  }
})
