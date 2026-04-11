export function getMediaUrl(path: string | undefined | null): string {
  if (!path) return ''
  return path
}

export function getAvatarUrl(filename: string | undefined | null): string {
  if (!filename) return ''
  
  if (filename.startsWith('http://') || filename.startsWith('https://')) {
    return filename
  }
  
  if (filename.startsWith('/uploads/')) {
    return filename
  }
  
  return `/uploads/avatars/${filename}`
}
