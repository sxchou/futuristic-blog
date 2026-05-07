<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted, nextTick, computed } from 'vue'
import { useBlogStore, useDialogStore, usePermissionStore } from '@/stores'
import { articleApi, fileApi, categoryApi, tagApi, utilsApi, parseUploadError } from '@/api'
import type { ArticleListItem, Article, ArticleFile } from '@/types'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { useDeletionConfirm } from '@/composables/useDeletionConfirm'
import DeletionConfirmDialog from '@/components/common/DeletionConfirmDialog.vue'
import { formatDateTime } from '@/utils/date'
import { getMediaUrl } from '@/utils/media'
import MarkdownEditor from '@/components/admin/MarkdownEditor.vue'
import FilePreview from '@/components/FilePreview.vue'
import ImageCropper from '@/components/common/ImageCropper.vue'

const blogStore = useBlogStore()
const dialog = useDialogStore()
const permissionStore = usePermissionStore()
const { requirePermission } = useAdminCheck()
const articleDeletion = useDeletionConfirm()
const fileDeletion = useDeletionConfirm()

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
const slugChecking = ref(false)
const slugExists = ref(false)
let slugCheckTimer: ReturnType<typeof setTimeout> | null = null
const titleChecking = ref(false)
const titleExists = ref(false)
let titleCheckTimer: ReturnType<typeof setTimeout> | null = null

const checkTitleUnique = async (title: string) => {
  if (!title.trim()) {
    titleExists.value = false
    return
  }
  
  titleChecking.value = true
  try {
    const result = await articleApi.checkUnique('title', title, editingArticle.value?.id)
    titleExists.value = result.exists
    if (result.exists) {
      validationErrors.value = validationErrors.value.filter(e => e.field !== 'title')
      validationErrors.value.push({ field: 'title', message: '文章标题已存在，请使用其他标题' })
    } else {
      validationErrors.value = validationErrors.value.filter(e => e.field !== 'title')
    }
  } catch (error) {
    console.error('Failed to check title uniqueness:', error)
  } finally {
    titleChecking.value = false
  }
}

const checkSlugUnique = async (slug: string) => {
  if (!slug.trim()) {
    slugExists.value = false
    return
  }
  
  slugChecking.value = true
  try {
    const result = await articleApi.checkUnique('slug', slug, editingArticle.value?.id)
    slugExists.value = result.exists
    if (result.exists) {
      validationErrors.value = validationErrors.value.filter(e => e.field !== 'slug')
      validationErrors.value.push({ field: 'slug', message: 'Slug 已存在，请使用其他 Slug' })
    } else {
      validationErrors.value = validationErrors.value.filter(e => e.field !== 'slug')
    }
  } catch (error) {
    console.error('Failed to check slug uniqueness:', error)
  } finally {
    slugChecking.value = false
  }
}
const showCategoryModal = ref(false)
const showTagModal = ref(false)
const isCreatingCategory = ref(false)
const isCreatingTag = ref(false)
const isSubmitting = ref(false)
const showPreview = ref(false)
const previewFile = ref<ArticleFile | null>(null)
const draggedFileIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)
const selectedFileIds = ref<Set<number>>(new Set())
const isBatchDeleting = ref(false)
const showCoverSelector = ref(false)
const showCoverCropper = ref(false)
const coverCropperImageSrc = ref('')
const pendingCoverFile = ref<File | null>(null)
const showImageCropper = ref(false)
const imageCropperSrc = ref('')
const pendingImageFile = ref<File | null>(null)
const pendingImageCursorPosition = ref<{ start: number; end: number } | null>(null)

interface ValidationError {
  field: string
  message: string
}

const validationErrors = ref<ValidationError[]>([])

const canPublish = computed(() => {
  return permissionStore.hasPermission('article.publish')
})

const canUploadImage = computed(() => {
  return permissionStore.hasPermission('article.upload_image')
})

const canUploadFile = computed(() => {
  return permissionStore.hasPermission('article.upload_file')
})

interface UploadFileInfo {
  name: string
  size: number
  progress: number
  loaded: number
}

interface UploadErrorInfo {
  fileName: string
  type: 'network' | 'timeout' | 'size_limit' | 'server' | 'unknown'
  message: string
  suggestion: string
}

const currentUploadingFile = ref<UploadFileInfo | null>(null)
const overallUploadProgress = ref(0)
const totalUploadSize = ref(0)
const uploadedSize = ref(0)
const uploadError = ref<UploadErrorInfo | null>(null)
const uploadAbortController = ref<AbortController | null>(null)
const pendingFiles = ref<File[]>([])
const currentFileIndex = ref(0)

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
  cover_image: undefined as string | undefined,
  category_id: undefined as number | undefined,
  tag_ids: [] as number[],
  is_published: false,
  is_featured: false,
  is_pinned: false,
  pinned_order: 0
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
      const hasContent = draft.title?.trim() || 
                         draft.slug?.trim() || 
                         draft.summary?.trim() || 
                         draft.content?.trim() || 
                         draft.cover_image?.trim() ||
                         draft.category_id ||
                         (draft.tag_ids && draft.tag_ids.length > 0)
      
      if (!hasContent) {
        return false
      }
      
      form.value = {
        title: draft.title || '',
        slug: draft.slug || '',
        summary: draft.summary || '',
        content: draft.content || '',
        cover_image: draft.cover_image || undefined,
        category_id: draft.category_id || undefined,
        tag_ids: draft.tag_ids || [],
        is_published: draft.is_published || false,
        is_featured: draft.is_featured || false,
        is_pinned: draft.is_pinned || false,
        pinned_order: draft.pinned_order || 0
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
  if (!await requirePermission('article.edit', '编辑文章')) return
  
  editingArticle.value = article
  validationErrors.value = []
  slugExists.value = false
  slugChecking.value = false
  titleExists.value = false
  titleChecking.value = false
  
  try {
    const fullArticle = await articleApi.getAdminArticle(article.slug)
    form.value = {
      title: fullArticle.title,
      slug: fullArticle.slug,
      summary: fullArticle.summary || '',
      content: fullArticle.content || '',
      cover_image: fullArticle.cover_image || undefined,
      category_id: fullArticle.category?.id || undefined,
      tag_ids: fullArticle.tags.map(t => t.id),
      is_published: fullArticle.is_published,
      is_featured: fullArticle.is_featured,
      is_pinned: fullArticle.is_pinned || false,
      pinned_order: fullArticle.pinned_order || 0
    }
    await fetchArticleFiles(article.id)
    showEditor.value = true
  } catch (error) {
    console.error('Failed to fetch article:', error)
    await dialog.showError('获取文章详情失败', '错误')
  }
}

const handleDelete = async (article: ArticleListItem) => {
  if (!await requirePermission('article.delete', '删除文章')) return
  
  const previewed = await articleDeletion.requestDeletion('article', article.id, article.title)
  if (!previewed) return
}

const articleDeletionLoading = ref(false)
const executeArticleDeletion = async () => {
  try {
    articleDeletionLoading.value = true
    await articleApi.deleteArticle(articleDeletion.currentItemId.value)
    blogStore.removeArticle(articleDeletion.currentItemId.value)
    articles.value = articles.value.filter(a => a.id !== articleDeletion.currentItemId.value)
    articleDeletion.confirmDeletion()
    await dialog.showSuccess('文章已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete article:', error)
    articleDeletion.cancelDeletion()
  } finally {
    articleDeletionLoading.value = false
  }
}

const clearValidationError = (field: string) => {
  validationErrors.value = validationErrors.value.filter(e => e.field !== field)
}

const scrollToField = async (fieldId: string) => {
  await nextTick()
  const element = document.getElementById(fieldId)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    element.focus({ preventScroll: true })
  }
}

const validateForm = async (): Promise<boolean> => {
  validationErrors.value = []
  
  if (!form.value.title.trim()) {
    validationErrors.value.push({ field: 'title', message: '请输入文章标题' })
  }
  
  if (titleChecking.value) {
    await new Promise(resolve => setTimeout(resolve, 600))
  }
  
  if (titleExists.value) {
    validationErrors.value.push({ field: 'title', message: '文章标题已存在，请使用其他标题' })
  }
  
  if (!form.value.slug.trim()) {
    validationErrors.value.push({ field: 'slug', message: '请输入文章 Slug' })
  }
  
  if (slugChecking.value) {
    await new Promise(resolve => setTimeout(resolve, 600))
  }
  
  if (slugExists.value) {
    validationErrors.value.push({ field: 'slug', message: 'Slug 已存在，请使用其他 Slug' })
  }
  
  if (!form.value.summary.trim()) {
    validationErrors.value.push({ field: 'summary', message: '请输入文章摘要' })
  }
  
  if (!form.value.cover_image) {
    validationErrors.value.push({ field: 'cover_image', message: '请设置文章封面图' })
  }
  
  if (!form.value.content.trim()) {
    validationErrors.value.push({ field: 'content', message: '请输入文章内容' })
  }
  
  if (!form.value.category_id) {
    validationErrors.value.push({ field: 'category_id', message: '请选择文章分类' })
  }
  
  if (!form.value.tag_ids || form.value.tag_ids.length === 0) {
    validationErrors.value.push({ field: 'tag_ids', message: '请至少选择一个标签' })
  }
  
  if (validationErrors.value.length > 0) {
    const firstError = validationErrors.value[0]
    const fieldIdMap: Record<string, string> = {
      title: 'article-title',
      slug: 'article-slug',
      summary: 'article-summary',
      cover_image: 'cover-image-section',
      content: 'content-section',
      category_id: 'category-select',
      tag_ids: 'tags-section'
    }
    await scrollToField(fieldIdMap[firstError.field] || firstError.field)
    return false
  }
  
  return true
}

const hasError = (field: string): boolean => {
  return validationErrors.value.some(e => e.field === field)
}

const getErrorMessage = (field: string): string => {
  const error = validationErrors.value.find(e => e.field === field)
  return error?.message || ''
}

const handleSubmit = async () => {
  const permission = editingArticle.value ? 'article.edit' : 'article.create'
  if (!await requirePermission(permission, '保存文章')) return
  
  const isValid = await validateForm()
  if (!isValid) return
  
  isSubmitting.value = true
  try {
    let savedArticle: Article
    let response: any
    if (editingArticle.value) {
      response = await articleApi.updateArticle(editingArticle.value.id, form.value)
    } else {
      response = await articleApi.createArticle(form.value)
    }
    
    savedArticle = response
    
    const articleListItem: ArticleListItem = {
      id: savedArticle.id,
      title: savedArticle.title,
      slug: savedArticle.slug,
      summary: savedArticle.summary,
      cover_image: savedArticle.cover_image,
      is_published: savedArticle.is_published,
      is_featured: savedArticle.is_featured,
      is_pinned: savedArticle.is_pinned,
      pinned_order: savedArticle.pinned_order || 0,
      view_count: savedArticle.view_count,
      like_count: savedArticle.like_count,
      comment_count: 0,
      bookmark_count: savedArticle.bookmark_count || 0,
      reading_time: savedArticle.reading_time,
      created_at: savedArticle.created_at,
      published_at: savedArticle.published_at,
      category: savedArticle.category,
      tags: savedArticle.tags,
      author: savedArticle.author
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
    
    if (response.warning) {
      dialog.showWarning(response.warning)
    }
  } catch (error: any) {
    console.error('Failed to save article:', error)
    
    const errorDetail = error.response?.data?.detail
    if (typeof errorDetail === 'object' && errorDetail.field) {
      validationErrors.value = [{
        field: errorDetail.field,
        message: errorDetail.message
      }]
      
      const elementId = `article-${errorDetail.field}`
      const element = document.getElementById(elementId)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
        element.focus()
      }
    }
  } finally {
    isSubmitting.value = false
  }
}

const resetForm = () => {
  form.value = {
    title: '',
    slug: '',
    summary: '',
    content: '',
    cover_image: undefined,
    category_id: undefined,
    tag_ids: [],
    is_published: false,
    is_featured: false,
    is_pinned: false,
    pinned_order: 0
  }
  articleFiles.value = []
  selectedFileIds.value.clear()
  slugManuallyEdited.value = false
  slugExists.value = false
  slugChecking.value = false
  titleExists.value = false
  titleChecking.value = false
  validationErrors.value = []
  clearFormDraft()
}

const generateSlug = async () => {
  if (!form.value.title.trim() || slugManuallyEdited.value) return
  
  isGeneratingSlug.value = true
  try {
    const result = await utilsApi.generateSlug(form.value.title, 'article', editingArticle.value?.id)
    form.value.slug = result.slug
    validationErrors.value = validationErrors.value.filter(e => e.field !== 'slug')
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
  
  if (slugCheckTimer) {
    clearTimeout(slugCheckTimer)
  }
  slugExists.value = false
  validationErrors.value = validationErrors.value.filter(e => e.field !== 'slug')
  
  if (form.value.slug.trim()) {
    slugCheckTimer = setTimeout(() => {
      checkSlugUnique(form.value.slug)
    }, 500)
  }
}

const handleTitleBlur = () => {
  if (!slugManuallyEdited.value && form.value.title) {
    generateSlug()
  }
  if (form.value.title.trim()) {
    checkTitleUnique(form.value.title.trim())
  }
}

const handleTitleInput = () => {
  if (!form.value.slug || form.value.slug.trim() === '') {
    slugManuallyEdited.value = false
  }
  if (titleCheckTimer) {
    clearTimeout(titleCheckTimer)
    titleCheckTimer = null
  }
  titleExists.value = false
  titleChecking.value = false
  validationErrors.value = validationErrors.value.filter(e => e.field !== 'title')
  if (form.value.title.trim()) {
    titleCheckTimer = setTimeout(() => {
      checkTitleUnique(form.value.title.trim())
    }, 500)
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
  categoryModalErrors.value = []
  categoryChecking.value = { name: false, slug: false }
  categoryExists.value = { name: false, slug: false }
  showCategoryModal.value = true
}

const openTagModal = () => {
  newTag.value = {
    name: '',
    slug: '',
    color: '#00d4ff'
  }
  tagModalErrors.value = []
  tagChecking.value = { name: false, slug: false }
  tagExists.value = { name: false, slug: false }
  showTagModal.value = true
}

const categoryModalErrors = ref<ValidationError[]>([])
const tagModalErrors = ref<ValidationError[]>([])

const categoryChecking = ref({ name: false, slug: false })
const categoryExists = ref({ name: false, slug: false })
let categoryNameCheckTimer: ReturnType<typeof setTimeout> | null = null
let categorySlugCheckTimer: ReturnType<typeof setTimeout> | null = null

const tagChecking = ref({ name: false, slug: false })
const tagExists = ref({ name: false, slug: false })
let tagNameCheckTimer: ReturnType<typeof setTimeout> | null = null
let tagSlugCheckTimer: ReturnType<typeof setTimeout> | null = null

const checkCategoryUnique = async (field: 'name' | 'slug', value: string) => {
  if (!value.trim()) {
    categoryExists.value[field] = false
    categoryChecking.value[field] = false
    return
  }
  categoryChecking.value[field] = true
  try {
    const result = await categoryApi.checkUnique(field, value)
    categoryExists.value[field] = result.exists
    if (result.exists) {
      const existing = categoryModalErrors.value.find(e => e.field === field)
      if (existing) {
        existing.message = field === 'name' ? '分类名称已存在，请使用其他名称' : '分类 Slug 已存在，请使用其他 Slug'
      } else {
        categoryModalErrors.value.push({ field, message: field === 'name' ? '分类名称已存在，请使用其他名称' : '分类 Slug 已存在，请使用其他 Slug' })
      }
    } else {
      categoryModalErrors.value = categoryModalErrors.value.filter(e => !(e.field === field && e.message.includes('已存在')))
    }
  } catch (error) {
    console.error(`Failed to check category ${field} uniqueness:`, error)
  } finally {
    categoryChecking.value[field] = false
  }
}

const checkTagUnique = async (field: 'name' | 'slug', value: string) => {
  if (!value.trim()) {
    tagExists.value[field] = false
    tagChecking.value[field] = false
    return
  }
  tagChecking.value[field] = true
  try {
    const result = await tagApi.checkUnique(field, value)
    tagExists.value[field] = result.exists
    if (result.exists) {
      const existing = tagModalErrors.value.find(e => e.field === field)
      if (existing) {
        existing.message = field === 'name' ? '标签名称已存在，请使用其他名称' : '标签 Slug 已存在，请使用其他 Slug'
      } else {
        tagModalErrors.value.push({ field, message: field === 'name' ? '标签名称已存在，请使用其他名称' : '标签 Slug 已存在，请使用其他 Slug' })
      }
    } else {
      tagModalErrors.value = tagModalErrors.value.filter(e => !(e.field === field && e.message.includes('已存在')))
    }
  } catch (error) {
    console.error(`Failed to check tag ${field} uniqueness:`, error)
  } finally {
    tagChecking.value[field] = false
  }
}

const handleCategoryNameInput = () => {
  if (categoryNameCheckTimer) { clearTimeout(categoryNameCheckTimer); categoryNameCheckTimer = null }
  categoryExists.value.name = false
  categoryModalErrors.value = categoryModalErrors.value.filter(e => !(e.field === 'name' && e.message.includes('已存在')))
  if (newCategory.value.name.trim()) {
    categoryNameCheckTimer = setTimeout(() => checkCategoryUnique('name', newCategory.value.name.trim()), 500)
  }
}

const handleCategorySlugInput = () => {
  if (categorySlugCheckTimer) { clearTimeout(categorySlugCheckTimer); categorySlugCheckTimer = null }
  categoryExists.value.slug = false
  categoryModalErrors.value = categoryModalErrors.value.filter(e => !(e.field === 'slug' && e.message.includes('已存在')))
  if (newCategory.value.slug.trim()) {
    categorySlugCheckTimer = setTimeout(() => checkCategoryUnique('slug', newCategory.value.slug.trim()), 500)
  }
}

const handleTagNameInput = () => {
  if (tagNameCheckTimer) { clearTimeout(tagNameCheckTimer); tagNameCheckTimer = null }
  tagExists.value.name = false
  tagModalErrors.value = tagModalErrors.value.filter(e => !(e.field === 'name' && e.message.includes('已存在')))
  if (newTag.value.name.trim()) {
    tagNameCheckTimer = setTimeout(() => checkTagUnique('name', newTag.value.name.trim()), 500)
  }
}

const handleTagSlugInput = () => {
  if (tagSlugCheckTimer) { clearTimeout(tagSlugCheckTimer); tagSlugCheckTimer = null }
  tagExists.value.slug = false
  tagModalErrors.value = tagModalErrors.value.filter(e => !(e.field === 'slug' && e.message.includes('已存在')))
  if (newTag.value.slug.trim()) {
    tagSlugCheckTimer = setTimeout(() => checkTagUnique('slug', newTag.value.slug.trim()), 500)
  }
}

const handleCreateCategory = async () => {
  categoryModalErrors.value = []
  
  if (!newCategory.value.name.trim()) {
    categoryModalErrors.value.push({ field: 'name', message: '请输入分类名称' })
  }
  
  if (!newCategory.value.slug.trim()) {
    categoryModalErrors.value.push({ field: 'slug', message: '请输入分类 Slug' })
  }
  
  if (categoryChecking.value.name || categoryChecking.value.slug) {
    await new Promise(resolve => setTimeout(resolve, 600))
  }
  
  if (categoryExists.value.name) {
    const existing = categoryModalErrors.value.find(e => e.field === 'name')
    if (!existing) categoryModalErrors.value.push({ field: 'name', message: '分类名称已存在，请使用其他名称' })
  }
  if (categoryExists.value.slug) {
    const existing = categoryModalErrors.value.find(e => e.field === 'slug')
    if (!existing) categoryModalErrors.value.push({ field: 'slug', message: '分类 Slug 已存在，请使用其他 Slug' })
  }
  
  if (categoryModalErrors.value.length > 0) return
  
  isCreatingCategory.value = true
  try {
    const category = await categoryApi.createCategory(newCategory.value)
    blogStore.addCategory(category)
    form.value.category_id = category.id
    showCategoryModal.value = false
    await dialog.showSuccess('分类创建成功', '成功')
  } catch (error: any) {
    console.error('Failed to create category:', error)
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      if (detail.includes('名称')) {
        categoryModalErrors.value.push({ field: 'name', message: detail })
      } else if (detail.toLowerCase().includes('slug')) {
        categoryModalErrors.value.push({ field: 'slug', message: detail })
      } else {
        categoryModalErrors.value.push({ field: 'name', message: detail })
      }
    } else if (Array.isArray(detail)) {
      detail.forEach((err: any) => {
        const field = err.loc?.join('.') || err.field || 'name'
        categoryModalErrors.value.push({ field, message: err.msg || '验证失败' })
      })
    } else {
      categoryModalErrors.value.push({ field: 'name', message: '创建分类失败' })
    }
  } finally {
    isCreatingCategory.value = false
  }
}

const handleCreateTag = async () => {
  tagModalErrors.value = []
  
  if (!newTag.value.name.trim()) {
    tagModalErrors.value.push({ field: 'name', message: '请输入标签名称' })
  }
  
  if (!newTag.value.slug.trim()) {
    tagModalErrors.value.push({ field: 'slug', message: '请输入标签 Slug' })
  }
  
  if (tagChecking.value.name || tagChecking.value.slug) {
    await new Promise(resolve => setTimeout(resolve, 600))
  }
  
  if (tagExists.value.name) {
    const existing = tagModalErrors.value.find(e => e.field === 'name')
    if (!existing) tagModalErrors.value.push({ field: 'name', message: '标签名称已存在，请使用其他名称' })
  }
  if (tagExists.value.slug) {
    const existing = tagModalErrors.value.find(e => e.field === 'slug')
    if (!existing) tagModalErrors.value.push({ field: 'slug', message: '标签 Slug 已存在，请使用其他 Slug' })
  }
  
  if (tagModalErrors.value.length > 0) return
  
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
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      if (detail.includes('名称')) {
        tagModalErrors.value.push({ field: 'name', message: detail })
      } else if (detail.toLowerCase().includes('slug')) {
        tagModalErrors.value.push({ field: 'slug', message: detail })
      } else {
        tagModalErrors.value.push({ field: 'name', message: detail })
      }
    } else if (Array.isArray(detail)) {
      detail.forEach((err: any) => {
        const field = err.loc?.join('.') || err.field || 'name'
        tagModalErrors.value.push({ field, message: err.msg || '验证失败' })
      })
    } else {
      tagModalErrors.value.push({ field: 'name', message: '创建标签失败' })
    }
  } finally {
    isCreatingTag.value = false
  }
}

const generateCategorySlug = async () => {
  if (!newCategory.value.name.trim()) return
  
  try {
    const result = await utilsApi.generateSlug(newCategory.value.name, 'category')
    newCategory.value.slug = result.slug
    categoryModalErrors.value = categoryModalErrors.value.filter(e => e.field !== 'slug')
  } catch (error) {
    console.error('Failed to generate category slug:', error)
  }
}

const generateTagSlug = async () => {
  if (!newTag.value.name.trim()) return
  
  try {
    const result = await utilsApi.generateSlug(newTag.value.name, 'tag')
    newTag.value.slug = result.slug
    tagModalErrors.value = tagModalErrors.value.filter(e => e.field !== 'slug')
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

const cancelUpload = () => {
  if (uploadAbortController.value) {
    uploadAbortController.value.abort()
    uploadAbortController.value = null
  }
  resetUploadState()
}

const resetUploadState = () => {
  isUploading.value = false
  currentUploadingFile.value = null
  overallUploadProgress.value = 0
  uploadProgress.value = 0
  totalUploadSize.value = 0
  uploadedSize.value = 0
  uploadError.value = null
  pendingFiles.value = []
  currentFileIndex.value = 0
}

const retryUpload = async () => {
  if (pendingFiles.value.length === 0 || !editingArticle.value) return
  
  uploadError.value = null
  isUploading.value = true
  
  await processUploadQueue()
}

const processUploadQueue = async () => {
  if (!editingArticle.value) return
  
  for (let i = currentFileIndex.value; i < pendingFiles.value.length; i++) {
    if (!isUploading.value) break
    
    const file = pendingFiles.value[i]
    currentFileIndex.value = i
    
    currentUploadingFile.value = {
      name: file.name,
      size: file.size,
      progress: 0,
      loaded: 0
    }
    
    uploadAbortController.value = new AbortController()
    
    try {
      await fileApi.uploadFile(
        file,
        editingArticle.value.id,
        (progressEvent) => {
          if (currentUploadingFile.value) {
            currentUploadingFile.value.progress = progressEvent.progress
            currentUploadingFile.value.loaded = progressEvent.loaded
            
            const totalUploaded = uploadedSize.value + progressEvent.loaded
            overallUploadProgress.value = Math.round((totalUploaded / totalUploadSize.value) * 100)
            uploadProgress.value = overallUploadProgress.value
          }
        },
        uploadAbortController.value.signal
      )
      
      uploadedSize.value += file.size
    } catch (error: any) {
      if (error.name === 'AbortError' || error.name === 'CanceledError') {
        resetUploadState()
        return
      }
      
      const parsedError = parseUploadError(error)
      
      uploadError.value = {
        fileName: file.name,
        ...parsedError
      }
      isUploading.value = false
      return
    }
  }
  
  await fetchArticleFiles(editingArticle.value.id)
  await dialog.showSuccess('文件上传成功', '成功')
  resetUploadState()
}

const handleFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files || files.length === 0) return
  
  if (!editingArticle.value) {
    await dialog.showError('请先保存文章后再上传文件', '提示')
    return
  }
  
  const fileArray = Array.from(files)
  
  const oversizedFiles = fileArray.filter(f => f.size > 100 * 1024 * 1024)
  if (oversizedFiles.length > 0) {
    await dialog.showError(
      `以下文件超过100MB限制：\n${oversizedFiles.map(f => f.name).join('\n')}`,
      '文件大小超限'
    )
    target.value = ''
    return
  }
  
  pendingFiles.value = fileArray
  currentFileIndex.value = 0
  totalUploadSize.value = fileArray.reduce((sum, f) => sum + f.size, 0)
  uploadedSize.value = 0
  uploadError.value = null
  isUploading.value = true
  overallUploadProgress.value = 0
  uploadProgress.value = 0
  
  await processUploadQueue()
  
  target.value = ''
}

const handleImageUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  if (file.size > 100 * 1024 * 1024) {
    await dialog.showError('图片大小不能超过100MB', '文件大小超限')
    target.value = ''
    return
  }
  
  if (!file.type.startsWith('image/')) {
    await dialog.showError('请选择图片文件', '文件格式错误')
    target.value = ''
    return
  }
  
  const cursorPosition = markdownEditorRef.value?.getCursorPosition()
  pendingImageCursorPosition.value = cursorPosition || null
  pendingImageFile.value = file
  imageCropperSrc.value = URL.createObjectURL(file)
  showImageCropper.value = true
  target.value = ''
}

const handleImageCropConfirm = async (blob: Blob) => {
  if (!pendingImageFile.value) return
  
  const file = new File([blob], pendingImageFile.value.name, { type: 'image/jpeg' })
  const cursorPosition = pendingImageCursorPosition.value
  
  isUploading.value = true
  currentUploadingFile.value = {
    name: file.name,
    size: file.size,
    progress: 0,
    loaded: 0
  }
  uploadProgress.value = 0
  uploadAbortController.value = new AbortController()
  
  try {
    const response = await fileApi.uploadImage(
      file,
      (progressEvent) => {
        if (currentUploadingFile.value) {
          currentUploadingFile.value.progress = progressEvent.progress
          currentUploadingFile.value.loaded = progressEvent.loaded
          uploadProgress.value = progressEvent.progress
        }
      },
      uploadAbortController.value.signal,
      editingArticle.value?.id
    )
    const imageUrl = response.file_path
    const markdown = `![${file.name}](${imageUrl})`
    
    if (cursorPosition && markdownEditorRef.value) {
      markdownEditorRef.value.insertAtCursor(markdown, cursorPosition.start + markdown.length)
    } else {
      form.value.content += `\n${markdown}\n`
    }
  } catch (error: any) {
    if (error.name === 'AbortError' || error.name === 'CanceledError') {
      return
    }
    
    const parsedError = parseUploadError(error)
    
    uploadError.value = {
      fileName: file.name,
      ...parsedError
    }
  } finally {
    isUploading.value = false
    currentUploadingFile.value = null
    uploadProgress.value = 0
    uploadAbortController.value = null
    pendingImageFile.value = null
    pendingImageCursorPosition.value = null
    if (imageCropperSrc.value) {
      URL.revokeObjectURL(imageCropperSrc.value)
      imageCropperSrc.value = ''
    }
  }
}

const handleImageCropCancel = () => {
  pendingImageFile.value = null
  pendingImageCursorPosition.value = null
  if (imageCropperSrc.value) {
    URL.revokeObjectURL(imageCropperSrc.value)
    imageCropperSrc.value = ''
  }
}

const handleCoverUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  if (file.size > 100 * 1024 * 1024) {
    await dialog.showError('图片大小不能超过100MB', '文件大小超限')
    target.value = ''
    return
  }
  
  if (!file.type.startsWith('image/')) {
    await dialog.showError('请选择图片文件', '文件格式错误')
    target.value = ''
    return
  }
  
  pendingCoverFile.value = file
  coverCropperImageSrc.value = URL.createObjectURL(file)
  showCoverCropper.value = true
  target.value = ''
}

const handleCoverCropConfirm = async (blob: Blob) => {
  if (!pendingCoverFile.value) return
  
  const file = new File([blob], pendingCoverFile.value.name, { type: 'image/jpeg' })
  
  isUploading.value = true
  currentUploadingFile.value = {
    name: file.name,
    size: file.size,
    progress: 0,
    loaded: 0
  }
  uploadProgress.value = 0
  uploadAbortController.value = new AbortController()
  
  try {
    const response = await fileApi.uploadImage(
      file,
      (progressEvent) => {
        if (currentUploadingFile.value) {
          currentUploadingFile.value.progress = progressEvent.progress
          currentUploadingFile.value.loaded = progressEvent.loaded
          uploadProgress.value = progressEvent.progress
        }
      },
      uploadAbortController.value.signal,
      editingArticle.value?.id
    )
    form.value.cover_image = response.file_path
    clearValidationError('cover_image')
  } catch (error: any) {
    if (error.name === 'AbortError' || error.name === 'CanceledError') {
      return
    }
    
    const parsedError = parseUploadError(error)
    
    uploadError.value = {
      fileName: file.name,
      ...parsedError
    }
  } finally {
    isUploading.value = false
    currentUploadingFile.value = null
    uploadProgress.value = 0
    uploadAbortController.value = null
    pendingCoverFile.value = null
    if (coverCropperImageSrc.value) {
      URL.revokeObjectURL(coverCropperImageSrc.value)
      coverCropperImageSrc.value = ''
    }
  }
}

const handleCoverCropCancel = () => {
  pendingCoverFile.value = null
  if (coverCropperImageSrc.value) {
    URL.revokeObjectURL(coverCropperImageSrc.value)
    coverCropperImageSrc.value = ''
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

const downloadFile = async (file: ArticleFile) => {
  try {
    const response = await fileApi.downloadFile(file.id)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', file.original_filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error(`Failed to download file ${file.original_filename}:`, error)
  }
}

const handleDeleteFile = async (fileId: number) => {
  const previewed = await fileDeletion.requestDeletion('file', fileId)
  if (!previewed) return
}

const fileDeletionLoading = ref(false)
const executeFileDeletion = async () => {
  try {
    fileDeletionLoading.value = true
    await fileApi.deleteFile(fileDeletion.currentItemId.value)
    if (editingArticle.value) {
      await fetchArticleFiles(editingArticle.value.id)
    }
    fileDeletion.confirmDeletion()
    await dialog.showSuccess('文件已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete file:', error)
    fileDeletion.cancelDeletion()
  } finally {
    fileDeletionLoading.value = false
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

const toggleSelectAll = () => {
  if (selectedFileIds.value.size === articleFiles.value.length) {
    selectedFileIds.value.clear()
  } else {
    selectedFileIds.value = new Set(articleFiles.value.map(f => f.id))
  }
}

const toggleFileSelection = (fileId: number) => {
  if (selectedFileIds.value.has(fileId)) {
    selectedFileIds.value.delete(fileId)
  } else {
    selectedFileIds.value.add(fileId)
  }
}

const handleBatchDownload = async () => {
  if (selectedFileIds.value.size === 0) return
  
  const selectedFiles = articleFiles.value.filter(f => selectedFileIds.value.has(f.id))
  
  for (const file of selectedFiles) {
    try {
      const response = await fileApi.downloadFile(file.id)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', file.original_filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      await new Promise(resolve => setTimeout(resolve, 300))
    } catch (error) {
      console.error(`Failed to download file ${file.original_filename}:`, error)
    }
  }
}

const handleBatchDelete = async () => {
  if (selectedFileIds.value.size === 0) return
  
  const confirmed = await dialog.showConfirm({
    title: '批量删除确认',
    message: `确定要删除选中的 ${selectedFileIds.value.size} 个文件吗？此操作不可恢复。`
  })
  if (!confirmed) return
  
  isBatchDeleting.value = true
  let successCount = 0
  let failCount = 0
  
  try {
    for (const fileId of selectedFileIds.value) {
      try {
        await fileApi.deleteFile(fileId)
        successCount++
      } catch {
        failCount++
      }
    }
    
    if (editingArticle.value) {
      await fetchArticleFiles(editingArticle.value.id)
    }
    
    selectedFileIds.value.clear()
    
    if (failCount === 0) {
      await dialog.showSuccess(`成功删除 ${successCount} 个文件`, '成功')
    } else {
      await dialog.showError(`成功删除 ${successCount} 个文件，失败 ${failCount} 个`, '部分完成')
    }
  } catch (error: any) {
    console.error('Failed to batch delete files:', error)
    await dialog.showError('批量删除失败', '错误')
  } finally {
    isBatchDeleting.value = false
  }
}

const moveFileUp = async (index: number) => {
  if (index <= 0) return
  
  const files = [...articleFiles.value]
  const temp = files[index]
  files[index] = files[index - 1]
  files[index - 1] = temp
  
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

const moveFileDown = async (index: number) => {
  if (index >= articleFiles.value.length - 1) return
  
  const files = [...articleFiles.value]
  const temp = files[index]
  files[index] = files[index + 1]
  files[index + 1] = temp
  
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

const updateFileOrderNumber = async (fileId: number, newOrder: number) => {
  const files = [...articleFiles.value]
  const fileIndex = files.findIndex(f => f.id === fileId)
  if (fileIndex === -1) return
  
  const clampedOrder = Math.max(0, Math.min(newOrder, files.length - 1))
  if (clampedOrder === fileIndex) return
  
  const [file] = files.splice(fileIndex, 1)
  files.splice(clampedOrder, 0, file)
  
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
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><rect x="3" y="3" width="26" height="26" rx="3" fill="rgba(255,255,255,0.2)"/><circle cx="11" cy="11" r="3" fill="white"/><path d="M29 20l-7-7L7 29" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
    }
  }
  if (mimeType.includes('pdf') || ext === 'pdf') {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-red-500 to-red-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/><foreignObject x="4" y="16" width="24" height="12"><div xmlns="http://www.w3.org/1999/xhtml" style="color: white; font-size: 9px; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; line-height: 12px;">PDF</div></foreignObject></svg>`
    }
  }
  if (['doc', 'docx', 'rtf'].includes(ext) || mimeType.includes('word') || mimeType === 'application/msword' || mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-blue-500 to-blue-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/><foreignObject x="4" y="16" width="24" height="16"><div xmlns="http://www.w3.org/1999/xhtml" style="color: white; font-size: 14px; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; line-height: 16px;">W</div></foreignObject></svg>`
    }
  }
  if (['xls', 'xlsx', 'csv'].includes(ext) || mimeType.includes('excel') || mimeType.includes('spreadsheet') || mimeType === 'application/vnd.ms-excel' || mimeType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-emerald-500 to-emerald-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/><foreignObject x="4" y="16" width="24" height="16"><div xmlns="http://www.w3.org/1999/xhtml" style="color: white; font-size: 14px; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; line-height: 16px;">X</div></foreignObject></svg>`
    }
  }
  if (['ppt', 'pptx'].includes(ext) || mimeType.includes('powerpoint') || mimeType === 'application/vnd.ms-powerpoint' || mimeType === 'application/vnd.openxmlformats-officedocument.presentationml.presentation') {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-orange-500 to-orange-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/><foreignObject x="4" y="16" width="24" height="16"><div xmlns="http://www.w3.org/1999/xhtml" style="color: white; font-size: 14px; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; line-height: 16px;">P</div></foreignObject></svg>`
    }
  }
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext) || mimeType.includes('zip') || mimeType.includes('rar') || mimeType.includes('7z') || mimeType.includes('compressed')) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-amber-500 to-amber-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M28 10v18H4V10" fill="rgba(255,255,255,0.3)"/><path d="M30 4H2v6h28V4z" fill="rgba(255,255,255,0.5)"/><rect x="13" y="14" width="6" height="5" fill="white" rx="1"/><rect x="13" y="21" width="6" height="4" fill="rgba(255,255,255,0.5)" rx="1"/></svg>`
    }
  }
  if (['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'].includes(ext) || mimeType.includes('audio')) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-purple-500 to-purple-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M12 24V6l16-3v18" fill="rgba(255,255,255,0.5)"/><circle cx="8" cy="24" r="4" fill="white"/><circle cx="24" cy="21" r="4" fill="white"/></svg>`
    }
  }
  if (['mp4', 'webm', 'avi', 'mov', 'mkv'].includes(ext) || mimeType.includes('video')) {
    return {
      color: 'text-white',
      bg: 'bg-gradient-to-br from-pink-500 to-pink-700',
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><rect x="2" y="5" width="28" height="22" rx="3" fill="rgba(255,255,255,0.3)"/><polygon points="13,10 22,16 13,22" fill="white"/></svg>`
    }
  }
  return {
    color: 'text-white',
    bg: 'bg-gradient-to-br from-gray-400 to-gray-600',
    svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/></svg>`
  }
}

const openCreateModal = async () => {
  if (!await requirePermission('article.create', '新建文章')) return
  editingArticle.value = null
  
  const hasDraft = loadFormDraft()
  if (hasDraft) {
    const confirmed = await dialog.showConfirm({
      title: '发现未保存的草稿',
      message: '检测到上次未保存的文章内容，是否恢复？'
    })
    if (!confirmed) {
      resetForm()
    } else {
      if (form.value.title.trim()) {
        checkTitleUnique(form.value.title.trim())
      }
      if (form.value.slug.trim()) {
        checkSlugUnique(form.value.slug.trim())
      }
    }
  } else {
    resetForm()
  }
  showEditor.value = true
}

onMounted(() => {
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
    <div class="flex items-center justify-between mb-5 gap-2">
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
              d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          文章管理
        </h1>
      </div>
      <button
        class="btn-primary text-xs sm:text-sm px-3 sm:px-4 py-1.5 whitespace-nowrap"
        @click="openCreateModal"
      >
        新建文章
      </button>
    </div>

    <div
      v-if="isLoading"
      class="flex justify-center py-16"
    >
      <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <div
      v-else
      class="glass-card overflow-hidden"
    >
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-100 dark:bg-dark-100">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 w-[280px]">
                标题
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                分类
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                作者
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                状态
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                浏览
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                创建时间
              </th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400">
                操作
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-white/5">
            <tr
              v-for="article in articles"
              :key="article.id"
              class="hover:bg-gray-50 dark:hover:bg-white/5"
            >
              <td class="px-4 py-3 max-w-[280px]">
                <div class="flex items-center gap-2 min-w-0">
                  <span
                    v-if="article.is_pinned"
                    class="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium bg-amber-500/10 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 rounded border border-amber-500/30 flex-shrink-0"
                  >
                    <svg
                      class="w-3 h-3"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                    >
                      <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z" />
                    </svg>
                    置顶
                  </span>
                  <span
                    v-if="article.is_featured"
                    class="px-2 py-0.5 text-xs font-medium bg-primary text-white rounded-full flex-shrink-0"
                  >精选</span>
                  <span class="text-gray-900 dark:text-white truncate">{{ article.title }}</span>
                </div>
              </td>
              <td class="px-4 py-3">
                <span
                  v-if="article.category"
                  :style="{ color: article.category.color }"
                >
                  {{ article.category.name }}
                </span>
                <span
                  v-else
                  class="text-gray-500"
                >未分类</span>
              </td>
              <td class="px-4 py-3 text-gray-400">
                <span v-if="article.author || article.author_name">{{ article.author?.username || article.author_name || '已注销用户' }}</span>
                <span
                  v-else
                  class="text-gray-500"
                >-</span>
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
              <td class="px-4 py-3 text-gray-400">
                {{ article.view_count }}
              </td>
              <td class="px-4 py-3 text-gray-400">
                {{ formatDate(article.created_at) }}
              </td>
              <td class="px-4 py-3 text-right">
                <button
                  class="text-primary hover:text-primary/80 mr-3 text-sm"
                  @click="handleEdit(article)"
                >
                  编辑
                </button>
                <button
                  class="text-red-400 hover:text-red-300 text-sm"
                  @click="handleDelete(article)"
                >
                  删除
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div
      v-if="showEditor"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    >
      <div class="glass-card w-full max-w-5xl max-h-[90vh] overflow-hidden m-2 sm:m-4 p-4 sm:p-5 flex flex-col">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm sm:text-base font-bold text-gray-900 dark:text-white">
            {{ editingArticle ? '编辑文章' : '新建文章' }}
          </h2>
          <button
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
            @click="showEditor = false"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <form
          class="space-y-4 flex-1 overflow-y-auto pr-2"
          @submit.prevent="handleSubmit"
        >
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label
                for="article-title"
                class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >标题 <span class="text-red-500">*</span>
                <span v-if="titleChecking" class="ml-2 text-gray-400">检查中...</span>
              </label>
              <input
                id="article-title"
                v-model="form.title"
                type="text"
                name="title"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
                :class="hasError('title') || titleExists ? 'border-red-500 dark:border-red-500' : titleChecking ? 'border-yellow-500 dark:border-yellow-500' : 'border-gray-200 dark:border-white/10'"
                placeholder="请输入文章标题"
                @input="handleTitleInput"
                @blur="handleTitleBlur"
              >
              <p
                v-if="hasError('title') || titleExists"
                class="mt-1 text-xs text-red-500"
              >
                {{ titleExists ? '文章标题已存在，请使用其他标题' : getErrorMessage('title') }}
              </p>
            </div>
            <div>
              <label
                for="article-slug"
                class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >Slug <span class="text-red-500">*</span>
                <span v-if="slugChecking" class="ml-2 text-gray-400">检查中...</span>
              </label>
              <div class="relative">
                <input
                  id="article-slug"
                  v-model="form.slug"
                  type="text"
                  name="slug"
                  class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none pr-8"
                  :class="hasError('slug') || slugExists ? 'border-red-500 dark:border-red-500' : slugChecking ? 'border-yellow-500 dark:border-yellow-500' : 'border-gray-200 dark:border-white/10'"
                  placeholder="请输入文章 Slug"
                  @input="handleSlugInput"
                >
                <div 
                  v-if="isGeneratingSlug" 
                  class="absolute right-2 top-1/2 -translate-y-1/2"
                >
                  <svg
                    class="w-4 h-4 animate-spin text-gray-400"
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
                </div>
              </div>
              <p
                v-if="hasError('slug') || slugExists"
                class="mt-1 text-xs text-red-500"
              >
                {{ getErrorMessage('slug') || 'Slug 已存在，请使用其他 Slug' }}
              </p>
            </div>
          </div>

          <div>
            <label
              for="article-summary"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >摘要 <span class="text-red-500">*</span></label>
            <textarea
              id="article-summary"
              v-model="form.summary"
              name="summary"
              rows="2"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              :class="hasError('summary') ? 'border-red-500 dark:border-red-500' : 'border-gray-200 dark:border-white/10'"
              placeholder="请输入文章摘要"
              @input="clearValidationError('summary')"
            />
            <p
              v-if="hasError('summary')"
              class="mt-1 text-xs text-red-500"
            >
              {{ getErrorMessage('summary') }}
            </p>
          </div>

          <div id="cover-image-section">
            <label for="article-cover-upload" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              封面图 <span class="text-red-500">*</span>
            </label>
            <div
              class="flex gap-3 items-start"
              :class="hasError('cover_image') ? 'p-2 -m-2 rounded-lg bg-red-50 dark:bg-red-900/10' : ''"
            >
              <div
                v-if="form.cover_image"
                class="relative group"
              >
                <img
                  :src="getMediaUrl(form.cover_image)"
                  alt="封面图预览"
                  class="w-32 h-20 object-cover rounded-lg border border-gray-200 dark:border-white/10"
                >
                <button
                  type="button"
                  class="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center shadow-lg"
                  @click="form.cover_image = undefined; clearValidationError('cover_image')"
                >
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
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
              <div
                v-else
                class="w-32 h-20 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg flex items-center justify-center"
              >
                <span class="text-xs text-gray-400">暂无封面</span>
              </div>
              <div class="flex-1 space-y-2">
                <div class="flex gap-2">
                  <label :class="canUploadImage ? 'cursor-pointer' : 'cursor-not-allowed'">
                    <input id="article-cover-upload"
                      type="file"
                      accept="image/*"
                      class="hidden"
                      :disabled="isUploading || !canUploadImage"
                      @change="handleCoverUpload"
                    >
                    <span
                      class="inline-flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg transition-all shadow-sm"
                      :class="canUploadImage 
                        ? 'bg-primary text-white hover:bg-primary/90' 
                        : 'bg-gray-200 dark:bg-dark-300 text-gray-400 dark:text-gray-500 cursor-not-allowed'"
                    >
                      <svg
                        class="w-3.5 h-3.5"
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
                      上传封面
                    </span>
                  </label>
                  <button
                    v-if="articleFiles.some(f => f.file_type === 'image')"
                    type="button"
                    class="inline-flex items-center gap-1 px-3 py-1.5 text-xs bg-gray-100 dark:bg-dark-200 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-300 transition-all border border-gray-200 dark:border-white/10"
                    @click="showCoverSelector = true"
                  >
                    <svg
                      class="w-3.5 h-3.5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
                      />
                    </svg>
                    从附件选择
                  </button>
                </div>
                <p v-if="!canUploadImage" class="text-[10px] text-amber-500 flex items-center gap-1">
                  <svg class="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  无上传图片权限，请联系管理员
                </p>
                <p v-else class="text-[10px] text-gray-400">
                  建议尺寸: 1200x630px，支持 JPG、PNG、WebP 格式
                </p>
                <p
                  v-if="hasError('cover_image')"
                  class="mt-1 text-xs text-red-500"
                >
                  {{ getErrorMessage('cover_image') }}
                </p>
              </div>
            </div>
          </div>

          <div id="content-section">
            <label
              for="textarea-markdown-editor"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >内容 (Markdown) <span class="text-red-500">*</span></label>
            <div :class="hasError('content') ? 'p-1 rounded-lg bg-red-50 dark:bg-red-900/10' : ''">
              <MarkdownEditor
                ref="markdownEditorRef"
                v-model="form.content"
                placeholder="请输入文章内容，支持 Markdown 格式"
                :storage-key="editingArticle?.id ? `article-${editingArticle.id}` : 'new-article'"
                @update:model-value="clearValidationError('content')"
              />
            </div>
            <p
              v-if="hasError('content')"
              class="mt-1 text-xs text-red-500"
            >
              {{ getErrorMessage('content') }}
            </p>
          </div>

          <div class="p-3 bg-gray-50 dark:bg-dark-100 rounded-lg border border-gray-200 dark:border-white/10">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-medium text-gray-900 dark:text-white">
                文件上传
              </h3>
              <div class="flex gap-2">
                <label :class="canUploadImage ? 'cursor-pointer' : 'cursor-not-allowed'">
                  <input id="article-image-upload"
                    type="file"
                    accept="image/*"
                    class="hidden"
                    :disabled="isUploading || !canUploadImage"
                    @change="handleImageUpload"
                  >
                  <span 
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-all shadow-sm"
                    :class="canUploadImage 
                      ? 'bg-green-500 text-white hover:bg-green-600' 
                      : 'bg-gray-200 dark:bg-dark-300 text-gray-400 dark:text-gray-500 cursor-not-allowed'"
                  >
                    <span class="w-4 h-4">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <rect
                          x="3"
                          y="3"
                          width="18"
                          height="18"
                          rx="2"
                        />
                        <circle
                          cx="8.5"
                          cy="8.5"
                          r="1.5"
                          fill="currentColor"
                        />
                        <path d="M21 15l-5-5L5 21" />
                      </svg>
                    </span>
                    上传图片
                  </span>
                </label>
                <label :class="canUploadFile && editingArticle ? 'cursor-pointer' : 'cursor-not-allowed'">
                  <input id="article-file-upload"
                    type="file"
                    multiple
                    class="hidden"
                    :disabled="isUploading || !editingArticle || !canUploadFile"
                    @change="handleFileUpload"
                  >
                  <span 
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-all shadow-sm"
                    :class="canUploadFile && editingArticle 
                      ? 'bg-blue-500 text-white hover:bg-blue-600' 
                      : 'bg-gray-200 dark:bg-dark-300 text-gray-400 dark:text-gray-500 cursor-not-allowed'"
                  >
                    <span class="w-4 h-4">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                        <path d="M14 2v6h6" />
                      </svg>
                    </span>
                    上传附件
                  </span>
                </label>
              </div>
            </div>
            <div v-if="!canUploadImage && !canUploadFile" class="mb-2 text-xs text-amber-500 flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              无上传文件权限，请联系管理员
            </div>
            <div v-else-if="!canUploadImage" class="mb-2 text-xs text-amber-500 flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              无上传图片权限，请联系管理员
            </div>
            <div v-else-if="!canUploadFile" class="mb-2 text-xs text-amber-500 flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              无上传附件权限，请联系管理员
            </div>
            
            <div
              v-if="uploadError"
              class="mb-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
            >
              <div class="flex items-start gap-2">
                <svg
                  class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"
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
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-red-800 dark:text-red-200">
                    {{ uploadError.message }}
                  </div>
                  <div class="text-xs text-red-600 dark:text-red-400 mt-0.5">
                    {{ uploadError.suggestion }}
                  </div>
                  <div
                    v-if="uploadError.fileName"
                    class="text-xs text-red-500 dark:text-red-500 mt-1 truncate"
                  >
                    文件: {{ uploadError.fileName }}
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-2 mt-2">
                <button
                  type="button"
                  class="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors flex items-center gap-1"
                  @click="retryUpload"
                >
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
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  重试
                </button>
                <button
                  type="button"
                  class="px-3 py-1 text-xs text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-colors"
                  @click="resetUploadState"
                >
                  取消
                </button>
              </div>
            </div>
            
            <div
              v-if="isUploading && currentUploadingFile"
              class="mb-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg"
            >
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2 min-w-0 flex-1">
                  <svg
                    class="w-4 h-4 text-blue-500 animate-spin flex-shrink-0"
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
                  <span class="text-xs text-blue-700 dark:text-blue-300 truncate">{{ currentUploadingFile.name }}</span>
                </div>
                <button
                  type="button"
                  class="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 flex-shrink-0 ml-2"
                  @click="cancelUpload"
                >
                  取消
                </button>
              </div>
              
              <div class="space-y-2">
                <div>
                  <div class="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                    <span>当前文件</span>
                    <span>{{ formatFileSize(currentUploadingFile.loaded) }} / {{ formatFileSize(currentUploadingFile.size) }}</span>
                  </div>
                  <div class="h-2 bg-blue-200 dark:bg-blue-900 rounded-full overflow-hidden">
                    <div 
                      class="h-full bg-blue-500 transition-all duration-150"
                      :style="{ width: currentUploadingFile.progress + '%' }"
                    />
                  </div>
                  <div class="text-xs text-blue-600 dark:text-blue-400 text-right mt-0.5">
                    {{ currentUploadingFile.progress }}%
                  </div>
                </div>
                
                <div v-if="pendingFiles.length > 1">
                  <div class="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                    <span>整体进度 ({{ currentFileIndex + 1 }}/{{ pendingFiles.length }})</span>
                    <span>{{ formatFileSize(uploadedSize + currentUploadingFile.loaded) }} / {{ formatFileSize(totalUploadSize) }}</span>
                  </div>
                  <div class="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      class="h-full bg-primary transition-all duration-150"
                      :style="{ width: overallUploadProgress + '%' }"
                    />
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400 text-right mt-0.5">
                    {{ overallUploadProgress }}%
                  </div>
                </div>
              </div>
            </div>

            <div
              v-if="!editingArticle && canUploadFile"
              class="text-xs text-gray-500 dark:text-gray-400 mb-2"
            >
              💡 请先保存文章后再上传附件文件
            </div>

            <div
              v-if="articleFiles.length > 0"
              class="space-y-1.5"
            >
              <div class="flex items-center justify-between mb-1">
                <div class="flex items-center gap-2 text-xs">
                  <label class="flex items-center gap-1.5 cursor-pointer">
                    <input id="article-is-published"
                      type="checkbox"
                      :checked="selectedFileIds.size === articleFiles.length && articleFiles.length > 0"
                      :indeterminate="selectedFileIds.size > 0 && selectedFileIds.size < articleFiles.length"
                      class="w-3.5 h-3.5 rounded border-gray-300 text-primary focus:ring-primary"
                      @change="toggleSelectAll"
                    >
                    <span class="text-gray-700 dark:text-gray-300 font-medium">全选</span>
                  </label>
                  <span class="text-gray-400">|</span>
                  <span class="text-gray-500">{{ articleFiles.length }} 个文件</span>
                  <div class="flex items-center gap-1 text-primary">
                    <svg
                      class="w-3.5 h-3.5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"
                      />
                    </svg>
                    <span>可拖拽排序</span>
                  </div>
                </div>
                <div class="flex items-center gap-1">
                  <button
                    v-if="selectedFileIds.size > 0"
                    type="button"
                    class="px-2 py-0.5 text-xs bg-primary/10 text-primary hover:bg-primary/20 rounded transition-colors flex items-center gap-1"
                    @click="handleBatchDownload"
                  >
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
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                      />
                    </svg>
                    下载选中 ({{ selectedFileIds.size }})
                  </button>
                  <button
                    v-if="selectedFileIds.size > 0"
                    type="button"
                    :disabled="isBatchDeleting"
                    class="px-2 py-0.5 text-xs bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded transition-colors flex items-center gap-1"
                    @click="handleBatchDelete"
                  >
                    <svg
                      v-if="isBatchDeleting"
                      class="w-3 h-3 animate-spin"
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
                      class="w-3 h-3"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                    删除选中 ({{ selectedFileIds.size }})
                  </button>
                  <button
                    type="button"
                    class="px-2 py-0.5 text-xs text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-white/5 rounded transition-colors flex items-center gap-1"
                    title="按名称升序 (A-Z)"
                    @click="sortFilesAsc"
                  >
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
                        d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"
                      />
                    </svg>
                    升序
                  </button>
                  <button
                    type="button"
                    class="px-2 py-0.5 text-xs text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-white/5 rounded transition-colors flex items-center gap-1"
                    title="按名称降序 (Z-A)"
                    @click="sortFilesDesc"
                  >
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
                        d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4"
                      />
                    </svg>
                    降序
                  </button>
                </div>
              </div>
              <div 
                v-for="(file, index) in articleFiles" 
                :key="file.id"
                draggable="true"
                class="flex items-center justify-between p-2 bg-white dark:bg-dark-100 rounded border transition-all duration-200"
                :class="[
                  selectedFileIds.has(file.id) 
                    ? 'border-primary bg-primary/5' 
                    : draggedFileIndex === index 
                      ? 'border-primary bg-primary/5 opacity-50 scale-[0.98]' 
                      : dragOverIndex === index 
                        ? 'border-primary border-dashed bg-primary/5' 
                        : 'border-gray-200 dark:border-white/5 hover:border-gray-300 dark:hover:border-white/10'
                ]"
                @dragstart="handleDragStart($event, index)"
                @dragover="handleDragOver($event, index)"
                @dragleave="handleDragLeave"
                @drop="handleDrop($event, index)"
                @dragend="handleDragEnd"
              >
                <div class="flex items-center gap-2 min-w-0 flex-1">
                  <input :id="'article-file-select-' + file.id"
                    type="checkbox"
                    :checked="selectedFileIds.has(file.id)"
                    class="w-3.5 h-3.5 rounded border-gray-300 text-primary focus:ring-primary flex-shrink-0"
                    @change="toggleFileSelection(file.id)"
                  >
                  <span 
                    class="w-7 h-7 flex items-center justify-center rounded flex-shrink-0"
                    :class="[getFileIconInfo(file.file_type, file.mime_type, file.original_filename).bg, getFileIconInfo(file.file_type, file.mime_type, file.original_filename).color]"
                    v-html="getFileIconInfo(file.file_type, file.mime_type, file.original_filename).svg"
                  />
                  <div class="min-w-0 flex-1">
                    <div class="text-xs text-gray-900 dark:text-white break-all">
                      {{ file.original_filename }}
                    </div>
                    <div class="text-[10px] text-gray-500">
                      {{ formatFileSize(file.file_size) }} · {{ file.preview_count || 0 }} 次预览 · {{ file.download_count }} 次下载
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-0.5 flex-shrink-0 ml-2">
                  <input :id="'article-file-sort-' + file.id"
                    type="number"
                    :value="index + 1"
                    min="1"
                    :max="articleFiles.length"
                    class="w-10 px-1 py-0.5 text-xs text-center bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white focus:border-primary focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    title="输入序号排序"
                    @change="(e) => updateFileOrderNumber(file.id, parseInt((e.target as HTMLInputElement).value) - 1)"
                  >
                  <div class="flex flex-col gap-0.5">
                    <button
                      type="button"
                      :disabled="index === 0"
                      class="w-5 h-5 flex items-center justify-center text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-white/5 rounded transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                      title="上移"
                      @click="moveFileUp(index)"
                    >
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
                          d="M5 15l7-7 7 7"
                        />
                      </svg>
                    </button>
                    <button
                      type="button"
                      :disabled="index === articleFiles.length - 1"
                      class="w-5 h-5 flex items-center justify-center text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-white/5 rounded transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                      title="下移"
                      @click="moveFileDown(index)"
                    >
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
                          d="M19 9l-7 7-7-7"
                        />
                      </svg>
                    </button>
                  </div>
                  <div class="w-px h-4 bg-gray-200 dark:bg-white/10 mx-0.5" />
                  <button
                    type="button"
                    class="w-6 h-6 flex items-center justify-center text-emerald-500 hover:bg-emerald-500/10 rounded transition-colors"
                    title="预览"
                    @click="openPreview(file)"
                  >
                    <svg
                      class="w-3.5 h-3.5"
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
                  </button>
                  <button
                    type="button"
                    class="w-6 h-6 flex items-center justify-center text-primary hover:bg-primary/10 rounded transition-colors"
                    title="下载"
                    @click="downloadFile(file)"
                  >
                    <svg
                      class="w-3.5 h-3.5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                      />
                    </svg>
                  </button>
                  <button
                    type="button"
                    class="w-6 h-6 flex items-center justify-center text-red-400 hover:bg-red-500/10 rounded transition-colors"
                    title="删除"
                    @click="handleDeleteFile(file.id)"
                  >
                    <svg
                      class="w-3.5 h-3.5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            <div
              v-else-if="editingArticle"
              class="text-xs text-gray-400"
            >
              暂无附件
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <div class="flex items-center justify-between mb-1.5">
                <label for="category-select" class="block text-xs font-medium text-gray-700 dark:text-gray-300">分类 <span class="text-red-500">*</span></label>
                <button
                  type="button"
                  class="text-xs text-primary hover:text-primary/80"
                  @click="openCategoryModal"
                >
                  + 新建分类
                </button>
              </div>
              <select
                id="category-select"
                v-model="form.category_id"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none"
                :class="hasError('category_id') ? 'border-red-500 dark:border-red-500' : 'border-gray-200 dark:border-white/10'"
                @change="clearValidationError('category_id')"
              >
                <option :value="null">
                  选择分类
                </option>
                <option
                  v-for="category in blogStore.categories"
                  :key="category.id"
                  :value="category.id"
                >
                  {{ category.name }}
                </option>
              </select>
              <p
                v-if="hasError('category_id')"
                class="mt-1 text-xs text-red-500"
              >
                {{ getErrorMessage('category_id') }}
              </p>
            </div>
            <div id="tags-section">
              <div class="flex items-center justify-between mb-1.5">
                <label for="article-tags-helper" class="block text-xs font-medium text-gray-700 dark:text-gray-300">标签 <span class="text-red-500">*</span></label>
                <input id="article-tags-helper" type="text" class="sr-only" :value="form.tag_ids?.length || 0" tabindex="-1" readonly autocomplete="off">
                <button
                  type="button"
                  class="text-xs text-primary hover:text-primary/80"
                  @click="openTagModal"
                >
                  + 新建标签
                </button>
              </div>
              <div
                class="flex flex-wrap gap-2 p-2 bg-gray-100 dark:bg-dark-100 border rounded-lg max-h-32 overflow-y-auto"
                :class="hasError('tag_ids') ? 'border-red-500 dark:border-red-500' : 'border-gray-200 dark:border-white/10'"
              >
                <label
                  v-for="tag in blogStore.tags"
                  :key="tag.id"
                  class="flex items-center gap-1.5 cursor-pointer"
                >
                  <input :id="`article-tag-${tag.id}`"
                    v-model="form.tag_ids"
                    type="checkbox"
                    :value="tag.id"
                    class="rounded border-gray-300 dark:border-white/20 bg-white dark:bg-dark-100 text-primary focus:ring-primary"
                    @change="clearValidationError('tag_ids')"
                  >
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
              <p
                v-if="hasError('tag_ids')"
                class="mt-1 text-xs text-red-500"
              >
                {{ getErrorMessage('tag_ids') }}
              </p>
            </div>
          </div>

          <div class="space-y-2">
            <div>
              <label class="flex items-center gap-1.5" :class="canPublish ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'">
                <input id="input-form-is_published"
                  v-model="form.is_published"
                  type="checkbox"
                  :disabled="!canPublish"
                  class="rounded border-gray-300 dark:border-white/20 bg-white dark:bg-dark-100 text-primary focus:ring-primary"
                >
                <span class="text-gray-700 dark:text-gray-300 text-sm">发布文章</span>
              </label>
              <p v-if="!canPublish" class="text-[10px] text-amber-500 flex items-center gap-1 mt-0.5 ml-5">
                <svg class="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                无发布文章权限，请联系管理员
              </p>
            </div>
            <div class="flex flex-wrap items-center gap-3 sm:gap-4">
              <label class="flex items-center gap-1.5 cursor-pointer">
                <input id="input-form-is_pinned"
                  v-model="form.is_pinned"
                  type="checkbox"
                  class="rounded border-gray-300 dark:border-white/20 bg-white dark:bg-dark-100 text-primary focus:ring-primary"
                >
                <span class="text-gray-700 dark:text-gray-300 text-sm">置顶文章</span>
              </label>
              <div v-if="form.is_pinned" class="flex items-center gap-1.5">
                <label for="article-is-pinned" class="text-gray-700 dark:text-gray-300 text-sm whitespace-nowrap">排序:</label>
                <input id="article-is-pinned"
                  v-model.number="form.pinned_order"
                  type="number"
                  min="0"
                  max="999"
                  class="w-16 px-2 py-0.5 text-sm text-center rounded border border-gray-300 dark:border-white/20 bg-white dark:bg-dark-100 text-gray-900 dark:text-white focus:ring-1 focus:ring-primary focus:border-primary"
                  placeholder="0"
                >
                <span class="text-xs text-gray-400 dark:text-gray-500">(数字越小越靠前)</span>
              </div>
              <label class="flex items-center gap-1.5 cursor-pointer">
                <input id="input-form-is_featured"
                  v-model="form.is_featured"
                  type="checkbox"
                  class="rounded border-gray-300 dark:border-white/20 bg-white dark:bg-dark-100 text-primary focus:ring-primary"
                >
                <span class="text-gray-700 dark:text-gray-300 text-sm">设为精选</span>
              </label>
            </div>
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              @click="showEditor = false"
            >
              取消
            </button>
            <button
              type="submit"
              class="btn-primary text-sm px-4 py-1.5"
              :disabled="isSubmitting"
            >
              <span v-if="isSubmitting" class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                保存中...
              </span>
              <span v-else>保存</span>
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
          <h3 class="text-base font-bold text-gray-900 dark:text-white">
            新建分类
          </h3>
          <button
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
            @click="showCategoryModal = false"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <form
          class="space-y-3"
          @submit.prevent="handleCreateCategory"
        >
          <div>
            <label
              for="new-category-name"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >名称 <span class="text-red-500">*</span>
              <span v-if="categoryChecking.name" class="ml-2 text-gray-400">检查中...</span>
            </label>
            <input
              id="new-category-name"
              v-model="newCategory.name"
              type="text"
              name="name"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              :class="categoryModalErrors.some(e => e.field === 'name') || categoryExists.name ? 'border-red-500 dark:border-red-500' : categoryChecking.name ? 'border-yellow-500 dark:border-yellow-500' : 'border-gray-200 dark:border-white/10'"
              placeholder="分类名称"
              @blur="generateCategorySlug"
              @input="handleCategoryNameInput"
            >
            <p
              v-if="categoryModalErrors.some(e => e.field === 'name') || categoryExists.name"
              class="mt-1 text-xs text-red-500"
            >
              {{ categoryExists.name ? '分类名称已存在，请使用其他名称' : categoryModalErrors.find(e => e.field === 'name')?.message }}
            </p>
          </div>
          <div>
            <label
              for="new-category-slug"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >Slug <span class="text-red-500">*</span> <span class="text-gray-400 font-normal">(留空自动生成)</span>
              <span v-if="categoryChecking.slug" class="ml-2 text-gray-400">检查中...</span>
            </label>
            <input
              id="new-category-slug"
              v-model="newCategory.slug"
              type="text"
              name="slug"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              :class="categoryModalErrors.some(e => e.field === 'slug') || categoryExists.slug ? 'border-red-500 dark:border-red-500' : categoryChecking.slug ? 'border-yellow-500 dark:border-yellow-500' : 'border-gray-200 dark:border-white/10'"
              placeholder="留空自动生成"
              @input="handleCategorySlugInput"
            >
            <p
              v-if="categoryModalErrors.some(e => e.field === 'slug') || categoryExists.slug"
              class="mt-1 text-xs text-red-500"
            >
              {{ categoryExists.slug ? '分类 Slug 已存在，请使用其他 Slug' : categoryModalErrors.find(e => e.field === 'slug')?.message }}
            </p>
          </div>
          <div>
            <label
              for="new-category-description"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >描述</label>
            <textarea
              id="new-category-description"
              v-model="newCategory.description"
              name="description"
              rows="2"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="分类描述"
            />
          </div>
          <div>
            <label
              for="new-category-color"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >颜色</label>
            <div class="flex gap-2">
              <input
                id="new-category-color"
                v-model="newCategory.color"
                type="color"
                name="color"
                class="w-10 h-10 rounded-lg cursor-pointer"
              >
              <input
                id="new-category-color-text"
                v-model="newCategory.color"
                type="text"
                name="color-text"
                class="flex-1 px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
                placeholder="#00d4ff"
              >
            </div>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              @click="showCategoryModal = false"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="isCreatingCategory"
              class="btn-primary text-sm px-4 py-1.5"
            >
              <span v-if="isCreatingCategory" class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                创建中...
              </span>
              <span v-else>创建</span>
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
          <h3 class="text-base font-bold text-gray-900 dark:text-white">
            新建标签
          </h3>
          <button
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
            @click="showTagModal = false"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <form
          class="space-y-3"
          @submit.prevent="handleCreateTag"
        >
          <div>
            <label
              for="new-tag-name"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >名称 <span class="text-red-500">*</span>
              <span v-if="tagChecking.name" class="ml-2 text-gray-400">检查中...</span>
            </label>
            <input
              id="new-tag-name"
              v-model="newTag.name"
              type="text"
              name="name"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              :class="tagModalErrors.some(e => e.field === 'name') || tagExists.name ? 'border-red-500 dark:border-red-500' : tagChecking.name ? 'border-yellow-500 dark:border-yellow-500' : 'border-gray-200 dark:border-white/10'"
              placeholder="标签名称"
              @blur="generateTagSlug"
              @input="handleTagNameInput"
            >
            <p
              v-if="tagModalErrors.some(e => e.field === 'name') || tagExists.name"
              class="mt-1 text-xs text-red-500"
            >
              {{ tagExists.name ? '标签名称已存在，请使用其他名称' : tagModalErrors.find(e => e.field === 'name')?.message }}
            </p>
          </div>
          <div>
            <label
              for="new-tag-slug"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >Slug <span class="text-red-500">*</span> <span class="text-gray-400 font-normal">(留空自动生成)</span>
              <span v-if="tagChecking.slug" class="ml-2 text-gray-400">检查中...</span>
            </label>
            <input
              id="new-tag-slug"
              v-model="newTag.slug"
              type="text"
              name="slug"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              :class="tagModalErrors.some(e => e.field === 'slug') || tagExists.slug ? 'border-red-500 dark:border-red-500' : tagChecking.slug ? 'border-yellow-500 dark:border-yellow-500' : 'border-gray-200 dark:border-white/10'"
              placeholder="留空自动生成"
              @input="handleTagSlugInput"
            >
            <p
              v-if="tagModalErrors.some(e => e.field === 'slug') || tagExists.slug"
              class="mt-1 text-xs text-red-500"
            >
              {{ tagExists.slug ? '标签 Slug 已存在，请使用其他 Slug' : tagModalErrors.find(e => e.field === 'slug')?.message }}
            </p>
          </div>
          <div>
            <label
              for="new-tag-color"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >颜色</label>
            <div class="flex gap-2">
              <input
                id="new-tag-color"
                v-model="newTag.color"
                type="color"
                name="color"
                class="w-10 h-10 rounded-lg cursor-pointer"
              >
              <input
                id="new-tag-color-text"
                v-model="newTag.color"
                type="text"
                name="color-text"
                class="flex-1 px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
                placeholder="#00d4ff"
              >
            </div>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              @click="showTagModal = false"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="isCreatingTag"
              class="btn-primary text-sm px-4 py-1.5"
            >
              <span v-if="isCreatingTag" class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                创建中...
              </span>
              <span v-else>创建</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <div
      v-if="showCoverSelector"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/50"
    >
      <div class="glass-card w-full max-w-2xl max-h-[80vh] overflow-hidden m-4 p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-bold text-gray-900 dark:text-white">
            选择封面图
          </h3>
          <button
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
            @click="showCoverSelector = false"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <div
          v-if="articleFiles.filter(f => f.file_type === 'image').length === 0"
          class="text-center py-8 text-gray-400"
        >
          暂无图片附件
        </div>
        <div
          v-else
          class="grid grid-cols-4 gap-3 max-h-96 overflow-y-auto"
        >
          <button
            v-for="file in articleFiles.filter(f => f.file_type === 'image')"
            :key="file.id"
            type="button"
            class="relative aspect-video rounded-lg overflow-hidden border-2 border-transparent hover:border-primary transition-all group"
            :class="{ 'border-primary': form.cover_image === file.file_path }"
            @click="form.cover_image = file.file_path; showCoverSelector = false"
          >
            <img
              :src="file.file_path"
              :alt="file.original_filename"
              class="w-full h-full object-cover"
            >
            <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <span class="text-white text-xs">选择</span>
            </div>
            <div
              v-if="form.cover_image === file.file_path"
              class="absolute top-1 right-1 w-5 h-5 bg-primary rounded-full flex items-center justify-center"
            >
              <svg
                class="w-3 h-3 text-white"
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
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>

  <FilePreview
    v-if="showPreview && previewFile"
    :file="previewFile"
    @close="closePreview"
  />

  <ImageCropper
    v-model="showCoverCropper"
    :image-src="coverCropperImageSrc"
    :aspect-ratio="1200 / 630"
    :output-width="1200"
    :output-height="630"
    :output-quality="0.9"
    title="裁剪封面图"
    @confirm="handleCoverCropConfirm"
    @cancel="handleCoverCropCancel"
  />

  <ImageCropper
    v-model="showImageCropper"
    :image-src="imageCropperSrc"
    :aspect-ratio="NaN"
    :output-quality="0.85"
    title="裁剪图片"
    @confirm="handleImageCropConfirm"
    @cancel="handleImageCropCancel"
  />

  <DeletionConfirmDialog
    :visible="articleDeletion.showDeletionDialog.value"
    :preview="articleDeletion.deletionPreview.value"
    :loading="articleDeletionLoading"
    @confirm="executeArticleDeletion"
    @cancel="articleDeletion.cancelDeletion()"
  />

  <DeletionConfirmDialog
    :visible="fileDeletion.showDeletionDialog.value"
    :preview="fileDeletion.deletionPreview.value"
    :loading="fileDeletionLoading"
    @confirm="executeFileDeletion"
    @cancel="fileDeletion.cancelDeletion()"
  />
</template>
