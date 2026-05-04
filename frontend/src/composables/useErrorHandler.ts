import { ref, type Ref } from 'vue'
import { logger } from '@/utils/logger'

export interface AppError {
  message: string
  code?: string | number
  details?: any
  timestamp: Date
  handled: boolean
}

class ErrorHandler {
  private errors: AppError[] = []
  private maxErrors = 50
  private onErrorCallbacks: Array<(error: AppError) => void> = []

  addError(error: AppError): void {
    this.errors.unshift(error)
    if (this.errors.length > this.maxErrors) {
      this.errors.pop()
    }
    
    this.onErrorCallbacks.forEach(callback => callback(error))
  }

  onError(callback: (error: AppError) => void): () => void {
    this.onErrorCallbacks.push(callback)
    return () => {
      const index = this.onErrorCallbacks.indexOf(callback)
      if (index > -1) {
        this.onErrorCallbacks.splice(index, 1)
      }
    }
  }

  getErrors(): AppError[] {
    return [...this.errors]
  }

  clearErrors(): void {
    this.errors = []
  }

  markAsHandled(index: number): void {
    if (this.errors[index]) {
      this.errors[index].handled = true
    }
  }
}

const globalErrorHandler = new ErrorHandler()

export function useErrorHandler() {
  const lastError: Ref<AppError | null> = ref(null)
  const hasError = ref(false)

  const handleError = (error: unknown, context?: string): AppError => {
    const appError: AppError = {
      message: extractErrorMessage(error),
      code: extractErrorCode(error),
      details: error,
      timestamp: new Date(),
      handled: false
    }

    if (context) {
      logger.error(`${context}:`, appError.message)
    } else {
      logger.error('Error:', appError.message)
    }

    globalErrorHandler.addError(appError)
    lastError.value = appError
    hasError.value = true

    return appError
  }

  const handleAsyncError = async <T>(
    promise: Promise<T>,
    context?: string
  ): Promise<{ data: T | null; error: AppError | null }> => {
    try {
      const data = await promise
      return { data, error: null }
    } catch (error) {
      const appError = handleError(error, context)
      return { data: null, error: appError }
    }
  }

  const clearError = (): void => {
    lastError.value = null
    hasError.value = false
  }

  const getErrorMessage = (error: unknown): string => {
    return extractErrorMessage(error)
  }

  const isNetworkError = (error: unknown): boolean => {
    if (error instanceof Error) {
      return (
        error.message.includes('Network Error') ||
        error.message.includes('Failed to fetch') ||
        error.message.includes('NetworkError')
      )
    }
    return false
  }

  const isAuthError = (error: unknown): boolean => {
    if (error && typeof error === 'object' && 'response' in error) {
      const response = (error as any).response
      return response?.status === 401 || response?.status === 403
    }
    return false
  }

  const isValidationError = (error: unknown): boolean => {
    if (error && typeof error === 'object' && 'response' in error) {
      const response = (error as any).response
      return response?.status === 400 || response?.status === 422
    }
    return false
  }

  const getUserFriendlyMessage = (error: unknown): string => {
    if (isNetworkError(error)) {
      return '网络连接失败，请检查您的网络设置'
    }
    
    if (isAuthError(error)) {
      return '您的登录已过期，请重新登录'
    }
    
    if (isValidationError(error)) {
      return '提交的数据验证失败，请检查输入'
    }
    
    return extractErrorMessage(error) || '操作失败，请稍后重试'
  }

  return {
    lastError,
    hasError,
    handleError,
    handleAsyncError,
    clearError,
    getErrorMessage,
    isNetworkError,
    isAuthError,
    isValidationError,
    getUserFriendlyMessage
  }
}

function extractErrorMessage(error: unknown): string {
  if (!error) return '未知错误'
  
  if (typeof error === 'string') return error
  
  if (error instanceof Error) return error.message
  
  if (typeof error === 'object') {
    if ('response' in error) {
      const response = (error as any).response
      if (response?.data?.message) return response.data.message
      if (response?.data?.error) return response.data.error
      if (response?.data?.detail) return response.data.detail
    }
    
    if ('message' in error) return (error as any).message
    if ('error' in error) return (error as any).error
  }
  
  return '操作失败'
}

function extractErrorCode(error: unknown): string | number | undefined {
  if (!error || typeof error !== 'object') return undefined
  
  if ('response' in error) {
    const response = (error as any).response
    return response?.status || response?.data?.code
  }
  
  if ('code' in error) {
    return (error as any).code
  }
  
  return undefined
}

export { globalErrorHandler }

export default useErrorHandler
