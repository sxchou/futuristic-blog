import { computed, type ComputedRef } from 'vue'

export interface RoleInfo {
  code: string
  name: string
}

type RoleColorClasses = {
  bg: string
  text: string
  border: string
  combined: string
}

const ROLE_COLORS: Record<string, RoleColorClasses> = {
  super_admin: {
    bg: 'bg-indigo-500/20',
    text: 'text-indigo-400',
    border: 'border-indigo-500/30',
    combined: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
  },
  admin: {
    bg: 'bg-primary/10 dark:bg-primary/20',
    text: 'text-primary',
    border: 'border-primary/30',
    combined: 'bg-primary/10 dark:bg-primary/20 text-primary border-primary/30'
  },
  editor: {
    bg: 'bg-blue-500/20',
    text: 'text-blue-400',
    border: 'border-blue-500/30',
    combined: 'bg-blue-500/20 text-blue-400 border-blue-500/30'
  },
  author: {
    bg: 'bg-green-500/20',
    text: 'text-green-400',
    border: 'border-green-500/30',
    combined: 'bg-green-500/20 text-green-400 border-green-500/30'
  },
  user: {
    bg: 'bg-gray-100 dark:bg-dark-100',
    text: 'text-gray-600 dark:text-gray-400',
    border: 'border-gray-200 dark:border-white/10',
    combined: 'bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-white/10'
  }
}

const ROLE_PRIORITY: Record<string, number> = {
  super_admin: 100,
  admin: 80,
  editor: 60,
  author: 40,
  user: 20
}

const ROLE_NAMES: Record<string, string> = {
  super_admin: '超级管理员',
  admin: '管理员',
  editor: '编辑',
  author: '作者',
  user: '用户'
}

export function useRoleColor() {
  const getRoleColor = (roleCode: string): RoleColorClasses => {
    return ROLE_COLORS[roleCode] || ROLE_COLORS.user
  }

  const getRoleColorClasses = (roleCode: string, variant: 'badge' | 'tag' | 'label' = 'badge'): string => {
    const colors = getRoleColor(roleCode)
    
    switch (variant) {
      case 'badge':
        return `inline-flex items-center px-2 py-0.5 text-xs font-semibold rounded-full border ${colors.combined}`
      case 'tag':
        return `px-2 py-1 text-xs rounded ${colors.bg} ${colors.text}`
      case 'label':
        return `inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded ${colors.bg} ${colors.text}`
      default:
        return colors.combined
    }
  }

  const getRolePriority = (roleCode: string): number => {
    return ROLE_PRIORITY[roleCode] || 0
  }

  const getRoleName = (roleCode: string): string => {
    return ROLE_NAMES[roleCode] || '未知角色'
  }

  const isHigherRole = (roleCode1: string, roleCode2: string): boolean => {
    return getRolePriority(roleCode1) > getRolePriority(roleCode2)
  }

  const sortRolesByPriority = (roles: RoleInfo[]): RoleInfo[] => {
    return [...roles].sort((a, b) => getRolePriority(b.code) - getRolePriority(a.code))
  }

  const getHighestRole = (roles: RoleInfo[]): RoleInfo | null => {
    if (!roles || roles.length === 0) return null
    return sortRolesByPriority(roles)[0]
  }

  const useRoleClasses = (roleCode: string | undefined): ComputedRef<RoleColorClasses> => {
    return computed(() => getRoleColor(roleCode || 'user'))
  }

  return {
    getRoleColor,
    getRoleColorClasses,
    getRolePriority,
    getRoleName,
    isHigherRole,
    sortRolesByPriority,
    getHighestRole,
    useRoleClasses,
    ROLE_COLORS,
    ROLE_PRIORITY,
    ROLE_NAMES
  }
}

export default useRoleColor
