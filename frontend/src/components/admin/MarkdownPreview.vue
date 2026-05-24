<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { marked } from 'marked'
import hljs from '@/utils/hljs'
import DOMPurify from 'dompurify'
import { initMermaid, renderMermaidDiagrams, rerenderMermaidOnThemeChange, debounce } from '@/utils/mermaid'
import { useThemeStore } from '@/stores'

const props = defineProps<{
  content: string
}>()

const emit = defineEmits<{
  (e: 'scroll', scrollTop: number): void
}>()

const themeStore = useThemeStore()
const previewRef = ref<HTMLElement | null>(null)
const isRendering = ref(false)
const renderedHtml = ref('')

const renderer = new marked.Renderer()

renderer.code = (code: string, infostring: string | undefined, _escaped: boolean) => {
  if (infostring === 'mermaid') {
    const encodedCode = encodeURIComponent(code)
    const copyIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>`
    const langIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 inline-block mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>`
    return `<div class="code-block-wrapper relative group mermaid-wrapper" data-mermaid="${encodedCode}">
      <div class="absolute top-2 left-4 right-2 flex justify-between items-center z-20">
        <span class="text-sm text-gray-500 dark:text-gray-400">${langIcon}mermaid</span>
        <button class="copy-code-btn flex items-center justify-center w-8 h-8 rounded text-gray-500 hover:text-primary transition-colors" data-code="${encodedCode}">${copyIcon}</button>
      </div>
      <pre class="mermaid" data-mermaid-code="${encodedCode}">${code}</pre>
    </div>`
  }
  
  let validLang = 'plaintext'
  
  if (infostring) {
    const langMap: Record<string, string> = {
      'js': 'javascript',
      'ts': 'typescript',
      'py': 'python',
      'rb': 'ruby',
      'sh': 'bash',
      'shell': 'bash',
      'yml': 'yaml',
      'md': 'markdown',
      'cs': 'csharp',
      'c++': 'cpp',
      'c#': 'csharp',
    }
    
    const normalizedLang = infostring.toLowerCase()
    validLang = langMap[normalizedLang] || normalizedLang
    
    if (!hljs.getLanguage(validLang)) {
      validLang = 'plaintext'
    }
  }
  
  const highlighted = hljs.highlight(code, { language: validLang, ignoreIllegals: true }).value
  const encodedCode = encodeURIComponent(code)
  const copyIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>`
  const langIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 inline-block mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>`
  return `<div class="code-block-wrapper relative group">
    <div class="absolute top-2 left-4 right-2 flex justify-between items-center z-20">
      <span class="text-sm text-gray-500 dark:text-gray-400">${langIcon}${validLang}</span>
      <button class="copy-code-btn flex items-center justify-center w-8 h-8 rounded text-gray-500 hover:text-primary transition-colors" data-code="${encodedCode}">${copyIcon}</button>
    </div>
    <pre><code class="hljs language-${validLang}">${highlighted}</code></pre>
  </div>`
}

renderer.heading = (text: string, level: number, _raw: string) => {
  const id = text.toLowerCase().replace(/[^\w\u4e00-\u9fa5]+/g, '-')
  return `<h${level} id="${id}" class="heading-${level}">${text}</h${level}>`
}

renderer.link = (href: string, title: string | null | undefined, text: string) => {
  const titleAttr = title ? ` title="${title}"` : ''
  
  const hasBlankTarget = text.includes('{:target="_blank"}')
  const cleanText = text.replace('{:target="_blank"}', '').trim()
  
  const isInternal = href.startsWith('/') || href.startsWith('#') || href.startsWith(window.location.origin)
  
  if (hasBlankTarget) {
    return `<a href="${href}"${titleAttr} target="_blank" rel="noopener noreferrer" class="text-primary hover:underline">${cleanText}</a>`
  }
  
  if (isInternal) {
    return `<a href="${href}"${titleAttr} class="text-primary hover:underline">${cleanText}</a>`
  }
  
  return `<a href="${href}"${titleAttr} target="_blank" rel="noopener noreferrer" class="text-primary hover:underline">${cleanText}</a>`
}

renderer.image = (href: string, title: string | null | undefined, text: string) => {
  const titleAttr = title ? ` title="${title}"` : ''
  return `<img src="${href}" alt="${text}"${titleAttr} class="max-w-full h-auto rounded-lg my-4" loading="lazy" />`
}

renderer.blockquote = (quote: string) => {
  return `<blockquote class="border-l-4 border-primary pl-4 my-4 italic text-gray-400">${quote}</blockquote>`
}

renderer.list = (body: string, ordered: boolean, _start: number | string) => {
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

const renderMarkdown = () => {
  if (!props.content) {
    renderedHtml.value = ''
    return
  }
  
  isRendering.value = true
  
  try {
    const rawHtml = marked.parse(props.content, { async: false }) as string
    renderedHtml.value = DOMPurify.sanitize(rawHtml, {
      ADD_ATTR: ['target', 'rel', 'loading', 'class', 'data-mermaid', 'data-mermaid-code'],
      ADD_TAGS: ['iframe']
    })
  } catch (error) {
    console.error('Markdown render error:', error)
    renderedHtml.value = ''
  }
  
  nextTick(async () => {
    isRendering.value = false
    const previewContent = document.querySelector('.preview-content')
    if (previewContent) {
      await renderMermaidDiagrams(previewContent as HTMLElement, '.mermaid', themeStore.isDark)
    }
  })
}

const debouncedRender = debounce(renderMarkdown, 300)

watch(() => props.content, () => {
  debouncedRender()
}, { immediate: true })

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
  const btn = target.closest('.copy-code-btn') as HTMLElement
  if (btn) {
    const encodedCode = btn.getAttribute('data-code')
    if (encodedCode) {
      const code = decodeURIComponent(encodedCode)
      const originalHTML = btn.innerHTML
      const originalClass = btn.className
      navigator.clipboard.writeText(code).then(() => {
        btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>`
        btn.className = originalClass + ' text-green-400'
        setTimeout(() => {
          btn.innerHTML = originalHTML
          btn.className = originalClass
        }, 2000)
      })
    }
  }
}

onMounted(async () => {
  await initMermaid(themeStore.isDark)
  
  if (previewRef.value) {
    previewRef.value.addEventListener('click', handleCopyCode)
  }
})

watch(() => themeStore.isDark, async (isDark) => {
  const previewContent = document.querySelector('.preview-content')
  if (previewContent) {
    await rerenderMermaidOnThemeChange(previewContent as HTMLElement, '.mermaid', isDark)
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
      <div
        v-if="isRendering"
        class="flex items-center gap-2 text-xs text-gray-500"
      >
        <svg
          class="animate-spin h-3 w-3"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        <span>渲染中...</span>
      </div>
    </div>
    <div 
      ref="previewRef"
      class="preview-content flex-1 overflow-auto p-4 prose dark:prose-invert max-w-none"
      @scroll="handleScroll"
      v-html="renderedHtml"
    />
  </div>
</template>

<style scoped>
.markdown-preview-container {
  @apply bg-white dark:bg-dark-200;
}

.preview-content {
  min-height: 200px;
}

.preview-content :deep(h1) {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  @apply border-b border-gray-200 dark:border-white/10;
}

.preview-content :deep(h2) {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.25rem;
  @apply border-b border-gray-200 dark:border-white/5;
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
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.preview-content :deep(a) {
  @apply text-primary;
  text-decoration: none;
  transition: all 0.2s;
  word-break: break-word;
  overflow-wrap: break-word;
}

.preview-content :deep(a:hover) {
  text-decoration: underline;
  opacity: 0.8;
}

.preview-content :deep(code:not(.hljs)) {
  @apply bg-primary/10 text-primary;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  word-break: break-word;
}

.preview-content :deep(pre) {
  @apply bg-gray-50 dark:bg-dark-300;
  border-radius: 0.75rem;
  padding: 1rem;
  overflow-x: auto;
  overflow-y: hidden;
  margin: 1rem 0;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
  white-space: pre;
  word-wrap: normal;
}

.preview-content :deep(pre code) {
  white-space: pre;
}

.preview-content :deep(.code-block-wrapper) {
  position: relative;
}

.preview-content :deep(.code-block-wrapper pre) {
  @apply bg-gray-50 dark:bg-dark-300 rounded-xl overflow-x-auto overflow-y-hidden border border-gray-200 dark:border-white/5;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
  padding: 1rem;
  padding-top: 2.5rem;
  margin-bottom: 0.5rem;
}

.preview-content :deep(.code-block-wrapper pre.mermaid) {
  @apply bg-gray-50 dark:bg-dark-300 rounded-xl overflow-x-auto overflow-y-hidden border border-gray-200 dark:border-white/5;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
  padding: 1rem;
  padding-top: 2.5rem;
  margin-bottom: 0.5rem;
}

.preview-content :deep(.mermaid-wrapper) {
  width: 100%;
  margin-bottom: 1rem;
}

.preview-content :deep(.mermaid) {
  @apply bg-gray-50 dark:bg-dark-300 rounded-xl overflow-x-auto overflow-y-hidden border border-gray-200 dark:border-white/5;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
}

.preview-content :deep(.mermaid svg) {
  height: auto;
  display: block;
  margin: 0 auto;
}

.preview-content :deep(.hljs) {
  background: transparent;
  padding: 0;
}

.preview-content :deep(blockquote) {
  @apply border-l-4 border-primary;
  padding-left: 1rem;
  margin: 1rem 0;
  @apply text-gray-500 dark:text-gray-400;
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
  display: block;
  max-height: 80vh;
  object-fit: contain;
}

.preview-content :deep(hr) {
  border: none;
  @apply border-t border-gray-200 dark:border-white/10;
  margin: 2rem 0;
}

.preview-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.preview-content :deep(.overflow-x-auto) {
  overflow-x: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  margin: 1rem 0;
}

.preview-content :deep(th),
.preview-content :deep(td) {
  @apply border border-gray-200 dark:border-white/10;
  padding: 0.5rem 1rem;
  text-align: left;
  white-space: nowrap;
}

.preview-content :deep(th) {
  @apply bg-primary/10;
  font-weight: 600;
}

.preview-content :deep(strong) {
  font-weight: 600;
  @apply text-gray-900 dark:text-white;
}

.preview-content :deep(em) {
  font-style: italic;
}

.preview-content :deep(del) {
  text-decoration: line-through;
  @apply text-gray-500 dark:text-gray-400;
}

@media (max-width: 768px) {
  .preview-content {
    padding: 12px;
  }
  
  .preview-content :deep(h1) {
    font-size: 1.5rem;
    margin-bottom: 0.75rem;
  }
  
  .preview-content :deep(h2) {
    font-size: 1.25rem;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
  }
  
  .preview-content :deep(h3) {
    font-size: 1.125rem;
    margin-top: 0.875rem;
    margin-bottom: 0.375rem;
  }
  
  .preview-content :deep(h4),
  .preview-content :deep(h5),
  .preview-content :deep(h6) {
    font-size: 0.95rem;
  }
  
  .preview-content :deep(p) {
    margin-bottom: 0.75rem;
    line-height: 1.6;
    font-size: 14px;
  }
  
  .preview-content :deep(pre) {
    padding: 12px;
    margin: 0.75rem 0;
    font-size: 12px;
    border-radius: 6px;
  }
  
  .preview-content :deep(code:not(.hljs)) {
    font-size: 12px;
    padding: 0.1rem 0.25rem;
  }
  
  .preview-content :deep(blockquote) {
    padding-left: 0.75rem;
    margin: 0.75rem 0;
    font-size: 14px;
  }
  
  .preview-content :deep(ul),
  .preview-content :deep(ol) {
    margin: 0.75rem 0;
    padding-left: 1.25rem;
    font-size: 14px;
  }
  
  .preview-content :deep(li) {
    margin-bottom: 0.375rem;
  }
  
  .preview-content :deep(th),
  .preview-content :deep(td) {
    padding: 0.375rem 0.5rem;
    font-size: 13px;
  }
  
  .preview-content :deep(img) {
    margin: 0.75rem 0;
    border-radius: 6px;
  }
  
  .preview-content :deep(hr) {
    margin: 1.5rem 0;
  }
}

@media (max-width: 480px) {
  .preview-content {
    padding: 10px;
  }
  
  .preview-content :deep(h1) {
    font-size: 1.25rem;
    margin-bottom: 0.5rem;
    padding-bottom: 0.375rem;
  }
  
  .preview-content :deep(h2) {
    font-size: 1.125rem;
    margin-top: 0.75rem;
    margin-bottom: 0.375rem;
  }
  
  .preview-content :deep(h3) {
    font-size: 1rem;
    margin-top: 0.625rem;
    margin-bottom: 0.25rem;
  }
  
  .preview-content :deep(h4),
  .preview-content :deep(h5),
  .preview-content :deep(h6) {
    font-size: 0.875rem;
  }
  
  .preview-content :deep(p) {
    margin-bottom: 0.5rem;
    line-height: 1.5;
    font-size: 13px;
  }
  
  .preview-content :deep(pre) {
    padding: 10px;
    margin: 0.5rem 0;
    font-size: 11px;
    border-radius: 4px;
  }
  
  .preview-content :deep(code:not(.hljs)) {
    font-size: 11px;
    padding: 0.1rem 0.2rem;
  }
  
  .preview-content :deep(blockquote) {
    padding-left: 0.5rem;
    margin: 0.5rem 0;
    font-size: 13px;
    border-left-width: 3px;
  }
  
  .preview-content :deep(ul),
  .preview-content :deep(ol) {
    margin: 0.5rem 0;
    padding-left: 1rem;
    font-size: 13px;
  }
  
  .preview-content :deep(li) {
    margin-bottom: 0.25rem;
  }
  
  .preview-content :deep(th),
  .preview-content :deep(td) {
    padding: 0.25rem 0.375rem;
    font-size: 12px;
  }
  
  .preview-content :deep(img) {
    margin: 0.5rem 0;
    border-radius: 4px;
  }
  
  .preview-content :deep(hr) {
    margin: 1rem 0;
  }
  
  .preview-content :deep(.code-block-wrapper .copy-code-btn) {
    padding: 2px 6px;
    font-size: 10px;
  }
  
  .preview-content :deep(.code-block-wrapper .text-xs) {
    font-size: 10px;
  }
}

@media (max-width: 360px) {
  .preview-content {
    padding: 8px;
  }
  
  .preview-content :deep(h1) {
    font-size: 1.125rem;
  }
  
  .preview-content :deep(h2) {
    font-size: 1rem;
  }
  
  .preview-content :deep(h3) {
    font-size: 0.875rem;
  }
  
  .preview-content :deep(p) {
    font-size: 12px;
    line-height: 1.4;
  }
  
  .preview-content :deep(pre) {
    padding: 8px;
    font-size: 10px;
  }
  
  .preview-content :deep(code:not(.hljs)) {
    font-size: 10px;
  }
  
  .preview-content :deep(ul),
  .preview-content :deep(ol) {
    font-size: 12px;
    padding-left: 0.875rem;
  }
  
  .preview-content :deep(blockquote) {
    font-size: 12px;
  }
  
  .preview-content :deep(th),
  .preview-content :deep(td) {
    padding: 0.2rem 0.25rem;
    font-size: 11px;
  }
}
</style>
