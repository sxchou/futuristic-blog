<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { resourceApi, resourceCategoryApi } from '@/api'
import type { Resource } from '@/types'
import type { ResourceCategory } from '@/api/resourceCategories'
import { useDialogStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { 
  updateArrayItem, 
  addArrayItem, 
  removeArrayItem
} from '@/utils/reactiveUpdate'
import IconPicker from '@/components/common/IconPicker.vue'

const dialog = useDialogStore()
const { requireAdmin } = useAdminCheck()

const resources = ref<Resource[]>([])
const categories = ref<ResourceCategory[]>([])
const isLoading = ref(false)
const isSubmitting = ref(false)
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
    resources.value = await resourceApi.getAdminResources()
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

const getCategoryColor = (categoryId?: number | null) => {
  if (!categoryId) return '#6b7280'
  const category = categories.value.find(c => c.id === categoryId)
  return category?.icon ? '#00d4ff' : '#6b7280'
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
    await removeArrayItem(resources, resource.id)
    await dialog.showSuccess('资源已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete resource:', error)
    await dialog.showError(error.response?.data?.detail || '删除失败', '错误')
  }
}

const handleToggleResourceStatus = async (resource: Resource) => {
  if (!await requireAdmin('切换资源状态')) return
  
  const previousStatus = resource.is_active
  
  try {
    await resourceApi.updateResource(resource.id, { is_active: !resource.is_active })
    dialog.showSuccess(previousStatus ? '资源已禁用' : '资源已启用', '成功')
    await fetchResources()
  } catch (error: any) {
    console.error('Failed to toggle resource status:', error)
    await dialog.showError(error.response?.data?.detail || '状态切换失败', '错误')
  }
}

const handleSubmitResource = async () => {
  if (!await requireAdmin('保存资源')) return
  
  isSubmitting.value = true
  try {
    const isEditing = !!editingResource.value
    
    if (editingResource.value) {
      const resource = editingResource.value
      await updateArrayItem(resources, resource.id, () =>
        resourceApi.updateResource(resource.id, resourceForm.value)
      )
    } else {
      await addArrayItem(resources, () =>
        resourceApi.createResource(resourceForm.value)
      )
    }
    
    showResourceEditor.value = false
    editingResource.value = null
    resetResourceForm()
    
    await dialog.showSuccess(isEditing ? '资源已更新' : '资源已创建', '成功')
  } catch (error: any) {
    console.error('Failed to save resource:', error)
    await dialog.showError(error.response?.data?.detail || '保存失败', '错误')
  } finally {
    isSubmitting.value = false
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

const getResourceCount = (categoryId: number) => {
  return resources.value.filter(r => r.category_id === categoryId).length
}

onMounted(async () => {
  await Promise.all([fetchCategories(), fetchResources()])
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
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          资源管理
        </h1>
      </div>
      <button
        class="btn-primary text-xs sm:text-sm px-3 sm:px-4 py-1.5 whitespace-nowrap"
        @click="activeTab === 'resources' ? openCreateResourceModal() : openCreateCategoryModal()"
      >
        {{ activeTab === 'resources' ? '新建资源' : '新建分类' }}
      </button>
    </div>

    <div class="flex gap-1 mb-4 p-1 bg-gray-100 dark:bg-dark-200 rounded-lg w-fit">
      <button
        class="px-4 py-1.5 text-sm rounded-md transition-all"
        :class="activeTab === 'resources' 
          ? 'bg-white dark:bg-dark-400 text-gray-900 dark:text-white shadow-sm' 
          : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
        @click="activeTab = 'resources'"
      >
        资源
      </button>
      <button
        class="px-4 py-1.5 text-sm rounded-md transition-all"
        :class="activeTab === 'categories' 
          ? 'bg-white dark:bg-dark-400 text-gray-900 dark:text-white shadow-sm' 
          : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
        @click="activeTab = 'categories'"
      >
        分类
      </button>
    </div>

    <template v-if="isLoading && activeTab === 'resources'">
      <div class="flex justify-center py-16">
        <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    </template>

    <template v-else-if="activeTab === 'resources'">
      <div>
        <div
          v-if="resources.length === 0"
          class="text-center py-16 text-gray-500"
        >
          暂无资源，点击右上角按钮添加
        </div>

        <div
          v-else
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          <div
            v-for="resource in resources"
            :key="resource.id"
            class="glass-card p-4 flex flex-col min-h-[120px]"
            :class="resource.is_active ? '' : 'border-gray-300 dark:border-gray-600'"
          >
            <div class="flex items-center gap-2 mb-2">
              <div
                class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                :style="{ backgroundColor: getCategoryColor(resource.category_id) + '20' }"
              >
                <span
                  v-if="resource.icon"
                  class="text-base"
                >{{ resource.icon }}</span>
                <svg
                  v-else
                  class="w-4 h-4"
                  :style="{ color: getCategoryColor(resource.category_id) }"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                  />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="text-gray-900 dark:text-white font-medium text-sm truncate">
                  {{ resource.title }}
                </h3>
                <p class="text-gray-500 text-xs truncate">
                  {{ getCategoryName(resource.category_id) }}
                </p>
              </div>
            </div>
            
            <p
              class="text-gray-500 dark:text-gray-400 text-xs mb-2 flex-1 line-clamp-2"
            >
              {{ resource.description || '暂无描述' }}
            </p>
            
            <div class="flex items-center justify-between mt-auto pt-2 border-t border-gray-100 dark:border-dark-300">
              <button
                class="flex items-center gap-1.5 text-xs transition-colors"
                :class="resource.is_active ? 'text-green-500' : 'text-gray-400'"
                @click="handleToggleResourceStatus(resource)"
              >
                <span
                  class="w-2 h-2 rounded-full"
                  :class="resource.is_active ? 'bg-green-500' : 'bg-gray-400'"
                />
                {{ resource.is_active ? '已启用' : '已禁用' }}
              </button>
              <div class="flex gap-2">
                <button
                  class="text-primary hover:text-primary/80 text-xs"
                  @click="handleEditResource(resource)"
                >
                  编辑
                </button>
                <button
                  class="text-red-400 hover:text-red-300 text-xs"
                  @click="handleDeleteResource(resource)"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div
        v-if="categories.length === 0"
        class="text-center py-16 text-gray-500"
      >
        暂无分类，点击右上角按钮添加
      </div>

      <div
        v-else
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      >
        <div
          v-for="(category, index) in categories"
          :key="category.id"
          class="glass-card p-4 flex flex-col min-h-[120px]"
        >
          <div class="flex items-center gap-2 mb-2">
            <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <span
                v-if="category.icon"
                class="text-base"
              >{{ category.icon }}</span>
              <svg
                v-else
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
            <div class="flex-1 min-w-0">
              <h3 class="text-gray-900 dark:text-white font-medium text-sm truncate">
                {{ category.name }}
              </h3>
              <p class="text-gray-500 text-xs truncate">
                {{ category.slug }}
              </p>
            </div>
          </div>
          
          <p class="text-gray-500 dark:text-gray-400 text-xs mb-2 flex-1 line-clamp-2">
            {{ category.description || '暂无描述' }}
          </p>
          
          <div class="flex items-center justify-between mt-auto pt-2 border-t border-gray-100 dark:border-dark-300">
            <div class="flex items-center gap-2">
              <span class="text-gray-500 text-xs">{{ getResourceCount(category.id) }} 个资源</span>
              <div class="flex items-center gap-0.5">
                <button
                  class="p-1 text-gray-400 hover:text-primary disabled:opacity-30 transition-colors"
                  :disabled="index === 0"
                  @click="moveCategoryUp(index)"
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
                      d="M5 15l7-7 7 7"
                    />
                  </svg>
                </button>
                <button
                  class="p-1 text-gray-400 hover:text-primary disabled:opacity-30 transition-colors"
                  :disabled="index === categories.length - 1"
                  @click="moveCategoryDown(index)"
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
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
              </div>
            </div>
            <div class="flex gap-2">
              <button
                class="text-primary hover:text-primary/80 text-xs"
                @click="handleEditCategory(category)"
              >
                编辑
              </button>
              <button
                class="text-red-400 hover:text-red-300 text-xs"
                @click="handleDeleteCategory(category)"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div
      v-if="showResourceEditor"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    >
      <div class="glass-card w-full max-w-md m-4 p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-bold text-gray-900 dark:text-white">
            {{ editingResource ? '编辑资源' : '新建资源' }}
          </h2>
          <button
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
            @click="showResourceEditor = false; editingResource = null; resetResourceForm()"
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
          @submit.prevent="handleSubmitResource"
        >
          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">标题</label>
            <input
              v-model="resourceForm.title"
              type="text"
              required
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="资源标题"
            >
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">链接</label>
            <input
              v-model="resourceForm.url"
              type="url"
              required
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="https://example.com"
            >
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">描述</label>
            <textarea
              v-model="resourceForm.description"
              rows="2"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="资源描述"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">分类</label>
              <select
                v-model="resourceForm.category_id"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none"
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
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">图标</label>
              <IconPicker v-model="resourceForm.icon" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">排序</label>
              <input
                v-model.number="resourceForm.order"
                type="number"
                min="0"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              >
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">状态</label>
              <select
                v-model="resourceForm.is_active"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none"
              >
                <option :value="true">
                  启用
                </option>
                <option :value="false">
                  禁用
                </option>
              </select>
            </div>
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              :disabled="isSubmitting"
              @click="showResourceEditor = false; editingResource = null; resetResourceForm()"
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
      v-if="showCategoryEditor"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    >
      <div class="glass-card w-full max-w-md m-4 p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-bold text-gray-900 dark:text-white">
            {{ editingCategory ? '编辑分类' : '新建分类' }}
          </h2>
          <button
            class="text-gray-400 hover:text-gray-900 dark:hover:text-white"
            @click="showCategoryEditor = false; editingCategory = null; resetCategoryForm()"
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
          @submit.prevent="handleSubmitCategory"
        >
          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">名称</label>
            <input
              v-model="categoryForm.name"
              type="text"
              required
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="分类名称"
            >
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">Slug</label>
            <input
              v-model="categoryForm.slug"
              type="text"
              required
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="category-slug"
            >
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">描述</label>
            <textarea
              v-model="categoryForm.description"
              rows="2"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="分类描述"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">图标</label>
              <IconPicker v-model="categoryForm.icon" />
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">排序</label>
              <input
                v-model.number="categoryForm.order"
                type="number"
                min="0"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              >
            </div>
          </div>

          <div>
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                v-model="categoryForm.is_active"
                type="checkbox"
                class="rounded border-gray-300 dark:border-white/20 bg-white dark:bg-dark-100 text-primary focus:ring-primary"
              >
              <span class="text-gray-700 dark:text-gray-300 text-sm">启用</span>
            </label>
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              @click="showCategoryEditor = false; editingCategory = null; resetCategoryForm()"
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
