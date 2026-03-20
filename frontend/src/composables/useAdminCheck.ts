import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useDialogStore } from '@/stores/dialog'

export function useAdminCheck() {
  const authStore = useAuthStore()
  const dialog = useDialogStore()
  
  const isAdmin = computed(() => authStore.user?.is_admin === true)
  
  const requireAdmin = async (action?: string): Promise<boolean> => {
    if (isAdmin.value) {
      return true
    }
    
    const message = action 
      ? `"${action}" 需要管理员权限`
      : '此操作需要管理员权限'
    
    await dialog.showWarning(message, '权限不足')
    return false
  }
  
  const checkAdminAccess = async (): Promise<boolean> => {
    if (isAdmin.value) {
      return true
    }
    
    await dialog.showWarning('您没有权限访问此页面，请联系管理员', '权限不足')
    return false
  }
  
  const hasAdminAccess = (): boolean => {
    return isAdmin.value
  }
  
  const withAdminCheck = async <T>(
    action: string,
    callback: () => Promise<T> | T
  ): Promise<T | null> => {
    if (!await requireAdmin(action)) {
      return null
    }
    return await callback()
  }
  
  return {
    isAdmin,
    requireAdmin,
    checkAdminAccess,
    hasAdminAccess,
    withAdminCheck
  }
}
