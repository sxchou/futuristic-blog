<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore, useUserProfileStore, useDialogStore } from '@/stores'
import { userProfileApi } from '@/api/userProfile'
import { userApi } from '@/api/users'
import { checkServerHealth } from '@/api/client'
import AvatarCropper from '@/components/common/AvatarCropper.vue'
import { formatDateTime } from '@/utils/date'

const authStore = useAuthStore()
const userProfileStore = useUserProfileStore()
const dialogStore = useDialogStore()

const isLoading = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const fileInput = ref<HTMLInputElement | null>(null)
const showCropper = ref(false)
const selectedImageSrc = ref('')

const showPasswordSection = ref(false)
const isChangingPassword = ref(false)
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

const passwordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const passwordErrors = ref({
  current_password: '',
  new_password: '',
  confirm_password: ''
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
    confirm_password: ''
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
  if (!validatePasswordForm()) return
  
  isChangingPassword.value = true
  
  try {
    const serverReady = await checkServerHealth()
    if (!serverReady) {
      dialogStore.showError('服务器暂时不可用，请稍后重试')
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
    showPasswordSection.value = false
  } catch (error: any) {
    console.error('Password change error:', error)
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      dialogStore.showError(detail)
    } else if (error.message) {
      dialogStore.showError(error.message)
    } else {
      dialogStore.showError('密码修改失败')
    }
  } finally {
    isChangingPassword.value = false
  }
}

const togglePasswordSection = () => {
  showPasswordSection.value = !showPasswordSection.value
  if (!showPasswordSection.value) {
    passwordForm.value = {
      current_password: '',
      new_password: '',
      confirm_password: ''
    }
    passwordErrors.value = {
      current_password: '',
      new_password: '',
      confirm_password: ''
    }
  }
}

const showEmailSection = ref(false)
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
  
  sendOldCodeLoading.value = true
  try {
    await userApi.sendCodeToOldEmail()
    dialogStore.showSuccess('验证码已发送至当前邮箱')
    startOldEmailCountdown()
  } catch (error: any) {
    emailError.value = error.response?.data?.detail || '发送验证码失败'
  } finally {
    sendOldCodeLoading.value = false
  }
}

const handleSendCode = async () => {
  emailError.value = ''
  
  if (!emailForm.value.new_email) {
    emailError.value = '请输入新邮箱地址'
    return
  }
  
  if (!validateEmail(emailForm.value.new_email)) {
    emailError.value = '请输入有效的邮箱地址'
    return
  }
  
  if (emailForm.value.new_email === currentEmail.value) {
    emailError.value = '新邮箱不能与当前邮箱相同'
    return
  }
  
  if (emailVerificationType.value === 'password') {
    if (!emailForm.value.password) {
      emailError.value = '请输入当前密码'
      return
    }
  } else {
    if (!emailForm.value.old_email_code) {
      emailError.value = '请输入原邮箱验证码'
      return
    }
  }
  
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
    emailError.value = error.response?.data?.detail || '发送验证码失败'
  } finally {
    sendCodeLoading.value = false
  }
}

const handleEmailChange = async () => {
  emailError.value = ''
  
  if (!emailForm.value.new_email) {
    emailError.value = '请输入新邮箱地址'
    return
  }
  
  if (!emailForm.value.code) {
    emailError.value = '请输入验证码'
    return
  }
  
  isChangingEmail.value = true
  try {
    await userApi.verifyEmailChange({
      new_email: emailForm.value.new_email,
      code: emailForm.value.code,
      password: emailVerificationType.value === 'password' ? emailForm.value.password : undefined
    })
    dialogStore.showSuccess('邮箱修改成功')
    showEmailSection.value = false
    emailStep.value = 1
    emailForm.value = { new_email: '', password: '', code: '', old_email_code: '' }
    await authStore.fetchUser()
    await userProfileStore.refreshProfile()
  } catch (error: any) {
    emailError.value = error.response?.data?.detail || '邮箱修改失败'
  } finally {
    isChangingEmail.value = false
  }
}

const toggleEmailSection = () => {
  showEmailSection.value = !showEmailSection.value
  if (!showEmailSection.value) {
    emailStep.value = 1
    emailForm.value = { new_email: '', password: '', code: '', old_email_code: '' }
    emailError.value = ''
    emailVerificationType.value = 'password'
  }
}

const showUsernameSection = ref(false)
const isChangingUsername = ref(false)
const usernameError = ref('')

const usernameForm = ref({
  new_username: '',
  password: ''
})

const currentUsername = computed(() => authStore.user?.username || '')

const validateUsername = (username: string): { valid: boolean; message: string } => {
  if (!username) {
    return { valid: false, message: '请输入新用户名' }
  }
  
  if (username.length < 4) {
    return { valid: false, message: '用户名长度至少4个字符' }
  }
  
  if (username.length > 20) {
    return { valid: false, message: '用户名长度不能超过20个字符' }
  }
  
  const usernamePattern = /^[a-zA-Z0-9_\u4e00-\u9fa5]+$/
  if (!usernamePattern.test(username)) {
    return { valid: false, message: '用户名只能包含字母、数字、下划线和中文' }
  }
  
  return { valid: true, message: '' }
}

const handleUsernameChange = async () => {
  usernameError.value = ''
  
  const validation = validateUsername(usernameForm.value.new_username)
  if (!validation.valid) {
    usernameError.value = validation.message
    return
  }
  
  if (usernameForm.value.new_username === currentUsername.value) {
    usernameError.value = '新用户名不能与当前用户名相同'
    return
  }
  
  if (!usernameForm.value.password) {
    usernameError.value = '请输入当前密码'
    return
  }
  
  isChangingUsername.value = true
  try {
    await userApi.changeUsername({
      new_username: usernameForm.value.new_username,
      password: usernameForm.value.password
    })
    dialogStore.showSuccess('用户名修改成功')
    showUsernameSection.value = false
    usernameForm.value = { new_username: '', password: '' }
    await authStore.fetchUser()
    await userProfileStore.refreshProfile()
  } catch (error: any) {
    usernameError.value = error.response?.data?.detail || '用户名修改失败'
  } finally {
    isChangingUsername.value = false
  }
}

const toggleUsernameSection = () => {
  showUsernameSection.value = !showUsernameSection.value
  if (!showUsernameSection.value) {
    usernameForm.value = { new_username: '', password: '' }
    usernameError.value = ''
  }
}

onMounted(fetchProfile)
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
      class="space-y-5"
    >
      <div class="glass-card overflow-hidden">
        <div class="px-6 py-6">
          <div class="flex flex-col sm:flex-row items-center sm:items-start gap-5">
            <div class="relative group">
              <div
                class="w-20 h-20 rounded-2xl flex items-center justify-center font-bold text-white text-2xl shadow-lg overflow-hidden cursor-pointer transition-all duration-300 group-hover:scale-105 ring-2 ring-white dark:ring-gray-700"
                :style="avatarStyle"
                @click="triggerUpload"
              >
                <span v-if="showInitial">{{ initial }}</span>
              </div>
              
              <div
                v-if="isUploading"
                class="absolute inset-0 bg-black/50 rounded-2xl flex items-center justify-center backdrop-blur-sm"
              >
                <div class="text-center">
                  <div class="text-white text-base font-medium">{{ uploadProgress }}%</div>
                </div>
              </div>
              
              <div class="absolute -bottom-1 -right-1 flex gap-1">
                <button
                  class="w-6 h-6 bg-white dark:bg-gray-700 rounded-full shadow flex items-center justify-center text-gray-500 dark:text-gray-400 hover:text-primary transition-colors"
                  :disabled="isUploading"
                  title="更换头像"
                  @click="triggerUpload"
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
            
            <div class="flex-1 text-center sm:text-left">
              <div class="flex flex-col sm:flex-row sm:items-center gap-2 mb-2">
                <h2 class="text-xl font-bold text-gray-900 dark:text-white">
                  {{ user?.username }}
                </h2>
                <div class="flex items-center justify-center sm:justify-start gap-2">
                  <span 
                    class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                    :class="user?.is_admin ? 'bg-primary/10 dark:bg-primary/20 text-primary' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'"
                  >
                    {{ user?.is_admin ? '管理员' : '用户' }}
                  </span>
                  <span 
                    class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                    :class="user?.is_verified ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400'"
                  >
                    {{ user?.is_verified ? '已验证' : '未验证' }}
                  </span>
                </div>
              </div>
              
              <p class="text-gray-500 dark:text-gray-400 text-sm mb-3">
                {{ user?.email }}
              </p>
              
              <div class="flex flex-wrap gap-2 justify-center sm:justify-start">
                <button
                  v-if="profile?.oauth_avatar_url && profile?.avatar_type !== 'oauth'"
                  class="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-lg bg-primary/10 dark:bg-primary/20 text-primary hover:bg-primary/20 dark:hover:bg-primary/30 transition-colors"
                  :disabled="isUploading"
                  @click="handleUseOAuthAvatar"
                >
                  <svg
                    class="w-3.5 h-3.5 mr-1"
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
                  使用 OAuth 头像
                </button>
                <button
                  v-if="profile?.avatar_type === 'custom'"
                  class="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-lg bg-primary/10 dark:bg-primary/20 text-primary hover:bg-primary/20 dark:hover:bg-primary/30 transition-colors"
                  @click="handleResetAvatar"
                >
                  <svg
                    class="w-3.5 h-3.5 mr-1"
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
          </div>
        </div>
        
        <div class="px-6 py-3 border-t border-gray-100 dark:border-gray-800">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="text-center sm:text-left">
              <p class="text-xs text-gray-400 dark:text-gray-500 mb-0.5">注册时间</p>
              <p class="text-sm font-medium text-gray-900 dark:text-white">{{ formatDateTime(user?.created_at) }}</p>
            </div>
          </div>
        </div>
        
        <input
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

      <div class="glass-card">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
                <svg
                  class="w-5 h-5 text-primary"
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
              <div>
                <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
                  用户名设置
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  管理您的账户用户名
                </p>
              </div>
            </div>
            <button
              v-if="!showUsernameSection"
              class="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
              @click="showUsernameSection = true"
            >
              <svg
                class="w-3.5 h-3.5 mr-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                />
              </svg>
              更改用户名
            </button>
          </div>
        </div>
        
        <div
          v-if="!showUsernameSection"
          class="px-6 py-4"
        >
          <div class="flex items-center justify-between py-3 px-4 bg-primary/5 dark:bg-primary/10 rounded-xl">
            <div class="flex items-center gap-3">
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
              <div>
                <p class="text-sm font-medium text-gray-900 dark:text-white">当前用户名</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ currentUsername }}</p>
              </div>
            </div>
            <span class="text-sm text-gray-400 dark:text-gray-500">
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
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
            </span>
          </div>
        </div>
        
        <div
          v-else
          class="px-6 py-4"
        >
          <div class="space-y-4 mb-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                当前用户名
              </label>
              <input
                :value="currentUsername"
                type="text"
                disabled
                class="w-full px-4 py-2.5 text-sm bg-gray-100 dark:bg-gray-800 border-2 border-transparent rounded-xl text-gray-500 dark:text-gray-400 cursor-not-allowed"
              >
            </div>
            
            <div>
              <label
                for="new-username"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                新用户名
              </label>
              <input
                id="new-username"
                v-model="usernameForm.new_username"
                type="text"
                maxlength="20"
                placeholder="请输入新用户名（4-20个字符）"
                class="w-full px-4 py-2.5 text-sm bg-gray-50 dark:bg-gray-800/50 border-2 border-transparent focus:border-gray-400 dark:focus:border-gray-500 rounded-xl text-gray-900 dark:text-white transition-colors focus:outline-none"
              >
              <p class="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
                用户名只能包含字母、数字、下划线和中文
              </p>
            </div>
            
            <div>
              <label
                for="username-password"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                当前密码
              </label>
              <input
                id="username-password"
                v-model="usernameForm.password"
                type="password"
                placeholder="请输入当前密码"
                class="w-full px-4 py-2.5 text-sm bg-gray-50 dark:bg-gray-800/50 border-2 border-transparent focus:border-gray-400 dark:focus:border-gray-500 rounded-xl text-gray-900 dark:text-white transition-colors focus:outline-none"
              >
            </div>
            
            <div
              v-if="usernameError"
              class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl"
            >
              <p class="text-sm text-red-600 dark:text-red-400">
                {{ usernameError }}
              </p>
            </div>
          </div>
          
          <div class="flex gap-3 pt-2">
            <button
              class="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-xl bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="isChangingUsername"
              @click="handleUsernameChange"
            >
              <svg
                v-if="isChangingUsername"
                class="w-4 h-4 mr-1.5 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              {{ isChangingUsername ? '修改中...' : '确认更改' }}
            </button>
            <button
              class="px-5 py-2.5 text-sm font-medium rounded-xl bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              @click="toggleUsernameSection"
            >
              取消
            </button>
          </div>
        </div>
      </div>

      <div class="glass-card">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
                <svg
                  class="w-5 h-5 text-primary"
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
              <div>
                <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
                  安全设置
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  管理您的账户安全
                </p>
              </div>
            </div>
            <button
              v-if="!showPasswordSection"
              class="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
              @click="showPasswordSection = true"
            >
              <svg
                class="w-3.5 h-3.5 mr-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                />
              </svg>
              修改密码
            </button>
          </div>
        </div>
        
        <div
          v-if="!showPasswordSection"
          class="px-6 py-4"
        >
          <div class="flex items-center justify-between py-3 px-4 bg-primary/5 dark:bg-primary/10 rounded-xl">
            <div class="flex items-center gap-3">
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
                    d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                  />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-900 dark:text-white">登录密码</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">定期修改密码可以提高账户安全性</p>
              </div>
            </div>
            <span class="text-sm text-gray-400 dark:text-gray-500">••••••••</span>
          </div>
        </div>
        
        <div
          v-else
          class="px-6 py-4"
        >
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label
                for="current-password"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >当前密码</label>
              <div class="relative">
                <input
                  id="current-password"
                  v-model="passwordForm.current_password"
                  :type="showCurrentPassword ? 'text' : 'password'"
                  :class="[
                    'w-full px-4 py-2.5 pr-11 text-sm bg-gray-50 dark:bg-gray-800/50 border-2 rounded-xl text-gray-900 dark:text-white transition-colors focus:outline-none',
                    passwordErrors.current_password ? 'border-red-300 dark:border-red-500' : 'border-transparent focus:border-gray-400 dark:focus:border-gray-500'
                  ]"
                  placeholder="请输入当前密码"
                >
                <button
                  type="button"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                  @click="showCurrentPassword = !showCurrentPassword"
                >
                  <svg
                    v-if="showCurrentPassword"
                    class="w-5 h-5"
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
                    class="w-5 h-5"
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
                class="mt-1.5 text-xs text-red-500"
              >
                {{ passwordErrors.current_password }}
              </p>
            </div>
            
            <div>
              <label
                for="new-password"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >新密码</label>
              <div class="relative">
                <input
                  id="new-password"
                  v-model="passwordForm.new_password"
                  :type="showNewPassword ? 'text' : 'password'"
                  :class="[
                    'w-full px-4 py-2.5 pr-11 text-sm bg-gray-50 dark:bg-gray-800/50 border-2 rounded-xl text-gray-900 dark:text-white transition-colors focus:outline-none',
                    passwordErrors.new_password ? 'border-red-300 dark:border-red-500' : 'border-transparent focus:border-gray-400 dark:focus:border-gray-500'
                  ]"
                  placeholder="至少6位字符"
                >
                <button
                  type="button"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                  @click="showNewPassword = !showNewPassword"
                >
                  <svg
                    v-if="showNewPassword"
                    class="w-5 h-5"
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
                    class="w-5 h-5"
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
                class="mt-1.5 text-xs text-red-500"
              >
                {{ passwordErrors.new_password }}
              </p>
              <div
                v-if="passwordForm.new_password"
                class="mt-2 flex items-center gap-2"
              >
                <div class="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
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
              <label
                for="confirm-password"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >确认新密码</label>
              <div class="relative">
                <input
                  id="confirm-password"
                  v-model="passwordForm.confirm_password"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  :class="[
                    'w-full px-4 py-2.5 pr-11 text-sm bg-gray-50 dark:bg-gray-800/50 border-2 rounded-xl text-gray-900 dark:text-white transition-colors focus:outline-none',
                    passwordErrors.confirm_password ? 'border-red-300 dark:border-red-500' : 'border-transparent focus:border-gray-400 dark:focus:border-gray-500'
                  ]"
                  placeholder="再次输入新密码"
                >
                <button
                  type="button"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <svg
                    v-if="showConfirmPassword"
                    class="w-5 h-5"
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
                    class="w-5 h-5"
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
                class="mt-1.5 text-xs text-red-500"
              >
                {{ passwordErrors.confirm_password }}
              </p>
            </div>
          </div>
          
          <div class="flex gap-3 pt-2">
            <button
              class="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-xl bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="isChangingPassword"
              @click="handleChangePassword"
            >
              <svg
                v-if="isChangingPassword"
                class="w-4 h-4 mr-1.5 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              {{ isChangingPassword ? '修改中...' : '确认修改' }}
            </button>
            <button
              class="px-5 py-2.5 text-sm font-medium rounded-xl bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              @click="togglePasswordSection"
            >
              取消
            </button>
          </div>
        </div>
      </div>

      <div class="glass-card">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
                <svg
                  class="w-5 h-5 text-primary"
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
              <div>
                <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
                  邮箱设置
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  管理您的账户邮箱
                </p>
              </div>
            </div>
            <button
              v-if="!showEmailSection"
              class="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
              @click="showEmailSection = true"
            >
              <svg
                class="w-3.5 h-3.5 mr-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                />
              </svg>
              更改邮箱
            </button>
          </div>
        </div>
        
        <div
          v-if="!showEmailSection"
          class="px-6 py-4"
        >
          <div class="flex items-center justify-between py-3 px-4 bg-primary/5 dark:bg-primary/10 rounded-xl">
            <div class="flex items-center gap-3">
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
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-900 dark:text-white">当前邮箱</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ currentEmail }}</p>
              </div>
            </div>
            <span class="text-sm text-gray-400 dark:text-gray-500">
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
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </span>
          </div>
        </div>
        
        <div
          v-else
          class="px-6 py-4"
        >
          <div class="space-y-4 mb-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                当前邮箱
              </label>
              <input
                :value="currentEmail"
                type="email"
                disabled
                class="w-full px-4 py-2.5 text-sm bg-gray-100 dark:bg-gray-800 border-2 border-transparent rounded-xl text-gray-500 dark:text-gray-400 cursor-not-allowed"
              >
            </div>
            
            <div v-if="emailStep === 1">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                验证方式
              </label>
              <div class="grid grid-cols-2 gap-3">
                <button
                  :class="[
                    'p-3 rounded-xl border-2 transition-all text-left',
                    emailVerificationType === 'password' 
                      ? 'border-primary bg-primary/5 dark:bg-primary/10' 
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  ]"
                  @click="emailVerificationType = 'password'"
                >
                  <div class="flex items-center gap-2 mb-1">
                    <svg
                      class="w-4 h-4"
                      :class="emailVerificationType === 'password' ? 'text-primary' : 'text-gray-400'"
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
                    <span
                      class="text-sm font-medium"
                      :class="emailVerificationType === 'password' ? 'text-primary' : 'text-gray-700 dark:text-gray-300'"
                    >
                      密码验证
                    </span>
                  </div>
                  <p class="text-xs text-gray-500 dark:text-gray-400">
                    通过当前密码验证身份
                  </p>
                </button>
                
                <button
                  :class="[
                    'p-3 rounded-xl border-2 transition-all text-left',
                    emailVerificationType === 'old_email' 
                      ? 'border-primary bg-primary/5 dark:bg-primary/10' 
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  ]"
                  @click="emailVerificationType = 'old_email'"
                >
                  <div class="flex items-center gap-2 mb-1">
                    <svg
                      class="w-4 h-4"
                      :class="emailVerificationType === 'old_email' ? 'text-primary' : 'text-gray-400'"
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
                    <span
                      class="text-sm font-medium"
                      :class="emailVerificationType === 'old_email' ? 'text-primary' : 'text-gray-700 dark:text-gray-300'"
                    >
                      邮箱验证
                    </span>
                  </div>
                  <p class="text-xs text-gray-500 dark:text-gray-400">
                    通过原邮箱验证码验证
                  </p>
                </button>
              </div>
            </div>
            
            <div v-if="emailVerificationType === 'password' && emailStep === 1">
              <label
                for="email-password"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                当前密码
              </label>
              <input
                id="email-password"
                v-model="emailForm.password"
                type="password"
                placeholder="请输入当前密码"
                class="w-full px-4 py-2.5 text-sm bg-gray-50 dark:bg-gray-800/50 border-2 border-transparent focus:border-gray-400 dark:focus:border-gray-500 rounded-xl text-gray-900 dark:text-white transition-colors focus:outline-none"
              >
            </div>
            
            <div v-if="emailVerificationType === 'old_email' && emailStep === 1">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                原邮箱验证码
              </label>
              <div class="flex gap-2">
                <input
                  v-model="emailForm.old_email_code"
                  type="text"
                  maxlength="6"
                  placeholder="请输入6位验证码"
                  class="flex-1 px-4 py-2.5 text-sm bg-gray-50 dark:bg-gray-800/50 border-2 border-transparent focus:border-gray-400 dark:focus:border-gray-500 rounded-xl text-gray-900 dark:text-white transition-colors focus:outline-none"
                >
                <button
                  :disabled="oldEmailCountdown > 0 || sendOldCodeLoading"
                  class="px-4 py-2.5 text-sm font-medium rounded-xl bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                  @click="handleSendOldEmailCode"
                >
                  <span v-if="sendOldCodeLoading">发送中...</span>
                  <span v-else-if="oldEmailCountdown > 0">{{ oldEmailCountdown }}s</span>
                  <span v-else>获取验证码</span>
                </button>
              </div>
              <p class="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
                验证码将发送至 {{ currentEmail }}
              </p>
            </div>
            
            <div v-if="emailStep === 1">
              <label
                for="new-email"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                新邮箱
              </label>
              <input
                id="new-email"
                v-model="emailForm.new_email"
                type="email"
                placeholder="请输入新邮箱地址"
                class="w-full px-4 py-2.5 text-sm bg-gray-50 dark:bg-gray-800/50 border-2 border-transparent focus:border-gray-400 dark:focus:border-gray-500 rounded-xl text-gray-900 dark:text-white transition-colors focus:outline-none"
              >
            </div>
            
            <div v-if="emailStep === 2">
              <div class="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl mb-4">
                <p class="text-sm text-blue-600 dark:text-blue-400">
                  验证码已发送至 {{ emailForm.new_email }}，请查收邮件
                </p>
              </div>
              
              <label
                for="email-code"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                新邮箱验证码
              </label>
              <div class="flex gap-2">
                <input
                  id="email-code"
                  v-model="emailForm.code"
                  type="text"
                  maxlength="6"
                  placeholder="请输入6位验证码"
                  class="flex-1 px-4 py-2.5 text-sm bg-gray-50 dark:bg-gray-800/50 border-2 border-transparent focus:border-gray-400 dark:focus:border-gray-500 rounded-xl text-gray-900 dark:text-white transition-colors focus:outline-none"
                >
                <button
                  :disabled="countdown > 0 || sendCodeLoading"
                  class="px-4 py-2.5 text-sm font-medium rounded-xl bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                  @click="handleSendCode"
                >
                  <span v-if="sendCodeLoading">发送中...</span>
                  <span v-else-if="countdown > 0">{{ countdown }}s</span>
                  <span v-else>重新发送</span>
                </button>
              </div>
              <p class="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
                验证码有效期10分钟
              </p>
            </div>
            
            <div
              v-if="emailError"
              class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl"
            >
              <p class="text-sm text-red-600 dark:text-red-400">
                {{ emailError }}
              </p>
            </div>
          </div>
          
          <div class="flex gap-3 pt-2">
            <button
              v-if="emailStep === 1"
              class="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-xl bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="sendCodeLoading"
              @click="handleSendCode"
            >
              <svg
                v-if="sendCodeLoading"
                class="w-4 h-4 mr-1.5 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              {{ sendCodeLoading ? '发送中...' : '发送验证码' }}
            </button>
            <button
              v-if="emailStep === 2"
              class="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-xl bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="isChangingEmail"
              @click="handleEmailChange"
            >
              <svg
                v-if="isChangingEmail"
                class="w-4 h-4 mr-1.5 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              {{ isChangingEmail ? '修改中...' : '确认更改' }}
            </button>
            <button
              v-if="emailStep === 2"
              class="px-5 py-2.5 text-sm font-medium rounded-xl bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              @click="emailStep = 1"
            >
              返回上一步
            </button>
            <button
              class="px-5 py-2.5 text-sm font-medium rounded-xl bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              @click="toggleEmailSection"
            >
              取消
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="user?.is_admin"
        class="glass-card"
      >
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
              <svg
                class="w-5 h-5 text-primary"
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
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
                管理功能
              </h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                编辑网站所有者的公开资料信息
              </p>
            </div>
          </div>
        </div>
        <div class="px-6 py-4">
          <router-link
            to="/admin/profile"
            class="inline-flex items-center px-4 py-2 text-sm font-medium rounded-xl bg-primary text-white hover:bg-primary/90 transition-colors"
          >
            <svg
              class="w-4 h-4 mr-1.5"
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
            编辑网站资料
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
