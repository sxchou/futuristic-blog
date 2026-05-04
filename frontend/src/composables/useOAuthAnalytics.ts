const ANALYTICS_KEY = 'oauth_analytics'

interface AnalyticsEvent {
  event: string
  timestamp: number
  data?: Record<string, any>
}

interface OAuthAnalytics {
  events: AnalyticsEvent[]
  totalAttempts: number
  successfulVerifications: number
  resendCount: number
  changeEmailCount: number
}

const loadAnalytics = (): OAuthAnalytics => {
  try {
    const stored = localStorage.getItem(ANALYTICS_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch {}
  return {
    events: [],
    totalAttempts: 0,
    successfulVerifications: 0,
    resendCount: 0,
    changeEmailCount: 0
  }
}

const saveAnalytics = (analytics: OAuthAnalytics) => {
  try {
    localStorage.setItem(ANALYTICS_KEY, JSON.stringify(analytics))
  } catch {}
}

export function useOAuthAnalytics() {
  const trackEvent = (event: string, data?: Record<string, any>) => {
    const analytics = loadAnalytics()
    
    analytics.events.push({
      event,
      timestamp: Date.now(),
      data
    })
    
    if (analytics.events.length > 100) {
      analytics.events = analytics.events.slice(-100)
    }
    
    switch (event) {
      case 'oauth_login_attempt':
        analytics.totalAttempts++
        break
      case 'oauth_verification_complete':
        analytics.successfulVerifications++
        break
      case 'oauth_resend_verification':
        analytics.resendCount++
        break
      case 'oauth_change_email':
        analytics.changeEmailCount++
        break
    }
    
    saveAnalytics(analytics)
  }

  const getAnalytics = (): OAuthAnalytics => {
    return loadAnalytics()
  }

  const getCompletionRate = (): number => {
    const analytics = loadAnalytics()
    if (analytics.totalAttempts === 0) return 0
    return Math.round((analytics.successfulVerifications / analytics.totalAttempts) * 100)
  }

  const getResendRate = (): number => {
    const analytics = loadAnalytics()
    if (analytics.totalAttempts === 0) return 0
    return Math.round((analytics.resendCount / analytics.totalAttempts) * 100)
  }

  const getChangeEmailRate = (): number => {
    const analytics = loadAnalytics()
    if (analytics.totalAttempts === 0) return 0
    return Math.round((analytics.changeEmailCount / analytics.totalAttempts) * 100)
  }

  const clearAnalytics = () => {
    localStorage.removeItem(ANALYTICS_KEY)
  }

  return {
    trackEvent,
    getAnalytics,
    getCompletionRate,
    getResendRate,
    getChangeEmailRate,
    clearAnalytics
  }
}
