import { ref } from 'vue'

export interface DialogOptions {
  title?: string
  message: string
  type?: 'confirm' | 'alert' | 'success' | 'error'
  confirmText?: string
  cancelText?: string
  autoClose?: boolean
  duration?: number
}

const isVisible = ref(false)
const dialogOptions = ref<DialogOptions>({
  message: '',
  type: 'alert'
})

let resolvePromise: ((value: boolean) => void) | null = null
let autoCloseTimer: ReturnType<typeof setTimeout> | null = null

const clearAutoCloseTimer = () => {
  if (autoCloseTimer) {
    clearTimeout(autoCloseTimer)
    autoCloseTimer = null
  }
}

const closeDialog = (result: boolean) => {
  clearAutoCloseTimer()
  isVisible.value = false
  if (resolvePromise) {
    resolvePromise(result)
    resolvePromise = null
  }
}

const showConfirm = (options: DialogOptions): Promise<boolean> => {
  clearAutoCloseTimer()
  dialogOptions.value = { ...options, type: 'confirm' }
  isVisible.value = true
  
  return new Promise((resolve) => {
    resolvePromise = resolve
  })
}

const showAlert = (options: DialogOptions): Promise<boolean> => {
  clearAutoCloseTimer()
  dialogOptions.value = { ...options, type: options.type || 'alert' }
  isVisible.value = true
  
  const duration = options.duration ?? 3000
  const autoClose = options.autoClose ?? true
  
  return new Promise((resolve) => {
    resolvePromise = resolve
    
    if (autoClose && (options.type === 'success' || options.type === 'error' || options.type === 'alert')) {
      autoCloseTimer = setTimeout(() => {
        closeDialog(true)
      }, duration)
    }
  })
}

const showSuccess = (message: string, title?: string, autoClose: boolean = true, duration: number = 2000): Promise<boolean> => {
  return showAlert({ message, title, type: 'success', autoClose, duration })
}

const showError = (message: string, title?: string, autoClose: boolean = true, duration: number = 3000): Promise<boolean> => {
  return showAlert({ message, title, type: 'error', autoClose, duration })
}

const handleConfirm = () => {
  closeDialog(true)
}

const handleCancel = () => {
  closeDialog(false)
}

export function useDialogStore() {
  return {
    isVisible,
    dialogOptions,
    showConfirm,
    showAlert,
    showSuccess,
    showError,
    handleConfirm,
    handleCancel
  }
}
