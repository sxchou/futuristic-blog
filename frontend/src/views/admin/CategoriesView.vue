<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useDialogStore, useBlogStore } from '@/stores'
import { categoryApi, utilsApi } from '@/api'
import type { Category } from '@/types'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { useDeletionConfirm } from '@/composables/useDeletionConfirm'
import DeletionConfirmDialog from '@/components/common/DeletionConfirmDialog.vue'

const dialog = useDialogStore()
const blogStore = useBlogStore()
const { requirePermission } = useAdminCheck()
const deletion = useDeletionConfirm()

const isLoading = ref(false)
const isSubmitting = ref(false)
const showEditor = ref(false)
const editingCategory = ref<Category | null>(null)
const isGeneratingSlug = ref(false)
const slugManuallyEdited = ref(false)

const nameChecking = ref(false)
const slugChecking = ref(false)
const nameExists = ref(false)
const slugExists = ref(false)

let nameCheckTimer: ReturnType<typeof setTimeout> | null = null
let slugCheckTimer: ReturnType<typeof setTimeout> | null = null

const checkNameUnique = async (name: string) => {
  if (!name.trim()) {
    nameExists.value = false
    return
  }
  
  nameChecking.value = true
  try {
    const result = await categoryApi.checkUnique('name', name, editingCategory.value?.id)
    nameExists.value = result.exists
    if (result.exists) {
      validationErrors.value = validationErrors.value.filter(e => e.field !== 'name')
      validationErrors.value.push({ field: 'name', message: '分类名称已存在，请使用其他名称' })
    } else {
      validationErrors.value = validationErrors.value.filter(e => e.field !== 'name')
    }
  } catch (error) {
    console.error('Failed to check name uniqueness:', error)
  } finally {
    nameChecking.value = false
  }
}

const checkSlugUnique = async (slug: string) => {
  if (!slug.trim()) {
    slugExists.value = false
    return
  }
  
  slugChecking.value = true
  try {
    const result = await categoryApi.checkUnique('slug', slug, editingCategory.value?.id)
    slugExists.value = result.exists
    if (result.exists) {
      validationErrors.value = validationErrors.value.filter(e => e.field !== 'slug')
      validationErrors.value.push({ field: 'slug', message: '分类 Slug 已存在，请使用其他 Slug' })
    } else {
      validationErrors.value = validationErrors.value.filter(e => e.field !== 'slug')
    }
  } catch (error) {
    console.error('Failed to check slug uniqueness:', error)
  } finally {
    slugChecking.value = false
  }
}

const form = ref({
  name: '',
  slug: '',
  description: '',
  icon: '',
  color: '#00d4ff',
  order: 0
})

const fetchCategories = async () => {
  isLoading.value = true
  try {
    await blogStore.fetchCategories(true)
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  } finally {
    isLoading.value = false
  }
}

const handleEdit = async (category: Category) => {
  if (!await requirePermission('category.edit', '编辑分类')) return
  editingCategory.value = category
  form.value = {
    name: category.name,
    slug: category.slug,
    description: category.description || '',
    icon: category.icon || '',
    color: category.color,
    order: category.order
  }
  slugManuallyEdited.value = true
  nameExists.value = false
  slugExists.value = false
  nameChecking.value = false
  slugChecking.value = false
  validationErrors.value = []
  showEditor.value = true
}

const handleDelete = async (category: Category) => {
  if (!await requirePermission('category.delete', '删除分类')) return
  
  const previewed = await deletion.requestDeletion('category', category.id, category.name)
  if (!previewed) return
}

const deletionLoading = ref(false)
const executeDeletion = async () => {
  try {
    deletionLoading.value = true
    await categoryApi.deleteCategory(deletion.currentItemId.value)
    blogStore.removeCategory(deletion.currentItemId.value)
    deletion.confirmDeletion()
    await dialog.showSuccess('分类已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete category:', error)
    deletion.cancelDeletion()
  } finally {
    deletionLoading.value = false
  }
}

const handleSubmit = async () => {
  const permission = editingCategory.value ? 'category.edit' : 'category.create'
  if (!await requirePermission(permission, '保存分类')) return
  
  validationErrors.value = []
  
  if (!form.value.name.trim()) {
    validationErrors.value.push({ field: 'name', message: '请输入分类名称' })
  }
  
  if (!form.value.slug.trim()) {
    validationErrors.value.push({ field: 'slug', message: '请输入分类 Slug' })
  }
  
  if (nameChecking.value || slugChecking.value) {
    await new Promise(resolve => setTimeout(resolve, 600))
  }
  
  if (nameExists.value) {
    validationErrors.value.push({ field: 'name', message: '分类名称已存在，请使用其他名称' })
  }
  
  if (slugExists.value) {
    validationErrors.value.push({ field: 'slug', message: '分类 Slug 已存在，请使用其他 Slug' })
  }
  
  if (validationErrors.value.length > 0) {
    const firstError = validationErrors.value[0]
    const fieldIdMap: Record<string, string> = { name: 'category-name', slug: 'category-slug' }
    await scrollToField(fieldIdMap[firstError.field] || firstError.field)
    return
  }
  
  isSubmitting.value = true
  try {
    const isEditing = !!editingCategory.value
    let savedCategory: Category
    if (editingCategory.value) {
      savedCategory = await categoryApi.updateCategory(editingCategory.value.id, form.value)
    } else {
      savedCategory = await categoryApi.createCategory(form.value)
    }
    blogStore.addCategory(savedCategory)
    showEditor.value = false
    editingCategory.value = null
    resetForm()
    await dialog.showSuccess(isEditing ? '分类已更新' : '分类已创建', '成功')
  } catch (error: any) {
    console.error('Failed to save category:', error)
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      if (detail.includes('名称')) {
        validationErrors.value.push({ field: 'name', message: detail })
      } else if (detail.toLowerCase().includes('slug')) {
        validationErrors.value.push({ field: 'slug', message: detail })
      } else {
        await dialog.showError(detail, '错误')
      }
    } else if (Array.isArray(detail)) {
      detail.forEach((err: any) => {
        const field = err.loc?.join('.') || err.field || 'name'
        validationErrors.value.push({ field, message: err.msg || '验证失败' })
      })
    } else {
      await dialog.showError('保存分类失败', '错误')
    }
  } finally {
    isSubmitting.value = false
  }
}

const resetForm = () => {
  form.value = {
    name: '',
    slug: '',
    description: '',
    icon: '',
    color: '#00d4ff',
    order: 0
  }
  slugManuallyEdited.value = false
  validationErrors.value = []
  nameChecking.value = false
  slugChecking.value = false
  nameExists.value = false
  slugExists.value = false
  if (nameCheckTimer) {
    clearTimeout(nameCheckTimer)
    nameCheckTimer = null
  }
  if (slugCheckTimer) {
    clearTimeout(slugCheckTimer)
    slugCheckTimer = null
  }
}

const generateSlug = async () => {
  if (!form.value.name.trim() || slugManuallyEdited.value) return
  
  isGeneratingSlug.value = true
  try {
    const result = await utilsApi.generateSlug(form.value.name, 'category', editingCategory.value?.id)
    form.value.slug = result.slug
    validationErrors.value = validationErrors.value.filter(e => e.field !== 'slug')
  } catch (error) {
    console.error('Failed to generate slug:', error)
    form.value.slug = form.value.name
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
  validationErrors.value = validationErrors.value.filter(e => e.field !== 'slug')
}

const handleNameBlur = () => {
  if (!slugManuallyEdited.value && form.value.name) {
    generateSlug()
  }
}

const handleNameInput = () => {
  if (!form.value.slug || form.value.slug.trim() === '') {
    slugManuallyEdited.value = false
  }
  validationErrors.value = validationErrors.value.filter(e => e.field !== 'name')
}

const openCreateModal = async () => {
  if (!await requirePermission('category.create', '创建分类')) return
  editingCategory.value = null
  resetForm()
  showEditor.value = true
}

onMounted(fetchCategories)

interface ValidationError {
  field: string
  message: string
}

const validationErrors = ref<ValidationError[]>([])

const scrollToField = async (fieldId: string) => {
  await nextTick()
  const element = document.getElementById(fieldId)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    element.focus({ preventScroll: true })
  }
}

const hasError = (field: string): boolean => {
  return validationErrors.value.some(e => e.field === field)
}

const getErrorMessage = (field: string): string => {
  const error = validationErrors.value.find(e => e.field === field)
  return error?.message || ''
}

watch(() => form.value.name, (newName) => {
  if (nameCheckTimer) {
    clearTimeout(nameCheckTimer)
  }
  nameExists.value = false
  validationErrors.value = validationErrors.value.filter(e => e.field !== 'name')
  
  if (newName.trim()) {
    nameCheckTimer = setTimeout(() => {
      checkNameUnique(newName)
    }, 500)
  }
})

watch(() => form.value.slug, (newSlug) => {
  if (slugCheckTimer) {
    clearTimeout(slugCheckTimer)
  }
  slugExists.value = false
  validationErrors.value = validationErrors.value.filter(e => e.field !== 'slug')
  
  if (newSlug.trim()) {
    slugCheckTimer = setTimeout(() => {
      checkSlugUnique(newSlug)
    }, 500)
  }
})
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
              d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          分类管理
        </h1>
      </div>
      <button
        class="btn-primary text-xs sm:text-sm px-3 sm:px-4 py-1.5 whitespace-nowrap"
        @click="openCreateModal"
      >
        新建分类
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
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    >
      <div
        v-for="category in blogStore.categories"
        :key="category.id"
        class="glass-card p-4"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-2">
            <div
              class="w-8 h-8 rounded-lg flex items-center justify-center"
              :style="{ backgroundColor: category.color + '20' }"
            >
              <span
                class="text-base"
                :style="{ color: category.color }"
              >📁</span>
            </div>
            <div>
              <h3 class="text-gray-900 dark:text-white font-medium text-sm">
                {{ category.name }}
              </h3>
              <p class="text-gray-500 text-xs">
                {{ category.slug }}
              </p>
            </div>
          </div>
        </div>
        
        <p
          v-if="category.description"
          class="text-gray-500 dark:text-gray-400 text-xs mb-3"
        >
          {{ category.description }}
        </p>
        
        <div class="flex items-center justify-between">
          <span class="text-gray-500 text-xs">{{ category.article_count }} 篇文章</span>
          <div class="flex gap-2">
            <button
              class="text-primary hover:text-primary/80 text-xs"
              @click="handleEdit(category)"
            >
              编辑
            </button>
            <button
              class="text-red-400 hover:text-red-300 text-xs"
              @click="handleDelete(category)"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="showEditor"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    >
      <div class="glass-card w-full max-w-md m-4 p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-bold text-gray-900 dark:text-white">
            {{ editingCategory ? '编辑分类' : '新建分类' }}
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
          class="space-y-3"
          @submit.prevent="handleSubmit"
        >
          <div>
            <label
              for="category-name"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >名称 <span class="text-red-500">*</span>
              <span v-if="nameChecking" class="ml-2 text-gray-400">检查中...</span>
            </label>
            <input
              id="category-name"
              v-model="form.name"
              type="text"
              name="name"
              autocomplete="off"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              :class="hasError('name') || nameExists ? 'border-red-500 dark:border-red-500' : nameChecking ? 'border-yellow-500 dark:border-yellow-500' : 'border-gray-200 dark:border-white/10'"
              placeholder="分类名称"
              @input="handleNameInput"
              @blur="handleNameBlur"
            >
            <p
              v-if="hasError('name') || nameExists"
              class="mt-1 text-xs text-red-500"
            >
              {{ nameExists ? '分类名称已存在，请使用其他名称' : getErrorMessage('name') }}
            </p>
          </div>

          <div>
            <label
              for="category-slug"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >Slug <span class="text-red-500">*</span> <span class="text-gray-400 font-normal">(留空自动生成)</span>
              <span v-if="slugChecking" class="ml-2 text-gray-400">检查中...</span>
            </label>
            <div class="relative">
              <input
                id="category-slug"
                v-model="form.slug"
                type="text"
                name="slug"
                autocomplete="off"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none pr-8"
                :class="hasError('slug') || slugExists ? 'border-red-500 dark:border-red-500' : slugChecking ? 'border-yellow-500 dark:border-yellow-500' : 'border-gray-200 dark:border-white/10'"
                placeholder="留空自动生成"
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
              {{ slugExists ? '分类 Slug 已存在，请使用其他 Slug' : getErrorMessage('slug') }}
            </p>
          </div>

          <div>
            <label
              for="category-description"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >描述</label>
            <textarea
              id="category-description"
              v-model="form.description"
              name="description"
              rows="2"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="分类描述"
            />
          </div>

          <div>
            <label
              for="category-color"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >颜色</label>
            <div class="flex gap-2">
              <input
                id="category-color"
                v-model="form.color"
                type="color"
                name="color"
                autocomplete="off"
                class="w-10 h-10 rounded-lg cursor-pointer"
              >
              <input
                id="category-color-text"
                v-model="form.color"
                type="text"
                name="color-text"
                autocomplete="off"
                class="flex-1 px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
                placeholder="#00d4ff"
              >
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

    <DeletionConfirmDialog
      :visible="deletion.showDeletionDialog.value"
      :preview="deletion.deletionPreview.value"
      :loading="deletionLoading"
      @confirm="executeDeletion"
      @cancel="deletion.cancelDeletion()"
    />
  </div>
</template>
