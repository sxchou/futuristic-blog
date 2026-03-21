<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { tagApi } from '@/api'
import type { Tag } from '@/types'
import { useDialogStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'

const dialog = useDialogStore()
const { requireAdmin } = useAdminCheck()

const tags = ref<Tag[]>([])
const isLoading = ref(false)
const showEditor = ref(false)
const editingTag = ref<Tag | null>(null)

const form = ref({
  name: '',
  slug: '',
  color: '#00d4ff'
})

const fetchTags = async () => {
  isLoading.value = true
  try {
    tags.value = await tagApi.getTags()
  } catch (error) {
    console.error('Failed to fetch tags:', error)
  } finally {
    isLoading.value = false
  }
}

const handleEdit = async (tag: Tag) => {
  if (!await requireAdmin('编辑标签')) return
  editingTag.value = tag
  form.value = {
    name: tag.name,
    slug: tag.slug,
    color: tag.color
  }
  showEditor.value = true
}

const handleDelete = async (tag: Tag) => {
  if (!await requireAdmin('删除标签')) return
  
  const confirmed = await dialog.showConfirm({
    title: '确认删除',
    message: `确定要删除标签"${tag.name}"吗？`
  })
  if (!confirmed) return
  
  try {
    await tagApi.deleteTag(tag.id)
    await fetchTags()
    await dialog.showSuccess('标签已删除', '成功')
  } catch (error: any) {
    console.error('Failed to delete tag:', error)
    await dialog.showError(error.response?.data?.detail || '删除失败', '错误')
  }
}

const handleSubmit = async () => {
  if (!await requireAdmin('保存标签')) return
  
  try {
    const isEditing = !!editingTag.value
    if (editingTag.value) {
      await tagApi.updateTag(editingTag.value.id, form.value)
    } else {
      await tagApi.createTag(form.value)
    }
    showEditor.value = false
    editingTag.value = null
    resetForm()
    await fetchTags()
    await dialog.showSuccess(isEditing ? '标签已更新' : '标签已创建', '成功')
  } catch (error: any) {
    console.error('Failed to save tag:', error)
    await dialog.showError(error.response?.data?.detail || '保存失败', '错误')
  }
}

const resetForm = () => {
  form.value = {
    name: '',
    slug: '',
    color: '#00d4ff'
  }
}

const openCreateModal = async () => {
  if (!await requireAdmin('创建标签')) return
  editingTag.value = null
  resetForm()
  showEditor.value = true
}

onMounted(fetchTags)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">标签管理</h1>
      <button
        @click="openCreateModal"
        class="btn-primary text-sm px-4 py-1.5"
      >
        新建标签
      </button>
    </div>

    <div v-if="isLoading" class="flex justify-center py-16">
      <div class="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <div v-else class="flex flex-wrap gap-3">
      <div
        v-for="tag in tags"
        :key="tag.id"
        class="glass-card p-3 flex items-center gap-3"
      >
        <div
          class="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold"
          :style="{ backgroundColor: tag.color }"
        >
          {{ tag.name.charAt(0) }}
        </div>
        <div>
          <h3 class="text-gray-900 dark:text-white font-medium text-sm">{{ tag.name }}</h3>
          <p class="text-gray-500 text-xs">{{ tag.article_count }} 篇文章</p>
        </div>
        <div class="flex gap-2 ml-2">
          <button
            @click="handleEdit(tag)"
            class="text-primary hover:text-primary/80 text-xs"
          >
            编辑
          </button>
          <button
            @click="handleDelete(tag)"
            class="text-red-400 hover:text-red-300 text-xs"
          >
            删除
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showEditor"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    >
      <div class="glass-card w-full max-w-sm m-4 p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-bold text-gray-900 dark:text-white">
            {{ editingTag ? '编辑标签' : '新建标签' }}
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
            <label for="tag-name" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">名称</label>
            <input
              v-model="form.name"
              type="text"
              id="tag-name"
              name="name"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="标签名称"
            />
          </div>

          <div>
            <label for="tag-slug" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">Slug</label>
            <input
              v-model="form.slug"
              type="text"
              id="tag-slug"
              name="slug"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary focus:outline-none"
              placeholder="url-slug"
            />
          </div>

          <div>
            <label for="tag-color" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">颜色</label>
            <div class="flex gap-2">
              <input
                v-model="form.color"
                type="color"
                id="tag-color"
                name="color"
                class="w-10 h-10 rounded-lg cursor-pointer"
              />
              <input
                v-model="form.color"
                type="text"
                id="tag-color-text"
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
