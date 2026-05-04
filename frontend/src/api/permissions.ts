import apiClient from './client'

export interface Permission {
  id: number
  code: string
  name: string
  description: string | null
  module: string
  action: string
  is_active: boolean
  created_at: string | null
  updated_at: string | null
}

export interface PermissionCreate {
  code: string
  name: string
  description?: string
  module: string
  action: string
}

export interface PermissionUpdate {
  name?: string
  description?: string
  is_active?: boolean
}

export interface PermissionModule {
  module: string
  module_name: string
  permissions: Permission[]
}

export interface PermissionTree {
  modules: PermissionModule[]
}

export interface PermissionChangeLog {
  id: number
  operator_id: number | null
  operator_name: string | null
  target_type: string
  target_id: number | null
  target_name: string | null
  action: string
  old_value: string | null
  new_value: string | null
  description: string | null
  ip_address: string | null
  created_at: string | null
}

export const permissionApi = {
  getPermissions: async (module?: string, isActive?: boolean): Promise<Permission[]> => {
    const params = new URLSearchParams()
    if (module) params.append('module', module)
    if (isActive !== undefined) params.append('is_active', String(isActive))
    const response = await apiClient.get(`/permissions?${params.toString()}`)
    return response.data
  },

  getPermissionTree: async (): Promise<PermissionTree> => {
    const response = await apiClient.get('/permissions/tree')
    return response.data
  },

  createPermission: async (data: PermissionCreate): Promise<Permission> => {
    const response = await apiClient.post('/permissions', data)
    return response.data
  },

  updatePermission: async (id: number, data: PermissionUpdate): Promise<Permission> => {
    const response = await apiClient.put(`/permissions/${id}`, data)
    return response.data
  },

  deletePermission: async (id: number): Promise<void> => {
    await apiClient.delete(`/permissions/${id}`)
  },

  exportPermissions: async (): Promise<{ permissions: Permission[]; roles: any[] }> => {
    const response = await apiClient.get('/permissions/export')
    return response.data
  },

  importPermissions: async (data: {
    permissions?: PermissionCreate[]
    roles?: any[]
  }): Promise<{ message: string; created_permissions: number; created_roles: number }> => {
    const response = await apiClient.post('/permissions/import', data)
    return response.data
  },

  getLogs: async (page = 1, pageSize = 20, targetType?: string): Promise<PermissionChangeLog[]> => {
    const params = new URLSearchParams()
    params.append('page', String(page))
    params.append('page_size', String(pageSize))
    if (targetType) params.append('target_type', targetType)
    const response = await apiClient.get(`/permissions/logs?${params.toString()}`)
    return response.data
  },

  checkPermission: async (permissionCode: string): Promise<{ has_permission: boolean }> => {
    const response = await apiClient.get(`/permissions/check/${permissionCode}`)
    return response.data
  },

  getMyPermissions: async (): Promise<{
    permissions: string[]
    roles: { id: number; name: string; code: string }[]
  }> => {
    const response = await apiClient.get('/permissions/my-permissions')
    return response.data
  },
}
