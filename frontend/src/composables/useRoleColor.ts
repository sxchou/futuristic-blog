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
    bg: 'bg-amber-50/70 dark:bg-white/5',
    text: 'text-amber-800/80 dark:text-amber-300/80',
    border: 'border-amber-200/60 dark:border-amber-700/20',
    combined: 'bg-amber-50/70 dark:bg-white/5 text-amber-800/80 dark:text-amber-300/80 border-amber-200/60 dark:border-amber-700/20'
  },
  admin: {
    bg: 'bg-blue-50/70 dark:bg-white/5',
    text: 'text-blue-800/80 dark:text-blue-300/80',
    border: 'border-blue-200/60 dark:border-blue-700/20',
    combined: 'bg-blue-50/70 dark:bg-white/5 text-blue-800/80 dark:text-blue-300/80 border-blue-200/60 dark:border-blue-700/20'
  },
  editor: {
    bg: 'bg-purple-50/70 dark:bg-white/5',
    text: 'text-purple-800/80 dark:text-purple-300/80',
    border: 'border-purple-200/60 dark:border-purple-700/20',
    combined: 'bg-purple-50/70 dark:bg-white/5 text-purple-800/80 dark:text-purple-300/80 border-purple-200/60 dark:border-purple-700/20'
  },
  author: {
    bg: 'bg-green-50/70 dark:bg-white/5',
    text: 'text-green-800/80 dark:text-green-300/80',
    border: 'border-green-200/60 dark:border-green-700/20',
    combined: 'bg-green-50/70 dark:bg-white/5 text-green-800/80 dark:text-green-300/80 border-green-200/60 dark:border-green-700/20'
  },
  guest: {
    bg: 'bg-gray-100/80 dark:bg-white/5',
    text: 'text-gray-600/90 dark:text-gray-400/90',
    border: 'border-gray-200/60 dark:border-white/10',
    combined: 'bg-gray-100/80 dark:bg-white/5 text-gray-600/90 dark:text-gray-400/90 border-gray-200/60 dark:border-white/10'
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
  guest: '访客'
}

export function useRoleColor() {
  const getRoleColor = (roleCode: string): RoleColorClasses => {
    return ROLE_COLORS[roleCode] || ROLE_COLORS.guest
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
