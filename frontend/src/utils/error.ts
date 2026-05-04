export const isCancelError = (error: unknown): boolean => {
  if (error instanceof Error && error.message === '请求已取消') {
    return true
  }
  if (typeof error === 'object' && error !== null && 'isCancel' in error) {
    return true
  }
  return false
}
