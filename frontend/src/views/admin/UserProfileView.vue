<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore, useUserProfileStore, useDialogStore } from '@/stores'
import { userProfileApi } from '@/api/userProfile'
import { userApi } from '@/api/users'
import { checkServerHealth } from '@/api/client'
import AvatarCropper from '@/components/common/AvatarCropper.vue'
import { useRoleColor } from '@/composables/useRoleColor'
import { formatDateTime } from '@/utils/date'

const { getRoleColorClasses } = useRoleColor()

const authStore = useAuthStore()
const userProfileStore = useUserProfileStore()
const dialogStore = useDialogStore()

const isLoading = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const fileInput = ref<HTMLInputElement | null>(null)
const showCropper = ref(false)
const selectedImageSrc = ref('')

const showUsernameModal = ref(false)
const showEmailModal = ref(false)
const showPasswordModal = ref(false)

const isChangingPassword = ref(false)
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

const hasPassword = computed(() => authStore.user?.has_password ?? true)
const setPasswordStep = ref(1)
const setPasswordCode = ref('')
const setPasswordForm = ref({
  new_password: '',
  confirm_password: ''
})
const setPasswordErrors = ref({
  code: '',
  new_password: '',
  confirm_password: '',
  general: ''
})
const setPasswordCountdown = ref(0)
const isSettingPassword = ref(false)
let setPasswordTimer: ReturnType<typeof setInterval> | null = null

const passwordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const passwordErrors = ref({
  current_password: '',
  new_password: '',
  confirm_password: '',
  general: ''
})

const passwordStrength = computed(() => {
  const password = passwordForm.value.new_password
  if (!password) return { level: 0, text: '', color: '' }
  
  let strength = 0
  if (password.length >= 6) strength++
  if (password.length >= 10) strength++
  if (/[A-Z]/.test(password)) strength++
  if (/[a-z]/.test(password)) strength++
  if (/[0-9]/.test(password)) strength++
  if (/[^A-Za-z0-9]/.test(password)) strength++
  
  if (strength <= 2) return { level: 1, text: '弱', color: 'bg-red-500' }
  if (strength <= 4) return { level: 2, text: '中', color: 'bg-yellow-500' }
  return { level: 3, text: '强', color: 'bg-green-500' }
})

const user = computed(() => authStore.user)
const profile = computed(() => userProfileStore.profile)

const avatarStyle = computed(() => {
  if (!profile.value) return {}
  
  if (profile.value.avatar_type === 'custom' && profile.value.avatar_url) {
    return {
      backgroundImage: `url(${profile.value.avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (profile.value.oauth_avatar_url) {
    return {
      backgroundImage: `url(${profile.value.oauth_avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (profile.value.default_avatar_gradient && profile.value.default_avatar_gradient.length >= 1) {
    return {
      backgroundColor: profile.value.default_avatar_gradient[0]
    }
  }
  
  return {
    backgroundColor: '#667eea'
  }
})

const showInitial = computed(() => {
  if (!profile.value) return true
  if (profile.value.avatar_type === 'custom' && profile.value.avatar_url) return false
  if (profile.value.oauth_avatar_url) return false
  return true
})

const initial = computed(() => {
  if (profile.value?.username) {
    return profile.value.username.charAt(0).toUpperCase()
  }
  if (user.value?.username) {
    return user.value.username.charAt(0).toUpperCase()
  }
  return 'U'
})

const fetchProfile = async () => {
  isLoading.value = true
  try {
    await userProfileStore.fetchProfile()
  } catch (error) {
    console.error('Failed to fetch profile:', error)
  } finally {
    isLoading.value = false
  }
}

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    dialogStore.showError('仅支持 JPG、PNG、WebP 格式的图片')
    return
  }
  
  if (file.size > 10 * 1024 * 1024) {
    dialogStore.showError('文件大小不能超过 10MB')
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    selectedImageSrc.value = e.target?.result as string
    showCropper.value = true
  }
  reader.readAsDataURL(file)
  
  if (target) {
    target.value = ''
  }
}

const handleCropConfirm = async (blob: Blob) => {
  isUploading.value = true
  uploadProgress.value = 0
  
  try {
    const formData = new FormData()
    formData.append('file', blob, 'avatar.jpg')
    
    const interval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 100)
    
    await userProfileApi.uploadAvatar(formData)
    
    clearInterval(interval)
    uploadProgress.value = 100
    
    dialogStore.showSuccess('头像上传成功')
    await userProfileStore.refreshProfile()
    
    setTimeout(() => {
      isUploading.value = false
      uploadProgress.value = 0
    }, 500)
  } catch (error: any) {
    isUploading.value = false
    uploadProgress.value = 0
    dialogStore.showError(error.response?.data?.detail || '头像上传失败')
  }
}

const handleResetAvatar = async () => {
  const confirmed = await dialogStore.showConfirm({ message: '确定要恢复默认头像吗？' })
  if (!confirmed) return
  
  try {
    await userProfileApi.resetAvatar()
    dialogStore.showSuccess('已恢复默认头像')
    await userProfileStore.refreshProfile()
  } catch (error: any) {
    dialogStore.showError(error.response?.data?.detail || '操作失败')
  }
}

const handleUseOAuthAvatar = async () => {
  const confirmed = await dialogStore.showConfirm({ message: '确定要使用OAuth头像吗？' })
  if (!confirmed) return
  
  try {
    await userProfileApi.useOAuthAvatar()
    dialogStore.showSuccess('已切换到OAuth头像')
    await userProfileStore.refreshProfile()
  } catch (error: any) {
    dialogStore.showError(error.response?.data?.detail || '操作失败')
  }
}

const validatePasswordForm = (): boolean => {
  let isValid = true
  passwordErrors.value = {
    current_password: '',
    new_password: '',
    confirm_password: '',
    general: ''
  }
  
  if (!passwordForm.value.current_password) {
    passwordErrors.value.current_password = '请输入当前密码'
    isValid = false
  }
  
  if (!passwordForm.value.new_password) {
    passwordErrors.value.new_password = '请输入新密码'
    isValid = false
  } else if (passwordForm.value.new_password.length < 6) {
    passwordErrors.value.new_password = '密码长度至少6位'
    isValid = false
  } else if (passwordForm.value.new_password.length > 50) {
    passwordErrors.value.new_password = '密码长度不能超过50位'
    isValid = false
  }
  
  if (!passwordForm.value.confirm_password) {
    passwordErrors.value.confirm_password = '请确认新密码'
    isValid = false
  } else if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    passwordErrors.value.confirm_password = '两次输入的密码不一致'
    isValid = false
  }
  
  return isValid
}

const handleChangePassword = async () => {
  passwordErrors.value.general = ''
  if (!validatePasswordForm()) return
  
  isChangingPassword.value = true
  
  try {
    const serverReady = await checkServerHealth()
    if (!serverReady) {
      passwordErrors.value.general = '服务器暂时不可用，请稍后重试'
      isChangingPassword.value = false
      return
    }
    
    await userApi.changePassword({
      current_password: passwordForm.value.current_password,
      new_password: passwordForm.value.new_password,
      confirm_password: passwordForm.value.confirm_password
    })
    
    dialogStore.showSuccess('密码修改成功')
    passwordForm.value = {
      current_password: '',
      new_password: '',
      confirm_password: ''
    }
    showPasswordModal.value = false
  } catch (error: any) {
    console.error('Password change error:', error)
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      if (detail.includes('未设置密码')) {
        passwordErrors.value.general = detail
      } else if (detail.includes('当前密码错误')) {
        passwordErrors.value.current_password = '当前密码输入错误'
      } else if (detail.includes('same') || detail.includes('相同')) {
        passwordErrors.value.new_password = '新密码不能与当前密码相同'
      } else if (detail.includes('weak') || detail.includes('强度')) {
        passwordErrors.value.new_password = '密码强度不足，请使用更复杂的密码'
      } else {
        passwordErrors.value.general = detail
      }
    } else if (error.message) {
      passwordErrors.value.general = error.message
    } else {
      passwordErrors.value.general = '密码修改失败，请稍后重试'
    }
  } finally {
    isChangingPassword.value = false
  }
}

const openPasswordModal = () => {
  if (!hasPassword.value) {
    setPasswordStep.value = 1
    setPasswordCode.value = ''
    setPasswordForm.value = { new_password: '', confirm_password: '' }
    setPasswordErrors.value = { code: '', new_password: '', confirm_password: '', general: '' }
    setPasswordCountdown.value = 0
    showNewPassword.value = false
    showConfirmPassword.value = false
    showPasswordModal.value = true
    return
  }
  passwordForm.value = {
    current_password: '',
    new_password: '',
    confirm_password: ''
  }
  passwordErrors.value = {
    current_password: '',
    new_password: '',
    confirm_password: '',
    general: ''
  }
  showCurrentPassword.value = false
  showNewPassword.value = false
  showConfirmPassword.value = false
  showPasswordModal.value = true
}

const startSetPasswordCountdown = (seconds: number) => {
  setPasswordCountdown.value = seconds
  if (setPasswordTimer) clearInterval(setPasswordTimer)
  setPasswordTimer = setInterval(() => {
    setPasswordCountdown.value--
    if (setPasswordCountdown.value <= 0) {
      if (setPasswordTimer) clearInterval(setPasswordTimer)
      setPasswordTimer = null
    }
  }, 1000)
}

const handleSendSetPasswordCode = async () => {
  setPasswordErrors.value = { code: '', new_password: '', confirm_password: '', general: '' }
  isSettingPassword.value = true
  try {
    const response = await userApi.requestSetPassword()
    dialogStore.showSuccess('验证码已发送至您的邮箱')
    startSetPasswordCountdown(Math.min(response.expires_in, 60))
  } catch (error: any) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      if (detail.includes('频繁') || detail.includes('too many')) {
        setPasswordErrors.value.general = '发送过于频繁，请稍后再试'
      } else {
        setPasswordErrors.value.general = detail
      }
    } else {
      setPasswordErrors.value.general = '发送验证码失败，请稍后重试'
    }
  } finally {
    isSettingPassword.value = false
  }
}

const validateSetPasswordForm = (): boolean => {
  setPasswordErrors.value = { code: '', new_password: '', confirm_password: '', general: '' }
  let isValid = true

  if (!setPasswordCode.value) {
    setPasswordErrors.value.code = '请输入验证码'
    isValid = false
  } else if (setPasswordCode.value.length !== 6) {
    setPasswordErrors.value.code = '验证码为6位数字'
    isValid = false
  }

  if (!setPasswordForm.value.new_password) {
    setPasswordErrors.value.new_password = '请输入新密码'
    isValid = false
  } else if (setPasswordForm.value.new_password.length < 6) {
    setPasswordErrors.value.new_password = '密码长度至少6位'
    isValid = false
  } else if (setPasswordForm.value.new_password.length > 50) {
    setPasswordErrors.value.new_password = '密码长度不能超过50位'
  }

  if (!setPasswordForm.value.confirm_password) {
    setPasswordErrors.value.confirm_password = '请确认新密码'
    isValid = false
  } else if (setPasswordForm.value.new_password !== setPasswordForm.value.confirm_password) {
    setPasswordErrors.value.confirm_password = '两次输入的密码不一致'
    isValid = false
  }

  return isValid
}

const handleSetPassword = async () => {
  if (!validateSetPasswordForm()) return

  isSettingPassword.value = true
  try {
    await userApi.verifySetPassword({
      code: setPasswordCode.value,
      new_password: setPasswordForm.value.new_password,
      confirm_password: setPasswordForm.value.confirm_password
    })
    dialogStore.showSuccess('密码设置成功')
    showPasswordModal.value = false
    await authStore.fetchUser()
  } catch (error: any) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      if (detail.includes('验证码无效') || detail.includes('验证码错误') || detail.includes('验证码已过期')) {
        setPasswordErrors.value.code = '验证码错误或已过期，请重新获取'
      } else if (detail.includes('密码长度')) {
        setPasswordErrors.value.new_password = detail
      } else if (detail.includes('不一致')) {
        setPasswordErrors.value.confirm_password = detail
      } else {
        setPasswordErrors.value.general = detail
      }
    } else {
      setPasswordErrors.value.general = '密码设置失败，请稍后重试'
    }
  } finally {
    isSettingPassword.value = false
  }
}

const isChangingEmail = ref(false)
const sendCodeLoading = ref(false)
const sendOldCodeLoading = ref(false)
const countdown = ref(0)
const oldEmailCountdown = ref(0)
const emailError = ref('')
const emailVerificationType = ref<'password' | 'old_email'>('password')
const emailStep = ref(1)

const emailForm = ref({
  new_email: '',
  password: '',
  code: '',
  old_email_code: ''
})

const emailErrors = ref({
  new_email: '',
  password: '',
  code: '',
  old_email_code: ''
})

const currentEmail = computed(() => authStore.user?.email || '')

const validateEmail = (email: string): boolean => {
  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  return emailPattern.test(email)
}

const startCountdown = () => {
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer)
    }
  }, 1000)
}

const startOldEmailCountdown = () => {
  oldEmailCountdown.value = 60
  const timer = setInterval(() => {
    oldEmailCountdown.value--
    if (oldEmailCountdown.value <= 0) {
      clearInterval(timer)
    }
  }, 1000)
}

const handleSendOldEmailCode = async () => {
  emailError.value = ''
  emailErrors.value.old_email_code = ''
  
  sendOldCodeLoading.value = true
  try {
    await userApi.sendCodeToOldEmail()
    dialogStore.showSuccess('验证码已发送至当前邮箱')
    startOldEmailCountdown()
  } catch (error: any) {
    console.error('Send old email code error:', error)
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      if (detail.includes('rate limit') || detail.includes('频繁') || detail.includes('too many')) {
        emailErrors.value.old_email_code = '发送过于频繁，请稍后再试'
      } else if (detail.includes('not found') || detail.includes('未找到')) {
        emailErrors.value.old_email_code = '邮箱地址不存在'
      } else {
        emailErrors.value.old_email_code = detail
      }
    } else if (error.message) {
      emailErrors.value.old_email_code = error.message
    } else {
      emailErrors.value.old_email_code = '发送验证码失败，请稍后重试'
    }
  } finally {
    sendOldCodeLoading.value = false
  }
}

const validateEmailStep1 = (): boolean => {
  emailErrors.value = { new_email: '', password: '', code: '', old_email_code: '' }
  let isValid = true
  
  if (!emailForm.value.new_email) {
    emailErrors.value.new_email = '请输入新邮箱地址'
    isValid = false
  } else if (!validateEmail(emailForm.value.new_email)) {
    emailErrors.value.new_email = '请输入有效的邮箱地址'
    isValid = false
  } else if (emailForm.value.new_email === currentEmail.value) {
    emailErrors.value.new_email = '新邮箱不能与当前邮箱相同'
    isValid = false
  }
  
  if (emailVerificationType.value === 'password') {
    if (!emailForm.value.password) {
      emailErrors.value.password = '请输入当前密码'
      isValid = false
    }
  } else {
    if (!emailForm.value.old_email_code) {
      emailErrors.value.old_email_code = '请输入原邮箱验证码'
      isValid = false
    } else if (emailForm.value.old_email_code.length !== 6) {
      emailErrors.value.old_email_code = '验证码为6位数字'
      isValid = false
    }
  }
  
  return isValid
}

const handleSendCode = async () => {
  emailError.value = ''
  
  if (!validateEmailStep1()) return
  
  sendCodeLoading.value = true
  try {
    await userApi.requestEmailChange({
      new_email: emailForm.value.new_email,
      password: emailVerificationType.value === 'password' ? emailForm.value.password : undefined,
      verification_type: emailVerificationType.value,
      old_email_code: emailVerificationType.value === 'old_email' ? emailForm.value.old_email_code : undefined
    })
    dialogStore.showSuccess('验证码已发送至新邮箱')
    emailStep.value = 2
    startCountdown()
  } catch (error: any) {
    console.error('Send email code error:', error)
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      if (detail.includes('rate limit') || detail.includes('频繁') || detail.includes('too many')) {
        emailError.value = '发送过于频繁，请稍后再试'
      } else if (detail.includes('already exists') || detail.includes('已存在')) {
        emailErrors.value.new_email = '该邮箱已被其他账户使用'
      } else if (detail.includes('未设置密码')) {
        emailError.value = detail
      } else if (detail.includes('当前密码错误') || detail.includes('请输入当前密码')) {
        if (emailVerificationType.value === 'password') {
          emailErrors.value.password = detail.includes('当前密码错误') ? '当前密码输入错误' : '请输入当前密码'
        } else {
          emailError.value = '当前账号未设置密码，请使用原邮箱验证方式'
        }
      } else if (detail.includes('原邮箱验证码无效') || detail.includes('原邮箱验证码错误')) {
        emailErrors.value.old_email_code = '原邮箱验证码错误或已过期'
      } else {
        emailError.value = detail
      }
    } else if (error.message) {
      emailError.value = error.message
    } else {
      emailError.value = '发送验证码失败，请稍后重试'
    }
  } finally {
    sendCodeLoading.value = false
  }
}

const handleEmailChange = async () => {
  emailError.value = ''
  emailErrors.value.code = ''
  
  if (!emailForm.value.code) {
    emailErrors.value.code = '请输入验证码'
    return
  } else if (emailForm.value.code.length !== 6) {
    emailErrors.value.code = '验证码为6位数字'
    return
  }
  
  isChangingEmail.value = true
  try {
    await userApi.verifyEmailChange({
      new_email: emailForm.value.new_email,
      code: emailForm.value.code,
      password: emailVerificationType.value === 'password' ? emailForm.value.password : undefined,
      verification_type: emailVerificationType.value
    })
    dialogStore.showSuccess('邮箱修改成功')
    showEmailModal.value = false
    await authStore.fetchUser()
    await userProfileStore.refreshProfile()
  } catch (error: any) {
    console.error('Email change error:', error)
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      if (detail.includes('验证码无效') || detail.includes('验证码错误') || detail.includes('验证码已过期')) {
        emailErrors.value.code = '验证码错误或已过期，请重新获取'
      } else if (detail.includes('already exists') || detail.includes('已存在')) {
        emailErrors.value.new_email = '该邮箱已被其他账户使用'
      } else if (detail.includes('当前密码错误') || detail.includes('请输入当前密码')) {
        if (emailVerificationType.value === 'password') {
          emailErrors.value.password = detail.includes('当前密码错误') ? '当前密码输入错误' : '请输入当前密码'
        } else {
          emailError.value = '当前账号未设置密码，请使用原邮箱验证方式'
        }
      } else {
        emailError.value = detail
      }
    } else if (error.message) {
      emailError.value = error.message
    } else {
      emailError.value = '邮箱修改失败，请稍后重试'
    }
  } finally {
    isChangingEmail.value = false
  }
}

const openEmailModal = () => {
  emailStep.value = 1
  emailForm.value = { new_email: '', password: '', code: '', old_email_code: '' }
  emailErrors.value = { new_email: '', password: '', code: '', old_email_code: '' }
  emailError.value = ''
  emailVerificationType.value = 'password'
  countdown.value = 0
  oldEmailCountdown.value = 0
  showEmailModal.value = true
}

const isChangingUsername = ref(false)
const usernameError = ref('')

const usernameForm = ref({
  new_username: '',
  password: ''
})

const usernameErrors = ref({
  new_username: '',
  password: ''
})

const currentUsername = computed(() => authStore.user?.username || '')

const validateUsernameForm = (): boolean => {
  usernameErrors.value = { new_username: '', password: '' }
  let isValid = true
  
  if (!usernameForm.value.new_username) {
    usernameErrors.value.new_username = '请输入新用户名'
    isValid = false
  } else if (usernameForm.value.new_username.length < 4) {
    usernameErrors.value.new_username = '用户名长度至少4个字符'
    isValid = false
  } else if (usernameForm.value.new_username.length > 20) {
    usernameErrors.value.new_username = '用户名长度不能超过20个字符'
    isValid = false
  } else {
    const usernamePattern = /^[a-zA-Z0-9_\u4e00-\u9fa5]+$/
    if (!usernamePattern.test(usernameForm.value.new_username)) {
      usernameErrors.value.new_username = '用户名只能包含字母、数字、下划线和中文'
      isValid = false
    } else if (usernameForm.value.new_username === currentUsername.value) {
      usernameErrors.value.new_username = '新用户名不能与当前用户名相同'
      isValid = false
    }
  }
  
  if (!usernameForm.value.password) {
    usernameErrors.value.password = '请输入当前密码以确认身份'
    isValid = false
  }
  
  return isValid
}

const handleUsernameChange = async () => {
  usernameError.value = ''
  
  if (!validateUsernameForm()) return
  
  isChangingUsername.value = true
  try {
    await userApi.changeUsername({
      new_username: usernameForm.value.new_username,
      password: usernameForm.value.password
    })
    dialogStore.showSuccess('用户名修改成功')
    showUsernameModal.value = false
    await authStore.fetchUser()
    await userProfileStore.refreshProfile()
  } catch (error: any) {
    console.error('Username change error:', error)
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      if (detail.includes('already exists') || detail.includes('已存在')) {
        usernameErrors.value.new_username = '该用户名已被使用，请换一个'
      } else if (detail.includes('未设置密码')) {
        usernameError.value = detail
      } else if (detail.includes('当前密码错误')) {
        usernameErrors.value.password = '当前密码输入错误'
      } else {
        usernameError.value = detail
      }
    } else if (error.message) {
      usernameError.value = error.message
    } else {
      usernameError.value = '用户名修改失败，请稍后重试'
    }
  } finally {
    isChangingUsername.value = false
  }
}

const openUsernameModal = () => {
  usernameForm.value = { new_username: '', password: '' }
  usernameErrors.value = { new_username: '', password: '' }
  usernameError.value = ''
  showUsernameModal.value = true
}

onMounted(fetchProfile)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
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
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          我的资料
        </h1>
      </div>
    </div>

    <div
      v-if="isLoading"
      class="flex justify-center py-16"
    >
      <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <div
      v-else
      class="space-y-4"
    >
      <div class="glass-card p-4">
        <div class="flex items-center gap-4">
          <div class="relative group shrink-0">
            <div
              class="w-14 h-14 rounded-xl flex items-center justify-center font-bold text-white text-lg shadow-lg overflow-hidden cursor-pointer transition-all duration-300 group-hover:scale-105 ring-2 ring-white dark:ring-gray-700"
              :style="avatarStyle"
              @click="triggerUpload"
            >
              <span v-if="showInitial">{{ initial }}</span>
            </div>
            
            <div
              v-if="isUploading"
              class="absolute inset-0 bg-black/50 rounded-xl flex items-center justify-center backdrop-blur-sm"
            >
              <div class="text-white text-sm font-medium">{{ uploadProgress }}%</div>
            </div>
            
            <div class="absolute -bottom-1 -right-1 flex gap-1">
              <button
                class="w-5 h-5 bg-white dark:bg-gray-700 rounded-full shadow flex items-center justify-center text-gray-500 dark:text-gray-400 hover:text-primary transition-colors"
                :disabled="isUploading"
                title="更换头像"
                @click="triggerUpload"
              >
                <svg
                  class="w-3 h-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              </button>
            </div>
          </div>
          
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <h2 class="text-base font-bold text-gray-900 dark:text-white">
                {{ user?.username }}
              </h2>
              <template v-if="user?.roles && user.roles.length > 0">
                <span
                  v-for="role in user.roles"
                  :key="role.id"
                  :class="getRoleColorClasses(role.code, 'label')"
                >
                  {{ role.name }}
                </span>
              </template>
            </div>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              注册于 {{ formatDateTime(user?.created_at) }}
            </p>
          </div>
          
          <div class="hidden sm:flex items-center gap-2 shrink-0">
            <button
              v-if="profile?.oauth_avatar_url && profile.avatar_type !== 'custom'"
              class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-lg bg-primary/10 dark:bg-primary/20 text-primary hover:bg-primary/20 dark:hover:bg-primary/30 transition-colors"
              @click="handleUseOAuthAvatar"
            >
              <svg
                class="w-3 h-3 mr-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              OAuth头像
            </button>
            <button
              v-if="profile?.avatar_type === 'custom'"
              class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              @click="handleResetAvatar"
            >
              <svg
                class="w-3 h-3 mr-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              恢复默认
            </button>
          </div>
        </div>
        
        <div class="flex sm:hidden items-center gap-2 mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
          <button
            v-if="profile?.oauth_avatar_url && profile.avatar_type !== 'custom'"
            class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-lg bg-primary/10 dark:bg-primary/20 text-primary hover:bg-primary/20 dark:hover:bg-primary/30 transition-colors"
            @click="handleUseOAuthAvatar"
          >
            <svg
              class="w-3 h-3 mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            OAuth头像
          </button>
          <button
            v-if="profile?.avatar_type === 'custom'"
            class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            @click="handleResetAvatar"
          >
            <svg
              class="w-3 h-3 mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            恢复默认
          </button>
        </div>
        
        <input id="profile-avatar-upload"
          ref="fileInput"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          class="hidden"
          @change="handleFileChange"
        >
        
        <AvatarCropper
          v-model="showCropper"
          :image-src="selectedImageSrc"
          @confirm="handleCropConfirm"
        />
      </div>

      <div class="glass-card divide-y divide-gray-100 dark:divide-gray-800">
        <div class="p-4 flex items-center justify-between">
          <div class="flex items-center gap-3 min-w-0 flex-1">
            <div class="w-8 h-8 rounded-lg bg-blue-500/10 dark:bg-blue-500/20 flex items-center justify-center shrink-0">
              <svg
                class="w-4 h-4 text-blue-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
            </div>
            <div class="min-w-0">
              <p class="text-sm font-medium text-gray-900 dark:text-white">用户名</p>
              <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ currentUsername }}</p>
            </div>
          </div>
          <button
            class="text-xs text-primary hover:text-primary/80 font-medium shrink-0 ml-2"
            @click="openUsernameModal"
          >
            修改
          </button>
        </div>
        
        <div class="p-4 flex items-center justify-between">
          <div class="flex items-center gap-3 min-w-0 flex-1">
            <div class="w-8 h-8 rounded-lg bg-green-500/10 dark:bg-green-500/20 flex items-center justify-center shrink-0">
              <svg
                class="w-4 h-4 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <div class="min-w-0">
              <p class="text-sm font-medium text-gray-900 dark:text-white">邮箱</p>
              <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ currentEmail }}</p>
            </div>
          </div>
          <button
            class="text-xs text-primary hover:text-primary/80 font-medium shrink-0 ml-2"
            @click="openEmailModal"
          >
            修改
          </button>
        </div>
        
        <div class="p-4 flex items-center justify-between">
          <div class="flex items-center gap-3 min-w-0 flex-1">
            <div class="w-8 h-8 rounded-lg bg-orange-500/10 dark:bg-orange-500/20 flex items-center justify-center shrink-0">
              <svg
                class="w-4 h-4 text-orange-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </div>
            <div class="min-w-0">
              <p class="text-sm font-medium text-gray-900 dark:text-white">密码</p>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ hasPassword ? '定期修改可提高账户安全性' : '未设置密码，建议设置以增强账户安全' }}</p>
            </div>
          </div>
          <button
            class="text-xs text-primary hover:text-primary/80 font-medium shrink-0 ml-2"
            @click="openPasswordModal"
          >
            {{ hasPassword ? '修改' : '设置' }}
          </button>
        </div>
      </div>

      <div
        v-if="user?.is_admin"
        class="glass-card p-4"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-purple-500/10 dark:bg-purple-500/20 flex items-center justify-center">
              <svg
                class="w-4 h-4 text-purple-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white">网站资料</p>
              <p class="text-xs text-gray-500 dark:text-gray-400">编辑网站所有者的公开资料</p>
            </div>
          </div>
          <router-link
            to="/admin/profile"
            class="text-xs text-primary hover:text-primary/80 font-medium"
          >
            前往编辑
          </router-link>
        </div>
      </div>
    </div>

    <div
      v-if="showUsernameModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      @click.self="showUsernameModal = false"
    >
      <div class="glass-card w-full max-w-md p-5 animate-fade-in">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-bold text-gray-900 dark:text-white">修改用户名</h3>
          <button
            class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-200 rounded-lg transition-colors"
            @click="showUsernameModal = false"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <form
          class="space-y-3"
          @submit.prevent="handleUsernameChange"
        >
          <div>
            <label for="input-current-username" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              当前用户名
            </label>
            <input id="input-current-username"
              :value="currentUsername"
              type="text"
              name="current-username"
              readonly
              autocomplete="username"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 dark:text-gray-400 cursor-not-allowed"
            >
          </div>
          
          <div>
            <label for="input-usernameForm-new_username" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              新用户名 <span class="text-red-500">*</span>
            </label>
            <input id="input-usernameForm-new_username"
              v-model="usernameForm.new_username"
              type="text"
              name="new-username"
              maxlength="20"
              autocomplete="username"
              placeholder="4-20个字符"
              :class="[
                'w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800/50 border rounded-lg text-gray-900 dark:text-white focus:outline-none',
                usernameErrors.new_username ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-gray-700 focus:border-primary'
              ]"
            >
            <p v-if="usernameErrors.new_username" class="mt-1 text-xs text-red-500">{{ usernameErrors.new_username }}</p>
          </div>
          
          <div>
            <label for="input-usernameForm-password" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              当前密码 <span class="text-red-500">*</span>
            </label>
            <input id="input-usernameForm-password"
              v-model="usernameForm.password"
              type="password"
              name="username-password"
              autocomplete="current-password"
              placeholder="请输入当前密码"
              :class="[
                'w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800/50 border rounded-lg text-gray-900 dark:text-white focus:outline-none',
                usernameErrors.password ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-gray-700 focus:border-primary'
              ]"
            >
            <p v-if="usernameErrors.password" class="mt-1 text-xs text-red-500">{{ usernameErrors.password }}</p>
          </div>
          
          <div
            v-if="usernameError"
            class="p-2.5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-2"
          >
            <svg class="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-xs text-red-600 dark:text-red-400">{{ usernameError }}</p>
          </div>
        </form>
        
        <div
          v-if="passwordErrors.general"
          class="mt-3 p-2.5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-2"
        >
          <svg class="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="text-xs text-red-600 dark:text-red-400">{{ passwordErrors.general }}</p>
        </div>
        
        <div class="flex justify-end gap-2 mt-5 pt-4 border-t border-gray-100 dark:border-gray-800">
          <button
            class="px-4 py-2 text-xs font-medium rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            @click="showUsernameModal = false"
          >
            取消
          </button>
          <button
            class="px-4 py-2 text-xs font-medium rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50"
            :disabled="isChangingUsername"
            @click="handleUsernameChange"
          >
            {{ isChangingUsername ? '修改中...' : '确认修改' }}
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showEmailModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      @click.self="showEmailModal = false"
    >
      <div class="glass-card w-full max-w-md p-5 animate-fade-in max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-bold text-gray-900 dark:text-white">修改邮箱</h3>
          <button
            class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-200 rounded-lg transition-colors"
            @click="showEmailModal = false"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <form
          class="space-y-3"
          @submit.prevent="handleEmailChange"
        >
          <div>
            <label for="input-current-email" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              当前邮箱
            </label>
            <input id="input-current-email"
              :value="currentEmail"
              type="email"
              name="current-email"
              readonly
              autocomplete="username email"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 dark:text-gray-400 cursor-not-allowed"
            >
          </div>
          
          <div v-if="emailStep === 1">
            <label for="email-verification-type-helper" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              验证方式
            </label>
            <input id="email-verification-type-helper" type="text" class="sr-only" :value="emailVerificationType" tabindex="-1" readonly autocomplete="off">
            <div class="grid grid-cols-2 gap-2">
              <button
                type="button"
                :class="[
                  'px-3 py-2 rounded-lg text-xs font-medium transition-all text-center',
                  emailVerificationType === 'password' 
                    ? 'bg-primary text-white shadow-sm' 
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                ]"
                @click="emailVerificationType = 'password'"
              >
                密码验证
              </button>
              
              <button
                type="button"
                :class="[
                  'px-3 py-2 rounded-lg text-xs font-medium transition-all text-center',
                  emailVerificationType === 'old_email' 
                    ? 'bg-primary text-white shadow-sm' 
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                ]"
                @click="emailVerificationType = 'old_email'"
              >
                邮箱验证
              </button>
            </div>
          </div>
          
          <div v-if="emailVerificationType === 'password' && emailStep === 1">
            <label for="email-password-username" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              当前用户名
            </label>
            <input id="email-password-username"
              :value="currentUsername"
              type="text"
              name="username"
              readonly
              autocomplete="username"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 dark:text-gray-400 cursor-not-allowed"
            >
          </div>
          <div v-if="emailVerificationType === 'password' && emailStep === 1">
            <label for="input-emailForm-password" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              当前密码 <span class="text-red-500">*</span>
            </label>
            <input id="input-emailForm-password"
              v-model="emailForm.password"
              type="password"
              name="email-password"
              autocomplete="current-password"
              placeholder="请输入当前密码"
              :class="[
                'w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800/50 border rounded-lg text-gray-900 dark:text-white focus:outline-none',
                emailErrors.password ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-gray-700 focus:border-primary'
              ]"
            >
            <p v-if="emailErrors.password" class="mt-1 text-xs text-red-500">{{ emailErrors.password }}</p>
          </div>
          
          <div
            v-if="emailVerificationType === 'old_email' && emailStep === 1"
            class="flex gap-2"
          >
            <div class="flex-1">
              <label for="input-emailForm-old_email_code" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                原邮箱验证码 <span class="text-red-500">*</span>
              </label>
              <input id="input-emailForm-old_email_code"
                v-model="emailForm.old_email_code"
                type="text"
                name="old-email-code"
                maxlength="6"
                autocomplete="one-time-code"
                placeholder="6位验证码"
                :class="[
                  'w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800/50 border rounded-lg text-gray-900 dark:text-white focus:outline-none',
                  emailErrors.old_email_code ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-gray-700 focus:border-primary'
                ]"
              >
              <p v-if="emailErrors.old_email_code" class="mt-1 text-xs text-red-500">{{ emailErrors.old_email_code }}</p>
            </div>
            <div class="flex items-end">
              <button
                type="button"
                :disabled="oldEmailCountdown > 0 || sendOldCodeLoading"
                class="px-3 py-2 text-xs font-medium rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50 whitespace-nowrap"
                @click="handleSendOldEmailCode"
              >
                <span v-if="sendOldCodeLoading">发送中</span>
                <span v-else-if="oldEmailCountdown > 0">{{ oldEmailCountdown }}s</span>
                <span v-else>获取</span>
              </button>
            </div>
          </div>
          
          <div v-if="emailStep === 1">
            <label for="input-emailForm-new_email" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              新邮箱 <span class="text-red-500">*</span>
            </label>
            <input id="input-emailForm-new_email"
              v-model="emailForm.new_email"
              type="email"
              name="new-email"
              autocomplete="email"
              placeholder="请输入新邮箱"
              :class="[
                'w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800/50 border rounded-lg text-gray-900 dark:text-white focus:outline-none',
                emailErrors.new_email ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-gray-700 focus:border-primary'
              ]"
            >
            <p v-if="emailErrors.new_email" class="mt-1 text-xs text-red-500">{{ emailErrors.new_email }}</p>
          </div>
          
          <div
            v-if="emailStep === 2"
            class="space-y-3"
          >
            <div class="p-2.5 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg flex items-start gap-2">
              <svg class="w-4 h-4 text-blue-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p class="text-xs text-blue-600 dark:text-blue-400">
                验证码已发送至 {{ emailForm.new_email }}
              </p>
            </div>
            
            <div class="flex gap-2">
              <div class="flex-1">
                <label for="input-emailForm-code" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  新邮箱验证码 <span class="text-red-500">*</span>
                </label>
                <input id="input-emailForm-code"
                  v-model="emailForm.code"
                  type="text"
                  name="new-email-code"
                  maxlength="6"
                  autocomplete="one-time-code"
                  placeholder="6位验证码"
                  :class="[
                    'w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800/50 border rounded-lg text-gray-900 dark:text-white focus:outline-none',
                    emailErrors.code ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-gray-700 focus:border-primary'
                  ]"
                >
                <p v-if="emailErrors.code" class="mt-1 text-xs text-red-500">{{ emailErrors.code }}</p>
              </div>
              <div class="flex items-end">
                <button
                  type="button"
                  :disabled="countdown > 0 || sendCodeLoading"
                  class="px-3 py-2 text-xs font-medium rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50 whitespace-nowrap"
                  @click="handleSendCode"
                >
                  <span v-if="sendCodeLoading">发送中</span>
                  <span v-else-if="countdown > 0">{{ countdown }}s</span>
                  <span v-else>重发</span>
                </button>
              </div>
            </div>
          </div>
          
          <div
            v-if="emailError"
            class="p-2.5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-2"
          >
            <svg class="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-xs text-red-600 dark:text-red-400">{{ emailError }}</p>
          </div>
        </form>
        
        <div class="flex justify-end gap-2 mt-5 pt-4 border-t border-gray-100 dark:border-gray-800">
          <button
            type="button"
            v-if="emailStep === 2"
            class="px-4 py-2 text-xs font-medium rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            @click="emailStep = 1"
          >
            返回
          </button>
          <button
            type="button"
            class="px-4 py-2 text-xs font-medium rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            @click="showEmailModal = false"
          >
            取消
          </button>
          <button
            type="button"
            v-if="emailStep === 1"
            class="px-4 py-2 text-xs font-medium rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50"
            :disabled="sendCodeLoading"
            @click="handleSendCode"
          >
            {{ sendCodeLoading ? '发送中...' : '发送验证码' }}
          </button>
          <button
            type="button"
            v-if="emailStep === 2"
            class="px-4 py-2 text-xs font-medium rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50"
            :disabled="isChangingEmail"
            @click="handleEmailChange"
          >
            {{ isChangingEmail ? '修改中...' : '确认修改' }}
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showPasswordModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      @click.self="showPasswordModal = false"
    >
      <div class="glass-card w-full max-w-lg p-5 animate-fade-in">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-bold text-gray-900 dark:text-white">{{ hasPassword ? '修改密码' : '设置密码' }}</h3>
          <button
            class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-200 rounded-lg transition-colors"
            @click="showPasswordModal = false"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <template v-if="hasPassword">
          <form
            class="grid grid-cols-1 sm:grid-cols-3 gap-3"
            @submit.prevent="handleChangePassword"
          >
            <div>
              <label for="password-current-username" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                当前用户名
              </label>
              <input id="password-current-username"
                :value="currentUsername"
                type="text"
                name="username"
                readonly
                autocomplete="username"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 dark:text-gray-400 cursor-not-allowed"
              >
            </div>
            <div>
              <label for="input-passwordForm-current_password" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                当前密码
              </label>
              <div class="relative">
                <input id="input-passwordForm-current_password"
                  v-model="passwordForm.current_password"
                  :type="showCurrentPassword ? 'text' : 'password'"
                  name="current-password"
                  autocomplete="current-password"
                  :class="[
                    'w-full px-3 py-2 pr-9 text-sm bg-gray-50 dark:bg-gray-800/50 border rounded-lg text-gray-900 dark:text-white focus:outline-none',
                    passwordErrors.current_password ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-gray-700 focus:border-primary'
                  ]"
                  placeholder="请输入当前密码"
                >
                <button
                  type="button"
                  class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  @click="showCurrentPassword = !showCurrentPassword"
                >
                  <svg
                    v-if="showCurrentPassword"
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                    />
                  </svg>
                  <svg
                    v-else
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                    />
                  </svg>
                </button>
              </div>
              <p
                v-if="passwordErrors.current_password"
                class="mt-1.5 text-xs text-red-500 flex items-center gap-1"
              >
                <svg class="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {{ passwordErrors.current_password }}
              </p>
            </div>
            
            <div>
              <label for="input-passwordForm-new_password" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                新密码
              </label>
              <div class="relative">
                <input id="input-passwordForm-new_password"
                  v-model="passwordForm.new_password"
                  :type="showNewPassword ? 'text' : 'password'"
                  name="new-password"
                  autocomplete="new-password"
                  :class="[
                    'w-full px-3 py-2 pr-9 text-sm bg-gray-50 dark:bg-gray-800/50 border rounded-lg text-gray-900 dark:text-white focus:outline-none',
                    passwordErrors.new_password ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-gray-700 focus:border-primary'
                  ]"
                  placeholder="至少6位字符"
                >
                <button
                  type="button"
                  class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  @click="showNewPassword = !showNewPassword"
                >
                  <svg
                    v-if="showNewPassword"
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                    />
                  </svg>
                  <svg
                    v-else
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                    />
                  </svg>
                </button>
              </div>
              <p
                v-if="passwordErrors.new_password"
                class="mt-1.5 text-xs text-red-500 flex items-center gap-1"
              >
                <svg class="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {{ passwordErrors.new_password }}
              </p>
              <div
                v-if="passwordForm.new_password"
                class="mt-1.5 flex items-center gap-2"
              >
                <div class="flex-1 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    class="h-full transition-all duration-300 rounded-full"
                    :class="passwordStrength.color"
                    :style="{ width: `${passwordStrength.level * 33.33}%` }"
                  />
                </div>
                <span class="text-xs font-medium" :class="passwordStrength.level === 1 ? 'text-red-500' : passwordStrength.level === 2 ? 'text-yellow-500' : 'text-green-500'">{{ passwordStrength.text }}</span>
              </div>
            </div>
            
            <div>
              <label for="input-passwordForm-confirm_password" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                确认密码
              </label>
              <div class="relative">
                <input id="input-passwordForm-confirm_password"
                  v-model="passwordForm.confirm_password"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  name="confirm-password"
                  autocomplete="new-password"
                  :class="[
                    'w-full px-3 py-2 pr-9 text-sm bg-gray-50 dark:bg-gray-800/50 border rounded-lg text-gray-900 dark:text-white focus:outline-none',
                    passwordErrors.confirm_password ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-gray-700 focus:border-primary'
                  ]"
                  placeholder="再次输入新密码"
                >
                <button
                  type="button"
                  class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <svg
                    v-if="showConfirmPassword"
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                    />
                  </svg>
                  <svg
                    v-else
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                    />
                  </svg>
                </button>
              </div>
              <p
                v-if="passwordErrors.confirm_password"
                class="mt-1.5 text-xs text-red-500 flex items-center gap-1"
              >
                <svg class="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {{ passwordErrors.confirm_password }}
              </p>
            </div>
          </form>

          <div
            v-if="passwordErrors.general"
            class="mt-3 p-2.5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-2"
          >
            <svg class="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-xs text-red-600 dark:text-red-400">{{ passwordErrors.general }}</p>
          </div>

          <div class="flex justify-end gap-2 mt-5 pt-4 border-t border-gray-100 dark:border-gray-800">
            <button
              class="px-4 py-2 text-xs font-medium rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              @click="showPasswordModal = false"
            >
              取消
            </button>
            <button
              class="px-4 py-2 text-xs font-medium rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50"
              :disabled="isChangingPassword"
              @click="handleChangePassword"
            >
              {{ isChangingPassword ? '修改中...' : '确认修改' }}
            </button>
          </div>
        </template>

        <template v-else>
          <div class="mb-3 p-2.5 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg flex items-start gap-2">
            <svg class="w-4 h-4 text-blue-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-xs text-blue-600 dark:text-blue-400">当前账号通过第三方登录，尚未设置密码。请通过邮箱验证码设置密码。</p>
          </div>

          <form
            class="space-y-3"
            @submit.prevent="handleSetPassword"
          >
            <div>
              <label for="input-setPassword-email" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                邮箱
              </label>
              <input id="input-setPassword-email"
                :value="currentEmail"
                type="text"
                readonly
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 dark:text-gray-400 cursor-not-allowed"
              >
            </div>

            <div>
              <label for="input-setPassword-code" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                验证码
              </label>
              <div class="flex gap-2">
                <input id="input-setPassword-code"
                  v-model="setPasswordCode"
                  type="text"
                  maxlength="6"
                  placeholder="请输入6位验证码"
                  :class="[
                    'flex-1 px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800/50 border rounded-lg text-gray-900 dark:text-white focus:outline-none',
                    setPasswordErrors.code ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-gray-700 focus:border-primary'
                  ]"
                >
                <button
                  type="button"
                  :disabled="setPasswordCountdown > 0 || isSettingPassword"
                  class="px-3 py-2 text-xs font-medium rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50 whitespace-nowrap"
                  @click="handleSendSetPasswordCode"
                >
                  <span v-if="isSettingPassword && setPasswordCountdown <= 0">发送中</span>
                  <span v-else-if="setPasswordCountdown > 0">{{ setPasswordCountdown }}s</span>
                  <span v-else>发送验证码</span>
                </button>
              </div>
              <p
                v-if="setPasswordErrors.code"
                class="mt-1 text-xs text-red-500"
              >
                {{ setPasswordErrors.code }}
              </p>
            </div>

            <div>
              <label for="input-setPassword-new_password" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                新密码
              </label>
              <div class="relative">
                <input id="input-setPassword-new_password"
                  v-model="setPasswordForm.new_password"
                  :type="showNewPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  :class="[
                    'w-full px-3 py-2 pr-9 text-sm bg-gray-50 dark:bg-gray-800/50 border rounded-lg text-gray-900 dark:text-white focus:outline-none',
                    setPasswordErrors.new_password ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-gray-700 focus:border-primary'
                  ]"
                  placeholder="至少6位字符"
                >
                <button
                  type="button"
                  class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  @click="showNewPassword = !showNewPassword"
                >
                  <svg
                    v-if="showNewPassword"
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                  <svg
                    v-else
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
              </div>
              <p
                v-if="setPasswordErrors.new_password"
                class="mt-1 text-xs text-red-500"
              >
                {{ setPasswordErrors.new_password }}
              </p>
            </div>

            <div>
              <label for="input-setPassword-confirm_password" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                确认密码
              </label>
              <div class="relative">
                <input id="input-setPassword-confirm_password"
                  v-model="setPasswordForm.confirm_password"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  :class="[
                    'w-full px-3 py-2 pr-9 text-sm bg-gray-50 dark:bg-gray-800/50 border rounded-lg text-gray-900 dark:text-white focus:outline-none',
                    setPasswordErrors.confirm_password ? 'border-red-300 dark:border-red-500' : 'border-gray-200 dark:border-gray-700 focus:border-primary'
                  ]"
                  placeholder="再次输入新密码"
                >
                <button
                  type="button"
                  class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <svg
                    v-if="showConfirmPassword"
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                  <svg
                    v-else
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
              </div>
              <p
                v-if="setPasswordErrors.confirm_password"
                class="mt-1 text-xs text-red-500"
              >
                {{ setPasswordErrors.confirm_password }}
              </p>
            </div>
          </form>

          <div
            v-if="setPasswordErrors.general"
            class="mt-3 p-2.5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-2"
          >
            <svg class="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-xs text-red-600 dark:text-red-400">{{ setPasswordErrors.general }}</p>
          </div>

          <div class="flex justify-end gap-2 mt-5 pt-4 border-t border-gray-100 dark:border-gray-800">
            <button
              class="px-4 py-2 text-xs font-medium rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              @click="showPasswordModal = false"
            >
              取消
            </button>
            <button
              class="px-4 py-2 text-xs font-medium rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50"
              :disabled="isSettingPassword"
              @click="handleSetPassword"
            >
              {{ isSettingPassword ? '设置中...' : '确认设置' }}
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
