import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const ACTIVITY_EVENTS = ['mousedown', 'keydown', 'touchstart', 'scroll']
const ACTIVITY_THROTTLE = 60000
const SESSION_CHECK_INTERVAL = 300000

export function useSessionManager() {
  const authStore = useAuthStore()
  const lastActivityTime = ref(Date.now())
  const isSessionActive = ref(true)
  
  let activityThrottleTimer: ReturnType<typeof setTimeout> | null = null
  let sessionCheckTimer: ReturnType<typeof setInterval> | null = null

  const updateActivity = () => {
    if (activityThrottleTimer) return
    
    activityThrottleTimer = setTimeout(() => {
      activityThrottleTimer = null
    }, ACTIVITY_THROTTLE)
    
    lastActivityTime.value = Date.now()
    isSessionActive.value = true
  }

  const checkSession = async () => {
    if (!authStore.isAuthenticated) return
    
    const timeSinceLastActivity = Date.now() - lastActivityTime.value
    const isInactive = timeSinceLastActivity > SESSION_CHECK_INTERVAL
    
    if (isInactive) {
      isSessionActive.value = false
      return
    }
    
    await authStore.checkAndRefreshToken()
  }

  const startSessionManagement = () => {
    ACTIVITY_EVENTS.forEach(event => {
      window.addEventListener(event, updateActivity, { passive: true })
    })
    
    sessionCheckTimer = setInterval(checkSession, SESSION_CHECK_INTERVAL)
  }

  const stopSessionManagement = () => {
    ACTIVITY_EVENTS.forEach(event => {
      window.removeEventListener(event, updateActivity)
    })
    
    if (activityThrottleTimer) {
      clearTimeout(activityThrottleTimer)
      activityThrottleTimer = null
    }
    
    if (sessionCheckTimer) {
      clearInterval(sessionCheckTimer)
      sessionCheckTimer = null
    }
  }

  const extendSession = async () => {
    if (!authStore.refreshToken) return false
    return await authStore.refreshAccessToken()
  }

  onMounted(() => {
    if (authStore.isAuthenticated) {
      startSessionManagement()
    }
  })

  onUnmounted(() => {
    stopSessionManagement()
  })

  return {
    lastActivityTime,
    isSessionActive,
    extendSession,
    startSessionManagement,
    stopSessionManagement
  }
}

export function useActivityTracker() {
  const authStore = useAuthStore()
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null
  const HEARTBEAT_INTERVAL = 600000

  const startHeartbeat = () => {
    if (heartbeatTimer) return
    
    heartbeatTimer = setInterval(async () => {
      if (authStore.isAuthenticated && authStore.refreshToken) {
        const tokenExpiry = localStorage.getItem('token_expiry')
        if (tokenExpiry) {
          const expiryTime = parseInt(tokenExpiry)
          const timeUntilExpiry = expiryTime - Date.now()
          
          if (timeUntilExpiry < 3600000) {
            await authStore.refreshAccessToken()
          }
        }
      }
    }, HEARTBEAT_INTERVAL)
  }

  const stopHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  onMounted(() => {
    if (authStore.isAuthenticated) {
      startHeartbeat()
    }
  })

  onUnmounted(() => {
    stopHeartbeat()
  })

  return {
    startHeartbeat,
    stopHeartbeat
  }
}
