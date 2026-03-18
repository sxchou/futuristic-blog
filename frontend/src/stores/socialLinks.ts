import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { profileApi } from '@/api/profile'
import type { Profile } from '@/types'

export interface SocialLink {
  id: string
  name: string
  url: string
  icon: string
  color: string
  hoverColor: string
  type: 'link' | 'email'
}

let fetchProfilePromise: Promise<void> | null = null

export const useSocialLinksStore = defineStore('socialLinks', () => {
  const profile = ref<Profile | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastFetchTime = ref(0)
  const CACHE_TTL = 60000

  const socialLinks = computed<SocialLink[]>(() => {
    const links: SocialLink[] = []

    if (profile.value?.social_github) {
      links.push({
        id: 'github',
        name: 'GitHub',
        url: profile.value.social_github,
        icon: 'github',
        color: 'hover:text-gray-900 dark:hover:text-white',
        hoverColor: 'hover:border-gray-400 dark:hover:border-gray-500',
        type: 'link'
      })
    }

    if (profile.value?.social_email) {
      links.push({
        id: 'email',
        name: 'Email',
        url: `mailto:${profile.value.social_email}`,
        icon: 'email',
        color: 'hover:text-accent',
        hoverColor: 'hover:border-accent/50',
        type: 'email'
      })
    }

    if (profile.value?.social_blog) {
      links.push({
        id: 'blog',
        name: 'Blog',
        url: profile.value.social_blog,
        icon: 'blog',
        color: 'hover:text-cyber-green',
        hoverColor: 'hover:border-cyber-green/50',
        type: 'link'
      })
    }

    return links
  })

  const hasSocialLinks = computed(() => socialLinks.value.length > 0)

  const github = computed(() => profile.value?.social_github || '')
  const email = computed(() => profile.value?.social_email || '')
  const blog = computed(() => profile.value?.social_blog || '')

  const fetchProfile = async (force = false) => {
    if (!force && profile.value && Date.now() - lastFetchTime.value < CACHE_TTL) {
      return
    }
    
    if (fetchProfilePromise) {
      return fetchProfilePromise
    }
    
    fetchProfilePromise = (async () => {
      loading.value = true
      error.value = null
      
      try {
        profile.value = await profileApi.getProfile()
        lastFetchTime.value = Date.now()
      } catch (err) {
        console.error('Failed to fetch profile for social links:', err)
        error.value = 'Failed to load social links'
      } finally {
        loading.value = false
        fetchProfilePromise = null
      }
    })()
    
    return fetchProfilePromise
  }

  const refreshProfile = async () => {
    profile.value = null
    lastFetchTime.value = 0
    await fetchProfile(true)
  }

  return {
    profile,
    loading,
    error,
    socialLinks,
    hasSocialLinks,
    github,
    email,
    blog,
    fetchProfile,
    refreshProfile
  }
})
