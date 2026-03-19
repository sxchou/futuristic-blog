<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useBlogStore, useDialogStore } from '@/stores'
import { articleApi, fileApi } from '@/api'
import type { ArticleListItem } from '@/types'

interface ArticleFile {
  id: number
  filename: string
  original_filename: string
  file_size: number
  file_type: string
  mime_type: string
  is_image: boolean
  download_count: number
  created_at: string
}

const blogStore = useBlogStore()
const dialog = useDialogStore()

const articles = ref<ArticleListItem[]>([])
const isLoading = ref(false)
const showEditor = ref(false)
const editingArticle = ref<ArticleListItem | null>(null)
const articleFiles = ref<ArticleFile[]>([])
const isUploading = ref(false)
const uploadProgress = ref(0)

const form = ref({
  title: '',
  slug: '',
  summary: '',
  content: '',
  category_id: undefined as number | undefined,
  tag_ids: [] as number[],
  is_published: false,
  is_featured: false,
  is_pinned: false
})

const fetchArticles = async () => {
  isLoading.value = true
  try {
    const response = await articleApi.getAdminArticles({ page: 1, page_size: 100 })
    articles.value = response.items
  } catch (error) {
    console.error('Failed to fetch articles:', error)
  } finally {
    isLoading.value = false
  }
}

const fetchArticleFiles = async (articleId: number) => {
  try {
    const files = await fileApi.getFiles(articleId)
    articleFiles.value = files
  } catch (error) {
    console.error('Failed to fetch article files:', error)
    articleFiles.value = []
  }
}

const handleEdit = async (article: ArticleListItem) => {
  editingArticle.value = article
  
  try {
    const fullArticle = await articleApi.getAdminArticle(article.slug)
    form.value = {
      title: fullArticle.title,
      slug: fullArticle.slug,
      summary: fullArticle.summary || '',
      content: fullArticle.content || '',
      category_id: fullArticle.category?.id || undefined,
      tag_ids: fullArticle.tags.map(t => t.id),
      is_published: fullArticle.is_published,
      is_featured: fullArticle.is_featured,
      is_pinned: fullArticle.is_pinned || false
    }
    await fetchArticleFiles(article.id)
    showEditor.value = true
  } catch (error) {
    console.error('Failed to fetch article:', error)
    await dialog.showError('获取文章详情失败', '错误')
  }
}

const handleDelete = async (article: ArticleListItem) => {
  const confirmed = await dialog.showConfirm({
    title: '确认删除',
    message: `确定要删除文章"${article.title}"吗？`
  })
  if (!confirmed) return
  
  try {
    await articleApi.deleteArticle(article.id)
    await fetchArticles()
    await dialog.showSuccess('文章已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete article:', error)
    if (error.response?.status === 403) {
      await dialog.showError('无权限删除此文章', '权限不足')
    } else {
      await dialog.showError(error.response?.data?.detail || '删除失败', '错误')
    }
  }
}

const handleSubmit = async () => {
  try {
    if (editingArticle.value) {
      await articleApi.updateArticle(editingArticle.value.id, form.value)
    } else {
      await articleApi.createArticle(form.value)
    }
    showEditor.value = false
    editingArticle.value = null
    resetForm()
    await fetchArticles()
  } catch (error: any) {
    console.error('Failed to save article:', error)
    if (error.response?.status === 403) {
      await dialog.showError('无权限修改此文章', '权限不足')
    } else {
      await dialog.showError(error.response?.data?.detail || '保存失败', '错误')
    }
  }
}

const resetForm = () => {
  form.value = {
    title: '',
    slug: '',
    summary: '',
    content: '',
    category_id: undefined,
    tag_ids: [],
    is_published: false,
    is_featured: false,
    is_pinned: false
  }
  articleFiles.value = []
}

const generateSlug = () => {
  form.value.slug = form.value.title
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
    .replace(/^-|-$/g, '')
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const handleFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files || files.length === 0) return
  
  if (!editingArticle.value) {
    await dialog.showError('请先保存文章后再上传文件', '提示')
    return
  }
  
  isUploading.value = true
  uploadProgress.value = 0
  
  try {
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      uploadProgress.value = ((i + 1) / files.length) * 100
      await fileApi.uploadFile(file, editingArticle.value.id)
    }
    await fetchArticleFiles(editingArticle.value.id)
    await dialog.showSuccess('文件上传成功', '成功')
  } catch (error: any) {
    console.error('Failed to upload file:', error)
    await dialog.showError(error.response?.data?.detail || '文件上传失败', '错误')
  } finally {
    isUploading.value = false
    uploadProgress.value = 0
    target.value = ''
  }
}

const handleImageUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  isUploading.value = true
  
  try {
    const response = await fileApi.uploadImage(file)
    const imageUrl = `/uploads/images/${response.filename}`
    const markdown = `![${file.name}](${imageUrl})`
    
    const textarea = document.querySelector('textarea[name="content"]') as HTMLTextAreaElement
    if (textarea) {
      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const text = form.value.content
      form.value.content = text.substring(0, start) + markdown + text.substring(end)
      
      setTimeout(() => {
        textarea.focus()
        textarea.selectionStart = textarea.selectionEnd = start + markdown.length
      }, 0)
    } else {
      form.value.content += `\n${markdown}\n`
    }
  } catch (error: any) {
    console.error('Failed to upload image:', error)
    await dialog.showError(error.response?.data?.detail || '图片上传失败', '错误')
  } finally {
    isUploading.value = false
    target.value = ''
  }
}

const handleDeleteFile = async (fileId: number) => {
  const confirmed = await dialog.showConfirm({
    title: '确认删除',
    message: '确定要删除此文件吗？'
  })
  if (!confirmed) return
  
  try {
    await fileApi.deleteFile(fileId)
    if (editingArticle.value) {
      await fetchArticleFiles(editingArticle.value.id)
    }
    await dialog.showSuccess('文件已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete file:', error)
    await dialog.showError(error.response?.data?.detail || '删除失败', '错误')
  }
}

const getFileIcon = (fileType: string, mimeType: string): string => {
  if (fileType === 'image') return '🖼️'
  if (mimeType.includes('pdf')) return '📄'
  if (mimeType.includes('word') || mimeType.includes('document')) return '📝'
  if (mimeType.includes('excel') || mimeType.includes('sheet')) return '📊'
  if (mimeType.includes('zip') || mimeType.includes('rar') || mimeType.includes('7z')) return '📦'
  return '📎'
}

onMounted(() => {
  fetchArticles()
  blogStore.fetchCategories()
  blogStore.fetchTags()
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold text-gray-900 dark:text-white">文章管理</h1>
      <button
        @click="showEditor = true; editingArticle = null; resetForm()"
        class="btn-primary text-sm px-4 py-1.5"
      >
        新建文章
      </button>
    </div>

    <div v-if="isLoading" class="flex justify-center py-16">
      <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <div v-else class="glass-card overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-100 dark:bg-dark-100">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">标题</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">分类</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">状态</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">浏览</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">创建时间</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-white/5">
          <tr v-for="article in articles" :key="article.id" class="hover:bg-gray-50 dark:hover:bg-white/5">
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <span v-if="article.is_pinned" class="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-600 dark:text-amber-400 rounded border border-amber-500/30">
                  <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/>
                  </svg>
                  置顶
                </span>
                <span v-if="article.is_featured" class="px-2 py-0.5 text-xs font-medium bg-gradient-to-r from-primary to-accent text-white rounded-full">精选</span>
                <span class="text-gray-900 dark:text-white">{{ article.title }}</span>
              </div>
            </td>
            <td class="px-4 py-3">
              <span v-if="article.category" :style="{ color: article.category.color }">
                {{ article.category.name }}
              </span>
              <span v-else class="text-gray-500">未分类</span>
            </td>
            <td class="px-4 py-3">
              <span
                v-if="article.is_published"
                class="px-1.5 py-0.5 text-xs rounded bg-green-500/20 text-green-400"
              >
                已发布
              </span>
              <span
                v-else
                class="px-1.5 py-0.5 text-xs rounded bg-yellow-500/20 text-yellow-400"
              >
                未发布
              </span>
            </td>
            <td class="px-4 py-3 text-gray-400">{{ article.view_count }}</td>
            <td class="px-4 py-3 text-gray-400">
              {{ new Date(article.created_at).toLocaleDateString('zh-CN') }}
            </td>
            <td class="px-4 py-3 text-right">
              <button
                @click="handleEdit(article)"
                class="text-primary hover:text-primary/80 mr-3 text-sm"
              >
                编辑
              </button>
              <button
                @click="handleDelete(article)"
                class="text-red-400 hover:text-red-300 text-sm"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-if="showEditor"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    >
      <div class="glass-card w-full max-w-3xl max-h-[90vh] overflow-y-auto m-4 p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-bold text-gray-900 dark:text-white">
            {{ editingArticle ? '编辑文章' : '新建文章' }}
          </h2>
          <button
            @click="showEditor = false"
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">标题</label>
              <input
                v-model="form.title"
                type="text"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
                placeholder="请输入文章标题"
                @blur="generateSlug"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">Slug</label>
              <input
                v-model="form.slug"
                type="text"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
                placeholder="url-slug"
              />
            </div>
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">摘要</label>
            <textarea
              v-model="form.summary"
              rows="2"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="请输入文章摘要"
            />
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">内容 (Markdown)</label>
            <textarea
              v-model="form.content"
              name="content"
              rows="8"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none font-mono"
              placeholder="请输入文章内容，支持 Markdown 格式"
            />
          </div>

          <div class="p-3 bg-gray-50 dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-medium text-gray-900 dark:text-white">文件上传</h3>
              <div class="flex gap-2">
                <label class="cursor-pointer">
                  <input
                    type="file"
                    accept="image/*"
                    @change="handleImageUpload"
                    class="hidden"
                    :disabled="isUploading"
                  />
                  <span class="inline-flex items-center gap-1 px-3 py-1.5 text-xs bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors">
                    <span>🖼️</span>
                    上传图片
                  </span>
                </label>
                <label class="cursor-pointer">
                  <input
                    type="file"
                    multiple
                    @change="handleFileUpload"
                    class="hidden"
                    :disabled="isUploading || !editingArticle"
                  />
                  <span 
                    class="inline-flex items-center gap-1 px-3 py-1.5 text-xs bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors"
                    :class="{ 'opacity-50 cursor-not-allowed': !editingArticle }"
                  >
                    <span>📎</span>
                    上传附件
                  </span>
                </label>
              </div>
            </div>
            
            <div v-if="isUploading" class="mb-3">
              <div class="flex items-center gap-2">
                <div class="flex-1 h-2 bg-gray-200 dark:bg-dark-200 rounded-full overflow-hidden">
                  <div 
                    class="h-full bg-primary transition-all duration-300"
                    :style="{ width: uploadProgress + '%' }"
                  />
                </div>
                <span class="text-xs text-gray-500">{{ Math.round(uploadProgress) }}%</span>
              </div>
            </div>

            <div v-if="!editingArticle" class="text-xs text-gray-500 dark:text-gray-400 mb-2">
              💡 请先保存文章后再上传附件文件
            </div>

            <div v-if="articleFiles.length > 0" class="space-y-2">
              <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">已上传文件：</div>
              <div 
                v-for="file in articleFiles" 
                :key="file.id"
                class="flex items-center justify-between p-2 bg-white dark:bg-dark-200 rounded border border-gray-200 dark:border-white/5"
              >
                <div class="flex items-center gap-2">
                  <span class="text-lg">{{ getFileIcon(file.file_type, file.mime_type) }}</span>
                  <div>
                    <div class="text-sm text-gray-900 dark:text-white">{{ file.original_filename }}</div>
                    <div class="text-xs text-gray-500">
                      {{ formatFileSize(file.file_size) }} · 下载 {{ file.download_count }} 次
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  @click="handleDeleteFile(file.id)"
                  class="text-red-400 hover:text-red-300 text-xs"
                >
                  删除
                </button>
              </div>
            </div>
            <div v-else-if="editingArticle" class="text-xs text-gray-400">
              暂无附件
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">分类</label>
              <select
                v-model="form.category_id"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none"
              >
                <option :value="null">选择分类</option>
                <option
                  v-for="category in blogStore.categories"
                  :key="category.id"
                  :value="category.id"
                >
                  {{ category.name }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">标签</label>
              <div class="flex flex-wrap gap-2 p-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg">
                <label
                  v-for="tag in blogStore.tags"
                  :key="tag.id"
                  class="flex items-center gap-1.5 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    :value="tag.id"
                    v-model="form.tag_ids"
                    class="rounded border-gray-300 dark:border-white/20 bg-white dark:bg-dark-200 text-primary focus:ring-primary"
                  />
                  <span 
                    class="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full border"
                    :style="{ 
                      color: tag.color, 
                      backgroundColor: tag.color + '15',
                      borderColor: tag.color + '40'
                    }"
                  >
                    {{ tag.name }}
                  </span>
                </label>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-4">
            <label class="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                v-model="form.is_published"
                class="rounded border-gray-300 dark:border-white/20 bg-white dark:bg-dark-200 text-primary focus:ring-primary"
              />
              <span class="text-gray-700 dark:text-gray-300 text-sm">发布文章</span>
            </label>
            <label class="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                v-model="form.is_pinned"
                class="rounded border-gray-300 dark:border-white/20 bg-white dark:bg-dark-200 text-primary focus:ring-primary"
              />
              <span class="text-gray-700 dark:text-gray-300 text-sm">置顶文章</span>
            </label>
            <label class="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                v-model="form.is_featured"
                class="rounded border-gray-300 dark:border-white/20 bg-white dark:bg-dark-200 text-primary focus:ring-primary"
              />
              <span class="text-gray-700 dark:text-gray-300 text-sm">设为精选</span>
            </label>
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              @click="showEditor = false"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              class="btn-primary text-sm px-4 py-1.5"
            >
              保存
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
