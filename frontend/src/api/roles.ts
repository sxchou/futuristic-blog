import apiClient from './client'
import type { Permission } from './permissions'

export interface Role {
  id: number
  name: string
  code: string
  description: string | null
  is_system: boolean
  is_active: boolean
  priority: number
  permissions: Permission[]
  created_at: string | null
  updated_at: string | null
}

export interface RoleCreate {
  name: string
  code: string
  description?: string
  priority?: number
  permission_ids?: number[]
}

export interface RoleUpdate {
  name?: string
  description?: string
  is_active?: boolean
  priority?: number
  permission_ids?: number[]
}

export interface RoleTemplateCreate {
  name: string
  code: string
  description?: string
  copy_from_role_id: number
}

export interface UserRoleAssign {
  user_ids: number[]
  role_ids: number[]
}

export interface UserWithRoles {
  id: number
  username: string
  email: string | null
  is_admin: boolean
  roles: Role[]
  created_at: string | null
}

export const roleApi = {
  getRoles: async (isActive?: boolean): Promise<Role[]> => {
    const params = new URLSearchParams()
    if (isActive !== undefined) params.append('is_active', String(isActive))
    const response = await apiClient.get(`/roles?${params.toString()}`)
    return response.data
  },

  getRole: async (id: number): Promise<Role> => {
    const response = await apiClient.get(`/roles/${id}`)
    return response.data
  },

  createRole: async (data: RoleCreate): Promise<Role> => {
    const response = await apiClient.post('/roles', data)
    return response.data
  },

  createRoleFromTemplate: async (data: RoleTemplateCreate): Promise<Role> => {
    const response = await apiClient.post('/roles/from-template', data)
    return response.data
  },

  updateRole: async (id: number, data: RoleUpdate): Promise<Role> => {
    const response = await apiClient.put(`/roles/${id}`, data)
    return response.data
  },

  updateRolePermissions: async (id: number, permissionIds: number[]): Promise<void> => {
    await apiClient.put(`/roles/${id}/permissions`, { permission_ids: permissionIds })
  },

  deleteRole: async (id: number): Promise<void> => {
    await apiClient.delete(`/roles/${id}`)
  },

  assignRoles: async (data: UserRoleAssign): Promise<{ message: string }> => {
    const response = await apiClient.post('/roles/assign', data)
    return response.data
  },

  removeRoles: async (data: UserRoleAssign): Promise<{ message: string }> => {
    const response = await apiClient.post('/roles/remove', data)
    return response.data
  },

  getUserWithRoles: async (userId: number): Promise<UserWithRoles> => {
    const response = await apiClient.get(`/roles/users/${userId}`)
    return response.data
  },

  getUsersByRole: async (
    roleId: number,
    page = 1,
    pageSize = 20
  ): Promise<{
    items: any[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }> => {
    const response = await apiClient.get(
      `/roles/${roleId}/users?page=${page}&page_size=${pageSize}`
    )
    return response.data
  },

  resetRolePermissions: async (roleId: number): Promise<{ message: string; permission_count: number }> => {
    const response = await apiClient.post(`/roles/${roleId}/reset-permissions`)
    return response.data
  },
}
