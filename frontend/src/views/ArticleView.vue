<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { marked } from 'marked'
import hljs from '@/utils/hljs'
import DOMPurify from 'dompurify'
import { initMermaid, renderMermaidDiagrams, rerenderMermaidOnThemeChange } from '@/utils/mermaid'
import { useRoute, useRouter } from 'vue-router'
import { articleApi, likeApi, bookmarkApi, fileApi } from '@/api'
import { useAuthStore, useUserInteractionStore, useThemeStore } from '@/stores'
import { dataPrefetch } from '@/utils/prefetch'
import type { Article, ArticleFile } from '@/types'
import CommentSection from '@/components/comments/CommentSection.vue'
import FilePreview from '@/components/FilePreview.vue'
import BlogSidebar from '@/components/common/BlogSidebar.vue'
import LeftSidebar from '@/components/common/LeftSidebar.vue'
import MermaidFullscreen from '@/components/common/MermaidFullscreen.vue'
import { getMediaUrl } from '@/utils/media'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const userInteractionStore = useUserInteractionStore()
const article = ref<Article | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const showCopySuccess = ref(false)
const isLiked = ref(false)
const likeCount = ref(0)
const isLiking = ref(false)
const isBookmarked = ref(false)
const bookmarkCount = ref(0)
const mermaidFullscreen = ref<InstanceType<typeof MermaidFullscreen>>()
const isBookmarking = ref(false)
const articleFiles = ref<ArticleFile[]>([])
const previewFile = ref<ArticleFile | null>(null)
const showPreview = ref(false)
const selectedFileIds = ref<Set<number>>(new Set())
const highlightKeyword = ref('')

const coverImageUrl = computed(() => getMediaUrl(article.value?.cover_image))
const activeHeading = ref('')
const showToc = ref(false)
const showMobileToc = ref(false)
const mobileTocNavRef = ref<HTMLElement | null>(null)
const coverImageHeight = ref<number>(0)
const coverObjectPosition = ref<string>('center center')
const articleHeaderRef = ref<HTMLElement | null>(null)
const coverImageRef = ref<HTMLImageElement | null>(null)
const tocNavRef = ref<HTMLElement | null>(null)

const tocItems = ref<Array<{ id: string; text: string; level: number }>>([])

const extractToc = (html: string) => {
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = html
  const headings = tempDiv.querySelectorAll('h1, h2, h3, h4')
  const items: Array<{ id: string; text: string; level: number }> = []
  headings.forEach((heading, index) => {
    const id = `heading-${index}`
    heading.id = id
    items.push({
      id,
      text: heading.textContent || '',
      level: parseInt(heading.tagName[1])
    })
  })
  return { html: tempDiv.innerHTML, items }
}

const highlightText = (text: string, keyword: string): string => {
  if (!keyword || !text) return text
  const escapeRegExp = (str: string) => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const pattern = escapeRegExp(keyword)
  const regex = new RegExp(`(${pattern})`, 'gi')
  return text.replace(regex, '<mark class="search-highlight">$1</mark>')
}

const renderer = new marked.Renderer()

renderer.code = (code: string, infostring: string | undefined, _escaped: boolean) => {
  if (infostring === 'mermaid') {
    const encodedCode = encodeURIComponent(code)
    const copyIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>`
    const fullscreenIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>`
    const langIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 inline-block mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>`
    return `<div class="code-block-wrapper relative group mermaid-wrapper" data-mermaid="${encodedCode}">
      <div class="absolute top-2 left-4 right-2 flex justify-between items-center z-20">
        <span class="text-sm text-gray-500 dark:text-gray-400">${langIcon}mermaid</span>
        <div class="flex items-center gap-1">
          <button class="mermaid-fullscreen-btn flex items-center justify-center w-8 h-8 rounded text-gray-500 hover:text-primary transition-colors" data-code="${encodedCode}" data-tooltip="全屏查看">${fullscreenIcon}</button>
          <button class="copy-code-btn flex items-center justify-center w-8 h-8 rounded text-gray-500 hover:text-primary transition-colors" data-code="${encodedCode}" data-tooltip="复制代码">${copyIcon}</button>
        </div>
      </div>
      <pre class="mermaid" data-mermaid-code="${encodedCode}">${code}</pre>
    </div>`
  }
  const validLang = infostring && hljs.getLanguage(infostring) ? infostring : 'plaintext'
  const highlighted = hljs.highlight(code, { language: validLang }).value
  const encodedCode = encodeURIComponent(code)
  const copyIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>`
  const langIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 inline-block mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>`
  return `<div class="code-block-wrapper relative group">
    <div class="absolute top-2 left-4 right-2 flex justify-between items-center z-20">
      <span class="text-sm text-gray-500 dark:text-gray-400">${langIcon}${validLang}</span>
      <button class="copy-code-btn flex items-center justify-center w-8 h-8 rounded text-gray-500 hover:text-primary transition-colors" data-code="${encodedCode}" data-tooltip="复制代码">${copyIcon}</button>
    </div>
    <pre><code class="hljs language-${validLang}">${highlighted}</code></pre>
  </div>`
}

renderer.link = (href: string, title: string | null | undefined, text: string) => {
  const titleAttr = title ? ` title="${title}"` : ''
  const currentOrigin = typeof window !== 'undefined' ? window.location.origin : ''
  const isInternal = href.startsWith('/') || href.startsWith('#') || (currentOrigin && href.startsWith(currentOrigin))
  if (isInternal) {
    return `<a href="${href}"${titleAttr} class="text-primary hover:underline">${text}</a>`
  }
  return `<a href="${href}"${titleAttr} target="_blank" rel="noopener noreferrer" class="text-primary hover:underline">${text}</a>`
}

renderer.table = (header: string, body: string) => {
  return `<div class="overflow-x-auto my-4"><table class="min-w-full border-collapse border border-gray-200 dark:border-white/10"><thead class="bg-gray-50 dark:bg-dark-300">${header}</thead><tbody>${body}</tbody></table></div>`
}

marked.setOptions({ renderer, gfm: true, breaks: true })

const renderedContent = computed(() => {
  if (!article.value?.content) return ''
  const rawHtml = marked.parse(article.value.content, { async: false }) as string
  let sanitizedHtml = DOMPurify.sanitize(rawHtml, {
    ADD_ATTR: ['target', 'rel', 'loading', 'class', 'id', 'data-mermaid', 'data-mermaid-code'],
    ADD_TAGS: ['iframe', 'mark']
  })
  
  const { html: htmlWithIds, items } = extractToc(sanitizedHtml)
  // eslint-disable-next-line vue/no-side-effects-in-computed-properties
  tocItems.value = items
  sanitizedHtml = htmlWithIds
  
  if (highlightKeyword.value) {
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = sanitizedHtml
    const walkAndHighlight = (node: Node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent || ''
        if (text.trim()) {
          const highlighted = highlightText(text, highlightKeyword.value)
          if (highlighted !== text) {
            const span = document.createElement('span')
            span.innerHTML = highlighted
            node.parentNode?.replaceChild(span, node)
          }
        }
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        const element = node as Element
        if (element.tagName !== 'CODE' && element.tagName !== 'PRE') {
          Array.from(node.childNodes).forEach(walkAndHighlight)
        }
      }
    }
    walkAndHighlight(tempDiv)
    sanitizedHtml = tempDiv.innerHTML
  }
  
  return sanitizedHtml
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
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  if (isLiking.value || !article.value) return
  isLiking.value = true

  const prevLiked = isLiked.value
  const prevCount = likeCount.value
  isLiked.value = !prevLiked
  likeCount.value = prevLiked ? prevCount - 1 : prevCount + 1
  userInteractionStore.setLiked(article.value.id, !prevLiked)

  try {
    const result = await likeApi.toggle(article.value.id)
    isLiked.value = result.is_liked
    likeCount.value = result.like_count
    userInteractionStore.setLiked(article.value.id, result.is_liked)
  } catch (error) {
    console.error('Failed to toggle like:', error)
    isLiked.value = prevLiked
    likeCount.value = prevCount
    userInteractionStore.setLiked(article.value.id, prevLiked)
  } finally {
    isLiking.value = false
  }
}

const handleBookmark = async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  if (isBookmarking.value || !article.value) return
  isBookmarking.value = true

  const prevBookmarked = isBookmarked.value
  const prevBookmarkCount = bookmarkCount.value
  isBookmarked.value = !prevBookmarked
  bookmarkCount.value = prevBookmarked ? prevBookmarkCount - 1 : prevBookmarkCount + 1
  userInteractionStore.setBookmarked(article.value.id, !prevBookmarked)

  try {
    const result = await bookmarkApi.toggle(article.value.id)
    isBookmarked.value = result.is_bookmarked
    bookmarkCount.value = result.bookmark_count ?? 0
    userInteractionStore.setBookmarked(article.value.id, result.is_bookmarked)
  } catch (error) {
    console.error('Failed to toggle bookmark:', error)
    isBookmarked.value = prevBookmarked
    bookmarkCount.value = prevBookmarkCount
    userInteractionStore.setBookmarked(article.value.id, prevBookmarked)
  } finally {
    isBookmarking.value = false
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
  setTimeout(() => { showCopySuccess.value = false }, 2000)
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const getFileIconInfo = (fileType: string, mimeType: string, filename: string): { color: string; bg: string; svg: string } => {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  
  if (fileType === 'image' || ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico'].includes(ext)) {
    return { 
      color: 'text-white', 
      bg: 'bg-gradient-to-br from-green-400 to-green-600', 
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><rect x="3" y="3" width="26" height="26" rx="3" fill="rgba(255,255,255,0.2)"/><circle cx="11" cy="11" r="3" fill="white"/><path d="M29 20l-7-7L7 29" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>` 
    }
  }
  
  if (mimeType.includes('pdf') || ext === 'pdf') {
    return { 
      color: 'text-white', 
      bg: 'bg-gradient-to-br from-red-500 to-red-700', 
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/><text x="16" y="22" text-anchor="middle" fill="white" font-size="8" font-weight="bold" font-family="sans-serif">PDF</text></svg>` 
    }
  }
  
  if (['doc', 'docx'].includes(ext)) {
    return { 
      color: 'text-white', 
      bg: 'bg-gradient-to-br from-blue-500 to-blue-700', 
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/><text x="16" y="22" text-anchor="middle" fill="white" font-size="12" font-weight="bold" font-family="sans-serif">W</text></svg>` 
    }
  }
  
  if (['xls', 'xlsx'].includes(ext)) {
    return { 
      color: 'text-white', 
      bg: 'bg-gradient-to-br from-emerald-500 to-emerald-700', 
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/><text x="16" y="22" text-anchor="middle" fill="white" font-size="12" font-weight="bold" font-family="sans-serif">X</text></svg>` 
    }
  }
  
  if (['ppt', 'pptx'].includes(ext)) {
    return { 
      color: 'text-white', 
      bg: 'bg-gradient-to-br from-orange-500 to-orange-700', 
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/><text x="16" y="22" text-anchor="middle" fill="white" font-size="12" font-weight="bold" font-family="sans-serif">P</text></svg>` 
    }
  }
  
  if (['txt', 'md', 'csv', 'json', 'xml', 'html', 'css', 'js', 'ts', 'py', 'java', 'c', 'cpp', 'h', 'hpp', 'sql', 'yaml', 'yml', 'ini', 'conf', 'log', 'sh', 'bat'].includes(ext)) {
    return { 
      color: 'text-white', 
      bg: 'bg-gradient-to-br from-slate-500 to-slate-700', 
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/><path d="M9 16h14M9 21h10" stroke="white" stroke-width="2.5" stroke-linecap="round"/></svg>` 
    }
  }
  
  if (['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma'].includes(ext) || mimeType.startsWith('audio/')) {
    return { 
      color: 'text-white', 
      bg: 'bg-gradient-to-br from-purple-500 to-purple-700', 
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M12 24V6l16-3v18" fill="rgba(255,255,255,0.5)"/><circle cx="8" cy="24" r="4" fill="white"/><circle cx="24" cy="21" r="4" fill="white"/></svg>` 
    }
  }
  
  if (['mp4', 'webm', 'avi', 'mov', 'wmv', 'flv', 'mkv'].includes(ext) || mimeType.startsWith('video/')) {
    return { 
      color: 'text-white', 
      bg: 'bg-gradient-to-br from-pink-500 to-pink-700', 
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><rect x="2" y="5" width="28" height="22" rx="3" fill="rgba(255,255,255,0.3)"/><polygon points="13,10 22,16 13,22" fill="white"/></svg>` 
    }
  }
  
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
    return { 
      color: 'text-white', 
      bg: 'bg-gradient-to-br from-amber-500 to-amber-700', 
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M28 10v18H4V10" fill="rgba(255,255,255,0.3)"/><path d="M30 4H2v6h28V4z" fill="rgba(255,255,255,0.5)"/><rect x="13" y="14" width="6" height="5" fill="white" rx="1"/><rect x="13" y="21" width="6" height="4" fill="rgba(255,255,255,0.5)" rx="1"/></svg>` 
    }
  }
  
  return { 
    color: 'text-white', 
    bg: 'bg-gradient-to-br from-gray-400 to-gray-600', 
    svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><path d="M18 2H6a2 2 0 00-2 2v24a2 2 0 002 2h20a2 2 0 002-2V10l-8-8z" fill="rgba(255,255,255,0.3)"/><path d="M18 2v8h8" stroke="white" stroke-width="2" fill="none"/></svg>` 
  }
}

const downloadFile = async (file: ArticleFile) => {
  try {
    const response = await fileApi.downloadFile(file.id)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', file.original_filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error(`Failed to download file ${file.original_filename}:`, error)
  }
}

const toggleSelectAll = () => {
  if (selectedFileIds.value.size === articleFiles.value.length) {
    selectedFileIds.value.clear()
  } else {
    selectedFileIds.value = new Set(articleFiles.value.map(f => f.id))
  }
}

const toggleFileSelection = (fileId: number) => {
  if (selectedFileIds.value.has(fileId)) {
    selectedFileIds.value.delete(fileId)
  } else {
    selectedFileIds.value.add(fileId)
  }
}

const handleBatchDownload = async () => {
  if (selectedFileIds.value.size === 0) return
  const selectedFiles = articleFiles.value.filter(f => selectedFileIds.value.has(f.id))
  for (const file of selectedFiles) {
    try {
      const response = await fileApi.downloadFile(file.id)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', file.original_filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      await new Promise(resolve => setTimeout(resolve, 300))
    } catch (error) {
      console.error(`Failed to download file ${file.original_filename}:`, error)
    }
  }
}

const openPreview = async (file: ArticleFile) => {
  previewFile.value = file
  showPreview.value = true
  try {
    const result = await fileApi.previewFile(file.id)
    const fileIndex = articleFiles.value.findIndex(f => f.id === file.id)
    if (fileIndex !== -1) {
      articleFiles.value[fileIndex].preview_count = result.preview_count
    }
  } catch (error) {
    console.error('Failed to update preview count:', error)
  }
}

const closePreview = () => {
  showPreview.value = false
  previewFile.value = null
}

const refreshPage = () => {
  window.location.reload()
}

const fetchArticleFiles = async (articleId: number) => {
  try {
    const files = await fileApi.getFiles(articleId)
    articleFiles.value = files
  } catch (error) {
    console.error('Failed to fetch article files:', error)
    articleFiles.value = []
  }
}

const handleCopyCode = (e: Event) => {
  const target = e.target as HTMLElement
  const btn = target.closest('.copy-code-btn') as HTMLElement
  if (btn) {
    const encodedCode = btn.getAttribute('data-code')
    if (encodedCode) {
      const code = decodeURIComponent(encodedCode)
      const svg = btn.querySelector('svg')
      if (!svg) return
      
      const originalSvg = svg.outerHTML
      const originalTooltip = btn.getAttribute('data-tooltip')
      svg.outerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>`
      btn.setAttribute('data-tooltip', '已复制')
      
      setTimeout(() => {
        const newSvg = btn.querySelector('svg')
        if (newSvg) newSvg.outerHTML = originalSvg
        if (originalTooltip) btn.setAttribute('data-tooltip', originalTooltip)
      }, 2000)
      
      navigator.clipboard.writeText(code)
    }
  }
}

const handleMermaidFullscreen = (e: Event) => {
  const target = e.target as HTMLElement
  const btn = target.closest('.mermaid-fullscreen-btn') as HTMLElement
  if (btn) {
    const wrapper = btn.closest('.mermaid-wrapper')
    if (wrapper) {
      const pre = wrapper.querySelector('.mermaid') as HTMLElement
      const encodedCode = btn.getAttribute('data-code') || pre?.getAttribute('data-mermaid-code') || ''
      const svg = pre?.querySelector('svg')
      if (svg && mermaidFullscreen.value) {
        mermaidFullscreen.value.open(svg.outerHTML, encodedCode)
      }
    }
  }
}

const handleFileLinkClick = (e: Event) => {
  const target = e.target as HTMLElement
  const link = target.closest('a') as HTMLAnchorElement | null
  if (link) {
    const href = link.getAttribute('href')
    if (href && href.includes('#file-')) {
      const hashIndex = href.indexOf('#file-')
      const hash = href.substring(hashIndex)
      const fileId = parseInt(hash.replace('#file-', ''), 10)
      if (!isNaN(fileId)) {
        const currentPath = window.location.pathname
        const linkPath = href.substring(0, hashIndex) || currentPath
        const isSamePage = linkPath === currentPath || linkPath === ''
        if (isSamePage) {
          e.preventDefault()
          e.stopPropagation()
          const fileElement = document.getElementById(`file-${fileId}`)
          if (fileElement) {
            fileElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
            fileElement.classList.remove('file-highlight')
            setTimeout(() => { fileElement.classList.add('file-highlight') }, 100)
            setTimeout(() => { fileElement.classList.remove('file-highlight') }, 3100)
            history.pushState(null, '', hash)
          }
        }
      }
    }
  }
}

const openMobileToc = () => {
  showMobileToc.value = true
  nextTick(() => {
    if (!mobileTocNavRef.value || !activeHeading.value) return
    const activeBtn = mobileTocNavRef.value.querySelector(`[data-mobile-heading-id="${activeHeading.value}"]`) as HTMLElement
    if (activeBtn) {
      activeBtn.scrollIntoView({ block: 'center', behavior: 'instant' })
    }
  })
}

const scrollToHeading = (id: string) => {
  const element = document.getElementById(id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    activeHeading.value = id
  }
}

const updateActiveHeading = () => {
  for (let i = tocItems.value.length - 1; i >= 0; i--) {
    const element = document.getElementById(tocItems.value[i].id)
    if (element) {
      const rect = element.getBoundingClientRect()
      if (rect.top <= 100) {
        activeHeading.value = tocItems.value[i].id
        scrollToActiveTocItem(tocItems.value[i].id)
        return
      }
    }
  }
  if (tocItems.value.length > 0) {
    activeHeading.value = tocItems.value[0].id
    scrollToActiveTocItem(tocItems.value[0].id)
  }
}

const scrollToActiveTocItem = (headingId: string) => {
  if (!tocNavRef.value) return
  
  const activeButton = tocNavRef.value.querySelector(`[data-heading-id="${headingId}"]`) as HTMLElement
  if (!activeButton) return
  
  const navContainer = tocNavRef.value
  const containerRect = navContainer.getBoundingClientRect()
  const buttonRect = activeButton.getBoundingClientRect()
  
  const isAbove = buttonRect.top < containerRect.top
  const isBelow = buttonRect.bottom > containerRect.bottom
  
  if (isAbove || isBelow) {
    const scrollOffset = activeButton.offsetTop - (containerRect.height / 2) + (buttonRect.height / 2)
    navContainer.scrollTo({
      top: Math.max(0, scrollOffset),
      behavior: 'smooth'
    })
  }
}

const loadArticle = async (slug: string) => {
  loading.value = true
  error.value = null
  article.value = null
  tocItems.value = []
  articleFiles.value = []
  
  try {
    const cached = dataPrefetch.get<Article>(`article-${slug}`)
    if (cached) {
      article.value = cached
      dataPrefetch.invalidate(`article-${slug}`)
    } else {
      article.value = await articleApi.getArticle(slug)
    }
    likeCount.value = article.value?.like_count || 0
    isLiked.value = article.value?.is_liked || false
    bookmarkCount.value = article.value?.bookmark_count || 0
    if (article.value?.id) {
      if (article.value.files && article.value.files.length > 0) {
        articleFiles.value = [...article.value.files].sort((a, b) => (a.order || 0) - (b.order || 0))
      } else {
        fetchArticleFiles(article.value.id)
      }
      if (authStore.isAuthenticated) {
        bookmarkApi.getStatus(article.value.id).then(bookmarkStatus => {
          isBookmarked.value = bookmarkStatus.is_bookmarked
          bookmarkCount.value = bookmarkStatus.bookmark_count || 0
        }).catch(error => {
          console.error('Failed to fetch bookmark status:', error)
        })
      }
    }
  } catch (err: unknown) {
    console.error('Failed to fetch article:', err)
    if (err instanceof Error) {
      if ((err as unknown as Record<string, unknown>)?.isCancel) return
      if (err.message.includes('404')) error.value = '文章不存在'
      else if (err.message.includes('Network Error') || err.message.includes('timeout')) error.value = '网络连接失败，请检查网络后重试'
      else error.value = '加载文章失败，请稍后重试'
    } else {
      error.value = '加载文章失败，请稍后重试'
    }
  } finally {
    loading.value = false
    await nextTick()
    const articleContent = document.querySelector('.article-content')
    if (articleContent) {
      await renderMermaidDiagrams(articleContent as HTMLElement, '.mermaid', themeStore.isDark)
    }
  }
}

onMounted(async () => {
  await initMermaid(themeStore.isDark)
  
  document.addEventListener('click', handleCopyCode)
  document.addEventListener('click', handleMermaidFullscreen)
  document.addEventListener('click', handleFileLinkClick)
  window.addEventListener('scroll', updateActiveHeading, { passive: true })
  window.addEventListener('resize', updateCoverHeight, { passive: true })
  
  const highlight = route.query.highlight as string
  if (highlight) highlightKeyword.value = highlight
  
  const slug = route.params.slug as string
  await loadArticle(slug)
  
  if (route.hash) {
    if (route.hash === '#comments') {
      setTimeout(() => {
        const commentsSection = document.getElementById('comments')
        if (commentsSection) {
          const rect = commentsSection.getBoundingClientRect()
          const scrollTop = window.pageYOffset || document.documentElement.scrollTop
          window.scrollTo({
            top: rect.top + scrollTop - 80,
            behavior: 'smooth'
          })
        }
      }, 100)
    } else if (route.hash.startsWith('#comment-')) {
      const commentId = parseInt(route.hash.replace('#comment-', ''), 10)
      if (!isNaN(commentId)) {
        setTimeout(() => {
          const commentElement = document.getElementById(`comment-${commentId}`)
          if (commentElement) {
            const rect = commentElement.getBoundingClientRect()
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop
            window.scrollTo({
              top: rect.top + scrollTop - 80,
              behavior: 'smooth'
            })
            commentElement.classList.add('highlight-comment')
            setTimeout(() => { commentElement.classList.remove('highlight-comment') }, 3000)
          } else {
            const commentsSection = document.getElementById('comments')
            if (commentsSection) {
              const rect = commentsSection.getBoundingClientRect()
              const scrollTop = window.pageYOffset || document.documentElement.scrollTop
              window.scrollTo({
                top: rect.top + scrollTop - 80,
                behavior: 'smooth'
              })
            }
          }
        }, 100)
      }
    }
  }
})

watch(() => route.params.slug, async (newSlug, oldSlug) => {
  if (newSlug && newSlug !== oldSlug) {
    const highlight = route.query.highlight as string
    highlightKeyword.value = highlight || ''
    await loadArticle(newSlug as string)
  }
})

watch(() => themeStore.isDark, async (isDark) => {
  const articleContent = document.querySelector('.article-content')
  if (articleContent) {
    await rerenderMermaidOnThemeChange(articleContent as HTMLElement, '.mermaid', isDark)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleCopyCode)
  document.removeEventListener('click', handleMermaidFullscreen)
  document.removeEventListener('click', handleFileLinkClick)
  window.removeEventListener('scroll', updateActiveHeading)
  window.removeEventListener('resize', updateCoverHeight)
})

const updateCoverHeight = () => {
  if (!articleHeaderRef.value) return
  const headerEl = articleHeaderRef.value
  const coverContainer = headerEl.querySelector('.cover-side-image')
  if (coverContainer) {
    const textContent = headerEl.querySelector('.cover-text-content')
    if (textContent) {
      const textRect = textContent.getBoundingClientRect()
      coverImageHeight.value = Math.ceil(textRect.height)
    }
  } else {
    const headerRect = headerEl.getBoundingClientRect()
    const computedStyle = window.getComputedStyle(headerEl)
    const marginBottom = parseFloat(computedStyle.marginBottom) || 0
    coverImageHeight.value = Math.ceil(headerRect.height + marginBottom)
  }
}

const computeSmartCrop = (img: HTMLImageElement) => {
  const naturalWidth = img.naturalWidth
  const naturalHeight = img.naturalHeight
  if (!naturalWidth || !naturalHeight) return

  const containerWidth = img.clientWidth
  const containerHeight = img.clientHeight
  if (!containerWidth || !containerHeight) return

  const imgRatio = naturalWidth / naturalHeight
  const containerRatio = containerWidth / containerHeight

  if (imgRatio > containerRatio) {
    const scale = containerHeight / naturalHeight
    const displayedWidth = naturalWidth * scale
    const overflow = displayedWidth - containerWidth
    const percentOverflow = (overflow / displayedWidth) * 100
    const centerOffset = Math.min(percentOverflow / 2, 35)
    coverObjectPosition.value = `${50 + centerOffset}% center`
  } else {
    const scale = containerWidth / naturalWidth
    const displayedHeight = naturalHeight * scale
    const overflow = displayedHeight - containerHeight
    const percentOverflow = (overflow / displayedHeight) * 100
    const topOffset = Math.min(percentOverflow * 0.3, 20)
    coverObjectPosition.value = `center ${topOffset}%`
  }
}

watch(article, async (newVal) => {
  if (newVal?.cover_image) {
    await nextTick()
    if (coverImageRef.value) {
      if (coverImageRef.value.complete && coverImageRef.value.naturalWidth > 0) {
        updateCoverHeight()
        computeSmartCrop(coverImageRef.value)
      } else {
        coverImageRef.value.onload = () => {
          updateCoverHeight()
          computeSmartCrop(coverImageRef.value!)
        }
      }
    } else {
      updateCoverHeight()
    }
  }
})
</script>

<template>
  <div>
    <div
      v-if="loading"
      class="flex justify-center py-20"
    >
      <div class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>

    <article
      v-else-if="article"
      class="flex flex-col lg:flex-row gap-6"
    >
      <div class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-1">
        <div class="lg:sticky lg:top-20">
          <LeftSidebar />
        </div>
      </div>
      
      <div class="flex-1 min-w-0 lg:order-2">
        <header
          ref="articleHeaderRef"
          class="mb-8"
        >
          <div
            v-if="article.cover_image"
            class="relative rounded-2xl overflow-hidden mb-4 md:hidden"
          >
            <img
              ref="coverImageRef"
              :src="coverImageUrl"
              :alt="article.title"
              class="w-full h-48 sm:h-64 object-cover"
              loading="eager"
              decoding="async"
            >
            <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
          </div>

          <div class="md:hidden mb-6">
            <div class="flex items-center gap-2 mb-3">
              <span
                v-if="article.is_featured"
                class="px-2.5 py-0.5 bg-primary text-white text-xs font-medium rounded-full"
              >精选</span>
              <span
                v-if="article.is_pinned"
                class="px-2.5 py-0.5 bg-amber-500/90 text-white text-xs font-medium rounded-full"
              >置顶</span>
            </div>

            <h1 class="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-3 leading-tight">
              {{ article.title }}
            </h1>

            <div class="flex flex-wrap items-center gap-2 text-xs text-gray-400 mb-3">
              <span
                v-if="article.author || article.author_name"
                class="flex items-center gap-1"
              >
                <svg
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                /></svg>
                {{ article.author?.username || article.author_name || '已注销用户' }}
              </span>
              <span class="flex items-center gap-1">
                <svg
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                /></svg>
                {{ formatDate(article.created_at) }}
              </span>
              <span
                v-if="article.reading_time"
                class="flex items-center gap-1"
              >
                <svg
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                /></svg>
                {{ article.reading_time }} 分钟
              </span>
              <span class="flex items-center gap-1">
                <svg
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                /><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                /></svg>
                {{ article.view_count }}
              </span>
            </div>

            <div class="flex flex-wrap items-center gap-1.5 mb-3">
              <router-link
                v-if="article.category"
                :to="`/categories/${article.category.slug}`"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium transition-colors hover:opacity-80"
                :style="{ backgroundColor: article.category.color + '15', color: article.category.color, borderColor: article.category.color + '30' }"
              >
                <span
                  class="w-1.5 h-1.5 rounded-full"
                  :style="{ backgroundColor: article.category.color }"
                />
                {{ article.category.name }}
              </router-link>
              <router-link
                v-for="tag in article.tags"
                :key="tag.id"
                :to="`/tags/${tag.slug}`"
                class="tag-badge text-xs"
                :style="{ color: tag.color, backgroundColor: tag.color + '10', borderColor: tag.color + '30' }"
              >
                #{{ tag.name }}
              </router-link>
            </div>

            <div
              v-if="article.summary"
              class="p-3 bg-gray-50 dark:bg-dark-200/50 rounded-xl border border-gray-100 dark:border-white/5"
            >
              <p class="text-gray-500 dark:text-gray-400 text-xs leading-relaxed">
                {{ article.summary }}
              </p>
            </div>
          </div>

          <div
            v-if="article.cover_image"
            class="hidden md:block mb-8"
          >
            <div class="flex gap-6 items-stretch">
              <div class="flex-1 min-w-0 cover-text-content">
                <div class="flex items-center gap-2 mb-4">
                  <span
                    v-if="article.is_featured"
                    class="px-2.5 py-0.5 bg-primary text-white text-xs font-medium rounded-full"
                  >精选</span>
                  <span
                    v-if="article.is_pinned"
                    class="px-2.5 py-0.5 bg-amber-500/90 text-white text-xs font-medium rounded-full"
                  >置顶</span>
                </div>

                <h1 class="text-2xl sm:text-3xl md:text-3xl font-bold text-gray-900 dark:text-white mb-4 leading-tight">
                  {{ article.title }}
                </h1>

                <div class="flex flex-wrap items-center gap-3 text-sm text-gray-400 mb-4">
                  <span
                    v-if="article.author || article.author_name"
                    class="flex items-center gap-1.5"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    ><path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    /></svg>
                    {{ article.author?.username || article.author_name || '已注销用户' }}
                  </span>
                  <span class="flex items-center gap-1.5">
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    ><path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                    /></svg>
                    {{ formatDate(article.created_at) }}
                  </span>
                  <span
                    v-if="article.reading_time"
                    class="flex items-center gap-1.5"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    ><path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    /></svg>
                    {{ article.reading_time }} 分钟
                  </span>
                  <span class="flex items-center gap-1.5">
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    ><path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    /><path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                    /></svg>
                    {{ article.view_count }}
                  </span>
                </div>

                <div class="flex flex-wrap items-center gap-2">
                  <router-link
                    v-if="article.category"
                    :to="`/categories/${article.category.slug}`"
                    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors hover:opacity-80"
                    :style="{ backgroundColor: article.category.color + '15', color: article.category.color, borderColor: article.category.color + '30' }"
                  >
                    <span
                      class="w-1.5 h-1.5 rounded-full"
                      :style="{ backgroundColor: article.category.color }"
                    />
                    {{ article.category.name }}
                  </router-link>
                  <router-link
                    v-for="tag in article.tags"
                    :key="tag.id"
                    :to="`/tags/${tag.slug}`"
                    class="tag-badge"
                    :style="{ color: tag.color, backgroundColor: tag.color + '10', borderColor: tag.color + '30' }"
                  >
                    #{{ tag.name }}
                  </router-link>
                </div>
              </div>

              <div
                class="w-2/5 flex-shrink-0 relative rounded-2xl overflow-hidden cover-side-image"
                :style="coverImageHeight > 0 ? { height: coverImageHeight + 'px' } : {}"
              >
                <img
                  ref="coverImageRef"
                  :src="coverImageUrl"
                  :alt="article.title"
                  class="w-full h-full object-cover"
                  :style="{ objectPosition: coverObjectPosition }"
                  loading="eager"
                  decoding="async"
                />
                <div class="absolute inset-0 bg-gradient-to-r from-black/20 via-transparent to-transparent" />
              </div>
            </div>

            <div
              v-if="article.summary"
              class="mt-4 p-4 bg-gray-50 dark:bg-dark-200/50 rounded-xl border border-gray-100 dark:border-white/5"
            >
              <p class="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">
                {{ article.summary }}
              </p>
            </div>
          </div>

          <template v-if="!article.cover_image">
            <div class="flex items-center gap-2 mb-4">
              <span
                v-if="article.is_featured"
                class="px-2.5 py-0.5 bg-primary text-white text-xs font-medium rounded-full"
              >精选</span>
              <span
                v-if="article.is_pinned"
                class="px-2.5 py-0.5 bg-amber-500/90 text-white text-xs font-medium rounded-full"
              >置顶</span>
            </div>

            <h1 class="text-2xl sm:text-3xl md:text-3xl font-bold text-gray-900 dark:text-white mb-4 leading-tight">
              {{ article.title }}
            </h1>

            <div class="flex flex-wrap items-center gap-3 text-sm text-gray-400 mb-4">
              <span
                v-if="article.author || article.author_name"
                class="flex items-center gap-1.5"
              >
                <svg
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                /></svg>
                {{ article.author?.username || article.author_name || '已注销用户' }}
              </span>
              <span class="flex items-center gap-1.5">
                <svg
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                /></svg>
                {{ formatDate(article.created_at) }}
              </span>
              <span
                v-if="article.reading_time"
                class="flex items-center gap-1.5"
              >
                <svg
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                /></svg>
                {{ article.reading_time }} 分钟
              </span>
              <span class="flex items-center gap-1.5">
                <svg
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                /><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                /></svg>
                {{ article.view_count }}
              </span>
            </div>

            <div class="flex flex-wrap items-center gap-2 mb-4">
              <router-link
                v-if="article.category"
                :to="`/categories/${article.category.slug}`"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors hover:opacity-80"
                :style="{ backgroundColor: article.category.color + '15', color: article.category.color, borderColor: article.category.color + '30' }"
              >
                <span
                  class="w-1.5 h-1.5 rounded-full"
                  :style="{ backgroundColor: article.category.color }"
                />
                {{ article.category.name }}
              </router-link>
              <router-link
                v-for="tag in article.tags"
                :key="tag.id"
                :to="`/tags/${tag.slug}`"
                class="tag-badge"
                :style="{ color: tag.color, backgroundColor: tag.color + '10', borderColor: tag.color + '30' }"
              >
                #{{ tag.name }}
              </router-link>
            </div>

            <div
              v-if="article.summary"
              class="p-4 bg-gray-50 dark:bg-dark-200/50 rounded-xl border border-gray-100 dark:border-white/5 mb-6"
            >
              <p class="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">
                {{ article.summary }}
              </p>
            </div>
          </template>
        </header>

        <div
          class="article-content"
          v-html="renderedContent"
        />

        <div
          v-if="articleFiles.length > 0"
          class="mt-8 p-4 glass-card"
        >
          <div class="mb-3">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2 mb-2">
              <svg
                class="w-4 h-4 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
              /></svg>
              附件下载
            </h3>
            <div class="flex items-center justify-between text-xs">
              <div class="flex items-center gap-2">
                <label class="flex items-center gap-1.5 cursor-pointer">
                  <input id="article-select-all-files"
                    type="checkbox"
                    :checked="selectedFileIds.size === articleFiles.length && articleFiles.length > 0"
                    class="w-3.5 h-3.5 rounded border-gray-300 text-primary focus:ring-primary"
                    @change="toggleSelectAll"
                  >
                  <span class="text-gray-700 dark:text-gray-300 font-medium">全选</span>
                </label>
                <span class="text-gray-400">|</span>
                <span class="text-gray-500">{{ articleFiles.length }} 个文件</span>
              </div>
              <button
                class="flex items-center justify-center gap-1 px-2 py-1 bg-primary/10 text-primary hover:bg-primary/20 rounded transition-colors min-w-[100px]"
                :class="{ 'opacity-0 pointer-events-none': selectedFileIds.size === 0 }"
                @click="handleBatchDownload"
              >
                <svg
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                下载选中 ({{ selectedFileIds.size }})
              </button>
            </div>
          </div>
          <div class="space-y-2">
            <div
              v-for="file in articleFiles"
              :id="`file-${file.id}`"
              :key="file.id"
              class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-dark-300/50 rounded-lg border transition-colors scroll-mt-20"
              :class="[selectedFileIds.has(file.id) ? 'border-primary bg-primary/5' : 'border-gray-200 dark:border-white/5 hover:border-primary/30']"
            >
              <div class="flex items-center gap-2 min-w-0 flex-1">
                <input :id="'article-select-file-' + file.id"
                  type="checkbox"
                  :checked="selectedFileIds.has(file.id)"
                  class="w-3.5 h-3.5 rounded border-gray-300 text-primary focus:ring-primary flex-shrink-0"
                  @change="toggleFileSelection(file.id)"
                >
                <span
                  class="w-7 h-7 flex items-center justify-center rounded flex-shrink-0"
                  :class="[getFileIconInfo(file.file_type, file.mime_type, file.original_filename).bg, getFileIconInfo(file.file_type, file.mime_type, file.original_filename).color]"
                  v-html="getFileIconInfo(file.file_type, file.mime_type, file.original_filename).svg"
                />
                <div class="min-w-0 flex-1">
                  <div class="text-xs text-gray-900 dark:text-white break-all">
                    {{ file.original_filename }}
                  </div>
                  <div class="text-[10px] text-gray-500">
                    {{ formatFileSize(file.file_size) }} · {{ file.download_count }} 次下载
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-1 flex-shrink-0 ml-2">
                <button
                  class="w-7 h-7 flex items-center justify-center text-emerald-500 hover:bg-emerald-500/10 rounded transition-colors relative"
                  data-tooltip="预览"
                  @click="openPreview(file)"
                >
                  <svg
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  ><path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  /><path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  /></svg>
                </button>
                <button
                  class="w-7 h-7 flex items-center justify-center text-primary hover:bg-primary/10 rounded transition-colors relative"
                  data-tooltip="下载"
                  @click="downloadFile(file)"
                >
                  <svg
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  ><path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  /></svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <FilePreview
          v-if="showPreview && previewFile"
          :file="previewFile"
          @close="closePreview"
        />

        <div class="mt-8 pt-6 border-t border-gray-100 dark:border-white/5 flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center gap-2">
            <button
              :disabled="isLiking"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-all duration-200 relative"
              :class="isLiked 
                ? 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/20 text-red-500 hover:bg-red-100 dark:hover:bg-red-500/20' 
                : 'bg-gray-50 dark:bg-dark-300 border-gray-200 dark:border-white/5 text-gray-500 hover:text-red-500 hover:border-red-200 hover:bg-red-50 dark:hover:bg-red-500/10'"
              :data-tooltip="isLiked ? '取消点赞' : '点赞'"
              @click="handleLike"
            >
              <svg
                class="w-4 h-4 transition-transform duration-200"
                :class="{ 'scale-110': isLiked, 'group-hover:scale-110': !isLiked }"
                :fill="isLiked ? 'currentColor' : 'none'"
                stroke="currentColor"
                viewBox="0 0 24 24"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
              /></svg>
              <span class="text-sm">{{ likeCount }}</span>
            </button>
            <button
              :disabled="isBookmarking"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-all duration-200 relative"
              :class="isBookmarked 
                ? 'bg-amber-50 dark:bg-amber-500/10 border-amber-200 dark:border-amber-500/20 text-amber-500 hover:bg-amber-100 dark:hover:bg-amber-500/20' 
                : 'bg-gray-50 dark:bg-dark-300 border-gray-200 dark:border-white/5 text-gray-500 hover:text-amber-500 hover:border-amber-200 hover:bg-amber-50 dark:hover:bg-amber-500/10'"
              :data-tooltip="isBookmarked ? '取消收藏' : '收藏'"
              @click="handleBookmark"
            >
              <svg
                class="w-4 h-4 transition-transform duration-200"
                :class="{ 'scale-110': isBookmarked, 'group-hover:scale-110': !isBookmarked }"
                :fill="isBookmarked ? 'currentColor' : 'none'"
                stroke="currentColor"
                viewBox="0 0 24 24"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
              /></svg>
              <span class="text-sm">{{ isBookmarked ? '已收藏' : '收藏' }}</span>
              <span class="text-sm ml-0.5">{{ bookmarkCount }}</span>
            </button>
            <button
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-50 dark:bg-dark-300 border border-gray-200 dark:border-white/5 text-gray-500 hover:text-primary hover:border-primary/30 transition-colors relative"
              data-tooltip="复制链接"
              @click="copyLink"
            >
              <svg
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
              /></svg>
              <span class="text-sm">复制链接</span>
              <span
                v-if="showCopySuccess"
                class="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-cyber-green text-white text-xs rounded"
              >已复制!</span>
            </button>
            <button
              class="p-1.5 rounded-lg bg-gray-50 dark:bg-dark-300 border border-gray-200 dark:border-white/5 text-gray-400 hover:text-primary hover:border-primary/30 transition-colors relative"
              data-tooltip="分享到 X"
              @click="shareArticle('twitter')"
            >
              <svg
                class="w-4 h-4"
                fill="currentColor"
                viewBox="0 0 24 24"
              ><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" /></svg>
            </button>
            <button
              class="p-1.5 rounded-lg bg-gray-50 dark:bg-dark-300 border border-gray-200 dark:border-white/5 text-gray-400 hover:text-[#E6162D] hover:border-[#E6162D]/30 hover:bg-[#E6162D]/5 dark:hover:bg-[#E6162D]/10 transition-all duration-200 relative"
              data-tooltip="分享到微博"
              @click="shareArticle('weibo')"
            >
              <svg
                class="w-4 h-4"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <ellipse
                  cx="10"
                  cy="14"
                  rx="7"
                  ry="5"
                  transform="rotate(-15 10 14)"
                />
                <circle
                  cx="9"
                  cy="13.5"
                  r="2"
                  fill="white"
                />
                <path
                  d="M16 5c2.5 0 4.5 2 4.5 4.5"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  fill="none"
                />
                <path
                  d="M16 2c3.5 0 6 2.5 6 6"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  fill="none"
                />
              </svg>
            </button>
          </div>
          <router-link
            to="/"
            class="text-sm text-gray-400 hover:text-primary transition-colors flex items-center gap-1"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            ><path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            /></svg>
            返回首页
          </router-link>
        </div>

        <CommentSection
          v-if="article"
          :article-id="article.id"
          :article-title="article.title"
        />
      </div>

      <aside class="lg:w-72 flex-shrink-0 hidden lg:block lg:order-3">
        <div class="lg:sticky lg:top-20 space-y-6">
          <div
            v-if="tocItems.length > 0"
            class="glass-card p-5"
          >
            <div class="flex items-center justify-between mb-3">
              <h3 class="sidebar-widget-title mb-0 pb-0 border-0">
                目录
              </h3>
              <button
                class="lg:hidden p-1 rounded hover:bg-gray-100 dark:hover:bg-dark-300"
                @click="showToc = !showToc"
              >
                <svg
                  class="w-4 h-4 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  :d="showToc ? 'M5 15l7-7 7 7' : 'M19 9l-7 7-7-7'"
                /></svg>
              </button>
            </div>
            <nav
              ref="tocNavRef"
              :class="{ 'hidden lg:block': !showToc }"
              class="space-y-1 max-h-[60vh] overflow-y-auto"
            >
              <button
                v-for="item in tocItems"
                :key="item.id"
                :data-heading-id="item.id"
                class="block w-full text-left text-sm py-1 transition-colors truncate"
                :class="[
                  activeHeading === item.id ? 'text-primary font-medium' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300',
                  item.level === 1 ? 'pl-0' : item.level === 2 ? 'pl-3' : item.level === 3 ? 'pl-6' : 'pl-9'
                ]"
                @click="scrollToHeading(item.id)"
              >
                {{ item.text }}
              </button>
            </nav>
          </div>

          <BlogSidebar />
        </div>
      </aside>

      <aside class="lg:hidden mt-8 space-y-4" aria-label="侧边栏内容">
        <LeftSidebar />
        <BlogSidebar />
      </aside>

      <button
        v-if="tocItems.length > 0"
        class="lg:hidden fixed right-4 bottom-32 md:right-5 md:bottom-36 z-40 w-10 h-10 md:w-11 md:h-11 flex items-center justify-center rounded-full bg-primary text-white shadow-lg hover:bg-primary/90 transition-all active:scale-95"
        @click="openMobileToc"
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
            d="M4 6h16M4 10h16M4 14h10M4 18h7"
          />
        </svg>
      </button>

      <Teleport to="body">
        <div
          v-if="showMobileToc"
          class="lg:hidden fixed inset-0 z-50"
        >
          <div
            class="absolute inset-0 bg-black/50 backdrop-blur-sm"
            @click="showMobileToc = false"
          />
          <div class="mobile-toc-drawer absolute bottom-0 left-0 right-0 bg-white dark:bg-dark-200 rounded-t-2xl max-h-[70vh] flex flex-col">
            <div class="flex items-center justify-between px-5 py-3 border-b border-gray-200 dark:border-white/10 flex-shrink-0">
              <h3 class="text-base font-semibold text-gray-800 dark:text-gray-200">
                目录
              </h3>
              <button
                class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-300 text-gray-400"
                @click="showMobileToc = false"
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
            <nav ref="mobileTocNavRef" class="overflow-y-auto overscroll-contain px-5 py-3 space-y-1 flex-1">
              <button
                v-for="item in tocItems"
                :key="item.id"
                :data-mobile-heading-id="item.id"
                class="block w-full text-left text-sm py-2 transition-colors truncate"
                :class="[
                  activeHeading === item.id ? 'text-primary font-medium' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200',
                  item.level === 1 ? 'pl-0' : item.level === 2 ? 'pl-4' : item.level === 3 ? 'pl-8' : 'pl-12'
                ]"
                @click="scrollToHeading(item.id); showMobileToc = false"
              >
                {{ item.text }}
              </button>
            </nav>
          </div>
        </div>
      </Teleport>
    </article>

    <div
      v-else
      class="text-center py-20"
    >
      <div class="max-w-md mx-auto">
        <svg
          class="w-16 h-16 mx-auto mb-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p class="text-gray-400 text-lg mb-2">
          {{ error || '文章不存在' }}
        </p>
        <p
          v-if="error && error.includes('网络')"
          class="text-gray-500 text-sm mb-4"
        >
          请检查您的网络连接或尝试刷新页面
        </p>
        <div class="flex gap-4 justify-center">
          <button
            class="btn-primary"
            @click="refreshPage"
          >
            刷新页面
          </button>
          <router-link
            to="/"
            class="btn-secondary"
          >
            返回首页
          </router-link>
        </div>
      </div>
    </div>
    <MermaidFullscreen ref="mermaidFullscreen" />
  </div>
</template>

<style scoped>
.cover-side-image {
  transition: height 0.3s ease;
}

.cover-side-image img {
  transition: object-position 0.3s ease;
}

.article-content :deep(h1),
.article-content :deep(h2),
.article-content :deep(h3),
.article-content :deep(h4) {
  @apply text-gray-900 dark:text-white font-bold mt-8 mb-4 scroll-mt-20;
}

.article-content :deep(h1) { @apply text-2xl md:text-3xl; }
.article-content :deep(h2) { @apply text-xl md:text-2xl; }
.article-content :deep(h3) { @apply text-lg md:text-xl; }

.article-content :deep(p) {
  @apply text-gray-700 dark:text-gray-300 leading-relaxed mb-4;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.article-content :deep(a) { 
  @apply text-primary hover:underline;
  word-break: break-word;
  overflow-wrap: break-word;
}

.article-content :deep(ul),
.article-content :deep(ol) {
  @apply my-4 pl-6 text-gray-700 dark:text-gray-300;
}

.article-content :deep(ul) { @apply list-disc; }
.article-content :deep(ol) { @apply list-decimal; }
.article-content :deep(li) { @apply mb-2; }

.article-content :deep(blockquote) {
  @apply border-l-4 border-primary pl-4 my-4 text-gray-500 dark:text-gray-400 italic;
}

.article-content :deep(pre:not(.code-block-wrapper pre)) {
  @apply bg-gray-50 dark:bg-dark-300 rounded-xl p-4 overflow-x-auto overflow-y-hidden my-4 border border-gray-200 dark:border-white/5;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
}

.article-content :deep(.code-block-wrapper) {
  @apply relative overflow-visible;
  min-width: 0;
}

.article-content :deep(.code-block-wrapper pre) {
  @apply bg-gray-50 dark:bg-dark-300 rounded-xl overflow-x-auto overflow-y-hidden border border-gray-200 dark:border-white/5;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
  padding: 1rem;
  padding-top: 2.5rem;
  margin-bottom: 0.5rem;
}

.article-content :deep(.code-block-wrapper pre.mermaid) {
  @apply bg-gray-50 dark:bg-dark-300 rounded-xl overflow-x-auto overflow-y-hidden border border-gray-200 dark:border-white/5;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
  padding: 1rem;
  padding-top: 2.5rem;
  margin-bottom: 0.5rem;
}

.article-content :deep(.code-block-wrapper code) {
  white-space: pre;
}

.article-content :deep(code) {
  @apply text-sm font-mono;
}

.article-content :deep(p code) {
  @apply px-1.5 py-0.5 bg-gray-100 dark:bg-dark-300 rounded text-sm text-primary;
}

.article-content :deep(.overflow-x-auto:not(.mermaid)) {
  @apply my-4 -mx-4 px-4;
  max-width: calc(100vw - 2rem);
}

@media (min-width: 1024px) {
  .article-content :deep(.overflow-x-auto:not(.mermaid)) {
    @apply mx-0 px-0;
    max-width: 100%;
  }
}

.article-content :deep(table) {
  @apply border-collapse;
}

.article-content :deep(th),
.article-content :deep(td) {
  @apply border border-gray-200 dark:border-white/10 px-4 py-2 text-left text-gray-700 dark:text-gray-300 whitespace-nowrap;
}

.article-content :deep(th) {
  @apply bg-gray-50 dark:bg-dark-300 font-semibold text-gray-900 dark:text-white;
}

.article-content :deep(img) {
  @apply rounded-xl max-w-full h-auto my-4;
  display: block;
  width: auto;
  max-height: 80vh;
  object-fit: contain;
}

.article-content :deep(hr) {
  @apply border-gray-200 dark:border-white/10 my-8;
}

.file-highlight {
  animation: file-highlight-pulse 2s ease-in-out;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
  border-color: rgb(59, 130, 246) !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2), 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: scale(1.02);
  transition: all 0.3s ease;
}

.dark .file-highlight {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
  border-color: rgb(96, 165, 250) !important;
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.3), 0 4px 12px rgba(96, 165, 250, 0.2);
}

@keyframes file-highlight-pulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2), 0 4px 12px rgba(59, 130, 246, 0.15); }
  50% { box-shadow: 0 0 0 5px rgba(59, 130, 246, 0.3), 0 6px 16px rgba(59, 130, 246, 0.25); }
}

.article-content :deep(.mermaid-wrapper) {
  width: 100%;
  margin-bottom: 1rem;
}

.article-content :deep(.mermaid) {
  @apply bg-gray-50 dark:bg-dark-300 rounded-xl overflow-x-auto overflow-y-hidden border border-gray-200 dark:border-white/5;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
}

.article-content :deep(.mermaid svg) {
  height: auto;
  display: block;
  margin: 0 auto;
}

.mobile-toc-drawer {
  animation: mobile-toc-slide-up 0.25s ease-out;
}

@keyframes mobile-toc-slide-up {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}
</style>
