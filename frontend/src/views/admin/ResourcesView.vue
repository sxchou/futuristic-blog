<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { resourceApi, resourceCategoryApi } from '@/api'
import type { Resource } from '@/types'
import type { ResourceCategory } from '@/api/resourceCategories'
import { useDialogStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'

const dialog = useDialogStore()
const { requireAdmin } = useAdminCheck()

const resources = ref<Resource[]>([])
const categories = ref<ResourceCategory[]>([])
const isLoading = ref(false)
const activeTab = ref<'resources' | 'categories'>('resources')

const showResourceEditor = ref(false)
const editingResource = ref<Resource | null>(null)

const showCategoryEditor = ref(false)
const editingCategory = ref<ResourceCategory | null>(null)

const resourceForm = ref({
  title: '',
  description: '',
  url: '',
  icon: '',
  category_id: null as number | null,
  is_active: true,
  order: 0
})

const categoryForm = ref({
  name: '',
  slug: '',
  description: '',
  icon: '',
  order: 0,
  is_active: true
})

const fetchCategories = async () => {
  try {
    categories.value = await resourceCategoryApi.getCategories()
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

const fetchResources = async () => {
  isLoading.value = true
  try {
    resources.value = await resourceApi.getResources()
  } catch (error) {
    console.error('Failed to fetch resources:', error)
  } finally {
    isLoading.value = false
  }
}

const getCategoryName = (categoryId?: number | null) => {
  if (!categoryId) return '未分类'
  const category = categories.value.find(c => c.id === categoryId)
  return category ? category.name : '未分类'
}

const handleEditResource = async (resource: Resource) => {
  if (!await requireAdmin('编辑资源')) return
  editingResource.value = resource
  resourceForm.value = {
    title: resource.title,
    description: resource.description || '',
    url: resource.url,
    icon: resource.icon || '',
    category_id: resource.category_id || null,
    is_active: resource.is_active,
    order: resource.order
  }
  showResourceEditor.value = true
}

const handleDeleteResource = async (resource: Resource) => {
  if (!await requireAdmin('删除资源')) return
  
  const confirmed = await dialog.showConfirm({
    title: '确认删除',
    message: `确定要删除资源"${resource.title}"吗？`
  })
  if (!confirmed) return
  
  try {
    await resourceApi.deleteResource(resource.id)
    await fetchResources()
    await dialog.showSuccess('资源已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete resource:', error)
    await dialog.showError(error.response?.data?.detail || '删除失败', '错误')
  }
}

const handleSubmitResource = async () => {
  if (!await requireAdmin('保存资源')) return
  
  try {
    const isEditing = !!editingResource.value
    if (editingResource.value) {
      await resourceApi.updateResource(editingResource.value.id, resourceForm.value)
    } else {
      await resourceApi.createResource(resourceForm.value)
    }
    showResourceEditor.value = false
    editingResource.value = null
    resetResourceForm()
    await fetchResources()
    await dialog.showSuccess(isEditing ? '资源已更新' : '资源已创建', '成功')
  } catch (error: any) {
    console.error('Failed to save resource:', error)
    await dialog.showError(error.response?.data?.detail || '保存失败', '错误')
  }
}

const resetResourceForm = () => {
  resourceForm.value = {
    title: '',
    description: '',
    url: '',
    icon: '',
    category_id: null,
    is_active: true,
    order: 0
  }
}

const openCreateResourceModal = async () => {
  if (!await requireAdmin('创建资源')) return
  editingResource.value = null
  resetResourceForm()
  showResourceEditor.value = true
}

const handleEditCategory = async (category: ResourceCategory) => {
  if (!await requireAdmin('编辑资源分类')) return
  editingCategory.value = category
  categoryForm.value = {
    name: category.name,
    slug: category.slug,
    description: category.description || '',
    icon: category.icon || '',
    order: category.order,
    is_active: category.is_active
  }
  showCategoryEditor.value = true
}

const handleDeleteCategory = async (category: ResourceCategory) => {
  if (!await requireAdmin('删除资源分类')) return
  
  const confirmed = await dialog.showConfirm({
    title: '确认删除',
    message: `确定要删除分类"${category.name}"吗？`
  })
  if (!confirmed) return
  
  try {
    await resourceCategoryApi.deleteCategory(category.id)
    await fetchCategories()
    await dialog.showSuccess('分类已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete category:', error)
    await dialog.showError(error.response?.data?.detail || '删除失败', '错误')
  }
}

const handleSubmitCategory = async () => {
  if (!await requireAdmin('保存资源分类')) return
  
  try {
    const isEditing = !!editingCategory.value
    if (editingCategory.value) {
      await resourceCategoryApi.updateCategory(editingCategory.value.id, categoryForm.value)
    } else {
      await resourceCategoryApi.createCategory(categoryForm.value)
    }
    showCategoryEditor.value = false
    editingCategory.value = null
    resetCategoryForm()
    await fetchCategories()
    await dialog.showSuccess(isEditing ? '分类已更新' : '分类已创建', '成功')
  } catch (error: any) {
    console.error('Failed to save category:', error)
    await dialog.showError(error.response?.data?.detail || '保存失败', '错误')
  }
}

const resetCategoryForm = () => {
  categoryForm.value = {
    name: '',
    slug: '',
    description: '',
    icon: '',
    order: 0,
    is_active: true
  }
}

const openCreateCategoryModal = async () => {
  if (!await requireAdmin('创建资源分类')) return
  editingCategory.value = null
  resetCategoryForm()
  showCategoryEditor.value = true
}

const moveCategoryUp = async (index: number) => {
  if (index === 0) return
  const newCategories = [...categories.value]
  const temp = newCategories[index].order
  newCategories[index].order = newCategories[index - 1].order
  newCategories[index - 1].order = temp
  
  try {
    await resourceCategoryApi.reorderCategories(
      newCategories.map(c => ({ id: c.id, order: c.order }))
    )
    await fetchCategories()
  } catch (error: any) {
    console.error('Failed to reorder categories:', error)
    await dialog.showError('排序失败', '错误')
  }
}

const moveCategoryDown = async (index: number) => {
  if (index === categories.value.length - 1) return
  const newCategories = [...categories.value]
  const temp = newCategories[index].order
  newCategories[index].order = newCategories[index + 1].order
  newCategories[index + 1].order = temp
  
  try {
    await resourceCategoryApi.reorderCategories(
      newCategories.map(c => ({ id: c.id, order: c.order }))
    )
    await fetchCategories()
  } catch (error: any) {
    console.error('Failed to reorder categories:', error)
    await dialog.showError('排序失败', '错误')
  }
}

const activeCategories = computed(() => categories.value.filter(c => c.is_active))

onMounted(async () => {
  await Promise.all([fetchCategories(), fetchResources()])
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4 gap-2">
      <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
        资源管理
      </h1>
      <div class="flex items-center gap-2">
        <button
          v-if="activeTab === 'resources'"
          class="px-3 sm:px-4 py-1.5 bg-primary text-white rounded-lg text-xs sm:text-sm hover:bg-primary/90 transition-colors whitespace-nowrap"
          @click="openCreateResourceModal"
        >
          添加资源
        </button>
        <button
          v-else
          class="px-3 sm:px-4 py-1.5 bg-primary text-white rounded-lg text-xs sm:text-sm hover:bg-primary/90 transition-colors whitespace-nowrap"
          @click="openCreateCategoryModal"
        >
          添加分类
        </button>
      </div>
    </div>

    <div class="flex gap-2 mb-4">
      <button
        class="px-4 py-2 text-sm rounded-lg transition-colors"
        :class="activeTab === 'resources' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-dark-300 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-400'"
        @click="activeTab = 'resources'"
      >
        资源列表
      </button>
      <button
        class="px-4 py-2 text-sm rounded-lg transition-colors"
        :class="activeTab === 'categories' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-dark-300 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-400'"
        @click="activeTab = 'categories'"
      >
        分类管理
      </button>
    </div>

    <div
      v-if="isLoading && activeTab === 'resources'"
      class="flex justify-center py-16"
    >
      <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <template v-else-if="activeTab === 'resources'">
      <div class="glass-card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 dark:bg-dark-100">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  资源
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  分类
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  链接
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  状态
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  排序
                </th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  操作
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-white/10">
              <tr
                v-for="resource in resources"
                :key="resource.id"
                class="hover:bg-gray-50 dark:hover:bg-white/5"
              >
                <td class="px-4 py-3">
                  <div class="flex items-center gap-3">
                    <div
                      v-if="resource.icon"
                      class="w-8 h-8 rounded bg-gray-100 dark:bg-dark-100 flex items-center justify-center text-lg"
                    >
                      {{ resource.icon }}
                    </div>
                    <div>
                      <p class="font-medium text-gray-900 dark:text-white text-sm">
                        {{ resource.title }}
                      </p>
                      <p
                        v-if="resource.description"
                        class="text-gray-500 text-xs truncate max-w-xs"
                      >
                        {{ resource.description }}
                      </p>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <span class="px-2 py-1 text-xs rounded bg-primary/10 text-primary">
                    {{ getCategoryName(resource.category_id) }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <a
                    :href="resource.url"
                    target="_blank"
                    class="text-primary text-sm hover:underline truncate max-w-xs block"
                  >
                    {{ resource.url }}
                  </a>
                </td>
                <td class="px-4 py-3">
                  <span
                    :class="resource.is_active ? 'text-green-500' : 'text-gray-400'"
                    class="text-xs"
                  >
                    {{ resource.is_active ? '启用' : '禁用' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-gray-500 text-sm">
                  {{ resource.order }}
                </td>
                <td class="px-4 py-3 text-right">
                  <button
                    class="text-primary hover:text-primary/80 text-sm mr-3"
                    @click="handleEditResource(resource)"
                  >
                    编辑
                  </button>
                  <button
                    class="text-red-500 hover:text-red-400 text-sm"
                    @click="handleDeleteResource(resource)"
                  >
                    删除
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div
          v-if="resources.length === 0"
          class="text-center py-12 text-gray-500"
        >
          暂无资源
        </div>
      </div>
    </template>

    <template v-else>
      <div class="glass-card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 dark:bg-dark-100">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase w-12">
                  排序
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  分类
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  标识
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  状态
                </th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  操作
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-white/10">
              <tr
                v-for="(category, index) in categories"
                :key="category.id"
                class="hover:bg-gray-50 dark:hover:bg-white/5"
              >
                <td class="px-4 py-3">
                  <div class="flex items-center gap-1">
                    <button
                      class="p-1 text-gray-400 hover:text-primary disabled:opacity-30"
                      :disabled="index === 0"
                      @click="moveCategoryUp(index)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                      </svg>
                    </button>
                    <button
                      class="p-1 text-gray-400 hover:text-primary disabled:opacity-30"
                      :disabled="index === categories.length - 1"
                      @click="moveCategoryDown(index)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <div class="flex items-center gap-3">
                    <div
                      v-if="category.icon"
                      class="w-8 h-8 rounded bg-gray-100 dark:bg-dark-100 flex items-center justify-center text-lg"
                    >
                      {{ category.icon }}
                    </div>
                    <div>
                      <p class="font-medium text-gray-900 dark:text-white text-sm">
                        {{ category.name }}
                      </p>
                      <p
                        v-if="category.description"
                        class="text-gray-500 text-xs truncate max-w-xs"
                      >
                        {{ category.description }}
                      </p>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <code class="text-xs bg-gray-100 dark:bg-dark-300 px-2 py-1 rounded">
                    {{ category.slug }}
                  </code>
                </td>
                <td class="px-4 py-3">
                  <span
                    :class="category.is_active ? 'text-green-500' : 'text-gray-400'"
                    class="text-xs"
                  >
                    {{ category.is_active ? '启用' : '禁用' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right">
                  <button
                    class="text-primary hover:text-primary/80 text-sm mr-3"
                    @click="handleEditCategory(category)"
                  >
                    编辑
                  </button>
                  <button
                    class="text-red-500 hover:text-red-400 text-sm"
                    @click="handleDeleteCategory(category)"
                  >
                    删除
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div
          v-if="categories.length === 0"
          class="text-center py-12 text-gray-500"
        >
          暂无分类，请先添加分类
        </div>
      </div>
    </template>

    <div
      v-if="showResourceEditor"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white dark:bg-dark-100 rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div class="p-4 border-b border-gray-200 dark:border-white/10">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white">
            {{ editingResource ? '编辑资源' : '添加资源' }}
          </h2>
        </div>

        <form
          class="p-4 space-y-4"
          @submit.prevent="handleSubmitResource"
        >
          <div>
            <label
              for="resource-title"
              class="block text-sm text-gray-600 dark:text-gray-400 mb-1"
            >标题 *</label>
            <input
              id="resource-title"
              v-model="resourceForm.title"
              type="text"
              name="title"
              required
              class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white text-sm"
            >
          </div>

          <div>
            <label
              for="resource-url"
              class="block text-sm text-gray-600 dark:text-gray-400 mb-1"
            >链接 *</label>
            <input
              id="resource-url"
              v-model="resourceForm.url"
              type="url"
              name="url"
              required
              class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white text-sm"
            >
          </div>

          <div>
            <label
              for="resource-description"
              class="block text-sm text-gray-600 dark:text-gray-400 mb-1"
            >描述</label>
            <textarea
              id="resource-description"
              v-model="resourceForm.description"
              name="description"
              rows="2"
              class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white text-sm"
            />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label
                for="resource-category"
                class="block text-sm text-gray-600 dark:text-gray-400 mb-1"
              >分类</label>
              <select
                id="resource-category"
                v-model="resourceForm.category_id"
                name="category_id"
                class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white text-sm"
              >
                <option :value="null">
                  未分类
                </option>
                <option
                  v-for="cat in activeCategories"
                  :key="cat.id"
                  :value="cat.id"
                >
                  {{ cat.name }}
                </option>
              </select>
            </div>

            <div>
              <label
                for="resource-icon"
                class="block text-sm text-gray-600 dark:text-gray-400 mb-1"
              >图标</label>
              <input
                id="resource-icon"
                v-model="resourceForm.icon"
                type="text"
                name="icon"
                placeholder="emoji 或图标类名"
                class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white text-sm"
              >
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label
                for="resource-order"
                class="block text-sm text-gray-600 dark:text-gray-400 mb-1"
              >排序</label>
              <input
                id="resource-order"
                v-model.number="resourceForm.order"
                type="number"
                name="order"
                min="0"
                class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white text-sm"
              >
            </div>

            <div class="flex items-center pt-6">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  id="resource-is-active"
                  v-model="resourceForm.is_active"
                  type="checkbox"
                  name="is_active"
                  class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                >
                <span class="text-sm text-gray-600 dark:text-gray-400">启用</span>
              </label>
            </div>
          </div>

          <div class="flex justify-end gap-3 pt-4">
            <button
              type="button"
              class="px-4 py-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-sm"
              @click="showResourceEditor = false; editingResource = null; resetResourceForm()"
            >
              取消
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary/90"
            >
              保存
            </button>
          </div>
        </form>
      </div>
    </div>

    <div
      v-if="showCategoryEditor"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white dark:bg-dark-100 rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div class="p-4 border-b border-gray-200 dark:border-white/10">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white">
            {{ editingCategory ? '编辑分类' : '添加分类' }}
          </h2>
        </div>

        <form
          class="p-4 space-y-4"
          @submit.prevent="handleSubmitCategory"
        >
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label
                for="category-name"
                class="block text-sm text-gray-600 dark:text-gray-400 mb-1"
              >名称 *</label>
              <input
                id="category-name"
                v-model="categoryForm.name"
                type="text"
                name="name"
                required
                class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white text-sm"
              >
            </div>

            <div>
              <label
                for="category-slug"
                class="block text-sm text-gray-600 dark:text-gray-400 mb-1"
              >标识 *</label>
              <input
                id="category-slug"
                v-model="categoryForm.slug"
                type="text"
                name="slug"
                required
                placeholder="如: tool, framework"
                class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white text-sm"
              >
            </div>
          </div>

          <div>
            <label
              for="category-description"
              class="block text-sm text-gray-600 dark:text-gray-400 mb-1"
            >描述</label>
            <textarea
              id="category-description"
              v-model="categoryForm.description"
              name="description"
              rows="2"
              class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white text-sm"
            />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label
                for="category-icon"
                class="block text-sm text-gray-600 dark:text-gray-400 mb-1"
              >图标</label>
              <input
                id="category-icon"
                v-model="categoryForm.icon"
                type="text"
                name="icon"
                placeholder="emoji 或图标类名"
                class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white text-sm"
              >
            </div>

            <div>
              <label
                for="category-order"
                class="block text-sm text-gray-600 dark:text-gray-400 mb-1"
              >排序</label>
              <input
                id="category-order"
                v-model.number="categoryForm.order"
                type="number"
                name="order"
                min="0"
                class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-100 text-gray-900 dark:text-white text-sm"
              >
            </div>
          </div>

          <div class="flex items-center">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                id="category-is-active"
                v-model="categoryForm.is_active"
                type="checkbox"
                name="is_active"
                class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
              >
              <span class="text-sm text-gray-600 dark:text-gray-400">启用</span>
            </label>
          </div>

          <div class="flex justify-end gap-3 pt-4">
            <button
              type="button"
              class="px-4 py-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-sm"
              @click="showCategoryEditor = false; editingCategory = null; resetCategoryForm()"
            >
              取消
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary/90"
            >
              保存
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
