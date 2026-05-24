<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { marked } from 'marked'
import hljs from '@/utils/hljs'
import DOMPurify from 'dompurify'
import { initMermaid, renderMermaidDiagrams, rerenderMermaidOnThemeChange } from '@/utils/mermaid'
import { useThemeStore } from '@/stores'

const props = withDefaults(defineProps<{
  content: string
  showLangLabel?: boolean
}>(), {
  showLangLabel: false
})

const themeStore = useThemeStore()
const previewRef = ref<HTMLElement | null>(null)

const createRenderer = () => {
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
    
    const copyIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>`
      const langIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 inline-block mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>`
      
    return `<div class="code-block-wrapper relative group">
      <div class="absolute top-2 left-3 right-1 flex justify-between items-center z-20">
        <span class="text-sm text-gray-500 dark:text-gray-400">${langIcon}${validLang}</span>
        <button class="copy-code-btn flex items-center justify-center w-7 h-7 rounded text-gray-500 hover:text-primary transition-colors" data-code="${encodedCode}">${copyIcon}</button>
      </div>
      <pre><code class="hljs language-${validLang}">${highlighted}</code></pre>
    </div>`
  }

  renderer.heading = (text: string, level: number, _raw: string) => {
    const sizes: Record<number, string> = {
      1: 'text-lg font-bold',
      2: 'text-base font-bold',
      3: 'text-sm font-bold',
      4: 'text-sm font-semibold',
      5: 'text-sm font-medium',
      6: 'text-xs font-medium'
    }
    const id = text.toLowerCase().replace(/[^\w\u4e00-\u9fa5]+/g, '-')
    return `<h${level} id="${id}" class="${sizes[level] || 'text-sm font-medium'} mt-3 mb-2">${text}</h${level}>`
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

  renderer.image = (href: string, title: string | null | undefined, text: string) => {
    const titleAttr = title ? ` title="${title}"` : ''
    return `<img src="${href}" alt="${text}"${titleAttr} class="max-w-full h-auto rounded my-2 max-h-60 object-contain" loading="lazy" />`
  }

  renderer.blockquote = (quote: string) => {
    return `<blockquote class="border-l-2 border-primary/50 pl-3 my-2 text-gray-400 text-sm">${quote}</blockquote>`
  }

  renderer.list = (body: string, ordered: boolean, _start: number | string) => {
    const tag = ordered ? 'ol' : 'ul'
    return `<${tag} class="my-2 pl-4 text-sm ${ordered ? 'list-decimal' : 'list-disc'}">${body}</${tag}>`
  }

  renderer.listitem = (text: string, _task: boolean, _checked: boolean) => {
    return `<li class="mb-1">${text}</li>`
  }

  renderer.table = (header: string, body: string) => {
    return `<div class="overflow-x-auto my-2 text-sm"><table class="min-w-full border border-gray-200 dark:border-white/10 rounded"><thead class="bg-gray-100 dark:bg-dark-100">${header}</thead><tbody>${body}</tbody></table></div>`
  }

  renderer.tablecell = (content: string, flags: { header: boolean; align: string | null }) => {
    const tag = flags.header ? 'th' : 'td'
    const align = flags.align ? ` style="text-align:${flags.align}"` : ''
    return `<${tag} class="px-2 py-1 border border-gray-200 dark:border-white/10"${align}>${content}</${tag}>`
  }

  renderer.paragraph = (text: string) => {
    return `<p class="mb-2 last:mb-0">${text}</p>`
  }

  renderer.codespan = (code: string) => {
    return `<code class="bg-primary/10 text-primary px-1 py-0.5 rounded text-xs font-mono">${code}</code>`
  }

  renderer.strong = (text: string) => {
    return `<strong class="font-semibold text-white">${text}</strong>`
  }

  renderer.em = (text: string) => {
    return `<em class="italic">${text}</em>`
  }

  renderer.del = (text: string) => {
    return `<del class="line-through text-gray-500">${text}</del>`
  }

  renderer.hr = () => {
    return `<hr class="border-gray-200 dark:border-white/10 my-3" />`
  }

  return renderer
}

let cachedRenderer: ReturnType<typeof createRenderer> | null = null

const getRenderer = () => {
  if (!cachedRenderer) {
    cachedRenderer = createRenderer()
  }
  return cachedRenderer
}

const renderedContent = computed(() => {
  if (!props.content) return ''
  
  const renderer = getRenderer()
  
  const rawHtml = marked.parse(props.content, { renderer, gfm: true, breaks: true, async: false }) as string
  
  const html = DOMPurify.sanitize(rawHtml, {
    ADD_ATTR: ['target', 'rel', 'loading', 'class', 'data-mermaid', 'data-mermaid-code'],
    ADD_TAGS: ['iframe'],
  })
  
  return html.replace(/@([^\s<]+)/g, '<span class="mention text-primary font-medium hover:underline cursor-pointer">@$1</span>')
})

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
        btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>`
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
  
  nextTick(() => {
    if (previewRef.value) {
      renderMermaidDiagrams(previewRef.value, '.mermaid', themeStore.isDark)
    }
  })
})

watch(() => props.content, () => {
  nextTick(() => {
    if (previewRef.value) {
      renderMermaidDiagrams(previewRef.value, '.mermaid', themeStore.isDark)
    }
  })
})

onUnmounted(() => {
  if (previewRef.value) {
    previewRef.value.removeEventListener('click', handleCopyCode)
  }
})

watch(() => themeStore.isDark, async (isDark) => {
  if (previewRef.value) {
    await rerenderMermaidOnThemeChange(previewRef.value, '.mermaid', isDark)
  }
})
</script>

<template>
  <div 
    ref="previewRef"
    class="comment-markdown-preview text-gray-600 dark:text-gray-300 text-sm leading-relaxed"
    v-html="renderedContent"
  />
</template>

<style scoped>
.comment-markdown-preview :deep(pre) {
  @apply bg-gray-50 dark:bg-dark-300;
  border-radius: 0.75rem;
  padding: 0.75rem;
  overflow-x: auto;
  overflow-y: hidden;
  margin: 0.5rem 0;
  white-space: pre;
  word-wrap: normal;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
}

.comment-markdown-preview :deep(pre code) {
  white-space: pre;
}

.comment-markdown-preview :deep(.code-block-wrapper) {
  position: relative;
}

.comment-markdown-preview :deep(.code-block-wrapper pre) {
  @apply bg-gray-50 dark:bg-dark-300 rounded-xl overflow-x-auto overflow-y-hidden border border-gray-200 dark:border-white/5;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
  padding: 0.75rem;
  padding-top: 2.5rem;
  margin-bottom: 0.5rem;
}

.comment-markdown-preview :deep(.code-block-wrapper pre.mermaid) {
  @apply bg-gray-50 dark:bg-dark-300 rounded-xl overflow-x-auto overflow-y-hidden border border-gray-200 dark:border-white/5;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
  padding: 0.75rem;
  padding-top: 2.5rem;
  margin-bottom: 0.5rem;
}

.comment-markdown-preview :deep(.hljs) {
  background: transparent;
  padding: 0;
  font-size: 0.75rem;
}

.comment-markdown-preview :deep(code:not(.hljs)) {
  @apply bg-gray-200 dark:bg-dark-200 text-primary;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.comment-markdown-preview :deep(ul) {
  list-style-type: disc;
}

.comment-markdown-preview :deep(ol) {
  list-style-type: decimal;
}

.comment-markdown-preview :deep(a) {
  @apply text-primary;
  text-decoration: none;
  transition: all 0.2s;
  word-break: break-word;
  overflow-wrap: break-word;
}

.comment-markdown-preview :deep(a:hover) {
  text-decoration: underline;
  opacity: 0.8;
}

.comment-markdown-preview :deep(.mermaid-wrapper) {
  width: 100%;
  margin-bottom: 0.5rem;
}

.comment-markdown-preview :deep(.mermaid) {
  @apply bg-gray-50 dark:bg-dark-300 rounded-xl overflow-x-auto overflow-y-hidden border border-gray-200 dark:border-white/5;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
}

.comment-markdown-preview :deep(.mermaid svg) {
  height: auto;
  display: block;
  margin: 0 auto;
}
</style>
