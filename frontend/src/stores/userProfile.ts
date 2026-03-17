import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userProfileApi } from '@/api/userProfile'
import type { UserProfile } from '@/api/userProfile'

export const useUserProfileStore = defineStore('userProfile', () => {
  const profile = ref<UserProfile | null>(null)
  const loading = ref(false)
  const avatarUpdatedAt = ref<number>(Date.now())

  const fetchProfile = async () => {
    loading.value = true
    try {
      profile.value = await userProfileApi.getProfile()
    } catch (error) {
      console.error('Failed to fetch user profile:', error)
    } finally {
      loading.value = false
    }
  }

  const refreshProfile = async () => {
    try {
      profile.value = await userProfileApi.getProfile()
      avatarUpdatedAt.value = Date.now()
    } catch (error) {
      console.error('Failed to refresh user profile:', error)
    }
  }

  const clearProfile = () => {
    profile.value = null
  }

  const notifyAvatarUpdated = () => {
    avatarUpdatedAt.value = Date.now()
  }

  return {
    profile,
    loading,
    avatarUpdatedAt,
    fetchProfile,
    refreshProfile,
    clearProfile,
    notifyAvatarUpdated
  }
})
