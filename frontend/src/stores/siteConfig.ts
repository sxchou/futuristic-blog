import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { siteConfigApi } from '@/api'
import type { SiteConfig } from '@/types'

export interface GitHubStats {
  enabled: boolean
  stars: number
  forks: number
  watchers: number
  open_issues: number
  full_name?: string
  html_url?: string
}

let fetchConfigsPromise: Promise<void> | null = null

const updateFavicon = (logoUrl: string) => {
  let favicon = document.querySelector('link[rel="icon"]') as HTMLLinkElement
  
  if (!logoUrl) {
    if (favicon) {
      favicon.href = '/favicon.svg'
    }
    return
  }
  
  let fullUrl = logoUrl
  if (!logoUrl.startsWith('http')) {
    fullUrl = logoUrl.startsWith('/') ? logoUrl : `/${logoUrl}`
  }
  
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    const size = 64
    const canvas = document.createElement('canvas')
    canvas.width = size
    canvas.height = size
    const ctx = canvas.getContext('2d')
    
    if (ctx) {
      ctx.beginPath()
      ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2)
      ctx.closePath()
      ctx.clip()
      
      const minDim = Math.min(img.width, img.height)
      const sx = (img.width - minDim) / 2
      const sy = (img.height - minDim) / 2
      ctx.drawImage(img, sx, sy, minDim, minDim, 0, 0, size, size)
      
      if (!favicon) {
        favicon = document.createElement('link')
        favicon.rel = 'icon'
        document.head.appendChild(favicon)
      }
      favicon.href = canvas.toDataURL('image/png')
      
      let appleTouchIcon = document.querySelector('link[rel="apple-touch-icon"]') as HTMLLinkElement
      if (!appleTouchIcon) {
        appleTouchIcon = document.createElement('link')
        appleTouchIcon.rel = 'apple-touch-icon'
        document.head.appendChild(appleTouchIcon)
      }
      appleTouchIcon.href = canvas.toDataURL('image/png')
    }
  }
  img.onerror = () => {
    if (!favicon) {
      favicon = document.createElement('link')
      favicon.rel = 'icon'
      document.head.appendChild(favicon)
    }
    favicon.href = fullUrl
  }
  img.src = fullUrl
}

export const useSiteConfigStore = defineStore('siteConfig', () => {
  const configs = ref<SiteConfig[]>([])
  const siteName = ref('Futuristic Blog')
  const siteDescription = ref('探索前沿技术，分享工程实践')
  const siteKeywords = ref('')
  const siteLogoUrl = ref('')
  const githubRepoUrl = ref('')
  const showGithubStats = ref(false)
  const githubStats = ref<GitHubStats | null>(null)
  const githubStatsLastFetch = ref(0)
  const GITHUB_STATS_TTL = 30000
  const loading = ref(false)
  const lastFetchTime = ref(0)
  const CACHE_TTL = 600000

  const siteLogo = computed(() => {
    return siteName.value.charAt(0).toUpperCase()
  })

  watch(siteLogoUrl, (newUrl) => {
    updateFavicon(newUrl)
  }, { immediate: true })

  watch(siteName, (newName) => {
    document.title = newName
  })

  const fetchConfigs = async (force = false) => {
    if (!force && configs.value.length > 0 && Date.now() - lastFetchTime.value < CACHE_TTL) {
      return
    }
    
    if (fetchConfigsPromise) {
      return fetchConfigsPromise
    }
    
    fetchConfigsPromise = (async () => {
      loading.value = true
      try {
        configs.value = await siteConfigApi.getAll()
        lastFetchTime.value = Date.now()
        
        const nameConfig = configs.value.find(c => c.key === 'site_name')
        if (nameConfig?.value) {
          siteName.value = nameConfig.value
        }
        
        const descConfig = configs.value.find(c => c.key === 'site_description')
        if (descConfig?.value) {
          siteDescription.value = descConfig.value
        }
        
        const keywordsConfig = configs.value.find(c => c.key === 'site_keywords')
        if (keywordsConfig?.value) {
          siteKeywords.value = keywordsConfig.value
        }
        
        const logoConfig = configs.value.find(c => c.key === 'site_logo')
        if (logoConfig?.value) {
          siteLogoUrl.value = logoConfig.value
          updateFavicon(logoConfig.value)
        }
        
        const githubRepoConfig = configs.value.find(c => c.key === 'github_repo_url')
        if (githubRepoConfig?.value) {
          githubRepoUrl.value = githubRepoConfig.value
        }
        
        const showGithubConfig = configs.value.find(c => c.key === 'show_github_stats')
        if (showGithubConfig?.value) {
          showGithubStats.value = showGithubConfig.value === 'true'
        }
      } catch (error) {
        console.error('Failed to fetch site configs:', error)
      } finally {
        loading.value = false
        fetchConfigsPromise = null
      }
    })()
    
    return fetchConfigsPromise
  }

  const setConfigs = (configList: SiteConfig[]) => {
    configs.value = configList
    lastFetchTime.value = Date.now()
    
    const nameConfig = configList.find(c => c.key === 'site_name')
    if (nameConfig?.value) {
      siteName.value = nameConfig.value
    }
    
    const descConfig = configList.find(c => c.key === 'site_description')
    if (descConfig?.value) {
      siteDescription.value = descConfig.value
    }
    
    const keywordsConfig = configList.find(c => c.key === 'site_keywords')
    if (keywordsConfig?.value) {
      siteKeywords.value = keywordsConfig.value
    }
    
    const logoConfig = configList.find(c => c.key === 'site_logo')
    if (logoConfig?.value) {
      siteLogoUrl.value = logoConfig.value
      updateFavicon(logoConfig.value)
    }
    
    const githubRepoConfig = configList.find(c => c.key === 'github_repo_url')
    if (githubRepoConfig?.value) {
      githubRepoUrl.value = githubRepoConfig.value
    }
    
    const showGithubConfig = configList.find(c => c.key === 'show_github_stats')
    if (showGithubConfig?.value) {
      showGithubStats.value = showGithubConfig.value === 'true'
    }
  }

  const fetchGithubStats = async (force = false) => {
    const now = Date.now()
    if (!force) {
      if (githubStats.value?.enabled === true && githubStats.value?.stars && githubStats.value.stars > 0) return
      if (githubStatsLastFetch.value > 0 && now - githubStatsLastFetch.value < GITHUB_STATS_TTL) return
    }
    
    if (!githubRepoUrl.value) {
      githubStats.value = { enabled: false, stars: 0, forks: 0, watchers: 0, open_issues: 0 }
      return
    }
    
    try {
      githubStatsLastFetch.value = now
      githubStats.value = await siteConfigApi.getGitHubStats()
    } catch (error) {
      console.error('Failed to fetch GitHub stats:', error)
      githubStats.value = { enabled: false, stars: 0, forks: 0, watchers: 0, open_issues: 0 }
    }
  }

  const updateSiteName = async (name: string) => {
    try {
      await siteConfigApi.update('site_name', name, '网站名称')
      siteName.value = name
      document.title = name
    } catch (error: any) {
      console.error('Failed to update site name:', error)
      if (error.response?.status === 403) {
        throw new Error('无权限修改网站设置')
      }
      throw error
    }
  }

  const updateSiteDescription = async (description: string) => {
    try {
      await siteConfigApi.update('site_description', description, '网站描述')
      siteDescription.value = description
    } catch (error: any) {
      console.error('Failed to update site description:', error)
      if (error.response?.status === 403) {
        throw new Error('无权限修改网站设置')
      }
      throw error
    }
  }

  const updateSiteKeywords = async (keywords: string) => {
    try {
      await siteConfigApi.update('site_keywords', keywords, '网站关键词')
      siteKeywords.value = keywords
    } catch (error: any) {
      console.error('Failed to update site keywords:', error)
      if (error.response?.status === 403) {
        throw new Error('无权限修改网站设置')
      }
      throw error
    }
  }

  const updateSiteLogo = async (formData: FormData) => {
    try {
      const config = await siteConfigApi.uploadLogo(formData)
      siteLogoUrl.value = config.value || ''
      updateFavicon(config.value || '')
      return config
    } catch (error: any) {
      console.error('Failed to upload site logo:', error)
      if (error.response?.status === 403) {
        throw new Error('无权限上传网站Logo')
      }
      throw error
    }
  }

  const resetSiteLogo = async () => {
    try {
      const config = await siteConfigApi.resetLogo()
      siteLogoUrl.value = ''
      updateFavicon('')
      return config
    } catch (error: any) {
      console.error('Failed to reset site logo:', error)
      if (error.response?.status === 403) {
        throw new Error('无权限重置网站Logo')
      }
      throw error
    }
  }

  const updateGithubRepoUrl = async (url: string) => {
    try {
      await siteConfigApi.update('github_repo_url', url, 'GitHub仓库地址')
      githubRepoUrl.value = url
    } catch (error: any) {
      console.error('Failed to update github repo url:', error)
      if (error.response?.status === 403) {
        throw new Error('无权限修改网站设置')
      }
      throw error
    }
  }

  const updateShowGithubStats = async (show: boolean) => {
    try {
      await siteConfigApi.update('show_github_stats', show ? 'true' : 'false', '是否显示GitHub统计信息')
      showGithubStats.value = show
    } catch (error: any) {
      console.error('Failed to update show github stats:', error)
      if (error.response?.status === 403) {
        throw new Error('无权限修改网站设置')
      }
      throw error
    }
  }

  const setGithubStats = (stats: GitHubStats | null) => {
    githubStats.value = stats
    if (stats) {
      githubStatsLastFetch.value = Date.now()
    }
  }

  return {
    configs,
    siteName,
    siteDescription,
    siteKeywords,
    siteLogoUrl,
    siteLogo,
    githubRepoUrl,
    showGithubStats,
    githubStats,
    loading,
    fetchConfigs,
    fetchGithubStats,
    updateSiteName,
    updateSiteDescription,
    updateSiteKeywords,
    updateSiteLogo,
    resetSiteLogo,
    updateGithubRepoUrl,
    updateShowGithubStats,
    setConfigs,
    setGithubStats
  }
})
