<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import DOMPurify from 'dompurify'
import { useRoute } from 'vue-router'
import { articleApi, likeApi, fileApi } from '@/api'
import type { Article } from '@/types'
import CommentSection from '@/components/comments/CommentSection.vue'
import FileIcon from '@/components/FileIcon.vue'

interface ArticleFile {
  id: number
  filename: string
  original_filename: string
  file_size: number
  file_type: string
  mime_type: string
  is_image: boolean
  download_count: number
  view_count: number
  order: number
  created_at: string
}

const route = useRoute()
const article = ref<Article | null>(null)
const loading = ref(true)
const showCopySuccess = ref(false)
const isLiked = ref(false)
const likeCount = ref(0)
const isLiking = ref(false)
const articleFiles = ref<ArticleFile[]>([])

const renderer = new marked.Renderer()

renderer.code = (code: string, infostring: string | undefined, _escaped: boolean) => {
  const validLang = infostring && hljs.getLanguage(infostring) ? infostring : 'plaintext'
  const highlighted = hljs.highlight(code, { language: validLang }).value
  const encodedCode = encodeURIComponent(code)
  return `<div class="code-block-wrapper relative group">
    <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
      <button class="copy-code-btn px-2 py-1 bg-dark-200 rounded text-xs text-gray-400 hover:text-primary transition-colors" data-code="${encodedCode}">复制</button>
    </div>
    <pre><code class="hljs language-${validLang}">${highlighted}</code></pre>
  </div>`
}

marked.setOptions({
  renderer,
  gfm: true,
  breaks: true
})

const renderedContent = computed(() => {
  if (!article.value?.content) return ''
  return DOMPurify.sanitize(marked.parse(article.value.content, { async: false }) as string)
})

const formatDate = (date: string) => {
  if (!date) return ''
  
  const options: Intl.DateTimeFormatOptions = {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }
  
  return new Date(date).toLocaleDateString('zh-CN', options)
}

const handleLike = async () => {
  if (isLiking.value || !article.value) return
  
  isLiking.value = true
  try {
    const result = await likeApi.toggle(article.value.id)
    isLiked.value = result.is_liked
    likeCount.value = result.like_count
  } catch (error) {
    console.error('Failed to toggle like:', error)
  } finally {
    isLiking.value = false
  }
}

const shareArticle = (platform: string) => {
  const url = window.location.href
  const title = article.value?.title || ''
  
  const shareUrls: Record<string, string> = {
    twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`,
    weibo: `https://service.weibo.com/share/share.php?url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`
  }
  
  if (shareUrls[platform]) {
    window.open(shareUrls[platform], '_blank', 'width=600,height=400')
  }
}

const copyLink = async () => {
  await navigator.clipboard.writeText(window.location.href)
  showCopySuccess.value = true
  setTimeout(() => {
    showCopySuccess.value = false
  }, 2000)
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const isPreviewable = (_mimeType: string): boolean => {
  return true
}

const previewFile = (file: ArticleFile) => {
  const url = fileApi.getPreviewUrl(file.id)
  window.open(url, '_blank')
}

const downloadFile = (fileId: number) => {
  const url = fileApi.getDownloadUrl(fileId)
  window.open(url, '_blank')
}

const formatFileDateTime = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const fetchArticleFiles = async (articleId: number) => {
  try {
    const files = await fileApi.getFiles(articleId)
    articleFiles.value = files.filter(f => !f.is_image)
  } catch (error) {
    console.error('Failed to fetch article files:', error)
    articleFiles.value = []
  }
}

const handleCopyCode = (e: Event) => {
  const target = e.target as HTMLElement
  if (target.classList.contains('copy-code-btn')) {
    const encodedCode = target.getAttribute('data-code')
    if (encodedCode) {
      const code = decodeURIComponent(encodedCode)
      navigator.clipboard.writeText(code).then(() => {
        const originalText = target.textContent
        target.textContent = '已复制!'
        target.classList.add('text-green-400')
        setTimeout(() => {
          target.textContent = originalText
          target.classList.remove('text-green-400')
        }, 2000)
      })
    }
  }
}

const setupLazyLoading = () => {
  const images = document.querySelectorAll('.article-content img')
  images.forEach((img) => {
    img.setAttribute('loading', 'lazy')
    if (!img.hasAttribute('alt')) {
      img.setAttribute('alt', 'Article image')
    }
  })
}

const scrollToComment = (commentId: number) => {
  setTimeout(() => {
    const commentElement = document.getElementById(`comment-${commentId}`)
    if (commentElement) {
      commentElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
      commentElement.classList.add('highlight-comment')
      setTimeout(() => {
        commentElement.classList.remove('highlight-comment')
      }, 3000)
    } else {
      const commentsSection = document.getElementById('comments')
      if (commentsSection) {
        commentsSection.scrollIntoView({ behavior: 'smooth' })
      }
    }
  }, 500)
}

onMounted(async () => {
  document.addEventListener('click', handleCopyCode)
  
  const slug = route.params.slug as string
  try {
    article.value = await articleApi.getArticle(slug)
    likeCount.value = article.value?.like_count || 0
    isLiked.value = article.value?.is_liked || false
    if (article.value?.id) {
      fetchArticleFiles(article.value.id)
    }
    
    requestAnimationFrame(() => {
      setupLazyLoading()
    })
  } catch (error) {
    console.error('Failed to fetch article:', error)
  } finally {
    loading.value = false
  }
  
  if (route.hash) {
    if (route.hash === '#comments') {
      setTimeout(() => {
        const commentsSection = document.getElementById('comments')
        if (commentsSection) {
          commentsSection.scrollIntoView({ behavior: 'smooth' })
        }
      }, 100)
    } else if (route.hash.startsWith('#comment-')) {
      const commentId = parseInt(route.hash.replace('#comment-', ''), 10)
      if (!isNaN(commentId)) {
        scrollToComment(commentId)
      }
    }
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleCopyCode)
})
</script>

<template>
  <div class="pb-20">
    <div class="container mx-auto px-4">
      <div v-if="loading" class="flex justify-center py-20">
        <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>

      <article v-else-if="article" class="max-w-4xl mx-auto">
        <header class="mb-12">
          <div v-if="article.is_featured" class="mb-4">
            <span class="px-3 py-1 text-sm font-medium bg-gradient-to-r from-primary to-accent text-white rounded-full">
              精选文章
            </span>
          </div>

          <h1 class="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white mb-6">
            {{ article.title }}
          </h1>

          <div class="flex flex-wrap items-center gap-4 text-gray-400 mb-6">
            <span class="flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {{ formatDate(article.created_at) }}
            </span>
            <span class="flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {{ article.reading_time }} 分钟阅读
            </span>
            <span class="flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              {{ article.view_count }} 次阅读
            </span>
          </div>

          <div v-if="article.category" class="mb-4">
            <router-link
              :to="`/categories/${article.category.slug}`"
              class="inline-flex items-center gap-2 px-3 py-1 rounded-full border transition-colors hover:shadow-lg"
              :style="{ borderColor: article.category.color, color: article.category.color }"
            >
              <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: article.category.color }" />
              {{ article.category.name }}
            </router-link>
          </div>

          <div class="flex flex-wrap gap-2 mb-6">
            <router-link
              v-for="tag in article.tags"
              :key="tag.id"
              :to="`/tags/${tag.slug}`"
              class="tag"
              :style="{ borderColor: tag.color, color: tag.color }"
            >
              #{{ tag.name }}
            </router-link>
          </div>
        </header>

        <div
          class="prose prose-invert max-w-none article-content"
          v-html="renderedContent"
        />

        <div v-if="articleFiles.length > 0" class="mt-8 p-6 bg-gray-50 dark:bg-dark-100/50 rounded-xl border border-gray-200 dark:border-white/10">
          <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span>📎</span>
            <span>附件下载</span>
          </h3>
          <div class="space-y-3">
            <div
              v-for="file in articleFiles"
              :key="file.id"
              class="flex items-center justify-between p-4 bg-white dark:bg-dark-200 rounded-lg border border-gray-200 dark:border-white/5 hover:border-primary/30 transition-colors"
            >
              <div class="flex items-center gap-3 flex-1 min-w-0">
                <FileIcon :file-type="file.file_type" :mime-type="file.mime_type" size="md" />
                <div class="min-w-0 flex-1">
                  <div class="text-gray-900 dark:text-white font-medium truncate">{{ file.original_filename }}</div>
                  <div class="text-sm text-gray-500 flex flex-wrap gap-x-2">
                    <span>{{ formatFileSize(file.file_size) }}</span>
                    <span>·</span>
                    <span>上传: {{ formatFileDateTime(file.created_at) }}</span>
                    <span>·</span>
                    <span>下载 {{ file.download_count }} 次</span>
                    <span>·</span>
                    <span>预览 {{ file.view_count }} 次</span>
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-2 flex-shrink-0">
                <button
                  v-if="isPreviewable(file.mime_type)"
                  @click="previewFile(file)"
                  class="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-dark-100 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-50 transition-colors"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  <span>预览</span>
                </button>
                <button
                  @click="downloadFile(file.id)"
                  class="flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  <span>下载</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <CommentSection v-if="article" :article-id="article.id" :article-title="article.title" />

        <footer class="mt-12 pt-8 border-t border-gray-200 dark:border-white/10">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-3">分享文章</h3>
              <div class="flex gap-3">
                <button
                  @click="shareArticle('twitter')"
                  class="p-2 rounded-lg bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 hover:border-primary/50 hover:text-primary transition-colors"
                  title="分享到 Twitter"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                  </svg>
                </button>
                <button
                  @click="shareArticle('weibo')"
                  class="p-2 rounded-lg bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 hover:border-red-500/50 hover:text-red-500 transition-colors"
                  title="分享到微博"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M10.098 20.323c-3.977.391-7.414-1.406-7.672-4.02-.259-2.609 2.759-5.047 6.74-5.441 3.979-.394 7.413 1.404 7.671 4.018.259 2.6-2.759 5.049-6.737 5.439l-.002.004zM9.05 17.219c-.384.616-1.208.884-1.829.602-.612-.279-.793-.991-.406-1.593.379-.595 1.176-.861 1.793-.601.622.263.82.972.442 1.592zm1.27-1.627c-.141.237-.449.353-.689.253-.236-.09-.313-.361-.177-.586.138-.227.436-.346.672-.24.239.09.315.36.18.573h.014zm.176-2.719c-1.893-.493-4.033.45-4.857 2.118-.836 1.704-.026 3.591 1.886 4.21 1.983.64 4.318-.341 5.132-2.179.8-1.793-.201-3.642-2.161-4.149zm7.563-1.224c-.346-.105-.579-.18-.405-.649.381-.998.42-1.859.003-2.474-.785-1.16-2.93-1.097-5.367-.031 0 0-.768.334-.571-.271.376-1.217.32-2.237-.266-2.826-1.331-1.337-4.869.045-7.903 3.088C1.637 10.906 0 13.263 0 15.26c0 3.824 4.903 6.149 9.7 6.149 6.283 0 10.453-3.646 10.453-6.543 0-1.75-1.477-2.743-2.094-2.917zM22.461 4.028c-1.673-1.857-4.133-2.877-6.938-2.876-.001 0 .001 0 0 0-1.148.001-2.247.181-3.269.515-.402.131-.612.566-.481.969.132.402.567.613.97.481.864-.283 1.794-.435 2.766-.435 2.341-.001 4.391.851 5.78 2.393 1.389 1.542 2.092 3.658 1.979 5.96-.021.424.305.784.729.805.013.001.026.001.039.001.408 0 .747-.32.769-.732.137-2.77-.712-5.323-2.344-7.281zm-3.037 2.711c-.926-1.027-2.287-1.593-3.831-1.593-.001 0 .001 0 0 0-.635.001-1.243.1-1.808.285-.396.129-.617.554-.488.95.129.396.553.617.95.488.425-.139.882-.212 1.356-.212 1.139-.001 2.137.412 2.809 1.158.672.745.992 1.754.902 2.842-.031.423.287.79.71.821.019.001.039.002.058.002.397 0 .733-.307.763-.71.122-1.477-.317-2.839-1.371-3.831z"/>
                  </svg>
                </button>
                <button
                  @click="shareArticle('linkedin')"
                  class="p-2 rounded-lg bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 hover:border-blue-500/50 hover:text-blue-500 transition-colors"
                  title="分享到 LinkedIn"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                </button>
                <button
                  @click="copyLink"
                  class="p-2 rounded-lg bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 hover:border-accent/50 hover:text-accent transition-colors relative"
                  title="复制链接"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                  </svg>
                  <span
                    v-if="showCopySuccess"
                    class="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-cyber-green text-white text-xs rounded"
                  >
                    已复制!
                  </span>
                </button>
                <button
                  @click="handleLike"
                  class="p-2 rounded-lg bg-gray-100 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 hover:border-red-500/50 transition-colors"
                  :class="{ 'text-red-500': isLiked }"
                  title="点赞"
                >
                  <svg
                    class="w-5 h-5 transition-transform"
                    :class="{ 'scale-110': isLiked }"
                    :fill="isLiked ? 'currentColor' : 'none'"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                  <span class="ml-2">{{ likeCount }}</span>
                </button>
              </div>
            </div>

            <router-link to="/" class="btn-secondary">
              返回首页
            </router-link>
          </div>
        </footer>
      </article>

      <div v-else class="text-center py-20">
        <p class="text-gray-400 text-lg">文章不存在</p>
        <router-link to="/" class="btn-primary mt-4 inline-block">
          返回首页
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.article-content :deep(h1),
.article-content :deep(h2),
.article-content :deep(h3),
.article-content :deep(h4) {
  @apply text-gray-900 dark:text-white font-bold mt-8 mb-4;
}

.article-content :deep(h1) {
  @apply text-3xl;
}

.article-content :deep(h2) {
  @apply text-2xl;
}

.article-content :deep(h3) {
  @apply text-xl;
}

.article-content :deep(p) {
  @apply text-gray-700 dark:text-gray-300 leading-relaxed mb-4;
}

.article-content :deep(a) {
  @apply text-primary;
}

.article-content :deep(ul),
.article-content :deep(ol) {
  @apply my-4 pl-6 text-gray-700 dark:text-gray-300;
}

.article-content :deep(ul) {
  @apply list-disc;
}

.article-content :deep(ol) {
  @apply list-decimal;
}

.article-content :deep(li) {
  @apply mb-2;
}

.article-content :deep(blockquote) {
  @apply border-l-4 border-primary pl-4 my-4 text-gray-500 dark:text-gray-400 italic;
}

.article-content :deep(pre) {
  @apply bg-gray-100 dark:bg-dark-100 rounded-lg p-4 overflow-x-auto my-4;
}

.article-content :deep(code) {
  @apply text-sm font-mono;
}

.article-content :deep(table) {
  @apply w-full border-collapse my-4;
}

.article-content :deep(th),
.article-content :deep(td) {
  @apply border border-gray-200 dark:border-white/10 px-4 py-2 text-left text-gray-700 dark:text-gray-300;
}

.article-content :deep(th) {
  @apply bg-gray-100 dark:bg-dark-100 font-semibold text-gray-900 dark:text-white;
}

.article-content :deep(img) {
  @apply rounded-lg max-w-full h-auto my-4;
}
</style>
