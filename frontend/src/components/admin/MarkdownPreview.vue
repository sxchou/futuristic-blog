<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, nextTick } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import DOMPurify from 'dompurify'

const props = defineProps<{
  content: string
}>()

const emit = defineEmits<{
  (e: 'scroll', scrollTop: number): void
}>()

const previewRef = ref<HTMLElement | null>(null)
const isRendering = ref(false)

const renderer = new marked.Renderer()

renderer.code = (code: string, language: string | undefined) => {
  const validLang = language && hljs.getLanguage(language) ? language : 'plaintext'
  const highlighted = hljs.highlight(code, { language: validLang }).value
  const encodedCode = encodeURIComponent(code)
  return `<div class="code-block-wrapper relative group">
    <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
      <button class="copy-code-btn px-2 py-1 bg-dark-200 rounded text-xs text-gray-400 hover:text-primary transition-colors" data-code="${encodedCode}">复制</button>
    </div>
    <div class="text-xs text-gray-500 absolute top-2 left-2">${validLang}</div>
    <pre><code class="hljs language-${validLang}">${highlighted}</code></pre>
  </div>`
}

renderer.heading = (text: string, level: number) => {
  const id = text.toLowerCase().replace(/[^\w\u4e00-\u9fa5]+/g, '-')
  return `<h${level} id="${id}" class="heading-${level}">${text}</h${level}>`
}

renderer.link = (href: string, title: string | null | undefined, text: string) => {
  const titleAttr = title ? ` title="${title}"` : ''
  return `<a href="${href}"${titleAttr} target="_blank" rel="noopener noreferrer" class="text-primary hover:underline">${text}</a>`
}

renderer.image = (href: string, title: string | null | undefined, text: string) => {
  const titleAttr = title ? ` title="${title}"` : ''
  return `<img src="${href}" alt="${text}"${titleAttr} class="max-w-full h-auto rounded-lg my-4" loading="lazy" />`
}

renderer.blockquote = (quote: string) => {
  return `<blockquote class="border-l-4 border-primary pl-4 my-4 italic text-gray-400">${quote}</blockquote>`
}

renderer.list = (body: string, ordered: boolean) => {
  const tag = ordered ? 'ol' : 'ul'
  return `<${tag} class="my-4 pl-6 ${ordered ? 'list-decimal' : 'list-disc'}">${body}</${tag}>`
}

renderer.table = (header: string, body: string) => {
  return `<div class="overflow-x-auto my-4"><table class="min-w-full border border-gray-200 dark:border-white/10"><thead class="bg-gray-100 dark:bg-dark-100">${header}</thead><tbody>${body}</tbody></table></div>`
}

renderer.tablecell = (content: string, flags: { header: boolean; align: string | null }) => {
  const tag = flags.header ? 'th' : 'td'
  const align = flags.align ? ` style="text-align:${flags.align}"` : ''
  return `<${tag} class="px-4 py-2 border border-gray-200 dark:border-white/10"${align}>${content}</${tag}>`
}

marked.setOptions({
  renderer,
  gfm: true,
  breaks: true
})

const renderedContent = computed(() => {
  if (!props.content) return ''
  isRendering.value = true
  
  nextTick(() => {
    isRendering.value = false
  })
  
  return DOMPurify.sanitize(marked(props.content) as string)
})

const handleScroll = (e: Event) => {
  const target = e.target as HTMLElement
  emit('scroll', target.scrollTop)
}

const scrollTo = (scrollTop: number) => {
  if (previewRef.value) {
    previewRef.value.scrollTop = scrollTop
  }
}

const handleCopyCode = (e: MouseEvent) => {
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

onMounted(() => {
  if (previewRef.value) {
    previewRef.value.addEventListener('click', handleCopyCode)
  }
})

onUnmounted(() => {
  if (previewRef.value) {
    previewRef.value.removeEventListener('click', handleCopyCode)
  }
})

defineExpose({
  scrollTo,
  $el: previewRef
})
</script>

<template>
  <div class="markdown-preview-container h-full flex flex-col">
    <div class="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-dark-100 border-b border-gray-200 dark:border-white/10">
      <span class="text-sm font-medium text-gray-700 dark:text-gray-300">预览</span>
      <div v-if="isRendering" class="flex items-center gap-2 text-xs text-gray-500">
        <svg class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>渲染中...</span>
      </div>
    </div>
    <div 
      ref="previewRef"
      class="preview-content flex-1 overflow-auto p-4 prose prose-invert max-w-none"
      @scroll="handleScroll"
      v-html="renderedContent"
    />
  </div>
</template>

<style scoped>
.markdown-preview-container {
  background: var(--bg-color, #1a1a2e);
}

.preview-content {
  min-height: 200px;
}

.preview-content :deep(h1) {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.preview-content :deep(h2) {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.preview-content :deep(h3) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
}

.preview-content :deep(h4),
.preview-content :deep(h5),
.preview-content :deep(h6) {
  font-size: 1rem;
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.preview-content :deep(p) {
  margin-bottom: 1rem;
  line-height: 1.75;
}

.preview-content :deep(a) {
  color: #00d4ff;
  text-decoration: none;
  transition: all 0.2s;
}

.preview-content :deep(a:hover) {
  text-decoration: underline;
  opacity: 0.8;
}

.preview-content :deep(code:not(.hljs)) {
  background: rgba(0, 212, 255, 0.1);
  color: #00d4ff;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.preview-content :deep(pre) {
  background: #0d0d1a;
  border-radius: 0.5rem;
  padding: 1rem;
  overflow-x: auto;
  margin: 1rem 0;
}

.preview-content :deep(.code-block-wrapper) {
  position: relative;
}

.preview-content :deep(.hljs) {
  background: transparent;
  padding: 0;
}

.preview-content :deep(blockquote) {
  border-left: 4px solid #00d4ff;
  padding-left: 1rem;
  margin: 1rem 0;
  color: #9ca3af;
  font-style: italic;
}

.preview-content :deep(ul),
.preview-content :deep(ol) {
  margin: 1rem 0;
  padding-left: 1.5rem;
}

.preview-content :deep(ul) {
  list-style-type: disc;
}

.preview-content :deep(ol) {
  list-style-type: decimal;
}

.preview-content :deep(li) {
  margin-bottom: 0.5rem;
}

.preview-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.5rem;
  margin: 1rem 0;
}

.preview-content :deep(hr) {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin: 2rem 0;
}

.preview-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.preview-content :deep(th),
.preview-content :deep(td) {
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.5rem 1rem;
  text-align: left;
}

.preview-content :deep(th) {
  background: rgba(0, 212, 255, 0.1);
  font-weight: 600;
}

.preview-content :deep(strong) {
  font-weight: 600;
  color: #fff;
}

.preview-content :deep(em) {
  font-style: italic;
}

.preview-content :deep(del) {
  text-decoration: line-through;
  color: #9ca3af;
}
</style>
