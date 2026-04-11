export function getMediaUrl(path: string | undefined | null): string {
  if (!path) return ''
  
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  
  if (path.startsWith('/uploads/')) {
    const apiUrl = import.meta.env.VITE_API_URL || '/api/v1'
    const baseUrl = apiUrl.replace('/api/v1', '').replace(/\/$/, '')
    return `${baseUrl}${path}`
  }
  
  return path
}

export function getAvatarUrl(filename: string | undefined | null): string {
  if (!filename) return ''
  
  if (filename.startsWith('http://') || filename.startsWith('https://')) {
    return filename
  }
  
  const apiUrl = import.meta.env.VITE_API_URL || '/api/v1'
  const baseUrl = apiUrl.replace('/api/v1', '').replace(/\/$/, '')
  return `${baseUrl}/uploads/avatars/${filename}`
}
