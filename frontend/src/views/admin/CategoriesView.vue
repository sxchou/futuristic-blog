<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDialogStore, useBlogStore } from '@/stores'
import { categoryApi, utilsApi } from '@/api'
import type { Category } from '@/types'
import { useAdminCheck } from '@/composables/useAdminCheck'

const dialog = useDialogStore()
const blogStore = useBlogStore()
const { requireAdmin } = useAdminCheck()

const isLoading = ref(false)
const showEditor = ref(false)
const editingCategory = ref<Category | null>(null)
const isGeneratingSlug = ref(false)
const slugManuallyEdited = ref(false)

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
  if (!await requireAdmin('编辑分类')) return
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
  showEditor.value = true
}

const handleDelete = async (category: Category) => {
  if (!await requireAdmin('删除分类')) return
  
  const confirmed = await dialog.showConfirm({
    title: '确认删除',
    message: `确定要删除分类"${category.name}"吗？`
  })
  if (!confirmed) return
  
  try {
    await categoryApi.deleteCategory(category.id)
    await blogStore.fetchCategories(true)
    await dialog.showSuccess('分类已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete category:', error)
    await dialog.showError(error.response?.data?.detail || '删除失败', '错误')
  }
}

const handleSubmit = async () => {
  if (!await requireAdmin('保存分类')) return
  
  try {
    if (editingCategory.value) {
      await categoryApi.updateCategory(editingCategory.value.id, form.value)
    } else {
      await categoryApi.createCategory(form.value)
    }
    showEditor.value = false
    editingCategory.value = null
    resetForm()
    await blogStore.fetchCategories(true)
    await dialog.showSuccess('分类已保存', '成功')
  } catch (error: any) {
    console.error('Failed to save category:', error)
    await dialog.showError(error.response?.data?.detail || '保存失败', '错误')
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
}

const generateSlug = async () => {
  if (!form.value.name.trim() || slugManuallyEdited.value) return
  
  isGeneratingSlug.value = true
  try {
    const result = await utilsApi.generateSlug(form.value.name, 'category', editingCategory.value?.id)
    form.value.slug = result.slug
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
}

const openCreateModal = async () => {
  if (!await requireAdmin('创建分类')) return
  editingCategory.value = null
  resetForm()
  showEditor.value = true
}

onMounted(fetchCategories)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">分类管理</h1>
      <button
        @click="openCreateModal"
        class="btn-primary text-sm px-4 py-1.5"
      >
        新建分类
      </button>
    </div>

    <div v-if="isLoading" class="flex justify-center py-16">
      <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
              <span class="text-base" :style="{ color: category.color }">📁</span>
            </div>
            <div>
              <h3 class="text-gray-900 dark:text-white font-medium text-sm">{{ category.name }}</h3>
              <p class="text-gray-500 text-xs">{{ category.slug }}</p>
            </div>
          </div>
        </div>
        
        <p v-if="category.description" class="text-gray-500 dark:text-gray-400 text-xs mb-3">
          {{ category.description }}
        </p>
        
        <div class="flex items-center justify-between">
          <span class="text-gray-500 text-xs">{{ category.article_count }} 篇文章</span>
          <div class="flex gap-2">
            <button
              @click="handleEdit(category)"
              class="text-primary hover:text-primary/80 text-xs"
            >
              编辑
            </button>
            <button
              @click="handleDelete(category)"
              class="text-red-400 hover:text-red-300 text-xs"
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
            @click="showEditor = false"
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-3">
          <div>
            <label for="category-name" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">名称</label>
            <input
              v-model="form.name"
              type="text"
              id="category-name"
              name="name"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="分类名称"
              @input="handleNameInput"
              @blur="handleNameBlur"
            />
          </div>

          <div>
            <label for="category-slug" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">Slug (留空自动生成)</label>
            <div class="relative">
              <input
                v-model="form.slug"
                type="text"
                id="category-slug"
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

          <div>
            <label for="category-description" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">描述</label>
            <textarea
              v-model="form.description"
              id="category-description"
              name="description"
              rows="2"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="分类描述"
            />
          </div>

          <div>
            <label for="category-color" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">颜色</label>
            <div class="flex gap-2">
              <input
                v-model="form.color"
                type="color"
                id="category-color"
                name="color"
                class="w-10 h-10 rounded-lg cursor-pointer"
              />
              <input
                v-model="form.color"
                type="text"
                id="category-color-text"
                name="color-text"
                class="flex-1 px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
                placeholder="#00d4ff"
              />
            </div>
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
