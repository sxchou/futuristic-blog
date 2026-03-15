<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { resourceApi } from '@/api'
import type { Resource } from '@/types'
import ModalDialog from '@/components/common/ModalDialog.vue'

interface DialogOptions {
  title?: string
  message: string
  type?: 'confirm' | 'alert' | 'success' | 'error'
}

const resources = ref<Resource[]>([])
const isLoading = ref(false)
const showEditor = ref(false)
const editingResource = ref<Resource | null>(null)

const dialogVisible = ref(false)
const dialogOptions = ref<DialogOptions>({
  message: ''
})
let dialogResolve: ((value: boolean) => void) | null = null

const showDialog = (options: DialogOptions): Promise<boolean> => {
  dialogOptions.value = { ...options }
  dialogVisible.value = true
  return new Promise((resolve) => {
    dialogResolve = resolve
  })
}

const onDialogConfirm = () => {
  dialogVisible.value = false
  if (dialogResolve) {
    dialogResolve(true)
    dialogResolve = null
  }
}

const onDialogCancel = () => {
  dialogVisible.value = false
  if (dialogResolve) {
    dialogResolve(false)
    dialogResolve = null
  }
}

const form = ref({
  title: '',
  description: '',
  url: '',
  icon: '',
  category: 'tool',
  is_active: true,
  order: 0
})

const categoryOptions = [
  { value: 'tool', label: '工具' },
  { value: 'framework', label: '框架' },
  { value: 'library', label: '库' },
  { value: 'resource', label: '资源' },
  { value: 'other', label: '其他' }
]

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

const handleEdit = (resource: Resource) => {
  editingResource.value = resource
  form.value = {
    title: resource.title,
    description: resource.description || '',
    url: resource.url,
    icon: resource.icon || '',
    category: resource.category,
    is_active: resource.is_active,
    order: resource.order
  }
  showEditor.value = true
}

const handleDelete = async (resource: Resource) => {
  const confirmed = await showDialog({
    title: '确认删除',
    message: `确定要删除资源"${resource.title}"吗？`,
    type: 'confirm'
  })
  if (!confirmed) return
  
  try {
    await resourceApi.deleteResource(resource.id)
    await fetchResources()
    await showDialog({ title: '成功', message: '资源已删除', type: 'success' })
  } catch (error: any) {
    console.error('Failed to delete resource:', error)
    if (error.response?.status === 403) {
      await showDialog({ title: '权限不足', message: '无权限删除此资源', type: 'error' })
    } else {
      await showDialog({ title: '错误', message: error.response?.data?.detail || '删除失败', type: 'error' })
    }
  }
}

const handleSubmit = async () => {
  try {
    if (editingResource.value) {
      await resourceApi.updateResource(editingResource.value.id, form.value)
    } else {
      await resourceApi.createResource(form.value)
    }
    showEditor.value = false
    editingResource.value = null
    resetForm()
    await fetchResources()
    await showDialog({ title: '成功', message: editingResource.value ? '资源已更新' : '资源已创建', type: 'success' })
  } catch (error: any) {
    console.error('Failed to save resource:', error)
    if (error.response?.status === 403) {
      await showDialog({ title: '权限不足', message: '无权限修改此资源', type: 'error' })
    } else {
      await showDialog({ title: '错误', message: error.response?.data?.detail || '保存失败', type: 'error' })
    }
  }
}

const resetForm = () => {
  form.value = {
    title: '',
    description: '',
    url: '',
    icon: '',
    category: 'tool',
    is_active: true,
    order: 0
  }
}

const getCategoryLabel = (category: string) => {
  const option = categoryOptions.find(o => o.value === category)
  return option ? option.label : category
}

onMounted(() => {
  fetchResources()
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold text-gray-900 dark:text-white">资源管理</h1>
      <button
        @click="showEditor = true; editingResource = null; resetForm()"
        class="px-4 py-1.5 bg-primary text-white rounded-lg text-sm hover:bg-primary/90 transition-colors"
      >
        添加资源
      </button>
    </div>

    <div v-if="isLoading" class="flex justify-center py-16">
      <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <div v-else class="glass-card overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50 dark:bg-dark-100">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">资源</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">分类</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">链接</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">状态</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">排序</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-white/10">
          <tr v-for="resource in resources" :key="resource.id" class="hover:bg-gray-50 dark:hover:bg-white/5">
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <div v-if="resource.icon" class="w-8 h-8 rounded bg-gray-100 dark:bg-dark-200 flex items-center justify-center text-lg">
                  {{ resource.icon }}
                </div>
                <div>
                  <p class="font-medium text-gray-900 dark:text-white text-sm">{{ resource.title }}</p>
                  <p v-if="resource.description" class="text-gray-500 text-xs truncate max-w-xs">{{ resource.description }}</p>
                </div>
              </div>
            </td>
            <td class="px-4 py-3">
              <span class="px-2 py-1 text-xs rounded bg-primary/10 text-primary">
                {{ getCategoryLabel(resource.category) }}
              </span>
            </td>
            <td class="px-4 py-3">
              <a :href="resource.url" target="_blank" class="text-primary text-sm hover:underline truncate max-w-xs block">
                {{ resource.url }}
              </a>
            </td>
            <td class="px-4 py-3">
              <span :class="resource.is_active ? 'text-green-500' : 'text-gray-400'" class="text-xs">
                {{ resource.is_active ? '启用' : '禁用' }}
              </span>
            </td>
            <td class="px-4 py-3 text-gray-500 text-sm">
              {{ resource.order }}
            </td>
            <td class="px-4 py-3 text-right">
              <button
                @click="handleEdit(resource)"
                class="text-primary hover:text-primary/80 text-sm mr-3"
              >
                编辑
              </button>
              <button
                @click="handleDelete(resource)"
                class="text-red-500 hover:text-red-400 text-sm"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="resources.length === 0" class="text-center py-12 text-gray-500">
        暂无资源
      </div>
    </div>

    <div v-if="showEditor" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white dark:bg-dark-100 rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div class="p-4 border-b border-gray-200 dark:border-white/10">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">
            {{ editingResource ? '编辑资源' : '添加资源' }}
          </h2>
        </div>

        <form @submit.prevent="handleSubmit" class="p-4 space-y-4">
          <div>
            <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">标题 *</label>
            <input
              v-model="form.title"
              type="text"
              required
              class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-200 text-gray-900 dark:text-white text-sm"
            />
          </div>

          <div>
            <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">链接 *</label>
            <input
              v-model="form.url"
              type="url"
              required
              class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-200 text-gray-900 dark:text-white text-sm"
            />
          </div>

          <div>
            <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">描述</label>
            <textarea
              v-model="form.description"
              rows="2"
              class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-200 text-gray-900 dark:text-white text-sm"
            />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">分类</label>
              <select
                v-model="form.category"
                class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-200 text-gray-900 dark:text-white text-sm"
              >
                <option v-for="opt in categoryOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">图标</label>
              <input
                v-model="form.icon"
                type="text"
                placeholder="emoji 或图标类名"
                class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-200 text-gray-900 dark:text-white text-sm"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">排序</label>
              <input
                v-model.number="form.order"
                type="number"
                min="0"
                class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-dark-200 text-gray-900 dark:text-white text-sm"
              />
            </div>

            <div class="flex items-center pt-6">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="form.is_active"
                  type="checkbox"
                  class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <span class="text-sm text-gray-600 dark:text-gray-400">启用</span>
              </label>
            </div>
          </div>

          <div class="flex justify-end gap-3 pt-4">
            <button
              type="button"
              @click="showEditor = false; editingResource = null; resetForm()"
              class="px-4 py-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-sm"
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

    <ModalDialog
      v-model="dialogVisible"
      :title="dialogOptions.title"
      :message="dialogOptions.message"
      :type="dialogOptions.type"
      @confirm="onDialogConfirm"
      @cancel="onDialogCancel"
    />
  </div>
</template>
