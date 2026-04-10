<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { profileApi } from '@/api'
import type { Profile, TechStackItem, JourneyItem, Education } from '@/types'
import { useDialogStore } from '@/stores'
import { useAdminCheck } from '@/composables/useAdminCheck'

const dialog = useDialogStore()
const { requireAdmin } = useAdminCheck()
const profile = ref<Profile | null>(null)
const isLoading = ref(false)
const activeTab = ref('basic')

const tabs = [
  { key: 'basic', label: '基本信息' },
  { key: 'tech', label: '技术栈' },
  { key: 'journey', label: '职业经历' },
  { key: 'education', label: '教育背景' },
  { key: 'exploration', label: '探索方向' },
  { key: 'social', label: '社交链接' }
]

const form = ref({
  name: '',
  alias: '',
  slogan: '',
  tags: [] as string[],
  avatar: '',
  bio: '',
  tech_stack: [] as TechStackItem[],
  journey: [] as JourneyItem[],
  education: undefined as Education | undefined,
  exploration_areas: [] as string[],
  social_github: '',
  social_blog: '',
  social_email: ''
})

const newTag = ref('')
const newExplorationArea = ref('')
const newTechCategory = ref('')
const newTechItems = ref('')

const fetchProfile = async () => {
  isLoading.value = true
  try {
    profile.value = await profileApi.getProfile()
    form.value = {
      name: profile.value.name,
      alias: profile.value.alias || '',
      slogan: profile.value.slogan || '',
      tags: profile.value.tags || [],
      avatar: profile.value.avatar || '',
      bio: profile.value.bio || '',
      tech_stack: profile.value.tech_stack || [],
      journey: profile.value.journey || [],
      education: profile.value.education || undefined,
      exploration_areas: profile.value.exploration_areas || [],
      social_github: profile.value.social_github || '',
      social_blog: profile.value.social_blog || '',
      social_email: profile.value.social_email || ''
    }
  } catch (error) {
    console.error('Failed to fetch profile:', error)
  } finally {
    isLoading.value = false
  }
}

const handleSave = async () => {
  if (!await requireAdmin('保存个人资料')) return
  
  try {
    await profileApi.updateProfile(form.value)
    await dialog.showSuccess('保存成功', '成功')
    await fetchProfile()
  } catch (error: any) {
    await dialog.showError(error.response?.data?.detail || '保存失败', '错误')
  }
}

const addTag = async () => {
  if (!await requireAdmin('添加标签')) return
  if (newTag.value.trim()) {
    form.value.tags.push(newTag.value.trim())
    newTag.value = ''
  }
}

const removeTag = async (index: number) => {
  if (!await requireAdmin('删除标签')) return
  form.value.tags.splice(index, 1)
}

const addExplorationArea = async () => {
  if (!await requireAdmin('添加探索方向')) return
  if (newExplorationArea.value.trim()) {
    form.value.exploration_areas.push(newExplorationArea.value.trim())
    newExplorationArea.value = ''
  }
}

const removeExplorationArea = async (index: number) => {
  if (!await requireAdmin('删除探索方向')) return
  form.value.exploration_areas.splice(index, 1)
}

const addTechCategory = async () => {
  if (!await requireAdmin('添加技术分类')) return
  if (newTechCategory.value.trim() && newTechItems.value.trim()) {
    form.value.tech_stack.push({
      category: newTechCategory.value.trim(),
      items: newTechItems.value.split(',').map(s => s.trim()).filter(s => s)
    })
    newTechCategory.value = ''
    newTechItems.value = ''
  }
}

const removeTechCategory = async (index: number) => {
  if (!await requireAdmin('删除技术分类')) return
  form.value.tech_stack.splice(index, 1)
}

const addJourney = async () => {
  if (!await requireAdmin('添加职业经历')) return
  form.value.journey.push({
    period: '',
    company: '',
    position: '',
    achievements: ''
  })
}

const removeJourney = async (index: number) => {
  if (!await requireAdmin('删除职业经历')) return
  form.value.journey.splice(index, 1)
}

const initEducation = async () => {
  if (!await requireAdmin('添加教育背景')) return
  if (!form.value.education) {
    form.value.education = {
      period: '',
      school: '',
      major: '',
      degree: ''
    }
  }
}

onMounted(() => {
  fetchProfile()
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4 gap-2">
      <h1 class="text-base sm:text-xl font-bold text-gray-900 dark:text-white">
        个人资料管理
      </h1>
      <button
        class="btn-primary text-xs sm:text-sm px-3 sm:px-4 py-1.5 whitespace-nowrap"
        @click="handleSave"
      >
        保存更改
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
      <div class="flex border-b border-gray-200 dark:border-white/10">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="[
            'px-4 py-3 text-sm font-medium transition-colors',
            activeTab === tab.key
              ? 'text-primary border-b-2 border-primary'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          ]"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="p-6">
        <div
          v-if="activeTab === 'basic'"
          class="space-y-4"
        >
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label
                for="profile-name"
                class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >姓名</label>
              <input
                id="profile-name"
                v-model="form.name"
                type="text"
                name="name"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none"
              >
            </div>
            <div>
              <label
                for="profile-alias"
                class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >别名</label>
              <input
                id="profile-alias"
                v-model="form.alias"
                type="text"
                name="alias"
                class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none"
              >
            </div>
          </div>

          <div>
            <label
              for="profile-slogan"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >标语</label>
            <input
              id="profile-slogan"
              v-model="form.slogan"
              type="text"
              name="slogan"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none"
            >
          </div>

          <div>
            <label
              for="profile-avatar"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >头像 URL</label>
            <input
              id="profile-avatar"
              v-model="form.avatar"
              type="text"
              name="avatar"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none"
            >
          </div>

          <div>
            <label
              for="profile-new-tag"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >标签</label>
            <div class="flex flex-wrap gap-2 mb-2">
              <span
                v-for="(tag, index) in form.tags"
                :key="index"
                class="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full flex items-center gap-1"
              >
                {{ tag }}
                <button
                  class="hover:text-red-400"
                  @click="removeTag(index)"
                >×</button>
              </span>
            </div>
            <div class="flex gap-2">
              <input
                id="profile-new-tag"
                v-model="newTag"
                type="text"
                name="new-tag"
                class="flex-1 px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none"
                placeholder="输入标签"
                @keyup.enter="addTag"
              >
              <button
                class="px-3 py-2 bg-primary text-white text-sm rounded-lg"
                @click="addTag"
              >
                添加
              </button>
            </div>
          </div>

          <div>
            <label
              for="profile-bio"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >个人简介</label>
            <textarea
              id="profile-bio"
              v-model="form.bio"
              name="bio"
              rows="4"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none resize-none"
            />
          </div>
        </div>

        <div
          v-if="activeTab === 'tech'"
          class="space-y-4"
        >
          <div
            v-for="(tech, index) in form.tech_stack"
            :key="index"
            class="p-4 bg-gray-50 dark:bg-dark-100 rounded-lg"
          >
            <div class="flex items-center justify-between mb-2">
              <input
                v-model="tech.category"
                type="text"
                class="px-2 py-1 text-sm bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white focus:border-primary focus:outline-none"
                placeholder="分类名称"
              >
              <button
                class="text-red-400 hover:text-red-300 text-sm"
                @click="removeTechCategory(index)"
              >
                删除
              </button>
            </div>
            <input
              v-model="tech.items"
              type="text"
              class="w-full px-2 py-1 text-sm bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white focus:border-primary focus:outline-none"
              placeholder="技术项（逗号分隔）"
            >
          </div>

          <div class="p-4 border border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
            <div class="grid grid-cols-2 gap-2 mb-2">
              <input
                v-model="newTechCategory"
                type="text"
                class="px-2 py-1 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white focus:border-primary focus:outline-none"
                placeholder="分类名称"
              >
              <input
                v-model="newTechItems"
                type="text"
                class="px-2 py-1 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white focus:border-primary focus:outline-none"
                placeholder="技术项（逗号分隔）"
              >
            </div>
            <button
              class="w-full py-2 text-sm text-primary border border-primary/30 rounded-lg hover:bg-primary/10"
              @click="addTechCategory"
            >
              + 添加技术分类
            </button>
          </div>
        </div>

        <div
          v-if="activeTab === 'journey'"
          class="space-y-4"
        >
          <div
            v-for="(item, index) in form.journey"
            :key="index"
            class="p-4 bg-gray-50 dark:bg-dark-100 rounded-lg space-y-2"
          >
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">经历 {{ index + 1 }}</span>
              <button
                class="text-red-400 hover:text-red-300 text-sm"
                @click="removeJourney(index)"
              >
                删除
              </button>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <input
                v-model="item.period"
                type="text"
                class="px-2 py-1 text-sm bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white focus:border-primary focus:outline-none"
                placeholder="时间段"
              >
              <input
                v-model="item.company"
                type="text"
                class="px-2 py-1 text-sm bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white focus:border-primary focus:outline-none"
                placeholder="公司"
              >
            </div>
            <input
              v-model="item.position"
              type="text"
              class="w-full px-2 py-1 text-sm bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white focus:border-primary focus:outline-none"
              placeholder="职位"
            >
            <textarea
              v-model="item.achievements"
              rows="2"
              class="w-full px-2 py-1 text-sm bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white focus:border-primary focus:outline-none resize-none"
              placeholder="主要成就"
            />
          </div>

          <button
            class="w-full py-2 text-sm text-primary border border-primary/30 rounded-lg hover:bg-primary/10"
            @click="addJourney"
          >
            + 添加职业经历
          </button>
        </div>

        <div
          v-if="activeTab === 'education'"
          class="space-y-4"
        >
          <div
            v-if="form.education"
            class="p-4 bg-gray-50 dark:bg-dark-100 rounded-lg space-y-2"
          >
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label
                  for="edu-period"
                  class="block text-xs text-gray-500 mb-1"
                >时间段</label>
                <input
                  id="edu-period"
                  v-model="form.education.period"
                  type="text"
                  name="period"
                  class="w-full px-2 py-1 text-sm bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white focus:border-primary focus:outline-none"
                >
              </div>
              <div>
                <label
                  for="edu-school"
                  class="block text-xs text-gray-500 mb-1"
                >学校</label>
                <input
                  id="edu-school"
                  v-model="form.education.school"
                  type="text"
                  name="school"
                  class="w-full px-2 py-1 text-sm bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white focus:border-primary focus:outline-none"
                >
              </div>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label
                  for="edu-major"
                  class="block text-xs text-gray-500 mb-1"
                >专业</label>
                <input
                  id="edu-major"
                  v-model="form.education.major"
                  type="text"
                  name="major"
                  class="w-full px-2 py-1 text-sm bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white focus:border-primary focus:outline-none"
                >
              </div>
              <div>
                <label
                  for="edu-degree"
                  class="block text-xs text-gray-500 mb-1"
                >学位</label>
                <input
                  id="edu-degree"
                  v-model="form.education.degree"
                  type="text"
                  name="degree"
                  class="w-full px-2 py-1 text-sm bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded text-gray-900 dark:text-white focus:border-primary focus:outline-none"
                >
              </div>
            </div>
          </div>
          <button
            v-else
            class="w-full py-2 text-sm text-primary border border-primary/30 rounded-lg hover:bg-primary/10"
            @click="initEducation"
          >
            + 添加教育背景
          </button>
        </div>

        <div
          v-if="activeTab === 'exploration'"
          class="space-y-4"
        >
          <div class="flex flex-wrap gap-2">
            <span
              v-for="(area, index) in form.exploration_areas"
              :key="index"
              class="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full flex items-center gap-2"
            >
              {{ area }}
              <button
                class="hover:text-red-400"
                @click="removeExplorationArea(index)"
              >×</button>
            </span>
          </div>
          <div class="flex gap-2">
            <label
              for="profile-new-exploration"
              class="sr-only"
            >探索方向</label>
            <input
              id="profile-new-exploration"
              v-model="newExplorationArea"
              type="text"
              name="new-exploration"
              class="flex-1 px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none"
              placeholder="输入探索方向"
              @keyup.enter="addExplorationArea"
            >
            <button
              class="px-3 py-2 bg-primary text-white text-sm rounded-lg"
              @click="addExplorationArea"
            >
              添加
            </button>
          </div>
        </div>

        <div
          v-if="activeTab === 'social'"
          class="space-y-4"
        >
          <div>
            <label
              for="profile-github"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >GitHub</label>
            <input
              id="profile-github"
              v-model="form.social_github"
              type="text"
              name="github"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none"
              placeholder="https://github.com/username"
            >
          </div>
          <div>
            <label
              for="profile-blog"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >博客</label>
            <input
              id="profile-blog"
              v-model="form.social_blog"
              type="text"
              name="blog"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none"
              placeholder="https://your-blog.com"
            >
          </div>
          <div>
            <label
              for="profile-email"
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >邮箱</label>
            <input
              id="profile-email"
              v-model="form.social_email"
              type="email"
              name="email"
              autocomplete="email"
              class="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-primary focus:outline-none"
              placeholder="your@email.com"
            >
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
