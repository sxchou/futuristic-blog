<template>
  <div id="comments" class="comments-section mt-12">
    <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
      评论 ({{ totalComments }})
    </h3>

    <div v-if="!authStore.isAuthenticated" class="bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 rounded-lg p-6 text-center">
      <p class="text-gray-500 dark:text-gray-400 mb-4">登录后才能发表评论</p>
      <router-link to="/login" class="btn-primary">
        立即登录
      </router-link>
    </div>

    <div v-else class="comment-form mb-8">
      <div class="bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 rounded-lg p-4">
        <div class="flex justify-between items-center mb-1">
          <span class="text-xs text-gray-500">支持 Markdown 格式</span>
          <a 
            href="https://markdown.com.cn/basic-syntax/" 
            target="_blank" 
            class="text-xs text-primary hover:text-primary/80 transition-colors"
          >
            Markdown 语法帮助
          </a>
        </div>
        <CommentEditor
          v-model="newComment"
          placeholder="写下你的想法...&#10;&#10;支持 **粗体**、*斜体*、`代码`、[链接](url) 等 Markdown 语法"
          :disabled="submitting"
          :rows="4"
          storage-key="new-comment"
          :article-title="articleTitle"
          @submit="submitComment"
          ref="commentEditorRef"
        />
        <div class="flex justify-end mt-3">
          <button
            @click="submitComment"
            :disabled="!newComment.trim() || submitting"
            class="btn-primary text-sm px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ submitting ? '发送中...' : '发表评论' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-8">
      <div class="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <div v-else-if="comments.length === 0" class="text-center py-8 text-gray-500">
      暂无评论，快来发表第一条评论吧！
    </div>

    <div v-else class="comments-list space-y-4">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        :article-id="articleId"
        @reply="handleReply"
        @delete="handleDelete"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useAuthStore, useUserProfileStore } from '@/stores'
import { useDialogStore } from '@/stores'
import { commentApi } from '@/api'
import type { Comment } from '@/types'
import CommentItem from './CommentItem.vue'
import CommentEditor from './CommentEditor.vue'

const props = defineProps<{
  articleId: number
  articleTitle?: string
}>()

const authStore = useAuthStore()
const dialog = useDialogStore()
const userProfileStore = useUserProfileStore()
const comments = ref<Comment[]>([])
const loading = ref(true)
const newComment = ref('')
const submitting = ref(false)
const commentEditorRef = ref<InstanceType<typeof CommentEditor> | null>(null)

const totalComments = computed(() => {
  let count = 0
  const countReplies = (commentList: Comment[]) => {
    for (const comment of commentList) {
      count++
      if (comment.replies && comment.replies.length > 0) {
        countReplies(comment.replies)
      }
    }
  }
  countReplies(comments.value)
  return count
})

const fetchComments = async () => {
  try {
    comments.value = await commentApi.getArticleComments(props.articleId)
  } catch (error) {
    console.error('Failed to fetch comments:', error)
  } finally {
    loading.value = false
  }
}

const submitComment = async () => {
  if (!newComment.value.trim() || submitting.value) return
  
  submitting.value = true
  try {
    const comment = await commentApi.create({
      content: newComment.value.trim(),
      article_id: props.articleId
    })
    
    if (comment.status === 'approved') {
      comments.value.unshift(comment)
      await dialog.showSuccess('评论发表成功', '成功')
    } else if (comment.status === 'pending') {
      await dialog.showAlert({
        message: '评论已提交，等待审核通过后将显示',
        title: '提示',
        type: 'alert'
      })
    }
    
    newComment.value = ''
    commentEditorRef.value?.markAsSaved()
  } catch (error) {
    console.error('Failed to submit comment:', error)
    await dialog.showError('评论发送失败，请重试', '错误')
  } finally {
    submitting.value = false
  }
}

const findCommentById = (commentList: Comment[], id: number): Comment | null => {
  for (const comment of commentList) {
    if (comment.id === id) {
      return comment
    }
    if (comment.replies && comment.replies.length > 0) {
      const found = findCommentById(comment.replies, id)
      if (found) return found
    }
  }
  return null
}

const handleReply = async (data: { content: string; parentId: number; replyToUserId?: number }) => {
  try {
    const comment = await commentApi.create({
      content: data.content,
      article_id: props.articleId,
      parent_id: data.parentId
    })
    
    if (comment.status === 'approved') {
      const parentComment = findCommentById(comments.value, data.parentId)
      if (parentComment) {
        if (!parentComment.replies) {
          parentComment.replies = []
        }
        parentComment.replies.push(comment)
        await dialog.showSuccess('回复成功', '成功')
      }
    } else if (comment.status === 'pending') {
      await dialog.showAlert({
        message: '回复已提交，等待审核通过后将显示',
        title: '提示',
        type: 'alert'
      })
    }
  } catch (error) {
    console.error('Failed to reply:', error)
    await dialog.showError('回复发送失败，请重试', '错误')
  }
}

const markCommentAsDeleted = (commentList: Comment[], commentId: number): boolean => {
  for (const comment of commentList) {
    if (comment.id === commentId) {
      comment.is_deleted = true
      comment.deleted_by = 'user'
      comment.content = '此评论已被用户删除'
      return true
    }
    if (comment.replies && comment.replies.length > 0) {
      if (markCommentAsDeleted(comment.replies, commentId)) {
        return true
      }
    }
  }
  return false
}

const handleDelete = async (commentId: number) => {
  const confirmed = await dialog.showConfirm({
    title: '确认删除',
    message: '确定要删除这条评论吗？'
  })
  if (!confirmed) return
  
  try {
    await commentApi.delete(commentId)
    markCommentAsDeleted(comments.value, commentId)
    await dialog.showSuccess('评论已删除', '成功')
  } catch (error) {
    console.error('Failed to delete comment:', error)
    await dialog.showError('删除失败，请重试', '错误')
  }
}

onMounted(() => {
  fetchComments()
})

watch(() => userProfileStore.avatarUpdatedAt, () => {
  if (!loading.value) {
    fetchComments()
  }
})
</script>
