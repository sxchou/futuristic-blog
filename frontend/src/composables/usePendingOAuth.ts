import { ref, watch } from 'vue'

const PENDING_OAUTH_KEY = 'pending_oauth_verification'

interface PendingOAuthState {
  tempToken: string
  username: string
  providerName: string
  email?: string
  timestamp: number
}

const pendingState = ref<PendingOAuthState | null>(null)

const loadFromStorage = () => {
  try {
    const stored = localStorage.getItem(PENDING_OAUTH_KEY)
    if (stored) {
      const parsed = JSON.parse(stored) as PendingOAuthState
      if (parsed.timestamp && Date.now() - parsed.timestamp < 24 * 60 * 60 * 1000) {
        pendingState.value = parsed
      } else {
        localStorage.removeItem(PENDING_OAUTH_KEY)
      }
    }
  } catch {
    localStorage.removeItem(PENDING_OAUTH_KEY)
  }
}

loadFromStorage()

watch(pendingState, (newState) => {
  if (newState) {
    localStorage.setItem(PENDING_OAUTH_KEY, JSON.stringify(newState))
  } else {
    localStorage.removeItem(PENDING_OAUTH_KEY)
  }
}, { deep: true })

export function usePendingOAuth() {
  const setPendingState = (tempToken: string, username: string, providerName: string, email?: string) => {
    pendingState.value = {
      tempToken,
      username,
      providerName,
      email,
      timestamp: Date.now()
    }
  }

  const clearPendingState = () => {
    pendingState.value = null
  }

  const getPendingState = () => {
    return pendingState.value
  }

  const hasPendingState = () => {
    return pendingState.value !== null
  }

  return {
    pendingState,
    setPendingState,
    clearPendingState,
    getPendingState,
    hasPendingState
  }
}
