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
        
        <div v-if="comment.is_deleted" class="text-gray-400 dark:text-gray-500 text-sm italic mb-3 line-through">
          {{ comment.deleted_by === 'admin' ? '此评论已被管理员删除' : '此评论已被用户删除' }}
        </div>
        <div v-else-if="comment.status === 'pending'" class="text-yellow-600 dark:text-yellow-400 text-sm italic mb-3">
          评论待审核，审核通过后显示评论内容
        </div>
        <div v-else-if="comment.status === 'rejected'" class="text-red-500 dark:text-red-400 text-sm italic mb-3">
          审核不通过
        </div>
        <div v-else class="text-gray-600 dark:text-gray-300 text-sm leading-relaxed mb-3 comment-content prose prose-sm dark:prose-invert max-w-none" v-html="renderedContent" />
        
        <div v-if="!comment.is_deleted && comment.status === 'approved'" class="flex items-center gap-4 text-xs">
          <button
            v-if="authStore.isAuthenticated"
            @click="showReplyForm = !showReplyForm"
            class="text-gray-500 hover:text-primary transition-colors flex items-center gap-1"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
            回复
          </button>
          
          <button
            v-if="canDelete"
            @click="$emit('delete', comment.id)"
            class="text-gray-500 hover:text-red-500 transition-colors flex items-center gap-1"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            删除
          </button>
        </div>
        
        <div v-if="showReplyForm" class="mt-3">
          <div class="bg-gray-200 dark:bg-dark-200/50 border border-gray-300 dark:border-white/10 rounded-lg p-3">
            <div class="flex justify-between items-center mb-2">
              <span class="text-xs text-gray-500">
                回复 @{{ comment.author_name || '匿名用户' }}
              </span>
              <EmojiPicker @select="insertEmojiToReply" />
            </div>
            <textarea
              ref="replyTextarea"
              v-model="replyContent"
              placeholder="写下你的回复...&#10;支持 **粗体**、*斜体*、`代码` 等"
              class="w-full bg-transparent border-none outline-none text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 resize-none text-sm"
              rows="3"
              :disabled="submittingReply"
            />
            <div class="flex justify-end gap-2 mt-2">
              <button
                @click="showReplyForm = false"
                class="px-3 py-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                取消
              </button>
              <button
                @click="submitReply"
                :disabled="!replyContent.trim() || submittingReply"
                class="px-3 py-1 text-xs bg-primary text-white rounded hover:bg-primary/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {{ submittingReply ? '发送中...' : '发送' }}
              </button>
            </div>
          </div>
        </div>
        
        <div v-if="comment.replies && comment.replies.length > 0" class="mt-4 space-y-3 pl-4 border-l-2 border-gray-300 dark:border-white/10">
          <CommentItem
            v-for="reply in comment.replies"
            :key="reply.id"
            :comment="reply"
            :article-id="articleId"
            :depth="depth + 1"
            @reply="$emit('reply', $event)"
            @delete="$emit('delete', $event)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useAuthStore } from '@/stores/auth'
import type { Comment } from '@/types'
import EmojiPicker from '@/components/common/EmojiPicker.vue'

const props = withDefaults(defineProps<{
  comment: Comment
  articleId: number
  depth?: number
}>(), {
  depth: 0
})

const emit = defineEmits<{
  reply: [data: { content: string; parentId: number; replyToUserId?: number }]
  delete: [commentId: number]
}>()

const authStore = useAuthStore()
const showReplyForm = ref(false)
const replyContent = ref('')
const submittingReply = ref(false)
const replyTextarea = ref<HTMLTextAreaElement | null>(null)

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
  
  if (props.comment.author_avatar_gradient && props.comment.author_avatar_gradient.length >= 2) {
    const colors = props.comment.author_avatar_gradient
    return {
      background: `linear-gradient(135deg, ${colors[0]}, ${colors[1]})`
    }
  }
  
  return {
    background: 'linear-gradient(135deg, #667eea, #764ba2)'
  }
})

const canDelete = computed(() => {
  return authStore.isAuthenticated && 
         authStore.user && 
         props.comment.user_id === authStore.user.id &&
         !props.comment.is_deleted
})

const renderedContent = computed(() => {
  if (!props.comment.content) return ''
  
  let content = props.comment.content
  
  if (props.comment.reply_to_user_name) {
    content = `@${props.comment.reply_to_user_name} ${content}`
  }
  
  let html = DOMPurify.sanitize(marked(content) as string)
  
  html = html.replace(/@([^\s<]+)/g, '<span class="mention text-primary font-medium hover:underline cursor-pointer">@$1</span>')
  
  return html
})

const formatDate = (date: string) => {
  const commentDate = new Date(date)
  
  const year = commentDate.getFullYear()
  const month = String(commentDate.getMonth() + 1).padStart(2, '0')
  const day = String(commentDate.getDate()).padStart(2, '0')
  const hours = String(commentDate.getHours()).padStart(2, '0')
  const minutes = String(commentDate.getMinutes()).padStart(2, '0')
  const seconds = String(commentDate.getSeconds()).padStart(2, '0')
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const insertEmojiToReply = (emoji: string) => {
  if (!replyTextarea.value) return
  
  const textarea = replyTextarea.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  
  replyContent.value = 
    replyContent.value.substring(0, start) + 
    emoji + 
    replyContent.value.substring(end)
  
  setTimeout(() => {
    textarea.focus()
    textarea.selectionStart = textarea.selectionEnd = start + emoji.length
  }, 0)
}

const submitReply = async () => {
  if (!replyContent.value.trim() || submittingReply.value) return
  
  submittingReply.value = true
  try {
    emit('reply', {
      content: replyContent.value.trim(),
      parentId: props.comment.id,
      replyToUserId: props.comment.user_id
    })
    replyContent.value = ''
    showReplyForm.value = false
  } finally {
    submittingReply.value = false
  }
}
</script>
