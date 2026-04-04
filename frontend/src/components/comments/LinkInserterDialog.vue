<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { articleApi, fileApi } from '@/api'
import type { ArticleListItem, ArticleFile } from '@/types'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'insert', markdown: string): void
}>()

const activeTab = ref<'external' | 'article' | 'file'>('external')
const searchQuery = ref('')
const articles = ref<ArticleListItem[]>([])
const files = ref<ArticleFile[]>([])
const loading = ref(false)

const externalUrl = ref('')
const externalText = ref('')
const selectedArticle = ref<ArticleListItem | null>(null)
const selectedFile = ref<ArticleFile | null>(null)
const linkText = ref('')

const filteredArticles = computed(() => {
  if (!searchQuery.value) return articles.value
  const query = searchQuery.value.toLowerCase()
  return articles.value.filter(article => 
    article.title.toLowerCase().includes(query)
  )
})

const filteredFiles = computed(() => {
  let result = files.value.filter((file: ArticleFile) => file.article_id !== null)
  if (!searchQuery.value) return result
  const query = searchQuery.value.toLowerCase()
  return result.filter((file: ArticleFile) => 
    file.original_filename.toLowerCase().includes(query)
  )
})

const canInsert = computed(() => {
  if (activeTab.value === 'external') {
    return externalUrl.value.trim() !== ''
  } else if (activeTab.value === 'article') {
    return selectedArticle.value !== null
  } else if (activeTab.value === 'file') {
    return selectedFile.value !== null && selectedFile.value.article_id !== null
  }
  return false
})

const fetchArticles = async () => {
  loading.value = true
  try {
    const response = await articleApi.getArticles({ page: 1, page_size: 50 })
    articles.value = response.items
  } catch (error) {
    console.error('Failed to fetch articles:', error)
  } finally {
    loading.value = false
  }
}

const fetchFiles = async () => {
  loading.value = true
  try {
    files.value = await fileApi.getFiles()
  } catch (error) {
    console.error('Failed to fetch files:', error)
  } finally {
    loading.value = false
  }
}

const close = () => {
  emit('update:modelValue', false)
  resetForm()
}

const resetForm = () => {
  activeTab.value = 'external'
  externalUrl.value = ''
  externalText.value = ''
  selectedArticle.value = null
  selectedFile.value = null
  linkText.value = ''
  searchQuery.value = ''
}

const insertLink = () => {
  let markdown = ''
  
  if (activeTab.value === 'external') {
    if (!externalUrl.value.trim()) return
    let url = externalUrl.value.trim()
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url
    }
    const text = externalText.value.trim() || url
    markdown = `[${text}](${url})`
  } else if (activeTab.value === 'article' && selectedArticle.value) {
    const text = linkText.value.trim() || selectedArticle.value.title
    markdown = `[${text}](/article/${selectedArticle.value.slug})`
  } else if (activeTab.value === 'file' && selectedFile.value) {
    const text = linkText.value.trim() || selectedFile.value.original_filename
    const file = selectedFile.value
    if (file.article_id) {
      const article = articles.value.find(a => a.id === file.article_id)
      if (article) {
        markdown = `[${text}](/article/${article.slug}#file-${file.id})`
      } else {
        markdown = `[${text}](/article/${file.article_id}#file-${file.id})`
      }
    } else {
      return
    }
  }
  
  if (markdown) {
    emit('insert', markdown)
    close()
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    if (activeTab.value === 'article' && articles.value.length === 0) {
      fetchArticles()
    } else if (activeTab.value === 'file') {
      if (files.value.length === 0) {
        fetchFiles()
      }
      if (articles.value.length === 0) {
        fetchArticles()
      }
    }
  }
})

watch(activeTab, (newTab) => {
  if (newTab === 'article' && articles.value.length === 0) {
    fetchArticles()
  } else if (newTab === 'file') {
    if (files.value.length === 0) {
      fetchFiles()
    }
    if (articles.value.length === 0) {
      fetchArticles()
    }
  }
})
</script>

<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4"
    @click.self="close"
  >
    <div class="bg-white dark:bg-dark-100 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
      <div class="flex items-center justify-between p-3 border-b border-gray-200 dark:border-white/10 flex-shrink-0">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white">插入链接</h3>
        <button
          type="button"
          @click="close"
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div class="p-3 overflow-y-auto flex-1">
        <div class="flex gap-2 mb-3">
          <button
            v-for="tab in [
              { key: 'external', label: '外部链接' },
              { key: 'article', label: '文章链接' },
              { key: 'file', label: '文件链接' }
            ]"
            :key="tab.key"
            type="button"
            @click="activeTab = tab.key as any"
            :class="[
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              activeTab === tab.key
                ? 'bg-primary text-white'
                : 'bg-gray-100 dark:bg-dark-200 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-300'
            ]"
          >
            {{ tab.label }}
          </button>
        </div>
        
        <div v-if="activeTab === 'external'" class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              链接地址 <span class="text-red-500">*</span>
            </label>
            <input
              v-model="externalUrl"
              type="url"
              placeholder="https://example.com"
              class="input-cyber w-full text-sm"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              链接文本
            </label>
            <input
              v-model="externalText"
              type="text"
              placeholder="链接显示文本（可选）"
              class="input-cyber w-full text-sm"
            />
          </div>
        </div>
        
        <div v-else-if="activeTab === 'article'" class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              搜索文章
            </label>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="输入关键词搜索..."
              class="input-cyber w-full text-sm"
            />
          </div>
          
          <div v-if="loading" class="flex justify-center py-6">
            <div class="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
          
          <div v-else class="max-h-48 overflow-y-auto space-y-1.5">
            <button
              v-for="article in filteredArticles"
              :key="article.id"
              type="button"
              @click="selectedArticle = article"
              :class="[
                'w-full p-2 rounded-lg text-left transition-colors',
                selectedArticle?.id === article.id
                  ? 'bg-primary/10 border-2 border-primary'
                  : 'bg-gray-50 dark:bg-dark-200 hover:bg-gray-100 dark:hover:bg-dark-300 border-2 border-transparent'
              ]"
            >
              <div class="font-medium text-gray-900 dark:text-white text-sm">{{ article.title }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {{ article.category?.name || '未分类' }} · {{ article.view_count }} 次浏览
              </div>
            </button>
            
            <div v-if="filteredArticles.length === 0" class="text-center py-6 text-gray-500 dark:text-gray-400 text-sm">
              没有找到相关文章
            </div>
          </div>
          
          <div v-if="selectedArticle" class="mt-3">
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              链接文本
            </label>
            <input
              v-model="linkText"
              type="text"
              :placeholder="selectedArticle.title"
              class="input-cyber w-full text-sm"
            />
          </div>
        </div>
        
        <div v-else-if="activeTab === 'file'" class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              搜索文件
            </label>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="输入文件名搜索..."
              class="input-cyber w-full text-sm"
            />
          </div>
          
          <div v-if="loading" class="flex justify-center py-6">
            <div class="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
          
          <div v-else class="max-h-48 overflow-y-auto space-y-1.5">
            <button
              v-for="file in filteredFiles"
              :key="file.id"
              type="button"
              @click="selectedFile = file"
              :class="[
                'w-full p-2 rounded-lg text-left transition-colors',
                selectedFile?.id === file.id
                  ? 'bg-primary/10 border-2 border-primary'
                  : 'bg-gray-50 dark:bg-dark-200 hover:bg-gray-100 dark:hover:bg-dark-300 border-2 border-transparent'
              ]"
            >
              <div class="flex items-center gap-2">
                <svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                <div class="flex-1 min-w-0">
                  <div class="font-medium text-gray-900 dark:text-white truncate text-sm">{{ file.original_filename }}</div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    {{ file.file_type }} · {{ (file.file_size / 1024).toFixed(2) }} KB · {{ file.download_count }} 次下载
                  </div>
                </div>
              </div>
            </button>
            
            <div v-if="filteredFiles.length === 0" class="text-center py-6 text-gray-500 dark:text-gray-400 text-sm">
              没有找到相关文件
            </div>
          </div>
          
          <div v-if="selectedFile" class="mt-3">
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              链接文本
            </label>
            <input
              v-model="linkText"
              type="text"
              :placeholder="selectedFile.original_filename"
              class="input-cyber w-full text-sm"
            />
          </div>
        </div>
      </div>
      
      <div class="flex justify-end gap-2 p-3 border-t border-gray-200 dark:border-white/10 flex-shrink-0">
        <button
          type="button"
          @click="close"
          class="px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-dark-200 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-300 transition-colors"
        >
          取消
        </button>
        <button
          type="button"
          @click="insertLink"
          :disabled="!canInsert"
          :class="[
            'px-3 py-1.5 text-xs font-medium text-white rounded-lg transition-colors',
            canInsert
              ? 'bg-primary hover:bg-primary/90'
              : 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed'
          ]"
        >
          插入
        </button>
      </div>
    </div>
  </div>
</template>

