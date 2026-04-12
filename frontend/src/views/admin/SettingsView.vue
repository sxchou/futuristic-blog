<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSiteConfigStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'
import LogoUpload from '@/components/common/LogoUpload.vue'

const siteConfigStore = useSiteConfigStore()
const { requireAdmin } = useAdminCheck()

const formData = ref({
  siteName: '',
  siteDescription: '',
  siteKeywords: '',
  mobileArticleLayout: 'embedded' as 'embedded' | 'stacked'
})

const isSaving = ref(false)
const saveMessage = ref('')

onMounted(async () => {
  await siteConfigStore.fetchConfigs()
  formData.value = {
    siteName: siteConfigStore.siteName,
    siteDescription: siteConfigStore.siteDescription,
    siteKeywords: siteConfigStore.siteKeywords,
    mobileArticleLayout: siteConfigStore.mobileArticleLayout
  }
})

const handleSave = async () => {
  if (!await requireAdmin('保存网站设置')) return
  
  isSaving.value = true
  saveMessage.value = ''
  
  try {
    await siteConfigStore.updateSiteName(formData.value.siteName)
    await siteConfigStore.updateSiteDescription(formData.value.siteDescription)
    await siteConfigStore.updateSiteKeywords(formData.value.siteKeywords)
    await siteConfigStore.updateMobileArticleLayout(formData.value.mobileArticleLayout)
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

const handleLogoUpload = () => {
  siteConfigStore.fetchConfigs(true)
}

const handleLogoReset = () => {
  siteConfigStore.fetchConfigs(true)
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
          <svg
            class="w-5 h-5 text-primary"
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
          网站设置
        </h1>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
                    class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-colors"
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
                    class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-colors resize-none"
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
                class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-colors"
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
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
              <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
                移动端设置
              </h2>
            </div>
          </div>
          <div class="p-4 sm:p-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                文章卡片布局方式
              </label>
              <div class="grid grid-cols-2 gap-3">
                <label class="relative flex cursor-pointer">
                  <input
                    v-model="formData.mobileArticleLayout"
                    type="radio"
                    value="embedded"
                    name="mobile-layout"
                    class="peer sr-only"
                  >
                  <div class="flex-1 p-3 bg-gray-50 dark:bg-dark-100 border-2 border-gray-200 dark:border-white/10 rounded-lg peer-checked:border-primary peer-checked:bg-primary/5 dark:peer-checked:bg-primary/10 transition-all">
                    <div class="flex items-center gap-2 mb-1">
                      <svg
                        class="w-4 h-4 text-gray-600 dark:text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z"
                        />
                      </svg>
                      <span class="text-sm font-medium text-gray-900 dark:text-white">嵌入式</span>
                    </div>
                    <p class="text-xs text-gray-500 dark:text-gray-400">
                      封面作为背景，文字叠加显示
                    </p>
                  </div>
                </label>
                <label class="relative flex cursor-pointer">
                  <input
                    v-model="formData.mobileArticleLayout"
                    type="radio"
                    value="stacked"
                    name="mobile-layout"
                    class="peer sr-only"
                  >
                  <div class="flex-1 p-3 bg-gray-50 dark:bg-dark-100 border-2 border-gray-200 dark:border-white/10 rounded-lg peer-checked:border-primary peer-checked:bg-primary/5 dark:peer-checked:bg-primary/10 transition-all">
                    <div class="flex items-center gap-2 mb-1">
                      <svg
                        class="w-4 h-4 text-gray-600 dark:text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1v-2z"
                        />
                      </svg>
                      <span class="text-sm font-medium text-gray-900 dark:text-white">上下布局</span>
                    </div>
                    <p class="text-xs text-gray-500 dark:text-gray-400">
                      封面上方，文字内容下方
                    </p>
                  </div>
                </label>
              </div>
            </div>
          </div>
        </div>

        <div class="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
          <button
            type="button"
            :disabled="isSaving"
            class="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-gradient-to-r from-primary to-accent text-white text-sm font-medium rounded-lg hover:opacity-90 transition-all disabled:opacity-50 shadow-lg shadow-primary/25"
            @click="handleSave"
          >
            <svg
              v-if="isSaving"
              class="w-4 h-4 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <svg
              v-else
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
            {{ isSaving ? '保存中...' : '保存设置' }}
          </button>
          
          <transition
            enter-active-class="transition ease-out duration-300"
            enter-from-class="opacity-0 translate-x-2"
            enter-to-class="opacity-100 translate-x-0"
            leave-active-class="transition ease-in duration-200"
            leave-from-class="opacity-100 translate-x-0"
            leave-to-class="opacity-0 translate-x-2"
          >
            <span
              v-if="saveMessage"
              :class="[
                'inline-flex items-center gap-1.5 text-sm font-medium',
                saveMessage.includes('成功') ? 'text-green-500' : 'text-red-500'
              ]"
            >
              <svg
                v-if="saveMessage.includes('成功')"
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <svg
                v-else
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              {{ saveMessage }}
            </span>
          </transition>
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
            <div class="p-3 sm:p-4 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-dark-200 dark:to-dark-300 rounded-lg border border-gray-200 dark:border-white/5">
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
            
            <div class="p-3 sm:p-4 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-dark-200 dark:to-dark-300 rounded-lg border border-gray-200 dark:border-white/5">
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
            
            <div class="p-3 sm:p-4 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-dark-200 dark:to-dark-300 rounded-lg border border-gray-200 dark:border-white/5">
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

            <div class="p-3 sm:p-4 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-dark-200 dark:to-dark-300 rounded-lg border border-gray-200 dark:border-white/5">
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
                    d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"
                  />
                </svg>
                移动端布局
              </p>
              <div class="flex items-center gap-2">
                <span
                  :class="[
                    'inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full',
                    formData.mobileArticleLayout === 'embedded' 
                      ? 'bg-primary/10 text-primary' 
                      : 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
                  ]"
                >
                  <svg
                    v-if="formData.mobileArticleLayout === 'embedded'"
                    class="w-3 h-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z"
                    />
                  </svg>
                  <svg
                    v-else
                    class="w-3 h-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1v-2z"
                    />
                  </svg>
                  {{ formData.mobileArticleLayout === 'embedded' ? '嵌入式' : '上下布局' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
