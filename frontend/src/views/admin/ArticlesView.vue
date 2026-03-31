<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { useBlogStore, useDialogStore, useAuthStore } from '@/stores'
import { articleApi, fileApi, categoryApi, tagApi, utilsApi } from '@/api'
import type { ArticleListItem, Article } from '@/types'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { formatDateTime } from '@/utils/date'
import MarkdownEditor from '@/components/admin/MarkdownEditor.vue'
import FilePreview from '@/components/FilePreview.vue'

interface ArticleFile {
  id: number
  filename: string
  original_filename: string
  file_size: number
  file_type: string
  mime_type: string
  is_image: boolean
  download_count: number
  order: number
  created_at: string
}

const blogStore = useBlogStore()
const dialog = useDialogStore()
const authStore = useAuthStore()
const { requireAdmin, isAdmin } = useAdminCheck()

const articles = ref<ArticleListItem[]>([])
const isLoading = ref(false)
const showEditor = ref(false)
const editingArticle = ref<ArticleListItem | null>(null)
const articleFiles = ref<ArticleFile[]>([])
const isUploading = ref(false)
const uploadProgress = ref(0)
const markdownEditorRef = ref<InstanceType<typeof MarkdownEditor> | null>(null)
const isGeneratingSlug = ref(false)
const slugManuallyEdited = ref(false)
const showCategoryModal = ref(false)
const showTagModal = ref(false)
const isCreatingCategory = ref(false)
const isCreatingTag = ref(false)
const showPreview = ref(false)
const previewFile = ref<ArticleFile | null>(null)
const draggedFileIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

const newCategory = ref({
  name: '',
  slug: '',
  description: '',
  color: '#00d4ff',
  order: 0
})

const newTag = ref({
  name: '',
  slug: '',
  color: '#00d4ff'
})

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

const DRAFT_KEY = 'article_draft'

const saveFormDraft = () => {
  try {
    const draft = {
      ...form.value,
      savedAt: new Date().toISOString()
    }
    localStorage.setItem(DRAFT_KEY, JSON.stringify(draft))
  } catch (e) {
    console.warn('Failed to save form draft:', e)
  }
}

const loadFormDraft = () => {
  try {
    const draftStr = localStorage.getItem(DRAFT_KEY)
    if (draftStr) {
      const draft = JSON.parse(draftStr)
      form.value = {
        title: draft.title || '',
        slug: draft.slug || '',
        summary: draft.summary || '',
        content: draft.content || '',
        category_id: draft.category_id || undefined,
        tag_ids: draft.tag_ids || [],
        is_published: draft.is_published || false,
        is_featured: draft.is_featured || false,
        is_pinned: draft.is_pinned || false
      }
      return true
    }
  } catch (e) {
    console.warn('Failed to load form draft:', e)
  }
  return false
}

const clearFormDraft = () => {
  try {
    localStorage.removeItem(DRAFT_KEY)
  } catch (e) {
    console.warn('Failed to clear form draft:', e)
  }
}

let draftSaveTimer: ReturnType<typeof setTimeout> | null = null

const scheduleDraftSave = () => {
  if (draftSaveTimer) clearTimeout(draftSaveTimer)
  draftSaveTimer = setTimeout(() => {
    saveFormDraft()
  }, 500)
}

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
  if (!await requireAdmin('编辑文章')) return
  
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
  if (!await requireAdmin('删除文章')) return
  
  const confirmed = await dialog.showConfirm({
    title: '确认删除',
    message: `确定要删除文章"${article.title}"吗？`
  })
  if (!confirmed) return
  
  try {
    await articleApi.deleteArticle(article.id)
    blogStore.removeArticle(article.id)
    articles.value = articles.value.filter(a => a.id !== article.id)
    await dialog.showSuccess('文章已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete article:', error)
    await dialog.showError(error.response?.data?.detail || '删除失败', '错误')
  }
}

const handleSubmit = async () => {
  if (!await requireAdmin('保存文章')) return
  
  if (!form.value.category_id) {
    await dialog.showError('请选择文章分类', '验证失败')
    return
  }
  
  if (!form.value.tag_ids || form.value.tag_ids.length === 0) {
    await dialog.showError('请至少选择一个标签', '验证失败')
    return
  }
  
  try {
    let savedArticle: Article
    if (editingArticle.value) {
      savedArticle = await articleApi.updateArticle(editingArticle.value.id, form.value)
    } else {
      savedArticle = await articleApi.createArticle(form.value)
    }
    
    const articleListItem: ArticleListItem = {
      id: savedArticle.id,
      title: savedArticle.title,
      slug: savedArticle.slug,
      summary: savedArticle.summary,
      cover_image: savedArticle.cover_image,
      is_published: savedArticle.is_published,
      is_featured: savedArticle.is_featured,
      is_pinned: savedArticle.is_pinned,
      view_count: savedArticle.view_count,
      like_count: savedArticle.like_count,
      comment_count: 0,
      reading_time: savedArticle.reading_time,
      created_at: savedArticle.created_at,
      published_at: savedArticle.published_at,
      category: savedArticle.category,
      tags: savedArticle.tags
    }
    
    blogStore.addArticle(articleListItem)
    const existingIndex = articles.value.findIndex(a => a.id === savedArticle.id)
    if (existingIndex >= 0) {
      articles.value[existingIndex] = articleListItem
    } else {
      articles.value.unshift(articleListItem)
    }
    markdownEditorRef.value?.markAsSaved()
    showEditor.value = false
    editingArticle.value = null
    resetForm()
  } catch (error: any) {
    console.error('Failed to save article:', error)
    await dialog.showError(error.response?.data?.detail || '保存失败', '错误')
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
  slugManuallyEdited.value = false
  clearFormDraft()
}

const generateSlug = async () => {
  if (!form.value.title.trim() || slugManuallyEdited.value) return
  
  isGeneratingSlug.value = true
  try {
    const result = await utilsApi.generateSlug(form.value.title, 'article', editingArticle.value?.id)
    form.value.slug = result.slug
  } catch (error) {
    console.error('Failed to generate slug:', error)
    form.value.slug = form.value.title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
  } finally {
    isGeneratingSlug.value = false
  }
}

const handleSlugInput = () => {
  if (!form.value.slug || form.value.slug.trim() === '') {
    slugManuallyEdited.value = false
  } else {
    slugManuallyEdited.value = true
  }
}

const handleTitleBlur = () => {
  if (!slugManuallyEdited.value && form.value.title) {
    generateSlug()
  }
}

const handleTitleInput = () => {
  if (!form.value.slug || form.value.slug.trim() === '') {
    slugManuallyEdited.value = false
  }
}

const openCategoryModal = () => {
  newCategory.value = {
    name: '',
    slug: '',
    description: '',
    color: '#00d4ff',
    order: 0
  }
  showCategoryModal.value = true
}

const openTagModal = () => {
  newTag.value = {
    name: '',
    slug: '',
    color: '#00d4ff'
  }
  showTagModal.value = true
}

const handleCreateCategory = async () => {
  if (!newCategory.value.name.trim()) {
    await dialog.showError('请输入分类名称', '验证失败')
    return
  }
  
  isCreatingCategory.value = true
  try {
    const category = await categoryApi.createCategory(newCategory.value)
    blogStore.addCategory(category)
    form.value.category_id = category.id
    showCategoryModal.value = false
    await dialog.showSuccess('分类创建成功', '成功')
  } catch (error: any) {
    console.error('Failed to create category:', error)
    await dialog.showError(error.response?.data?.detail || '创建分类失败', '错误')
  } finally {
    isCreatingCategory.value = false
  }
}

const handleCreateTag = async () => {
  if (!newTag.value.name.trim()) {
    await dialog.showError('请输入标签名称', '验证失败')
    return
  }
  
  isCreatingTag.value = true
  try {
    const tag = await tagApi.createTag(newTag.value)
    blogStore.addTag(tag)
    if (!form.value.tag_ids.includes(tag.id)) {
      form.value.tag_ids.push(tag.id)
    }
    showTagModal.value = false
    await dialog.showSuccess('标签创建成功', '成功')
  } catch (error: any) {
    console.error('Failed to create tag:', error)
    await dialog.showError(error.response?.data?.detail || '创建标签失败', '错误')
  } finally {
    isCreatingTag.value = false
  }
}

const generateCategorySlug = async () => {
  if (!newCategory.value.name.trim()) return
  
  try {
    const result = await utilsApi.generateSlug(newCategory.value.name, 'category')
    newCategory.value.slug = result.slug
  } catch (error) {
    console.error('Failed to generate category slug:', error)
  }
}

const generateTagSlug = async () => {
  if (!newTag.value.name.trim()) return
  
  try {
    const result = await utilsApi.generateSlug(newTag.value.name, 'tag')
    newTag.value.slug = result.slug
  } catch (error) {
    console.error('Failed to generate tag slug:', error)
  }
}

const formatDate = (date: string) => formatDateTime(date)

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

const openPreview = (file: ArticleFile) => {
  previewFile.value = file
  showPreview.value = true
}

const closePreview = () => {
  showPreview.value = false
  previewFile.value = null
}

const downloadFile = (fileId: number) => {
  const url = fileApi.getDownloadUrl(fileId)
  window.open(url, '_blank')
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

const handleDragStart = (e: DragEvent, index: number) => {
  draggedFileIndex.value = index
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', String(index))
  }
}

const handleDragOver = (e: DragEvent, index: number) => {
  e.preventDefault()
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'move'
  }
  if (draggedFileIndex.value !== null && draggedFileIndex.value !== index) {
    dragOverIndex.value = index
  }
}

const handleDragLeave = () => {
  dragOverIndex.value = null
}

const handleDrop = async (e: DragEvent, targetIndex: number) => {
  e.preventDefault()
  
  if (draggedFileIndex.value === null || draggedFileIndex.value === targetIndex) {
    draggedFileIndex.value = null
    dragOverIndex.value = null
    return
  }
  
  const files = [...articleFiles.value]
  const [draggedFile] = files.splice(draggedFileIndex.value, 1)
  files.splice(targetIndex, 0, draggedFile)
  
  articleFiles.value = files
  
  const orders = files.map((f, idx) => ({
    id: f.id,
    order: idx
  }))
  
  try {
    await fileApi.updateFileOrder(orders)
  } catch (error) {
    console.error('Failed to update file order:', error)
    if (editingArticle.value) {
      await fetchArticleFiles(editingArticle.value.id)
    }
  }
  
  draggedFileIndex.value = null
  dragOverIndex.value = null
}

const handleDragEnd = () => {
  draggedFileIndex.value = null
  dragOverIndex.value = null
}

const sortFilesAsc = async () => {
  const files = [...articleFiles.value].sort((a, b) => 
    a.original_filename.localeCompare(b.original_filename, 'zh-CN')
  )
  articleFiles.value = files
  
  const orders = files.map((f, idx) => ({
    id: f.id,
    order: idx
  }))
  
  try {
    await fileApi.updateFileOrder(orders)
  } catch (error) {
    console.error('Failed to update file order:', error)
    if (editingArticle.value) {
      await fetchArticleFiles(editingArticle.value.id)
    }
  }
}

const sortFilesDesc = async () => {
  const files = [...articleFiles.value].sort((a, b) => 
    b.original_filename.localeCompare(a.original_filename, 'zh-CN')
  )
  articleFiles.value = files
  
  const orders = files.map((f, idx) => ({
    id: f.id,
    order: idx
  }))
  
  try {
    await fileApi.updateFileOrder(orders)
  } catch (error) {
    console.error('Failed to update file order:', error)
    if (editingArticle.value) {
      await fetchArticleFiles(editingArticle.value.id)
    }
  }
}

const getFileIconInfo = (fileType: string, mimeType: string, filename: string): { color: string; bg: string; svg: string } => {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  
  if (fileType === 'image') {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-green-400 to-green-600',
      svg: `<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="26" height="26" rx="3" fill="currentColor" fill-opacity="0.2"/><circle cx="11" cy="11" r="3" fill="currentColor"/><path d="M29 20l-7-7L7 29" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
    }
  }
  if (mimeType.includes('pdf') || ext === 'pdf') {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-red-500 to-red-700',
      svg: `<svg viewBox="0 0 32 32" fill="currentColor"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill-opacity="0.3"/><path d="M18 2v8h8" stroke="currentColor" stroke-width="2" fill="none"/><path d="M8 18h2v6H8zm4 0h2v6h-2zm4 0h2v3h-2z"/></svg>`
    }
  }
  if (['doc', 'docx', 'rtf'].includes(ext) || mimeType.includes('word') || mimeType === 'application/msword' || mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-blue-500 to-blue-700',
      svg: `<svg viewBox="0 0 32 32" fill="currentColor"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill-opacity="0.3"/><path d="M18 2v8h8" stroke="currentColor" stroke-width="2" fill="none"/><path d="M9 15h14v2H9zm0 4h10v2H9zm0 4h12v2H9z"/></svg>`
    }
  }
  if (['xls', 'xlsx', 'csv'].includes(ext) || mimeType.includes('excel') || mimeType.includes('spreadsheet') || mimeType === 'application/vnd.ms-excel' || mimeType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-emerald-500 to-emerald-700',
      svg: `<svg viewBox="0 0 32 32" fill="currentColor"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill-opacity="0.3"/><path d="M18 2v8h8" stroke="currentColor" stroke-width="2" fill="none"/><path d="M8 14h6v4H8zm8 0h6v4h-6zm-8 6h6v4H8zm8 0h6v4h-6z"/></svg>`
    }
  }
  if (['ppt', 'pptx'].includes(ext) || mimeType.includes('powerpoint') || mimeType === 'application/vnd.ms-powerpoint' || mimeType === 'application/vnd.openxmlformats-officedocument.presentationml.presentation') {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-orange-500 to-orange-700',
      svg: `<svg viewBox="0 0 32 32" fill="currentColor"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill-opacity="0.3"/><path d="M18 2v8h8" stroke="currentColor" stroke-width="2" fill="none"/><rect x="8" y="14" width="10" height="8" rx="1"/><circle cx="22" cy="16" r="3"/></svg>`
    }
  }
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext) || mimeType.includes('zip') || mimeType.includes('rar') || mimeType.includes('7z') || mimeType.includes('compressed')) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-amber-500 to-amber-700',
      svg: `<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2"><path d="M28 10v18H4V10" fill="currentColor" fill-opacity="0.3"/><path d="M30 4H2v6h28V4z" fill="currentColor" fill-opacity="0.5"/><rect x="13" y="14" width="6" height="5" fill="currentColor" rx="1"/><rect x="13" y="21" width="6" height="4" fill="currentColor" fill-opacity="0.5" rx="1"/></svg>`
    }
  }
  if (['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'].includes(ext) || mimeType.includes('audio')) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-purple-500 to-purple-700',
      svg: `<svg viewBox="0 0 32 32" fill="currentColor"><path d="M12 24V6l16-3v18"/><circle cx="8" cy="24" r="4"/><circle cx="24" cy="21" r="4"/></svg>`
    }
  }
  if (['mp4', 'webm', 'avi', 'mov', 'mkv'].includes(ext) || mimeType.includes('video')) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-pink-500 to-pink-700',
      svg: `<svg viewBox="0 0 32 32" fill="currentColor"><rect x="2" y="5" width="28" height="22" rx="3" fill-opacity="0.3"/><polygon points="13,10 22,16 13,22"/></svg>`
    }
  }
  return {
    color: 'text-white',
    bg: 'bg-gradient-to-br from-gray-400 to-gray-600',
    svg: `<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="currentColor" fill-opacity="0.3"/><path d="M18 2v8h8"/></svg>`
  }
}

const openCreateModal = async () => {
  if (!await requireAdmin('新建文章')) return
  editingArticle.value = null
  
  const hasDraft = loadFormDraft()
  if (hasDraft) {
    const confirmed = await dialog.showConfirm({
      title: '发现未保存的草稿',
      message: '检测到上次未保存的文章内容，是否恢复？'
    })
    if (!confirmed) {
      resetForm()
    }
  } else {
    resetForm()
  }
  showEditor.value = true
}

onMounted(async () => {
  await authStore.waitForInit()
  if (!isAdmin.value) return
  fetchArticles()
  blogStore.fetchCategories()
  blogStore.fetchTags()
})

watch(showEditor, (newVal) => {
  if (newVal) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
    if (!editingArticle.value) {
      saveFormDraft()
    }
  }
})

onUnmounted(() => {
  document.body.style.overflow = ''
  if (draftSaveTimer) clearTimeout(draftSaveTimer)
})

watch(form, () => {
  if (showEditor.value && !editingArticle.value) {
    scheduleDraftSave()
  }
}, { deep: true })
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">文章管理</h1>
      <button
        @click="openCreateModal"
        class="btn-primary text-sm px-4 py-1.5"
      >
        新建文章
      </button>
    </div>

    <div v-if="!isAdmin" class="glass-card p-8 text-center">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
        <svg class="w-8 h-8 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">权限不足</h2>
      <p class="text-gray-500 dark:text-gray-400">您没有权限访问此页面，请联系管理员</p>
    </div>

    <div v-else-if="isLoading" class="flex justify-center py-16">
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
              {{ formatDate(article.created_at) }}
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
      <div class="glass-card w-full max-w-5xl max-h-[90vh] overflow-hidden m-4 p-5 flex flex-col">
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

        <form @submit.prevent="handleSubmit" class="space-y-4 flex-1 overflow-y-auto pr-2">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="article-title" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">标题</label>
              <input
                v-model="form.title"
                type="text"
                id="article-title"
                name="title"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
                placeholder="请输入文章标题"
                @input="handleTitleInput"
                @blur="handleTitleBlur"
              />
            </div>
            <div>
              <label for="article-slug" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">Slug</label>
              <div class="relative">
                <input
                  v-model="form.slug"
                  type="text"
                  id="article-slug"
                  name="slug"
                  class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none pr-8"
                  placeholder="留空自动生成"
                  @input="handleSlugInput"
                />
                <div 
                  v-if="isGeneratingSlug" 
                  class="absolute right-2 top-1/2 -translate-y-1/2"
                >
                  <svg class="w-4 h-4 animate-spin text-gray-400" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <div>
            <label for="article-summary" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">摘要</label>
            <textarea
              v-model="form.summary"
              id="article-summary"
              name="summary"
              rows="2"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="请输入文章摘要"
            />
          </div>

          <div>
            <label for="article-content" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">内容 (Markdown)</label>
            <MarkdownEditor
              ref="markdownEditorRef"
              v-model="form.content"
              placeholder="请输入文章内容，支持 Markdown 格式"
              :storage-key="editingArticle?.id ? `article-${editingArticle.id}` : 'new-article'"
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
                  <span class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg hover:from-green-600 hover:to-green-700 transition-all shadow-sm">
                    <span class="w-4 h-4">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/>
                        <path d="M21 15l-5-5L5 21"/>
                      </svg>
                    </span>
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
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs bg-gradient-to-r from-primary to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all shadow-sm"
                    :class="{ 'opacity-50 cursor-not-allowed': !editingArticle }"
                  >
                    <span class="w-4 h-4">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                        <path d="M14 2v6h6"/>
                      </svg>
                    </span>
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

            <div v-if="articleFiles.length > 0" class="space-y-1.5">
              <div class="flex items-center justify-between mb-1">
                <div class="flex items-center gap-1.5 text-xs">
                  <span class="text-gray-700 dark:text-gray-300 font-medium">已上传文件：</span>
                  <div class="flex items-center gap-1 text-primary">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                    </svg>
                    <span>可拖拽排序</span>
                  </div>
                </div>
                <div class="flex items-center gap-1">
                  <button
                    type="button"
                    @click="sortFilesAsc"
                    class="px-2 py-0.5 text-xs text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-white/5 rounded transition-colors flex items-center gap-1"
                    title="按名称升序 (A-Z)"
                  >
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
                    </svg>
                    升序
                  </button>
                  <button
                    type="button"
                    @click="sortFilesDesc"
                    class="px-2 py-0.5 text-xs text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-white/5 rounded transition-colors flex items-center gap-1"
                    title="按名称降序 (Z-A)"
                  >
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
                    </svg>
                    降序
                  </button>
                </div>
              </div>
              <div 
                v-for="(file, index) in articleFiles" 
                :key="file.id"
                draggable="true"
                @dragstart="handleDragStart($event, index)"
                @dragover="handleDragOver($event, index)"
                @dragleave="handleDragLeave"
                @drop="handleDrop($event, index)"
                @dragend="handleDragEnd"
                class="flex items-center justify-between p-2 bg-white dark:bg-dark-200 rounded border transition-all duration-200 cursor-move"
                :class="[
                  draggedFileIndex === index 
                    ? 'border-primary bg-primary/5 opacity-50 scale-[0.98]' 
                    : dragOverIndex === index 
                      ? 'border-primary border-dashed bg-primary/5' 
                      : 'border-gray-200 dark:border-white/5 hover:border-gray-300 dark:hover:border-white/10'
                ]"
              >
                <div class="flex items-center gap-2 min-w-0 flex-1">
                  <div class="flex-shrink-0 text-gray-300 dark:text-gray-600 cursor-grab active:cursor-grabbing">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <circle cx="9" cy="6" r="1.5"/>
                      <circle cx="15" cy="6" r="1.5"/>
                      <circle cx="9" cy="12" r="1.5"/>
                      <circle cx="15" cy="12" r="1.5"/>
                      <circle cx="9" cy="18" r="1.5"/>
                      <circle cx="15" cy="18" r="1.5"/>
                    </svg>
                  </div>
                  <span 
                    class="w-8 h-8 flex items-center justify-center rounded flex-shrink-0"
                    :class="[getFileIconInfo(file.file_type, file.mime_type, file.original_filename).bg, getFileIconInfo(file.file_type, file.mime_type, file.original_filename).color]"
                    v-html="getFileIconInfo(file.file_type, file.mime_type, file.original_filename).svg"
                  ></span>
                  <div class="min-w-0 flex-1">
                    <div class="text-xs text-gray-900 dark:text-white break-all">{{ file.original_filename }}</div>
                    <div class="text-[10px] text-gray-500">
                      {{ formatFileSize(file.file_size) }} · {{ file.download_count }} 次下载
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-1 flex-shrink-0 ml-2">
                  <button
                    type="button"
                    @click="openPreview(file)"
                    class="w-7 h-7 flex items-center justify-center text-emerald-500 hover:bg-emerald-500/10 rounded transition-colors"
                    title="预览"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    @click="downloadFile(file.id)"
                    class="w-7 h-7 flex items-center justify-center text-primary hover:bg-primary/10 rounded transition-colors"
                    title="下载"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    @click="handleDeleteFile(file.id)"
                    class="w-7 h-7 flex items-center justify-center text-red-400 hover:bg-red-500/10 rounded transition-colors"
                    title="删除"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            <div v-else-if="editingArticle" class="text-xs text-gray-400">
              暂无附件
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <div class="flex items-center justify-between mb-1.5">
                <label class="block text-xs font-medium text-gray-700 dark:text-gray-300">分类</label>
                <button
                  type="button"
                  @click="openCategoryModal"
                  class="text-xs text-primary hover:text-primary/80"
                >
                  + 新建分类
                </button>
              </div>
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
              <div class="flex items-center justify-between mb-1.5">
                <label class="block text-xs font-medium text-gray-700 dark:text-gray-300">标签</label>
                <button
                  type="button"
                  @click="openTagModal"
                  class="text-xs text-primary hover:text-primary/80"
                >
                  + 新建标签
                </button>
              </div>
              <div class="flex flex-wrap gap-2 p-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg max-h-32 overflow-y-auto">
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

    <div
      v-if="showCategoryModal"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/50"
    >
      <div class="glass-card w-full max-w-md m-4 p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-bold text-gray-900 dark:text-white">新建分类</h3>
          <button
            @click="showCategoryModal = false"
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <form @submit.prevent="handleCreateCategory" class="space-y-3">
          <div>
            <label for="new-category-name" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">名称</label>
            <input
              v-model="newCategory.name"
              type="text"
              id="new-category-name"
              name="name"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="分类名称"
              @blur="generateCategorySlug"
            />
          </div>
          <div>
            <label for="new-category-slug" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">Slug (留空自动生成)</label>
            <input
              v-model="newCategory.slug"
              type="text"
              id="new-category-slug"
              name="slug"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="留空自动生成"
            />
          </div>
          <div>
            <label for="new-category-description" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">描述</label>
            <textarea
              v-model="newCategory.description"
              id="new-category-description"
              name="description"
              rows="2"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="分类描述"
            />
          </div>
          <div>
            <label for="new-category-color" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">颜色</label>
            <div class="flex gap-2">
              <input
                v-model="newCategory.color"
                type="color"
                id="new-category-color"
                name="color"
                class="w-10 h-10 rounded-lg cursor-pointer"
              />
              <input
                v-model="newCategory.color"
                type="text"
                id="new-category-color-text"
                name="color-text"
                class="flex-1 px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
                placeholder="#00d4ff"
              />
            </div>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              @click="showCategoryModal = false"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="isCreatingCategory"
              class="btn-primary text-sm px-4 py-1.5 disabled:opacity-50"
            >
              {{ isCreatingCategory ? '创建中...' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div
      v-if="showTagModal"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/50"
    >
      <div class="glass-card w-full max-w-md m-4 p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-bold text-gray-900 dark:text-white">新建标签</h3>
          <button
            @click="showTagModal = false"
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <form @submit.prevent="handleCreateTag" class="space-y-3">
          <div>
            <label for="new-tag-name" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">名称</label>
            <input
              v-model="newTag.name"
              type="text"
              id="new-tag-name"
              name="name"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="标签名称"
              @blur="generateTagSlug"
            />
          </div>
          <div>
            <label for="new-tag-slug" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">Slug (留空自动生成)</label>
            <input
              v-model="newTag.slug"
              type="text"
              id="new-tag-slug"
              name="slug"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="留空自动生成"
            />
          </div>
          <div>
            <label for="new-tag-color" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">颜色</label>
            <div class="flex gap-2">
              <input
                v-model="newTag.color"
                type="color"
                id="new-tag-color"
                name="color"
                class="w-10 h-10 rounded-lg cursor-pointer"
              />
              <input
                v-model="newTag.color"
                type="text"
                id="new-tag-color-text"
                name="color-text"
                class="flex-1 px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
                placeholder="#00d4ff"
              />
            </div>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              @click="showTagModal = false"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="isCreatingTag"
              class="btn-primary text-sm px-4 py-1.5 disabled:opacity-50"
            >
              {{ isCreatingTag ? '创建中...' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <FilePreview
    v-if="showPreview && previewFile"
    :file="previewFile"
    @close="closePreview"
  />
</template>
