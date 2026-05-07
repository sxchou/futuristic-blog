<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useSiteConfigStore, useDialogStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'
import LogoUpload from '@/components/common/LogoUpload.vue'

const siteConfigStore = useSiteConfigStore()
const dialog = useDialogStore()
const { requirePermission, hasPermission } = useAdminCheck()

const canEdit = computed(() => hasPermission('settings.edit'))

const warnReadonly = (action: string) => {
  dialog.showWarning(`无${action}权限，请联系管理员`, '权限不足')
}

const formData = ref({
  siteName: '',
  siteDescription: '',
  siteKeywords: '',
  githubRepoUrl: '',
  showGithubStats: false
})

const isSaving = ref(false)

onMounted(async () => {
  await siteConfigStore.fetchConfigs()
  formData.value = {
    siteName: siteConfigStore.siteName,
    siteDescription: siteConfigStore.siteDescription,
    siteKeywords: siteConfigStore.siteKeywords,
    githubRepoUrl: siteConfigStore.githubRepoUrl,
    showGithubStats: siteConfigStore.showGithubStats
  }
})

const handleSave = async () => {
  if (!await requirePermission('settings.edit', '保存网站设置')) return
  
  isSaving.value = true
  
  try {
    await siteConfigStore.updateSiteName(formData.value.siteName)
    await siteConfigStore.updateSiteDescription(formData.value.siteDescription)
    await siteConfigStore.updateSiteKeywords(formData.value.siteKeywords)
    await siteConfigStore.updateGithubRepoUrl(formData.value.githubRepoUrl)
    await siteConfigStore.updateShowGithubStats(formData.value.showGithubStats)
    
    formData.value = {
      siteName: siteConfigStore.siteName,
      siteDescription: siteConfigStore.siteDescription,
      siteKeywords: siteConfigStore.siteKeywords,
      githubRepoUrl: siteConfigStore.githubRepoUrl,
      showGithubStats: siteConfigStore.showGithubStats
    }
    
    dialog.showSuccess('保存成功！')
  } catch (error: any) {
    await dialog.showError(error.message || '保存失败，请重试')
  } finally {
    isSaving.value = false
  }
}

const handleLogoUpload = () => {
  siteConfigStore.fetchConfigs(true)
}

const handleLogoReset = () => {
  siteConfigStore.fetchConfigs(true)
}
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
          <svg
            class="w-4 h-4 text-primary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          系统设置
        </h1>
      </div>
    </div>

    <form class="grid grid-cols-1 lg:grid-cols-3 gap-6" @submit.prevent="handleSave">
      <div class="lg:col-span-2 space-y-4 sm:space-y-6">
        <div class="bg-white dark:bg-dark-100 rounded-xl border border-gray-200 dark:border-white/10 overflow-hidden">
          <div class="px-4 py-3 sm:px-6 sm:py-4 border-b border-gray-100 dark:border-white/5 bg-gray-50/50 dark:bg-white/[0.02]">
            <div class="flex items-center gap-2">
              <svg
                class="w-4 h-4 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
                网站标识
              </h2>
            </div>
          </div>
          <div class="p-4 sm:p-6">
            <div class="flex flex-col gap-6">
              <div class="flex justify-center sm:justify-start">
                <LogoUpload
                  size="md"
                  @upload="handleLogoUpload"
                  @reset="handleLogoReset"
                />
              </div>
              <div class="space-y-4">
                <div>
                  <label
                    for="settings-site-name"
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
                  >
                    网站名称
                  </label>
                  <input
                    id="settings-site-name"
                    v-model="formData.siteName"
                    type="text"
                    name="site-name"
                    :disabled="!canEdit"
                    class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    placeholder="请输入网站名称"
                  >
                </div>
                <div>
                  <label
                    for="settings-site-description"
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
                  >
                    网站描述
                  </label>
                  <textarea
                    id="settings-site-description"
                    v-model="formData.siteDescription"
                    name="site-description"
                    rows="2"
                    :disabled="!canEdit"
                    class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-colors resize-none disabled:opacity-50 disabled:cursor-not-allowed"
                    placeholder="请输入网站描述"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-dark-100 rounded-xl border border-gray-200 dark:border-white/10 overflow-hidden">
          <div class="px-4 py-3 sm:px-6 sm:py-4 border-b border-gray-100 dark:border-white/5 bg-gray-50/50 dark:bg-white/[0.02]">
            <div class="flex items-center gap-2">
              <svg
                class="w-4 h-4 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                />
              </svg>
              <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
                SEO 设置
              </h2>
            </div>
          </div>
          <div class="p-4 sm:p-6">
            <div>
              <label
                for="settings-site-keywords"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >
                网站关键词
              </label>
              <input
                id="settings-site-keywords"
                v-model="formData.siteKeywords"
                type="text"
                name="site-keywords"
                :disabled="!canEdit"
                class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="请输入网站关键词，用逗号分隔"
              >
              <p class="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
                多个关键词请用英文逗号分隔，用于搜索引擎优化
              </p>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-dark-100 rounded-xl border border-gray-200 dark:border-white/10 overflow-hidden">
          <div class="px-4 py-3 sm:px-6 sm:py-4 border-b border-gray-100 dark:border-white/5 bg-gray-50/50 dark:bg-white/[0.02]">
            <div class="flex items-center gap-2">
              <svg
                class="w-4 h-4 text-primary"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
                GitHub 设置
              </h2>
            </div>
          </div>
          <div class="p-4 sm:p-6 space-y-4">
            <div>
              <label
                for="settings-github-repo-url"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >
                GitHub 仓库地址
              </label>
              <input
                id="settings-github-repo-url"
                v-model="formData.githubRepoUrl"
                type="text"
                name="github-repo-url"
                :disabled="!canEdit"
                class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="例如: https://github.com/username/repo"
              >
              <p class="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
                填写 GitHub 仓库完整地址，用于在侧边栏显示仓库统计信息
              </p>
            </div>
            
            <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-dark-200 rounded-lg border border-gray-200 dark:border-white/5">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
                  <svg
                    class="w-4 h-4 text-primary"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                    />
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-900 dark:text-white">
                    在侧边栏显示 GitHub 信息
                  </p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">
                    开启后将在左侧侧边栏显示仓库的 Stars、Forks 等统计信息
                  </p>
                </div>
              </div>
              <button
                type="button"
                role="switch"
                :aria-checked="formData.showGithubStats"
                :class="[
                  'relative inline-flex h-6 w-11 flex-shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
                  'cursor-pointer',
                  formData.showGithubStats ? 'bg-primary' : 'bg-gray-200 dark:bg-dark-400'
                ]"
                @click="canEdit ? (formData.showGithubStats = !formData.showGithubStats) : warnReadonly('修改系统设置')"
              >
                <span
                  :class="[
                    'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                    formData.showGithubStats ? 'translate-x-5' : 'translate-x-0'
                  ]"
                />
              </button>
            </div>
          </div>
        </div>

        <div class="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
          <button
            type="button"
            :disabled="isSaving"
            :class="['btn-primary text-sm px-4 py-1.5', canEdit && !isSaving ? '' : 'opacity-50 cursor-not-allowed']"
            @click="canEdit ? handleSave() : warnReadonly('保存系统设置')"
          >
            <span v-if="isSaving" class="flex items-center gap-2">
              <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              保存中...
            </span>
            <span v-else>保存设置</span>
          </button>
        </div>
      </div>

      <div class="lg:col-span-1">
        <div class="bg-white dark:bg-dark-100 rounded-xl border border-gray-200 dark:border-white/10 overflow-hidden lg:sticky lg:top-6">
          <div class="px-4 py-3 sm:px-6 sm:py-4 border-b border-gray-100 dark:border-white/5 bg-gray-50/50 dark:bg-white/[0.02]">
            <div class="flex items-center gap-2">
              <svg
                class="w-4 h-4 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
              <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
                实时预览
              </h2>
            </div>
          </div>
          <div class="p-4 sm:p-6 space-y-3 sm:space-y-4">
            <div class="p-3 sm:p-4 bg-gray-50 dark:bg-dark-200 rounded-lg border border-gray-200 dark:border-white/5">
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-1 flex items-center gap-1">
                <svg
                  class="w-3 h-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                  />
                </svg>
                网站名称
              </p>
              <p class="text-base sm:text-lg font-bold gradient-text">
                {{ formData.siteName || 'Futuristic Blog' }}
              </p>
            </div>
            
            <div class="p-3 sm:p-4 bg-gray-50 dark:bg-dark-200 rounded-lg border border-gray-200 dark:border-white/5">
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-1 flex items-center gap-1">
                <svg
                  class="w-3 h-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                网站描述
              </p>
              <p class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                {{ formData.siteDescription || '暂无描述' }}
              </p>
            </div>
            
            <div class="p-3 sm:p-4 bg-gray-50 dark:bg-dark-200 rounded-lg border border-gray-200 dark:border-white/5">
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-2 flex items-center gap-1">
                <svg
                  class="w-3 h-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                  />
                </svg>
                网站关键词
              </p>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="(keyword, index) in formData.siteKeywords.split(',').filter(k => k.trim())"
                  :key="index"
                  class="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full"
                >
                  {{ keyword.trim() }}
                </span>
                <span
                  v-if="!formData.siteKeywords"
                  class="text-gray-400 text-xs"
                >
                  暂无关键词
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>
