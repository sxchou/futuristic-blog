<template>
  <div 
    :id="`comment-${comment.id}`"
    class="comment-item bg-gray-100 dark:bg-dark-100/30 border border-gray-200 dark:border-white/5 rounded-lg p-4 transition-all duration-300"
  >
    <div class="flex gap-3">
      <div 
        class="avatar w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0 overflow-hidden"
        :style="avatarStyle"
      >
        <span v-if="showAvatarInitial">{{ avatarText }}</span>
      </div>
      
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-2">
          <span class="font-medium text-gray-900 dark:text-white">{{ comment.author_name || '匿名用户' }}</span>
          <span class="text-xs text-gray-500">{{ formatDate(comment.created_at) }}</span>
          <span 
            v-if="comment.status === 'pending'" 
            class="text-xs px-2 py-0.5 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400"
          >
            待审核
          </span>
          <span 
            v-if="comment.status === 'rejected'" 
            class="text-xs px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
          >
            审核不通过
          </span>
        </div>
        
        <div
          v-if="comment.is_deleted"
          class="text-gray-400 dark:text-gray-500 text-sm italic mb-3 line-through"
        >
          {{ comment.deleted_by === 'admin' ? '此评论已被管理员删除' : '此评论已被用户删除' }}
        </div>
        <div
          v-else-if="comment.status === 'pending'"
          class="text-yellow-600 dark:text-yellow-400 text-sm italic mb-3"
        >
          评论待审核，审核通过后显示评论内容
        </div>
        <div
          v-else-if="comment.status === 'rejected'"
          class="text-red-500 dark:text-red-400 text-sm italic mb-3"
        >
          审核不通过
        </div>
        <div
          v-else
          class="text-gray-600 dark:text-gray-300 text-sm leading-relaxed mb-3 comment-content"
        >
          <div
            v-if="comment.reply_to_user_name"
            class="mb-1"
          >
            <span class="text-primary font-medium">@{{ comment.reply_to_user_name }}</span>
          </div>
          <div 
            ref="contentRef"
            class="relative"
            :class="{ 'max-h-[240px] overflow-hidden': !isExpanded && shouldShowExpand }"
          >
            <CommentMarkdownPreview :content="comment.content" />
            <div 
              v-if="!isExpanded && shouldShowExpand" 
              class="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-gray-100 dark:from-dark-100/30 to-transparent pointer-events-none"
            />
          </div>
          <button
            v-if="shouldShowExpand"
            class="mt-1 text-xs text-primary hover:text-primary/80 transition-colors flex items-center gap-1"
            @click="toggleExpand"
          >
            <svg 
              class="w-4 h-4 transition-transform duration-200" 
              :class="{ 'rotate-180': isExpanded }"
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
            {{ isExpanded ? '收起' : '展开全文' }}
          </button>
        </div>
        
        <div
          v-if="!comment.is_deleted && comment.status === 'approved'"
          class="flex items-center gap-4 text-xs"
        >
          <button
            v-if="authStore.isAuthenticated"
            class="text-gray-500 hover:text-primary transition-colors flex items-center gap-1"
            @click="showReplyForm = !showReplyForm"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
              />
            </svg>
            回复
          </button>
          
          <button
            v-if="canDelete"
            class="text-gray-500 hover:text-red-500 transition-colors flex items-center gap-1"
            @click="$emit('delete', comment.id)"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
            删除
          </button>
        </div>
        
        <div
          v-if="showReplyForm"
          class="mt-3"
        >
          <div class="bg-gray-200 dark:bg-dark-100/50 border border-gray-300 dark:border-white/10 rounded-lg p-3">
            <CommentEditor
              ref="replyEditorRef"
              v-model="replyContent"
              placeholder="写下你的回复...&#10;支持 **粗体**、*斜体*、`代码` 等"
              :reply-to="comment.author_name"
              :reply-to-content="comment.content"
              :disabled="submittingReply"
              :rows="3"
              :storage-key="`reply-${comment.id}`"
              :editor-id="`reply-${comment.id}`"
              @submit="submitReply"
            />
            <div class="flex justify-end gap-2 mt-2">
              <button
                class="px-3 py-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                @click="showReplyForm = false"
              >
                取消
              </button>
              <button
                :disabled="!replyContent.trim() || submittingReply"
                class="px-3 py-1 text-xs bg-primary text-white rounded hover:bg-primary/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                @click="submitReply"
              >
                {{ submittingReply ? '发送中...' : '发送' }}
              </button>
            </div>
          </div>
        </div>
        
        <div
          v-if="hasReplies || (isRootComment && totalReplyCount > 0)"
          class="mt-4"
        >
          <div
            v-if="displayedReplies.length > 0"
            :class="[
              'space-y-3',
              isDeeplyNested 
                ? 'bg-gray-50/50 dark:bg-white/[0.02] rounded-md px-2 py-1' 
                : 'pl-4 border-l-2 border-gray-300 dark:border-white/10'
            ]"
          >
            <CommentItem
              v-for="reply in (isDeeplyNested ? flattenedDeepReplies : displayedReplies)"
              :key="reply.id"
              :comment="reply"
              :article-id="articleId"
              :depth="isDeeplyNested ? MAX_DEPTH : depth + 1"
              :expand-target-id="expandTargetId"
              :root-comment-id="props.rootCommentId || (isRootComment ? props.comment.id : undefined)"
              @reply="$emit('reply', $event)"
              @delete="$emit('delete', $event)"
              @load-replies="$emit('loadReplies', $event)"
            />
          </div>

          <div
            v-if="isRootComment && totalReplyCount > 0"
            class="mt-3 pl-4"
          >
            <button
              class="text-xs text-primary hover:text-primary/80 transition-colors flex items-center gap-1.5 group"
              :disabled="isLoadingBatch"
              @click="handleReplyButtonClick"
            >
              <svg
                class="w-4 h-4 transition-transform duration-200"
                :class="{ 'rotate-180': !isCollapsed, 'group-hover:translate-y-0.5': isCollapsed, 'group-hover:-translate-y-0.5': !isCollapsed }"
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
              <span v-if="isLoadingBatch">加载中...</span>
              <span v-else>{{ replyButtonText }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import type { Comment } from '@/types'
import CommentMarkdownPreview from './CommentMarkdownPreview.vue'
import CommentEditor from './CommentEditor.vue'
import { formatDateTime } from '@/utils/date'

const FIRST_BATCH_SIZE = 2
const BATCH_SIZE = 3
const MAX_DEPTH = 3

const props = withDefaults(defineProps<{
  comment: Comment
  articleId: number
  depth?: number
  preloadedReplyData?: { items: Comment[]; total: number; has_more: boolean } | null
  expandTargetId?: number | null
  rootCommentId?: number
}>(), {
  depth: 0,
  preloadedReplyData: null,
  expandTargetId: null,
  rootCommentId: undefined
})

const emit = defineEmits<{
  reply: [data: { content: string; parentId: number; replyToUserId?: number; rootCommentId?: number }]
  delete: [commentId: number]
  loadReplies: [data: { commentId: number; offset: number; limit: number; resolve: (result: { items: Comment[]; total: number; has_more: boolean }) => void }]
}>()

const authStore = useAuthStore()
const showReplyForm = ref(false)
const replyContent = ref('')
const submittingReply = ref(false)
const replyEditorRef = ref<InstanceType<typeof CommentEditor> | null>(null)
const isExpanded = ref(false)
const contentRef = ref<HTMLElement | null>(null)
const shouldShowExpand = ref(false)

const isRootComment = computed(() => props.depth === 0)

const isDeeplyNested = computed(() => props.depth >= 1)

const totalReplyCount = computed(() => {
  return props.comment.reply_count ?? (props.comment.replies?.length ?? 0)
})

const allLoadedReplies = ref<Comment[]>([])
const currentOffset = ref(0)
const displayedCount = ref(0)
const isLoadingBatch = ref(false)
const isCollapsed = ref(true)

const hasReplies = computed(() => {
  return props.comment.replies && props.comment.replies.length > 0
})

const displayedReplies = computed(() => {
  if (!isRootComment.value) {
    return props.comment.replies || []
  }
  return allLoadedReplies.value.slice(0, displayedCount.value)
})

const flattenedDeepReplies = computed(() => {
  if (!isDeeplyNested.value) return []
  const items = isRootComment.value
    ? allLoadedReplies.value
    : (props.comment.replies || [])
  if (items.length === 0) return []
  const result: Comment[] = []
  function flatten(list: Comment[]) {
    for (let i = 0; i < list.length; i++) {
      const item = list[i]
      result.push({ id: item.id, content: item.content, author_name: item.author_name, user_id: item.user_id, created_at: item.created_at, status: item.status, is_deleted: item.is_deleted || false, reply_to_user_name: item.reply_to_user_name, reply_count: item.reply_count || 0, parent_id: item.parent_id, article_id: item.article_id, replies: [], author_avatar_type: item.author_avatar_type, author_avatar_url: item.author_avatar_url, author_avatar_gradient: item.author_avatar_gradient })
      if (item.replies && item.replies.length > 0) flatten(item.replies)
    }
  }
  flatten(items)
  return result
})

const replyButtonText = computed(() => {
  if (!isCollapsed.value) {
    return '收起全部回复'
  }
  if (displayedCount.value === 0) {
    return `展开 ${totalReplyCount.value} 条回复`
  }
  const remaining = totalReplyCount.value - displayedCount.value
  if (remaining <= 0) return '收起全部回复'
  return '展开更多回复'
})

const containsTarget = (comment: Comment, targetId: number): boolean => {
  if (comment.id === targetId) return true
  if (comment.replies) {
    for (const reply of comment.replies) {
      if (containsTarget(reply, targetId)) return true
    }
  }
  return false
}

const shouldAutoExpand = computed(() => {
  if (!props.expandTargetId) return false
  return containsTarget(props.comment, props.expandTargetId)
})

const avatarText = computed(() => {
  const name = props.comment.author_name || '匿'
  return name.charAt(0).toUpperCase()
})

const showAvatarInitial = computed(() => {
  return !props.comment.author_avatar_type || 
         props.comment.author_avatar_type === 'default' || 
         (props.comment.author_avatar_type !== 'custom' && props.comment.author_avatar_type !== 'oauth') ||
         !props.comment.author_avatar_url
})

const avatarStyle = computed(() => {
  if ((props.comment.author_avatar_type === 'custom' || props.comment.author_avatar_type === 'oauth') && props.comment.author_avatar_url) {
    return {
      backgroundImage: `url(${props.comment.author_avatar_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  
  if (props.comment.author_avatar_gradient && props.comment.author_avatar_gradient.length >= 1) {
    return {
      backgroundColor: props.comment.author_avatar_gradient[0]
    }
  }
  
  return {
    backgroundColor: '#667eea'
  }
})

const canDelete = computed(() => {
  return authStore.isAuthenticated && 
         authStore.user && 
         props.comment.user_id === authStore.user.id &&
         !props.comment.is_deleted
})

const formatDate = (date: string) => formatDateTime(date)

const checkContentHeight = () => {
  if (contentRef.value) {
    const maxHeight = 240
    shouldShowExpand.value = contentRef.value.scrollHeight > maxHeight + 10
  }
}

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

const handleReplyButtonClick = async () => {
  if (!isCollapsed.value) {
    isCollapsed.value = true
    displayedCount.value = 0
    allLoadedReplies.value = []
    currentOffset.value = 0
    nextTick(() => {
      const el = document.getElementById(`comment-${props.comment.id}`)
      if (el) {
        const navHeight = 80
        const top = el.getBoundingClientRect().top + window.scrollY - navHeight
        window.scrollTo({ behavior: 'smooth', top })
      }
    })
    return
  }
  await loadBatch()
}

const loadBatch = async (): Promise<void> => {
  isLoadingBatch.value = true
  try {
    const batchLimit = displayedCount.value === 0 ? FIRST_BATCH_SIZE : BATCH_SIZE
    const result = await new Promise<{ items: Comment[]; total: number; has_more: boolean }>((resolve) => {
      emit('loadReplies', {
        commentId: props.comment.id,
        offset: currentOffset.value,
        limit: batchLimit,
        resolve
      })
    })
    allLoadedReplies.value = [...allLoadedReplies.value, ...result.items]
    currentOffset.value += result.items.length
    displayedCount.value = allLoadedReplies.value.length
    if (!result.has_more || displayedCount.value >= totalReplyCount.value) {
      isCollapsed.value = false
    }
  } catch (error) {
    console.error('Failed to load replies:', error)
  } finally {
    isLoadingBatch.value = false
  }
}

const applyPreloadedData = (data: { items: Comment[]; total: number; has_more: boolean } | null | undefined) => {
  if (data && data.items.length > 0) {
    allLoadedReplies.value = data.items
    currentOffset.value = data.items.length
    const targetInItems = props.expandTargetId ? findInItems(data.items, props.expandTargetId) : false
    if (targetInItems || shouldAutoExpand.value || !data.has_more) {
      displayedCount.value = allLoadedReplies.value.length
      isCollapsed.value = false
    }
  }
}

const findInItems = (items: Comment[], targetId: number): boolean => {
  for (const item of items) {
    if (item.id === targetId) return true
    if (item.replies && findInItems(item.replies, targetId)) return true
  }
  return false
}

onMounted(() => {
  checkContentHeight()
  applyPreloadedData(props.preloadedReplyData)
})

watch(() => props.preloadedReplyData, (newData) => {
  applyPreloadedData(newData)
}, { immediate: true })

const submitReply = async () => {
  if (!replyContent.value.trim() || submittingReply.value) return
  
  submittingReply.value = true
  try {
    emit('reply', {
      content: replyContent.value.trim(),
      parentId: props.comment.id,
      replyToUserId: props.comment.user_id,
      rootCommentId: props.rootCommentId || (isRootComment.value ? props.comment.id : undefined)
    })
    replyContent.value = ''
    showReplyForm.value = false
    replyEditorRef.value?.markAsSaved()
  } finally {
    submittingReply.value = false
  }
}
</script>
