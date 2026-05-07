<script setup lang="ts">
import { ref, watch, reactive } from 'vue'
import { deletionPreviewApi } from '@/api/deletionPreview'
import type { DeletionPreview, AssociatedItem, DetailItem } from '@/api/deletionPreview'

const props = defineProps<{
  visible: boolean
  preview: DeletionPreview | null
  loading: boolean
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const ACTION_STYLES: Record<string, { color: string; label: string }> = {
  delete: { color: 'text-red-400', label: '将被删除' },
  unlink: { color: 'text-amber-400', label: '将解除关联' },
  nullify: { color: 'text-yellow-400', label: '将置为空' },
  soft_delete: { color: 'text-orange-400', label: '将被软删除' },
  blocked: { color: 'text-red-400', label: '阻止删除' },
}

const getActionStyle = (action: string, canDelete: boolean = true) => {
  if (!canDelete && (action === 'unlink' || action === 'delete')) {
    return ACTION_STYLES.blocked
  }
  return ACTION_STYLES[action] || ACTION_STYLES.delete
}

const groupedItems = ref<Record<string, AssociatedItem[]>>({})

interface DetailState {
  loading: boolean
  expanded: boolean
  items: DetailItem[]
  total: number
  showing: number
  currentLimit: number
  error: boolean
}

const detailStates = reactive<Record<string, DetailState>>({})

const getDetailKey = (item: AssociatedItem) => `${item.type}-${item.name}`

const getDetailState = (item: AssociatedItem): DetailState => {
  const key = getDetailKey(item)
  if (!detailStates[key]) {
    detailStates[key] = {
      loading: false,
      expanded: false,
      items: [],
      total: 0,
      showing: 0,
      currentLimit: 5,
      error: false,
    }
  }
  return detailStates[key]
}

const toggleDetails = async (item: AssociatedItem) => {
  const state = getDetailState(item)
  if (state.expanded) {
    state.expanded = false
    return
  }

  state.expanded = true
  state.currentLimit = 5
  await fetchDetails(item, 5)
}

const fetchDetails = async (item: AssociatedItem, limit: number) => {
  if (!props.preview) return

  const state = getDetailState(item)
  state.loading = true
  state.error = false
  state.currentLimit = limit

  try {
    const response = await deletionPreviewApi.details(
      props.preview.item_type,
      props.preview.item_id,
      item.type,
      item.name,
      limit
    )
    state.items = response.items
    state.total = response.total
    state.showing = response.showing
  } catch {
    state.items = []
    state.total = 0
    state.showing = 0
    state.error = true
  } finally {
    state.loading = false
  }
}

const loadMore = (item: AssociatedItem, limit: number) => {
  fetchDetails(item, limit)
}

watch(() => props.preview, (preview) => {
  if (!preview) {
    groupedItems.value = {}
    Object.keys(detailStates).forEach(key => delete detailStates[key])
    return
  }
  const groups: Record<string, AssociatedItem[]> = {}
  for (const item of preview.associated_items) {
    const key = item.action
    if (!groups[key]) groups[key] = []
    groups[key].push(item)
  }
  const ordered: Record<string, AssociatedItem[]> = {}
  for (const action of ['delete', 'soft_delete', 'unlink', 'nullify']) {
    if (groups[action]) ordered[action] = groups[action]
  }
  groupedItems.value = ordered
  Object.keys(detailStates).forEach(key => delete detailStates[key])
}, { immediate: true })

const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  emit('cancel')
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="visible"
        class="fixed inset-0 z-[9999] flex items-center justify-center"
      >
        <div
          class="absolute inset-0 bg-black/60 backdrop-blur-sm"
          @click="handleCancel"
        />
        <Transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="visible"
            class="relative bg-white dark:bg-gray-900 border border-gray-200 dark:border-white/10 rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden"
          >
            <div class="p-6">
              <div class="flex items-start gap-4">
                <div class="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-red-50 dark:bg-red-500/10">
                  <svg
                    class="w-6 h-6 text-red-500 dark:text-red-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                    确认删除{{ preview?.item_type_label }}
                  </h3>
                  <p class="text-gray-600 dark:text-gray-300 text-sm">
                    您即将删除 <span class="text-gray-900 dark:text-white font-medium">{{ preview?.item_name }}</span>
                  </p>
                </div>
              </div>

              <div
                v-if="preview && !preview.can_delete"
                class="mt-4 p-3 rounded-lg bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20"
              >
                <div class="flex items-start gap-2">
                  <svg class="w-5 h-5 text-red-500 dark:text-red-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                  </svg>
                  <p class="text-red-700 dark:text-red-300 text-sm">{{ preview.block_reason }}</p>
                </div>
              </div>

              <div
                v-if="preview && preview.associated_items.length > 0"
                class="mt-4"
              >
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-3">
                  {{ preview.can_delete ? `以下关联数据将受到影响（共 ${preview.total_affected} 项）：` : '以下数据阻止了删除操作：' }}
                </p>
                <div class="space-y-3 max-h-80 overflow-y-auto custom-scrollbar">
                  <template v-for="(items, action) in groupedItems" :key="action">
                    <div
                      v-for="item in items"
                      :key="`${item.type}-${item.name}`"
                      class="rounded-lg bg-gray-50 dark:bg-gray-800/50 overflow-hidden"
                    >
                      <div class="flex items-start gap-3 p-2.5">
                        <div
                          :class="[
                            'flex-shrink-0 w-2 h-2 rounded-full mt-1.5',
                            item.action === 'delete' ? 'bg-red-500' :
                            item.action === 'unlink' ? 'bg-amber-500' :
                            item.action === 'soft_delete' ? 'bg-orange-500' : 'bg-yellow-500'
                          ]"
                        />
                        <div class="flex-1 min-w-0">
                          <div class="flex items-center gap-2">
                            <span class="text-sm text-gray-900 dark:text-white font-medium">{{ item.name }}</span>
                            <span
                              :class="['text-xs px-1.5 py-0.5 rounded', getActionStyle(item.action, preview?.can_delete ?? true).color, 'bg-current/10']"
                              :style="{ backgroundColor: 'transparent' }"
                            >
                              {{ getActionStyle(item.action, preview?.can_delete ?? true).label }}
                            </span>
                          </div>
                          <p v-if="item.detail" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ item.detail }}</p>
                        </div>
                        <div class="flex items-center gap-2 flex-shrink-0">
                          <span
                            v-if="item.count > 1"
                            class="text-xs text-gray-500 dark:text-gray-400 bg-gray-200 dark:bg-gray-700/50 px-1.5 py-0.5 rounded"
                          >
                            ×{{ item.count }}
                          </span>
                          <button
                            v-if="item.count > 0"
                            class="text-xs text-blue-500 dark:text-blue-400 hover:text-blue-600 dark:hover:text-blue-300 transition-colors p-1 rounded hover:bg-blue-50 dark:hover:bg-blue-400/10"
                            :title="getDetailState(item).expanded ? '收起明细' : '查看明细'"
                            @click="toggleDetails(item)"
                          >
                            <svg
                              class="w-3.5 h-3.5 transition-transform duration-200"
                              :class="{ 'rotate-180': getDetailState(item).expanded }"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                            </svg>
                          </button>
                        </div>
                      </div>

                      <Transition
                        enter-active-class="transition ease-out duration-200"
                        enter-from-class="opacity-0 max-h-0"
                        enter-to-class="opacity-100 max-h-96"
                        leave-active-class="transition ease-in duration-150"
                        leave-from-class="opacity-100 max-h-96"
                        leave-to-class="opacity-0 max-h-0"
                      >
                        <div
                          v-if="getDetailState(item).expanded"
                          class="border-t border-gray-200 dark:border-white/5"
                        >
                          <div v-if="getDetailState(item).loading" class="flex items-center justify-center py-3">
                            <svg class="animate-spin w-4 h-4 text-blue-500 dark:text-blue-400" fill="none" viewBox="0 0 24 24">
                              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            <span class="ml-2 text-xs text-gray-500 dark:text-gray-400">加载中...</span>
                          </div>
                          <div v-else-if="getDetailState(item).error" class="py-2 px-3">
                            <span class="text-xs text-gray-500 dark:text-gray-400">加载失败，请重试</span>
                          </div>
                          <div v-else-if="getDetailState(item).items.length === 0" class="py-2 px-3">
                            <span class="text-xs text-gray-500 dark:text-gray-400">无明细</span>
                          </div>
                          <div v-else class="py-1.5 px-3">
                            <div
                              v-for="(detail, idx) in getDetailState(item).items"
                              :key="idx"
                              class="flex items-center gap-2 py-1.5 border-b border-gray-200 dark:border-white/5 last:border-0"
                            >
                              <div class="w-1 h-1 rounded-full bg-gray-400 dark:bg-gray-500 flex-shrink-0" />
                              <span class="text-xs text-gray-600 dark:text-gray-300 truncate flex-1">{{ detail.name }}</span>
                              <span v-if="detail.detail" class="text-xs text-gray-500 truncate max-w-[40%]">{{ detail.detail }}</span>
                            </div>

                            <div
                              v-if="getDetailState(item).total > getDetailState(item).showing"
                              class="flex items-center gap-2 pt-2 pb-1"
                            >
                              <span class="text-xs text-gray-500 dark:text-gray-400">
                                已显示 {{ getDetailState(item).showing }} / {{ getDetailState(item).total }} 项
                              </span>
                              <div class="flex items-center gap-1">
                                <button
                                  v-if="getDetailState(item).currentLimit < 5"
                                  class="text-xs text-blue-500 dark:text-blue-400 hover:text-blue-600 dark:hover:text-blue-300 px-1.5 py-0.5 rounded hover:bg-blue-50 dark:hover:bg-blue-400/10 transition-colors"
                                  @click="loadMore(item, 5)"
                                >
                                  前5项
                                </button>
                                <button
                                  v-if="getDetailState(item).currentLimit !== 10 && getDetailState(item).total > 5"
                                  class="text-xs text-blue-500 dark:text-blue-400 hover:text-blue-600 dark:hover:text-blue-300 px-1.5 py-0.5 rounded hover:bg-blue-50 dark:hover:bg-blue-400/10 transition-colors"
                                  @click="loadMore(item, 10)"
                                >
                                  前10项
                                </button>
                                <button
                                  v-if="getDetailState(item).total > 10"
                                  class="text-xs text-blue-500 dark:text-blue-400 hover:text-blue-600 dark:hover:text-blue-300 px-1.5 py-0.5 rounded hover:bg-blue-50 dark:hover:bg-blue-400/10 transition-colors"
                                  @click="loadMore(item, 0)"
                                >
                                  显示全部
                                </button>
                              </div>
                            </div>

                            <div
                              v-if="getDetailState(item).total <= getDetailState(item).showing && getDetailState(item).total > 0"
                              class="pt-1 pb-0.5"
                            >
                              <span class="text-xs text-gray-500 dark:text-gray-400">共 {{ getDetailState(item).total }} 项</span>
                            </div>
                          </div>
                        </div>
                      </Transition>
                    </div>
                  </template>
                </div>
              </div>

              <div
                v-if="preview?.can_delete && !preview?.associated_items?.length"
                class="mt-4 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50"
              >
                <p class="text-sm text-gray-500 dark:text-gray-400">此操作没有关联数据受影响，删除后无法恢复。</p>
              </div>
            </div>

            <div class="flex border-t border-gray-200 dark:border-white/10">
              <button
                type="button"
                class="flex-1 px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                :disabled="loading"
                @click="handleCancel"
              >
                取消
              </button>
              <button
                v-if="preview?.can_delete"
                type="button"
                class="flex-1 px-4 py-3 text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors disabled:opacity-50"
                :disabled="loading"
                @click="handleConfirm"
              >
                <span v-if="loading" class="flex items-center justify-center gap-2">
                  <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  删除中...
                </span>
                <span v-else>确认删除</span>
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
  border-radius: 2px;
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.25);
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
