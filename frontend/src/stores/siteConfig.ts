import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { siteConfigApi } from '@/api'
import type { SiteConfig } from '@/types'

export const useSiteConfigStore = defineStore('siteConfig', () => {
  const configs = ref<SiteConfig[]>([])
  const siteName = ref('Futuristic Blog')
  const siteDescription = ref('探索前沿技术，分享工程实践')
  const siteKeywords = ref('')
  const loading = ref(false)

  const siteLogo = computed(() => {
    return siteName.value.charAt(0).toUpperCase()
  })

  const fetchConfigs = async () => {
    loading.value = true
    try {
      configs.value = await siteConfigApi.getAll()
      
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
    } catch (error) {
      console.error('Failed to fetch site configs:', error)
    } finally {
      loading.value = false
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

  return {
    configs,
    siteName,
    siteDescription,
    siteKeywords,
    siteLogo,
    loading,
    fetchConfigs,
    updateSiteName,
    updateSiteDescription,
    updateSiteKeywords
  }
})
