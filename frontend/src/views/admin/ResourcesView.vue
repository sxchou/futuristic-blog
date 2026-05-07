<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { resourceApi } from '@/api'
import type { Resource } from '@/types'
import type { ResourceCategory } from '@/api/resources'
import { useDialogStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'
import { useDeletionConfirm } from '@/composables/useDeletionConfirm'
import DeletionConfirmDialog from '@/components/common/DeletionConfirmDialog.vue'
import { 
  updateArrayItem, 
  addArrayItem, 
  removeArrayItem
} from '@/utils/reactiveUpdate'
import IconPicker from '@/components/common/IconPicker.vue'

const dialog = useDialogStore()
const resourceDeletion = useDeletionConfirm()
const { requirePermission } = useAdminCheck()

const resources = ref<Resource[]>([])
const categories = ref<ResourceCategory[]>([])
const isLoading = ref(false)
const isSubmitting = ref(false)

const showResourceEditor = ref(false)
const editingResource = ref<Resource | null>(null)

const resourceForm = ref({
  title: '',
  description: '',
  url: '',
  icon: '',
  category_id: null as number | null,
  is_active: true,
  order: 0
})

const titleChecking = ref(false)
const urlChecking = ref(false)
const titleExists = ref(false)
const urlExists = ref(false)

let titleCheckTimer: ReturnType<typeof setTimeout> | null = null
let urlCheckTimer: ReturnType<typeof setTimeout> | null = null

const checkTitleUnique = async (title: string) => {
  if (!title.trim()) {
    titleExists.value = false
    return
  }
  
  titleChecking.value = true
  try {
    const result = await resourceApi.checkUnique('title', title, editingResource.value?.id)
    titleExists.value = result.exists
    if (result.exists) {
      resourceErrors.value = resourceErrors.value.filter(e => e.field !== 'title')
      resourceErrors.value.push({ field: 'title', message: '资源标题已存在，请使用其他标题' })
    } else {
      resourceErrors.value = resourceErrors.value.filter(e => e.field !== 'title')
    }
  } catch (error) {
    console.error('Failed to check title uniqueness:', error)
  } finally {
    titleChecking.value = false
  }
}

const checkUrlUnique = async (url: string) => {
  if (!url.trim()) {
    urlExists.value = false
    return
  }
  
  urlChecking.value = true
  try {
    const result = await resourceApi.checkUnique('url', url, editingResource.value?.id)
    urlExists.value = result.exists
    if (result.exists) {
      resourceErrors.value = resourceErrors.value.filter(e => e.field !== 'url')
      resourceErrors.value.push({ field: 'url', message: '资源链接已存在，请使用其他链接' })
    } else {
      resourceErrors.value = resourceErrors.value.filter(e => e.field !== 'url')
    }
  } catch (error) {
    console.error('Failed to check url uniqueness:', error)
  } finally {
    urlChecking.value = false
  }
}

watch(() => resourceForm.value.title, (newTitle) => {
  if (titleCheckTimer) {
    clearTimeout(titleCheckTimer)
  }
  titleExists.value = false
  resourceErrors.value = resourceErrors.value.filter(e => e.field !== 'title')
  
  if (newTitle.trim()) {
    titleCheckTimer = setTimeout(() => {
      checkTitleUnique(newTitle)
    }, 500)
  }
})

watch(() => resourceForm.value.url, (newUrl) => {
  if (urlCheckTimer) {
    clearTimeout(urlCheckTimer)
  }
  urlExists.value = false
  resourceErrors.value = resourceErrors.value.filter(e => e.field !== 'url')
  
  if (newUrl.trim()) {
    urlCheckTimer = setTimeout(() => {
      checkUrlUnique(newUrl)
    }, 500)
  }
})

const fetchCategories = async () => {
  try {
    categories.value = await resourceApi.getCategories()
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
  if (!await requirePermission('resource.edit', '编辑资源')) return
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
  titleExists.value = false
  urlExists.value = false
  titleChecking.value = false
  urlChecking.value = false
  resourceErrors.value = []
  showResourceEditor.value = true
}

const handleDeleteResource = async (resource: Resource) => {
  if (!await requirePermission('resource.delete', '删除资源')) return
  
  const previewed = await resourceDeletion.requestDeletion('resource', resource.id, resource.title)
  if (!previewed) return
}

const resourceDeletionLoading = ref(false)
const executeResourceDeletion = async () => {
  try {
    resourceDeletionLoading.value = true
    await resourceApi.deleteResource(resourceDeletion.currentItemId.value)
    await removeArrayItem(resources, resourceDeletion.currentItemId.value)
    resourceDeletion.confirmDeletion()
    await dialog.showSuccess('资源已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete resource:', error)
    resourceDeletion.cancelDeletion()
  } finally {
    resourceDeletionLoading.value = false
  }
}

const handleToggleResourceStatus = async (resource: Resource) => {
  if (!await requirePermission('resource.edit', '切换资源状态')) return
  
  const previousStatus = resource.is_active
  
  try {
    await resourceApi.updateResource(resource.id, { is_active: !resource.is_active })
    const index = resources.value.findIndex(r => r.id === resource.id)
    if (index !== -1) {
      resources.value[index] = { ...resources.value[index], is_active: !previousStatus }
    }
    dialog.showSuccess(previousStatus ? '资源已禁用' : '资源已启用', '成功')
  } catch (error: any) {
    console.error('Failed to toggle resource status:', error)
    await dialog.showError(error.response?.data?.detail || '状态切换失败', '错误')
  }
}

const handleSubmitResource = async () => {
  if (!await requirePermission('resource.edit', '保存资源')) return
  
  const isValid = await validateResourceForm()
  if (!isValid) return
  
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
  resourceErrors.value = []
  titleChecking.value = false
  urlChecking.value = false
  titleExists.value = false
  urlExists.value = false
  if (titleCheckTimer) {
    clearTimeout(titleCheckTimer)
    titleCheckTimer = null
  }
  if (urlCheckTimer) {
    clearTimeout(urlCheckTimer)
    urlCheckTimer = null
  }
}

const openCreateResourceModal = async () => {
  if (!await requirePermission('resource.create', '创建资源')) return
  editingResource.value = null
  resetResourceForm()
  showResourceEditor.value = true
}

const activeCategories = computed(() => categories.value)

interface ValidationError {
  field: string
  message: string
}

const resourceErrors = ref<ValidationError[]>([])

const scrollToField = async (fieldId: string) => {
  await nextTick()
  const element = document.getElementById(fieldId)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    element.focus({ preventScroll: true })
  }
}

const hasResourceError = (field: string): boolean => {
  return resourceErrors.value.some(e => e.field === field)
}

const getResourceErrorMessage = (field: string): string => {
  const error = resourceErrors.value.find(e => e.field === field)
  return error?.message || ''
}

const validateResourceForm = async (): Promise<boolean> => {
  resourceErrors.value = []

  if (!resourceForm.value.title.trim()) {
    resourceErrors.value.push({ field: 'title', message: '请输入资源标题' })
  }

  if (titleChecking.value || urlChecking.value) {
    await new Promise(resolve => setTimeout(resolve, 600))
  }

  if (titleExists.value) {
    resourceErrors.value.push({ field: 'title', message: '资源标题已存在，请使用其他标题' })
  }

  if (!resourceForm.value.url.trim()) {
    resourceErrors.value.push({ field: 'url', message: '请输入资源链接' })
  } else {
    try {
      new URL(resourceForm.value.url)
    } catch {
      resourceErrors.value.push({ field: 'url', message: '请输入有效的URL地址' })
    }
  }

  if (urlExists.value) {
    resourceErrors.value.push({ field: 'url', message: '资源链接已存在，请使用其他链接' })
  }

  if (resourceErrors.value.length > 0) {
    const firstError = resourceErrors.value[0]
    const fieldIdMap: Record<string, string> = { title: 'resource-title', url: 'resource-url' }
    await scrollToField(fieldIdMap[firstError.field] || firstError.field)
    return false
  }

  return true
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
              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
            />
          </svg>
        </div>
        <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
          资源管理
        </h1>
      </div>
      <button
        class="btn-primary text-xs sm:text-sm px-3 sm:px-4 py-1.5 whitespace-nowrap"
        @click="openCreateResourceModal"
      >
        新建资源
      </button>
    </div>

    <template v-if="isLoading">
      <div class="flex justify-center py-16">
        <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    </template>

    <template v-else>
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
            <label for="resource-title" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              标题 <span class="text-red-500">*</span>
              <span v-if="titleChecking" class="ml-2 text-gray-400">检查中...</span>
            </label>
            <input id="resource-title"
              v-model="resourceForm.title"
              type="text"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              :class="hasResourceError('title') || titleExists ? 'border-red-500 dark:border-red-500' : titleChecking ? 'border-yellow-500 dark:border-yellow-500' : 'border-gray-200 dark:border-white/10'"
              placeholder="资源标题"
            >
            <p
              v-if="hasResourceError('title')"
              class="mt-1 text-xs text-red-500"
            >
              {{ getResourceErrorMessage('title') }}
            </p>
          </div>

          <div>
            <label for="resource-url" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              链接 <span class="text-red-500">*</span>
              <span v-if="urlChecking" class="ml-2 text-gray-400">检查中...</span>
            </label>
            <input id="resource-url"
              v-model="resourceForm.url"
              type="url"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              :class="hasResourceError('url') || urlExists ? 'border-red-500 dark:border-red-500' : urlChecking ? 'border-yellow-500 dark:border-yellow-500' : 'border-gray-200 dark:border-white/10'"
              placeholder="https://example.com"
            >
            <p
              v-if="hasResourceError('url')"
              class="mt-1 text-xs text-red-500"
            >
              {{ getResourceErrorMessage('url') }}
            </p>
          </div>

          <div>
            <label for="textarea-resourceForm-description" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">描述</label>
            <textarea id="textarea-resourceForm-description"
              v-model="resourceForm.description"
              rows="2"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none resize-none"
              placeholder="资源描述"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="select-resourceForm-category_id" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">分类</label>
              <select id="select-resourceForm-category_id"
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
              <label for="resource-icon-helper" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">图标</label>
              <input id="resource-icon-helper" type="text" class="sr-only" :value="resourceForm.icon" tabindex="-1" readonly autocomplete="off">
              <IconPicker v-model="resourceForm.icon" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="resource-sort-order" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">排序</label>
              <input id="resource-sort-order"
                v-model.number="resourceForm.order"
                type="number"
                min="0"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              >
            </div>

            <div>
              <label for="select-resourceForm-is_active" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">状态</label>
              <select id="select-resourceForm-is_active"
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

    <DeletionConfirmDialog
      :visible="resourceDeletion.showDeletionDialog.value"
      :preview="resourceDeletion.deletionPreview.value"
      :loading="resourceDeletionLoading"
      @confirm="executeResourceDeletion"
      @cancel="resourceDeletion.cancelDeletion()"
    />
  </div>
</template>
