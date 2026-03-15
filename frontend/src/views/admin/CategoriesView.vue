<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDialogStore } from '@/stores'
import { categoryApi } from '@/api'
import type { Category } from '@/types'

const dialog = useDialogStore()

const categories = ref<Category[]>([])
const isLoading = ref(false)
const showEditor = ref(false)
const editingCategory = ref<Category | null>(null)

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
    categories.value = await categoryApi.getCategories()
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  } finally {
    isLoading.value = false
  }
}

const handleEdit = (category: Category) => {
  editingCategory.value = category
  form.value = {
    name: category.name,
    slug: category.slug,
    description: category.description || '',
    icon: category.icon || '',
    color: category.color,
    order: category.order
  }
  showEditor.value = true
}

const handleDelete = async (category: Category) => {
  const confirmed = await dialog.showConfirm({
    title: '确认删除',
    message: `确定要删除分类"${category.name}"吗？`
  })
  if (!confirmed) return
  
  try {
    await categoryApi.deleteCategory(category.id)
    await fetchCategories()
    await dialog.showSuccess('分类已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete category:', error)
    if (error.response?.status === 403) {
      await dialog.showError('无权限删除此分类', '权限不足')
    } else {
      await dialog.showError(error.response?.data?.detail || '删除失败', '错误')
    }
  }
}

const handleSubmit = async () => {
  try {
    if (editingCategory.value) {
      await categoryApi.updateCategory(editingCategory.value.id, form.value)
    } else {
      await categoryApi.createCategory(form.value)
    }
    showEditor.value = false
    editingCategory.value = null
    resetForm()
    await fetchCategories()
    await dialog.showSuccess('分类已保存', '成功')
  } catch (error: any) {
    console.error('Failed to save category:', error)
    if (error.response?.status === 403) {
      await dialog.showError('无权限修改此分类', '权限不足')
    } else {
      await dialog.showError(error.response?.data?.detail || '保存失败', '错误')
    }
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
}

onMounted(fetchCategories)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold text-gray-900 dark:text-white">分类管理</h1>
      <button
        @click="showEditor = true; editingCategory = null; resetForm()"
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
        v-for="category in categories"
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
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">名称</label>
            <input
              v-model="form.name"
              type="text"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="分类名称"
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

          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">描述</label>
            <textarea
              v-model="form.description"
              rows="2"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="分类描述"
            />
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">颜色</label>
            <div class="flex gap-2">
              <input
                v-model="form.color"
                type="color"
                class="w-10 h-10 rounded-lg cursor-pointer"
              />
              <input
                v-model="form.color"
                type="text"
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
