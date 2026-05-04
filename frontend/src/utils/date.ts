export const formatDate = (date: string | null | undefined, includeTime: boolean = true): string => {
  if (!date) return '-'
  
  const options: Intl.DateTimeFormatOptions = {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour12: false
  }
  
  if (includeTime) {
    options.hour = '2-digit'
    options.minute = '2-digit'
    options.second = '2-digit'
  }
  
  const formatted = new Date(date).toLocaleString('zh-CN', options)
  return formatted.replace(/\//g, '-').replace(/,/g, '')
}

export const formatDateShort = (date: string | null | undefined): string => {
  return formatDate(date, false)
}

export const formatDateTime = (date: string | null | undefined): string => {
  return formatDate(date, true)
}
