<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import DOMPurify from 'dompurify'

const props = withDefaults(defineProps<{
  content: string
  showLangLabel?: boolean
}>(), {
  showLangLabel: false
})

const previewRef = ref<HTMLElement | null>(null)

const createRenderer = () => {
  const renderer = new marked.Renderer()

  renderer.code = (code: string, infostring: string | undefined, _escaped: boolean) => {
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
    
    const langLabelHtml = props.showLangLabel 
      ? `<div class="text-xs text-gray-500 absolute top-1 left-2">${validLang}</div>` 
      : ''
    
    return `<div class="code-block-wrapper relative group">
      <div class="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
        <button class="copy-code-btn px-1.5 py-0.5 bg-dark-200 rounded text-xs text-gray-400 hover:text-primary transition-colors" data-code="${encodedCode}">复制</button>
      </div>
      ${langLabelHtml}
      <pre class="!my-2"><code class="hljs language-${validLang}">${highlighted}</code></pre>
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

const renderedContent = computed(() => {
  if (!props.content) return ''
  
  const renderer = createRenderer()
  
  const rawHtml = marked.parse(props.content, { renderer, gfm: true, breaks: true, async: false }) as string
  
  const html = DOMPurify.sanitize(rawHtml, {
    ADD_ATTR: ['target', 'rel', 'loading', 'class'],
    ADD_TAGS: ['iframe'],
  })
  
  return html.replace(/@([^\s<]+)/g, '<span class="mention text-primary font-medium hover:underline cursor-pointer">@$1</span>')
})

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
  background: #0d0d1a;
  border-radius: 0.375rem;
  padding: 0.75rem;
  overflow-x: auto;
  margin: 0.5rem 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.comment-markdown-preview :deep(.code-block-wrapper) {
  position: relative;
}

.comment-markdown-preview :deep(.hljs) {
  background: transparent;
  padding: 0;
  font-size: 0.75rem;
}

.comment-markdown-preview :deep(ul) {
  list-style-type: disc;
}

.comment-markdown-preview :deep(ol) {
  list-style-type: decimal;
}

.comment-markdown-preview :deep(a) {
  color: #00d4ff;
  text-decoration: none;
  transition: all 0.2s;
}

.comment-markdown-preview :deep(a:hover) {
  text-decoration: underline;
  opacity: 0.8;
}
</style>
