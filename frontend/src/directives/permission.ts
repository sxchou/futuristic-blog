import { Directive, DirectiveBinding } from 'vue'
import { usePermissionStore } from '@/stores/permission'
import { useDialogStore } from '@/stores/dialog'

const PERMISSION_NAMES: Record<string, string> = {
  'article.view': '查看文章',
  'article.create': '创建文章',
  'article.edit': '编辑文章',
  'article.delete': '删除文章',
  'article.publish': '发布文章',
  'article.upload_image': '上传图片',
  'article.upload_file': '上传附件',
  'category.view': '查看分类',
  'category.create': '创建分类',
  'category.edit': '编辑分类',
  'category.delete': '删除分类',
  'tag.view': '查看标签',
  'tag.create': '创建标签',
  'tag.edit': '编辑标签',
  'tag.delete': '删除标签',
  'comment.view': '查看评论',
  'comment.audit': '审核评论',
  'comment.delete': '删除评论',
  'user.view': '查看用户',
  'user.create': '创建用户',
  'user.edit': '编辑用户',
  'user.delete': '删除用户',
  'user.reset_password': '重置密码',
  'role.view': '查看角色',
  'role.create': '创建角色',
  'role.edit': '编辑角色',
  'role.delete': '删除角色',
  'role.assign': '分配角色',
  'permission.view': '查看权限',
  'permission.manage': '管理权限',
  'resource.view': '查看资源',
  'resource.create': '创建资源',
  'resource.edit': '编辑资源',
  'resource.delete': '删除资源',
  'announcement.view': '查看公告',
  'announcement.create': '创建公告',
  'announcement.edit': '编辑公告',
  'announcement.delete': '删除公告',
  'storage.view': '查看存储',
  'storage.delete': '删除文件',
  'settings.view': '查看设置',
  'settings.edit': '编辑设置',
  'log.view': '查看日志',
  'log.clear': '清理日志',
  'dashboard.view': '查看仪表盘',
  'dashboard.export': '导出仪表盘图表',
  'email.view': '查看邮件配置',
  'email.create': '创建邮箱配置',
  'email.edit': '编辑邮箱配置',
  'email.delete': '删除邮箱配置',
  'email.activate': '激活邮箱配置',
  'email.switch_provider': '切换邮件服务商',
  'email.test': '测试邮件发送',
  'email.view_logs': '查看邮件日志',
  'notification.view': '查看通知配置',
  'notification.edit': '编辑通知配置',
  'oauth.view': '查看OAuth配置',
  'oauth.edit': '编辑OAuth配置',
  'profile.view': '查看网站资料',
  'profile.edit': '编辑网站资料',
}

function getPermissionName(code: string): string {
  return PERMISSION_NAMES[code] || code
}

function checkPermission(binding: DirectiveBinding): { hasPermission: boolean; missingPermissions: string[] } {
  const permissionStore = usePermissionStore()
  const value = binding.value

  if (!value) {
    return { hasPermission: true, missingPermissions: [] }
  }

  if (typeof value === 'string') {
    const hasPermission = permissionStore.hasPermission(value)
    return {
      hasPermission,
      missingPermissions: hasPermission ? [] : [value]
    }
  }

  if (Array.isArray(value)) {
    if (binding.modifiers.all) {
      const hasAll = permissionStore.hasAllPermissions(value)
      const missing = value.filter(p => !permissionStore.hasPermission(p))
      return { hasPermission: hasAll, missingPermissions: missing }
    } else {
      const hasAny = permissionStore.hasAnyPermission(value)
      const missing = hasAny ? [] : value
      return { hasPermission: hasAny, missingPermissions: missing }
    }
  }

  return { hasPermission: true, missingPermissions: [] }
}

interface PermissionHTMLElement extends HTMLElement {
  _missingPermissions?: string[]
  _permissionHandler?: (e: Event) => boolean
}

function showPermissionDenied(missingPermissions: string[]) {
  const dialog = useDialogStore()
  const permissionNames = missingPermissions.map(p => getPermissionName(p)).join('、')
  dialog.showWarning(`无${permissionNames}权限，请联系管理员`, '权限不足')
}

export const permission: Directive = {
  mounted(el: PermissionHTMLElement, binding: DirectiveBinding) {
    const { hasPermission, missingPermissions } = checkPermission(binding)

    if (!hasPermission) {
      if (binding.modifiers.disable) {
        el.setAttribute('disabled', 'true')
        el.classList.add('is-disabled', 'permission-disabled')
        el.style.cursor = 'not-allowed'
        el.style.opacity = '0.5'
      } else if (binding.modifiers.hide) {
        el.style.display = 'none'
      } else {
        el.setAttribute('disabled', 'true')
        el.classList.add('is-disabled', 'permission-disabled')
        el.style.cursor = 'not-allowed'
        el.style.opacity = '0.5'
      }

      el._missingPermissions = missingPermissions
      el._permissionHandler = (e: Event) => {
        e.stopPropagation()
        e.preventDefault()
        showPermissionDenied(missingPermissions)
        return false
      }
      el.addEventListener('click', el._permissionHandler, true)
    }
  },
  updated(el: PermissionHTMLElement, binding: DirectiveBinding) {
    const { hasPermission, missingPermissions } = checkPermission(binding)

    if (el._permissionHandler) {
      el.removeEventListener('click', el._permissionHandler, true)
    }

    if (!hasPermission) {
      if (binding.modifiers.disable) {
        el.setAttribute('disabled', 'true')
        el.classList.add('is-disabled', 'permission-disabled')
        el.style.cursor = 'not-allowed'
        el.style.opacity = '0.5'
      } else if (binding.modifiers.hide) {
        el.style.display = 'none'
      } else {
        el.setAttribute('disabled', 'true')
        el.classList.add('is-disabled', 'permission-disabled')
        el.style.cursor = 'not-allowed'
        el.style.opacity = '0.5'
      }

      el._missingPermissions = missingPermissions
      el._permissionHandler = (e: Event) => {
        e.stopPropagation()
        e.preventDefault()
        showPermissionDenied(missingPermissions)
        return false
      }
      el.addEventListener('click', el._permissionHandler, true)
    } else {
      el.removeAttribute('disabled')
      el.classList.remove('is-disabled', 'permission-disabled')
      el.style.cursor = ''
      el.style.opacity = ''
      el.style.display = ''
      el._missingPermissions = []
    }
  },
  unmounted(el: PermissionHTMLElement) {
    if (el._permissionHandler) {
      el.removeEventListener('click', el._permissionHandler, true)
    }
  }
}

export const permissionTooltip: Directive = {
  mounted(el: PermissionHTMLElement, binding: DirectiveBinding) {
    const { hasPermission, missingPermissions } = checkPermission(binding)

    if (!hasPermission) {
      const permissionNames = missingPermissions.map(p => getPermissionName(p)).join('、')
      el.setAttribute('title', `无${permissionNames}权限`)
      el.classList.add('permission-tooltip')
    }
  },
  updated(el: PermissionHTMLElement, binding: DirectiveBinding) {
    const { hasPermission, missingPermissions } = checkPermission(binding)

    if (!hasPermission) {
      const permissionNames = missingPermissions.map(p => getPermissionName(p)).join('、')
      el.setAttribute('title', `无${permissionNames}权限`)
      el.classList.add('permission-tooltip')
    } else {
      el.removeAttribute('title')
      el.classList.remove('permission-tooltip')
    }
  }
}

export default {
  permission,
  permissionTooltip
}
