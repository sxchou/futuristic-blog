<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSiteConfigStore } from '@/stores'

const siteConfigStore = useSiteConfigStore()

const formData = ref({
  siteName: '',
  siteDescription: '',
  siteKeywords: ''
})

const isSaving = ref(false)
const saveMessage = ref('')

onMounted(async () => {
  await siteConfigStore.fetchConfigs()
  formData.value = {
    siteName: siteConfigStore.siteName,
    siteDescription: siteConfigStore.siteDescription,
    siteKeywords: siteConfigStore.siteKeywords
  }
})

const handleSave = async () => {
  isSaving.value = true
  saveMessage.value = ''
  
  try {
    await siteConfigStore.updateSiteName(formData.value.siteName)
    await siteConfigStore.updateSiteDescription(formData.value.siteDescription)
    await siteConfigStore.updateSiteKeywords(formData.value.siteKeywords)
    saveMessage.value = '保存成功！'
    setTimeout(() => {
      saveMessage.value = ''
    }, 3000)
  } catch (error: any) {
    saveMessage.value = error.message || '保存失败，请重试'
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">网站设置</h1>
    </div>

    <div class="bg-white dark:bg-dark-100 rounded-xl border border-gray-200 dark:border-white/10 p-6">
      <form @submit.prevent="handleSave" class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            网站名称
          </label>
          <input
            v-model="formData.siteName"
            type="text"
            class="w-full px-4 py-2 bg-gray-50 dark:bg-dark-200 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none transition-colors"
            placeholder="请输入网站名称"
          />
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            网站名称将显示在浏览器标签页和导航栏
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            网站描述
          </label>
          <textarea
            v-model="formData.siteDescription"
            rows="3"
            class="w-full px-4 py-2 bg-gray-50 dark:bg-dark-200 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none transition-colors resize-none"
            placeholder="请输入网站描述"
          />
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            网站描述将用于 SEO 优化和社交媒体分享
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            网站关键词
          </label>
          <input
            v-model="formData.siteKeywords"
            type="text"
            class="w-full px-4 py-2 bg-gray-50 dark:bg-dark-200 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none transition-colors"
            placeholder="请输入网站关键词，用逗号分隔"
          />
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            关键词用于 SEO 优化，多个关键词请用英文逗号分隔
          </p>
        </div>

        <div class="flex items-center gap-4">
          <button
            type="submit"
            :disabled="isSaving"
            class="px-6 py-2 bg-gradient-to-r from-primary to-accent text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {{ isSaving ? '保存中...' : '保存设置' }}
          </button>
          
          <span
            v-if="saveMessage"
            :class="[
              'text-sm',
              saveMessage.includes('成功') ? 'text-green-500' : 'text-red-500'
            ]"
          >
            {{ saveMessage }}
          </span>
        </div>
      </form>
    </div>

    <div class="bg-white dark:bg-dark-100 rounded-xl border border-gray-200 dark:border-white/10 p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">预览效果</h2>
      
      <div class="space-y-4">
        <div class="p-4 bg-gray-50 dark:bg-dark-200 rounded-lg">
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">网站名称</p>
          <p class="text-xl font-bold gradient-text">{{ formData.siteName || 'Futuristic Blog' }}</p>
        </div>
        
        <div class="p-4 bg-gray-50 dark:bg-dark-200 rounded-lg">
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">网站描述</p>
          <p class="text-gray-700 dark:text-gray-300">{{ formData.siteDescription || '暂无描述' }}</p>
        </div>
        
        <div class="p-4 bg-gray-50 dark:bg-dark-200 rounded-lg">
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">网站关键词</p>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="(keyword, index) in formData.siteKeywords.split(',').filter(k => k.trim())"
              :key="index"
              class="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full"
            >
              {{ keyword.trim() }}
            </span>
            <span
              v-if="!formData.siteKeywords"
              class="text-gray-400 text-sm"
            >
              暂无关键词
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
