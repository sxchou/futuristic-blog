import { ref, readonly } from 'vue'

interface DialogOptions {
  title?: string
  message: string
  type?: 'confirm' | 'alert' | 'success' | 'error'
  confirmText?: string
  cancelText?: string
}

const isVisible = ref(false)
const dialogOptions = ref<DialogOptions>({
  message: '',
  type: 'alert'
})

let resolvePromise: ((value: boolean) => void) | null = null

export function useDialog() {
  const showConfirm = (options: DialogOptions): Promise<boolean> => {
    dialogOptions.value = { ...options, type: 'confirm' }
    isVisible.value = true
    
    return new Promise((resolve) => {
      resolvePromise = resolve
    })
  }

  const showAlert = (options: DialogOptions): Promise<boolean> => {
    dialogOptions.value = { ...options, type: 'alert' }
    isVisible.value = true
    
    return new Promise((resolve) => {
      resolvePromise = resolve
    })
  }

  const showSuccess = (message: string, title?: string): Promise<boolean> => {
    return showAlert({ message, title, type: 'success' })
  }

  const showError = (message: string, title?: string): Promise<boolean> => {
    return showAlert({ message, title, type: 'error' })
  }

  const handleConfirm = () => {
    isVisible.value = false
    if (resolvePromise) {
      resolvePromise(true)
      resolvePromise = null
    }
  }

  const handleCancel = () => {
    isVisible.value = false
    if (resolvePromise) {
      resolvePromise(false)
      resolvePromise = null
    }
  }

  return {
    isVisible: readonly(isVisible),
    dialogOptions: readonly(dialogOptions),
    showConfirm,
    showAlert,
    showSuccess,
    showError,
    handleConfirm,
    handleCancel
  }
}
