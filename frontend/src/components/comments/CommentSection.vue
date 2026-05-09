<template>
  <div
    id="comments"
    class="comments-section mt-12"
  >
    <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
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
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        />
      </svg>
      评论 ({{ totalAllComments }})
    </h3>

    <div
      v-if="!authStore.isAuthenticated"
      class="bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 rounded-lg p-6 text-center"
    >
      <p class="text-gray-500 dark:text-gray-400 mb-4">
        登录后才能发表评论
      </p>
      <router-link
        to="/login"
        class="btn-primary"
      >
        立即登录
      </router-link>
    </div>

    <div
      v-else
      class="comment-form mb-8"
    >
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
          ref="commentEditorRef"
          v-model="newComment"
          placeholder="写下你的想法...&#10;&#10;支持 **粗体**、*斜体*、`代码`、[链接](url) 等 Markdown 语法"
          :disabled="submitting"
          :rows="4"
          storage-key="new-comment"
          editor-id="section-main"
          :article-title="articleTitle"
          @submit="submitComment"
        />
        <div class="flex justify-end mt-3">
          <button
            :disabled="!newComment.trim() || submitting"
            class="btn-primary text-sm px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
            @click="submitComment"
          >
            {{ submitting ? '发送中...' : '发表评论' }}
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="loading"
      class="flex justify-center py-8"
    >
      <div class="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <div
      v-else-if="comments.length === 0"
      class="text-center py-8 text-gray-500"
    >
      暂无评论，快来发表第一条评论吧！
    </div>

    <div v-else>
      <div class="comments-list space-y-4">
        <CommentItem
          v-for="comment in comments"
          :key="comment.id"
          :comment="comment"
          :article-id="articleId"
          :preloaded-reply-data="preloadedRepliesMap[comment.id] || null"
          :expand-target-id="expandTargetId"
          @reply="handleReply"
          @delete="handleDelete"
          @load-replies="handleLoadReplies"
        />
      </div>

      <div
        v-if="totalPages > 1"
        class="mt-8 flex items-center justify-center gap-1 sm:gap-2"
      >
        <button
          :disabled="currentPage <= 1 || pageChanging"
          class="px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-1"
          @click="goToPage(currentPage - 1)"
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
              d="M15 19l-7-7 7-7"
            />
          </svg>
          <span class="hidden sm:inline">上一页</span>
        </button>

        <template v-for="p in displayedPages" :key="p">
          <span
            v-if="p === '...'"
            class="px-2 py-2 text-sm text-gray-400"
          >…</span>
          <button
            v-else
            :class="[
              'px-3 py-2 text-sm rounded-lg transition-all duration-200 min-w-[36px]',
              p === currentPage
                ? 'bg-primary text-white shadow-md shadow-primary/25'
                : 'border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
            ]"
            @click="goToPage(p as number)"
          >
            {{ p }}
          </button>
        </template>

        <button
          :disabled="currentPage >= totalPages || pageChanging"
          class="px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-1"
          @click="goToPage(currentPage + 1)"
        >
          <span class="hidden sm:inline">下一页</span>
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
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      <div class="mt-3 text-center text-xs text-gray-400 dark:text-white/30">
        <span class="hidden md:inline">使用 ← → 方向键快速翻页</span>
      </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useAuthStore, useUserProfileStore } from '@/stores'
import { useDialogStore } from '@/stores'
import { commentApi } from '@/api'
import type { Comment, PaginatedResponse } from '@/types'
import CommentItem from './CommentItem.vue'
import CommentEditor from './CommentEditor.vue'

const props = defineProps<{
  articleId: number
  articleTitle?: string
  initialPage?: number
  preloadedCommentsData?: PaginatedResponse<Comment> | null
  preloadedRepliesMap?: Record<number, { items: Comment[]; total: number; has_more: boolean } | null>
  expandTargetId?: number | null
}>()

const authStore = useAuthStore()
const dialog = useDialogStore()
const userProfileStore = useUserProfileStore()
const comments = ref<Comment[]>([])
const loading = ref(true)
const newComment = ref('')
const submitting = ref(false)
const commentEditorRef = ref<InstanceType<typeof CommentEditor> | null>(null)

const preloadedRepliesMap = ref<Record<number, { items: Comment[]; total: number; has_more: boolean } | null>>(props.preloadedRepliesMap || {})
const expandTargetId = ref<number | null>(props.expandTargetId ?? null)

const currentPage = ref(1)
const pageSize = 5
const totalRootComments = ref(0)
const totalAllComments = ref(0)
const totalPages = ref(1)
const pageChanging = ref(false)

const displayedPages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  const pages: (number | string)[] = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (current > 3) pages.push('...')
    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)
    for (let i = start; i <= end; i++) pages.push(i)
    if (current < total - 2) pages.push('...')
    pages.push(total)
  }

  return pages
})

const fetchComments = async (page: number = 1) => {
  try {
    const res = await commentApi.getArticleComments(props.articleId, page, pageSize)
    comments.value = res.items
    totalRootComments.value = res.total
    totalAllComments.value = res.total_all ?? res.total
    totalPages.value = res.total_pages
    currentPage.value = res.page
  } catch (error) {
    console.error('Failed to fetch comments:', error)
  } finally {
    loading.value = false
    pageChanging.value = false
  }
}

const goToPage = (page: number) => {
  if (page < 1 || page > totalPages.value || page === currentPage.value) return
  pageChanging.value = true
  currentPage.value = page
  fetchComments(page)
  const el = document.getElementById('comments')
  if (el) {
    const navHeight = 80
    const top = el.getBoundingClientRect().top + window.scrollY - navHeight
    window.scrollTo({ behavior: 'smooth', top })
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
      if (currentPage.value === 1) {
        comments.value.unshift(comment)
        if (comments.value.length > pageSize) {
          comments.value = comments.value.slice(0, pageSize)
        }
      }
      totalRootComments.value += 1
      totalAllComments.value += 1
      totalPages.value = Math.max(1, Math.ceil(totalRootComments.value / pageSize))
      expandTargetId.value = comment.id
      nextTick(() => { setTimeout(() => scrollToTarget(comment.id, 0), 100) })
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

const findRootAncestorId = (targetId: number): number | null => {
  for (const root of comments.value) {
    if (root.id === targetId) return root.id
    if (findCommentById(root.replies || [], targetId)) return root.id
    const preloaded = preloadedRepliesMap.value[root.id]
    if (preloaded && findInItems(preloaded.items, targetId)) return root.id
  }
  return null
}

const findInItems = (items: Comment[], targetId: number): boolean => {
  for (const item of items) {
    if (item.id === targetId) return true
    if (item.replies && findInItems(item.replies, targetId)) return true
  }
  return false
}

const handleReply = async (data: { content: string; parentId: number; replyToUserId?: number; rootCommentId?: number }) => {
  try {
    const comment = await commentApi.create({
      content: data.content,
      article_id: props.articleId,
      parent_id: data.parentId
    })
    
    if (comment.status === 'approved') {
      const rootId = data.rootCommentId || findRootAncestorId(data.parentId)
      if (rootId) {
        const rootIndex = comments.value.findIndex(c => c.id === rootId)
        if (rootIndex !== -1) {
          const root = comments.value[rootIndex]
          comments.value[rootIndex] = { ...root, reply_count: (root.reply_count || 0) + 1 }
          totalAllComments.value += 1

          if (data.parentId === rootId) {
            const existing = preloadedRepliesMap.value[data.parentId]
            const newItems = existing ? [...existing.items, comment] : [comment]
            const newTotal = (existing?.total ?? 0) + 1
            preloadedRepliesMap.value = {
              ...preloadedRepliesMap.value,
              [data.parentId]: { items: newItems, total: newTotal, has_more: newItems.length < newTotal }
            }
          } else {
            try {
              const result = await commentApi.getCommentReplies(props.articleId, rootId)
              preloadedRepliesMap.value = { ...preloadedRepliesMap.value, [rootId]: result }
            } catch (e) {
              console.error('Failed to load root replies for nested reply:', e)
            }
          }

          expandTargetId.value = comment.id
          nextTick(() => {
            setTimeout(() => scrollToTarget(comment.id, 0), 100)
          })
        }
      }
      await dialog.showSuccess('回复成功', '成功')
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

const handleLoadReplies = async (data: { commentId: number; offset: number; limit: number; resolve: (result: { items: Comment[]; total: number; has_more: boolean }) => void }) => {
  try {
    const result = await commentApi.getCommentReplies(props.articleId, data.commentId, data.offset, data.limit)
    data.resolve(result)
  } catch (error) {
    console.error('Failed to load replies:', error)
    data.resolve({ items: [], total: 0, has_more: false })
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

const navigateToComment = async (commentId: number) => {
  try {
    expandTargetId.value = commentId
    const locateResult = await commentApi.locateComment(props.articleId, commentId, pageSize)
    const targetPage = locateResult.page
    const needPageChange = targetPage !== currentPage.value
    const needReplies = locateResult.is_reply && !!locateResult.root_comment_id

    const promises: Promise<void>[] = []
    if (needPageChange) {
      promises.push(fetchComments(targetPage))
    }
    if (needReplies) {
      const rootId = locateResult.root_comment_id!
      const existing = preloadedRepliesMap.value[rootId]
      if (!existing || !findInItems(existing.items, commentId)) {
        promises.push(
          commentApi.getCommentReplies(props.articleId, rootId).then(result => {
            preloadedRepliesMap.value = { ...preloadedRepliesMap.value, [rootId]: result }
          }).catch(e => console.error('Failed to load replies for navigation:', e))
        )
      }
    }

    await Promise.all(promises)
    scrollToTarget(commentId, 0)
  } catch (error) {
    console.error('Failed to navigate to comment:', error)
    expandTargetId.value = null
    const commentsSection = document.getElementById('comments')
    if (commentsSection) {
      const navHeight = 80
      const top = commentsSection.getBoundingClientRect().top + window.scrollY - navHeight
      window.scrollTo({ behavior: 'smooth', top })
    }
  }
}

const scrollToTarget = (commentId: number, retryCount: number): void => {
  nextTick(() => {
    const commentElement = document.getElementById(`comment-${commentId}`)
    if (commentElement) {
      const navHeight = 80
      const rect = commentElement.getBoundingClientRect()
      const top = rect.top + window.scrollY - navHeight - 20
      window.scrollTo({ behavior: 'smooth', top })
      commentElement.classList.add('highlight-comment')
      setTimeout(() => { 
        commentElement.classList.remove('highlight-comment')
        expandTargetId.value = null
      }, 3000)
    } else if (retryCount < 10) {
      setTimeout(() => scrollToTarget(commentId, retryCount + 1), 30)
    } else {
      expandTargetId.value = null
    }
  })
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'ArrowLeft' && currentPage.value > 1) {
    event.preventDefault()
    goToPage(currentPage.value - 1)
  } else if (event.key === 'ArrowRight' && currentPage.value < totalPages.value) {
    event.preventDefault()
    goToPage(currentPage.value + 1)
  }
}

defineExpose({ navigateToComment })

onMounted(() => {
  if (props.preloadedCommentsData) {
    comments.value = props.preloadedCommentsData.items
    totalRootComments.value = props.preloadedCommentsData.total
    totalAllComments.value = props.preloadedCommentsData.total_all ?? props.preloadedCommentsData.total
    totalPages.value = props.preloadedCommentsData.total_pages
    currentPage.value = props.preloadedCommentsData.page
    loading.value = false
  } else {
    fetchComments(props.initialPage || 1)
  }
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

watch(() => userProfileStore.avatarUpdatedAt, () => {
  if (!loading.value) {
    fetchComments(currentPage.value)
  }
})
</script>
