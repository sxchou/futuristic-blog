<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import CommentMarkdownPreview from './CommentMarkdownPreview.vue'
import EmojiPicker from '@/components/common/EmojiPicker.vue'
import LinkInserterDialog from './LinkInserterDialog.vue'

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
  disabled?: boolean
  replyTo?: string
  rows?: number
  storageKey?: string
  articleTitle?: string
  replyToContent?: string
}>(), {
  placeholder: '写下你的想法...',
  rows: 4
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'submit'): void
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const previewContainerRef = ref<HTMLElement | null>(null)
const showPreview = ref(true)
const previewContent = ref('')
const showLangSelector = ref(false)
const hasUnsavedChanges = ref(false)
const originalValue = ref('')
const isFullscreen = ref(false)
const isSyncingScroll = ref(false)
const langSelectorPosition = ref({ top: 0, left: 0 })
const showMarkdownHelp = ref(false)
const showLinkInserter = ref(false)

const programmingLanguages = [
  { code: 'javascript', label: 'JavaScript', alias: 'js' },
  { code: 'typescript', label: 'TypeScript', alias: 'ts' },
  { code: 'python', label: 'Python', alias: 'py' },
  { code: 'java', label: 'Java', alias: 'java' },
  { code: 'cpp', label: 'C++', alias: 'c++' },
  { code: 'csharp', label: 'C#', alias: 'c#' },
  { code: 'go', label: 'Go', alias: 'go' },
  { code: 'rust', label: 'Rust', alias: 'rust' },
  { code: 'ruby', label: 'Ruby', alias: 'rb' },
  { code: 'php', label: 'PHP', alias: 'php' },
  { code: 'swift', label: 'Swift', alias: 'swift' },
  { code: 'kotlin', label: 'Kotlin', alias: 'kotlin' },
  { code: 'bash', label: 'Bash/Shell', alias: 'sh' },
  { code: 'sql', label: 'SQL', alias: 'sql' },
  { code: 'html', label: 'HTML', alias: 'html' },
  { code: 'css', label: 'CSS', alias: 'css' },
  { code: 'json', label: 'JSON', alias: 'json' },
  { code: 'yaml', label: 'YAML', alias: 'yml' },
  { code: 'markdown', label: 'Markdown', alias: 'md' },
  { code: 'plaintext', label: 'Plain Text', alias: 'text' },
]

let debounceTimer: ReturnType<typeof setTimeout> | null = null
let autoSaveTimer: ReturnType<typeof setTimeout> | null = null

const getStorageKey = () => {
  return props.storageKey ? `comment_draft_${props.storageKey}` : null
}

const loadDraft = () => {
  const key = getStorageKey()
  if (!key) return
  
  try {
    const draft = localStorage.getItem(key)
    if (draft && draft.trim()) {
      emit('update:modelValue', draft)
      previewContent.value = draft
      originalValue.value = draft
    }
  } catch (e) {
    console.warn('Failed to load draft:', e)
  }
}

const saveDraft = (value: string) => {
  const key = getStorageKey()
  if (!key) return
  
  try {
    if (value.trim()) {
      localStorage.setItem(key, value)
    } else {
      localStorage.removeItem(key)
    }
  } catch (e) {
    console.warn('Failed to save draft:', e)
  }
}

const clearDraft = () => {
  const key = getStorageKey()
  if (!key) return
  
  try {
    localStorage.removeItem(key)
  } catch (e) {
    console.warn('Failed to clear draft:', e)
  }
}

const updatePreview = (value: string) => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    previewContent.value = value
  }, 200)
}

const handleInput = (e: Event) => {
  const target = e.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
  updatePreview(target.value)
  hasUnsavedChanges.value = target.value !== originalValue.value
  
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  autoSaveTimer = setTimeout(() => {
    saveDraft(target.value)
  }, 1000)
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Tab') {
    e.preventDefault()
    
    const textarea = textareaRef.value
    if (!textarea) return
    
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const value = props.modelValue
    
    if (e.shiftKey) {
      const lineStart = value.lastIndexOf('\n', start - 1) + 1
      const lineContent = value.substring(lineStart, start)
      if (lineContent.startsWith('  ')) {
        const newValue = value.substring(0, lineStart) + value.substring(lineStart + 2)
        emit('update:modelValue', newValue)
        nextTick(() => {
          textarea.selectionStart = textarea.selectionEnd = start - 2
        })
      }
    } else {
      const newValue = value.substring(0, start) + '  ' + value.substring(end)
      emit('update:modelValue', newValue)
      nextTick(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 2
      })
    }
  }
}

const insertEmoji = (emoji: string) => {
  if (!textareaRef.value) return
  
  const textarea = textareaRef.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  
  const newValue = props.modelValue.substring(0, start) + emoji + props.modelValue.substring(end)
  emit('update:modelValue', newValue)
  
  nextTick(() => {
    textarea.focus({ preventScroll: true })
    textarea.selectionStart = textarea.selectionEnd = start + emoji.length
  })
}

const insertText = (before: string, after: string = '', needsNewLine: boolean = false) => {
  if (!textareaRef.value) return
  
  const textarea = textareaRef.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selectedText = props.modelValue.substring(start, end)
  
  let prefix = ''
  if (needsNewLine && start > 0) {
    const charBefore = props.modelValue[start - 1]
    if (charBefore !== '\n') {
      prefix = '\n'
    }
  }
  
  const newValue = props.modelValue.substring(0, start) + prefix + before + selectedText + after + props.modelValue.substring(end)
  emit('update:modelValue', newValue)
  
  nextTick(() => {
    textarea.focus({ preventScroll: true })
    const newCursorPos = start + prefix.length + before.length + selectedText.length
    textarea.selectionStart = textarea.selectionEnd = newCursorPos
  })
}

const insertCodeBlock = (lang: string) => {
  showLangSelector.value = false
  
  if (!textareaRef.value) return
  
  const textarea = textareaRef.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selectedText = props.modelValue.substring(start, end)
  
  let prefix = ''
  if (start > 0) {
    const charBefore = props.modelValue[start - 1]
    if (charBefore !== '\n') {
      prefix = '\n'
    }
  }
  
  const codeBlock = `\`\`\`${lang}\n${selectedText || ''}\n\`\`\``
  
  const newValue = props.modelValue.substring(0, start) + prefix + codeBlock + props.modelValue.substring(end)
  emit('update:modelValue', newValue)
  
  nextTick(() => {
    textarea.focus({ preventScroll: true })
    const cursorPos = start + prefix.length + 3 + lang.length + 1
    textarea.selectionStart = textarea.selectionEnd = cursorPos
  })
}

const insertLink = (markdown: string) => {
  if (!textareaRef.value) return
  
  const textarea = textareaRef.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  
  const newValue = props.modelValue.substring(0, start) + markdown + props.modelValue.substring(end)
  emit('update:modelValue', newValue)
  
  nextTick(() => {
    textarea.focus({ preventScroll: true })
    textarea.selectionStart = textarea.selectionEnd = start + markdown.length
  })
}

const activeTooltip = ref<string | null>(null)

const showTooltip = (name: string) => {
  activeTooltip.value = name
}

const hideTooltip = () => {
  activeTooltip.value = null
}

const toolbarActions = [
  { icon: 'B', title: '粗体', key: 'bold', action: () => insertText('**', '**') },
  { icon: 'I', title: '斜体', key: 'italic', action: () => insertText('*', '*') },
  { icon: 'S', title: '删除线', key: 'strikethrough', action: () => insertText('~~', '~~') },
  { icon: '</>', title: '行内代码', key: 'code', action: () => insertText('`', '`') },
  { icon: '🔗', title: '插入链接', key: 'link', action: () => showLinkInserter.value = true },
  { icon: '•', title: '列表', key: 'list', action: () => insertText('- ', '', true) },
  { icon: '>', title: '引用', key: 'quote', action: () => insertText('> ', '', true) },
]

const togglePreview = () => {
  showPreview.value = !showPreview.value
  if (showPreview.value) {
    previewContent.value = props.modelValue
  }
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  if (isFullscreen.value) {
    showPreview.value = true
    previewContent.value = props.modelValue
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
}

const handleEditorScroll = () => {
  if (isSyncingScroll.value || !isFullscreen.value) return
  
  const editor = textareaRef.value
  const previewEl = previewContainerRef.value
  if (!editor || !previewEl) return
  
  const editorScrollRatio = editor.scrollTop / (editor.scrollHeight - editor.clientHeight || 1)
  const previewScrollTop = editorScrollRatio * (previewEl.scrollHeight - previewEl.clientHeight || 0)
  
  isSyncingScroll.value = true
  previewEl.scrollTop = previewScrollTop
  
  setTimeout(() => {
    isSyncingScroll.value = false
  }, 50)
}

const handlePreviewScroll = () => {
  if (isSyncingScroll.value || !isFullscreen.value) return
  
  const editor = textareaRef.value
  const previewEl = previewContainerRef.value
  if (!editor || !previewEl) return
  
  const previewScrollRatio = previewEl.scrollTop / (previewEl.scrollHeight - previewEl.clientHeight || 1)
  const editorScrollTop = previewScrollRatio * (editor.scrollHeight - editor.clientHeight || 0)
  
  isSyncingScroll.value = true
  editor.scrollTop = editorScrollTop
  
  setTimeout(() => {
    isSyncingScroll.value = false
  }, 50)
}

const toggleLangSelector = (event: MouseEvent) => {
  showLangSelector.value = !showLangSelector.value
  if (showLangSelector.value) {
    const target = event.currentTarget as HTMLElement
    const rect = target.getBoundingClientRect()
    langSelectorPosition.value = {
      top: rect.bottom + 4,
      left: Math.max(0, rect.right - 160)
    }
  }
}

const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.lang-selector-container')) {
    showLangSelector.value = false
  }
}

const markAsSaved = () => {
  originalValue.value = props.modelValue
  hasUnsavedChanges.value = false
  clearDraft()
}

const handleSubmit = () => {
  if (!props.modelValue.trim() || props.disabled) return
  emit('submit')
}

watch(() => props.modelValue, (newVal) => {
  if (showPreview.value) {
    previewContent.value = newVal
  }
})

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  loadDraft()
  originalValue.value = props.modelValue
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (debounceTimer) clearTimeout(debounceTimer)
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  document.body.style.overflow = ''
})

defineExpose({
  focus: () => textareaRef.value?.focus(),
  markAsSaved,
  clearDraft
})
</script>

<template>
  <div 
    class="comment-editor transition-all duration-300"
    :class="{ 'fixed inset-0 z-50 bg-white dark:bg-dark-100 p-4': isFullscreen }"
  >
    <!-- 非全屏模式下的工具栏 -->
    <div
      v-if="!isFullscreen"
      class="flex flex-wrap items-center gap-1 mb-2"
    >
      <button
        v-for="item in toolbarActions"
        :key="item.icon"
        type="button"
        class="px-1.5 py-0.5 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/10 rounded transition-colors relative"
        @click="item.action"
        @mouseenter="showTooltip(item.key)"
        @mouseleave="hideTooltip"
      >
        {{ item.icon }}
        <span
          v-if="activeTooltip === item.key"
          class="action-tooltip"
        >
          {{ item.title }}
        </span>
      </button>
      
      <div class="lang-selector-container relative">
        <button
          type="button"
          class="px-1.5 py-0.5 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/10 rounded transition-colors relative"
          @click="toggleLangSelector($event)"
          @mouseenter="showTooltip('codeblock')"
          @mouseleave="hideTooltip"
        >
          { }
          <span
            v-if="activeTooltip === 'codeblock'"
            class="action-tooltip"
          >
            代码块
          </span>
        </button>
        
        <div
          v-if="showLangSelector"
          class="fixed z-[200] bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg shadow-lg py-1 w-40 max-h-60 overflow-y-auto"
          :style="{ top: langSelectorPosition.top + 'px', left: langSelectorPosition.left + 'px' }"
        >
          <div class="px-2 py-1 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10">
            选择语言
          </div>
          <button
            v-for="lang in programmingLanguages"
            :key="lang.code"
            type="button"
            class="w-full px-2 py-1 text-xs text-left text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
            @click="insertCodeBlock(lang.code)"
          >
            {{ lang.label }}
          </button>
        </div>
      </div>
      
      <div class="w-px h-4 bg-gray-200 dark:bg-white/10 mx-1 hidden sm:block" />
      
      <EmojiPicker
        position="bottom"
        @select="insertEmoji"
      />
      
      <button
        type="button"
        class="p-1.5 rounded transition-colors text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/10 relative"
        @click="showMarkdownHelp = !showMarkdownHelp"
        @mouseenter="showTooltip('help')"
        @mouseleave="hideTooltip"
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
            d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span
          v-if="activeTooltip === 'help'"
          class="action-tooltip"
        >
          Markdown 语法帮助
        </span>
      </button>
      <button
        type="button"
        class="p-1.5 rounded transition-colors relative"
        :class="showPreview ? 'text-primary bg-primary/10' : 'text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/10'"
        @click="togglePreview"
        @mouseenter="showTooltip('preview')"
        @mouseleave="hideTooltip"
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
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
          />
        </svg>
        <span
          v-if="activeTooltip === 'preview'"
          class="action-tooltip"
        >
          {{ showPreview ? '隐藏预览' : '显示预览' }}
        </span>
      </button>
      <button
        type="button"
        class="p-1.5 rounded transition-colors relative"
        :class="isFullscreen ? 'text-primary bg-primary/10' : 'text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/10'"
        @click="toggleFullscreen"
        @mouseenter="showTooltip('fullscreen')"
        @mouseleave="hideTooltip"
      >
        <svg
          class="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            v-if="!isFullscreen"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
          />
          <path
            v-else
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25"
          />
        </svg>
        <span
          v-if="activeTooltip === 'fullscreen'"
          class="action-tooltip"
        >
          {{ isFullscreen ? '退出全屏' : '全屏编辑' }}
        </span>
      </button>
    </div>
    
    <!-- Markdown 语法帮助 -->
    <div 
      v-if="showMarkdownHelp && !isFullscreen" 
      class="mb-2 p-3 bg-gray-50 dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 rounded-lg text-xs text-gray-600 dark:text-gray-400"
    >
      <div class="flex justify-between items-center mb-3">
        <span class="font-medium text-gray-700 dark:text-gray-300">Markdown 语法参考</span>
        <button
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          @click="showMarkdownHelp = false"
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
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-x-4 gap-y-2">
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">**粗体**</code>
          <span class="text-gray-400">→</span>
          <strong class="truncate">粗体</strong>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">*斜体*</code>
          <span class="text-gray-400">→</span>
          <em class="truncate">斜体</em>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">~~删除线~~</code>
          <span class="text-gray-400">→</span>
          <del class="truncate">删除线</del>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">`代码`</code>
          <span class="text-gray-400">→</span>
          <code class="bg-gray-200 dark:bg-dark-100 px-1 rounded truncate">代码</code>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">[文字](url)</code>
          <span class="text-gray-400">→</span>
          <span class="text-primary truncate">链接</span>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">![图片](url)</code>
          <span class="text-gray-400">→</span>
          <span class="truncate">图片</span>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0"># 标题</code>
          <span class="text-gray-400">→</span>
          <span class="font-bold truncate">H1标题</span>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">## 标题</code>
          <span class="text-gray-400">→</span>
          <span class="font-semibold truncate">H2标题</span>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">- 列表</code>
          <span class="text-gray-400">→</span>
          <span class="truncate">无序列表</span>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">1. 列表</code>
          <span class="text-gray-400">→</span>
          <span class="truncate">有序列表</span>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">- [ ] 任务</code>
          <span class="text-gray-400">→</span>
          <span class="truncate">任务列表</span>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">> 引用</code>
          <span class="text-gray-400">→</span>
          <span class="truncate">引用块</span>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">---</code>
          <span class="text-gray-400">→</span>
          <span class="truncate">分隔线</span>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">```代码块```</code>
          <span class="text-gray-400">→</span>
          <span class="truncate">代码块</span>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">| 表格 |</code>
          <span class="text-gray-400">→</span>
          <span class="truncate">表格</span>
        </div>
        <div class="flex items-center gap-1.5">
          <code class="bg-gray-200 dark:bg-dark-100 px-1.5 py-0.5 rounded shrink-0">[^脚注]</code>
          <span class="text-gray-400">→</span>
          <span class="truncate">脚注</span>
        </div>
      </div>
    </div>
    
    <!-- 全屏模式：左右分栏 -->
    <div 
      v-if="isFullscreen" 
      class="flex flex-col"
      style="height: calc(100vh - 32px);"
    >
      <!-- 上下文信息区域 -->
      <div class="flex-shrink-0 mb-2 p-2 bg-gray-100 dark:bg-dark-100/50 rounded-lg border border-gray-200 dark:border-white/10">
        <div
          v-if="replyTo"
          class="text-sm"
        >
          <span class="text-gray-500 dark:text-gray-400">回复 </span>
          <span class="text-primary font-medium">@{{ replyTo }}</span>
          <div
            v-if="replyToContent"
            class="mt-1 text-gray-600 dark:text-gray-300 text-xs line-clamp-1 truncate bg-gray-200 dark:bg-dark-100/50 p-2 rounded"
          >
            {{ replyToContent }}
          </div>
        </div>
        <div
          v-else-if="articleTitle"
          class="text-sm"
        >
          <span class="text-gray-500 dark:text-gray-400">评论文章：</span>
          <span class="text-gray-900 dark:text-white font-medium">{{ articleTitle }}</span>
        </div>
      </div>
      
      <!-- 编辑和预览区域 -->
      <div class="flex gap-3 flex-1 min-h-0">
        <!-- 编辑区 -->
        <div class="flex-1 flex flex-col border border-gray-200 dark:border-white/10 rounded-lg overflow-visible">
          <div class="flex-shrink-0 min-h-8 px-3 py-1 bg-gray-50 dark:bg-dark-100 border-b border-gray-200 dark:border-white/10 rounded-t-lg flex justify-between items-center">
            <span class="text-xs text-gray-500 dark:text-gray-400">编辑</span>
            <div class="flex flex-wrap items-center gap-0.5">
              <button
                v-for="item in toolbarActions"
                :key="item.icon"
                type="button"
                class="px-1 py-0.5 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/10 rounded transition-colors relative"
                @click="item.action"
                @mouseenter="showTooltip('fs-' + item.key)"
                @mouseleave="hideTooltip"
              >
                {{ item.icon }}
                <span
                  v-if="activeTooltip === 'fs-' + item.key"
                  class="action-tooltip"
                >
                  {{ item.title }}
                </span>
              </button>
              <div class="lang-selector-container relative">
                <button
                  type="button"
                  class="px-1 py-0.5 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/10 rounded transition-colors relative"
                  @click="toggleLangSelector($event)"
                  @mouseenter="showTooltip('fs-codeblock')"
                  @mouseleave="hideTooltip"
                >
                  { }
                  <span
                    v-if="activeTooltip === 'fs-codeblock'"
                    class="action-tooltip"
                  >
                    代码块
                  </span>
                </button>
                <div
                  v-if="showLangSelector"
                  class="fixed z-[200] bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg shadow-lg py-1 w-40 max-h-60 overflow-y-auto"
                  :style="{ top: langSelectorPosition.top + 'px', left: langSelectorPosition.left + 'px' }"
                >
                  <div class="px-2 py-1 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10">
                    选择语言
                  </div>
                  <button
                    v-for="lang in programmingLanguages"
                    :key="lang.code"
                    type="button"
                    class="w-full px-2 py-1 text-xs text-left text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
                    @click="insertCodeBlock(lang.code)"
                  >
                    {{ lang.label }}
                  </button>
                </div>
              </div>
              <EmojiPicker
                position="bottom"
                @select="insertEmoji"
              />
            </div>
          </div>
          <textarea
            ref="textareaRef"
            :value="modelValue"
            :placeholder="replyTo ? `回复 @${replyTo}...` : placeholder"
            :disabled="disabled"
            class="flex-1 w-full p-3 bg-transparent border-none outline-none text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 resize-none text-sm leading-relaxed overflow-y-auto rounded-b-lg"
            @input="handleInput"
            @keydown="handleKeydown"
            @scroll="handleEditorScroll"
          />
        </div>
        
        <!-- 预览区 -->
        <div class="flex-1 flex flex-col border border-gray-200 dark:border-white/10 rounded-lg overflow-hidden">
          <div class="flex-shrink-0 h-8 px-3 bg-gray-50 dark:bg-dark-100 border-b border-gray-200 dark:border-white/10 rounded-t-lg flex items-center">
            <span class="text-xs text-gray-500 dark:text-gray-400">预览</span>
          </div>
          <div 
            ref="previewContainerRef"
            class="flex-1 p-3 overflow-y-auto"
            @scroll="handlePreviewScroll"
          >
            <CommentMarkdownPreview 
              :content="previewContent" 
              :show-lang-label="true"
            />
          </div>
        </div>
      </div>
      
      <!-- 底部操作按钮 -->
      <div class="flex-shrink-0 flex justify-end gap-2 mt-2 pt-2 border-t border-gray-200 dark:border-white/10">
        <button
          type="button"
          class="px-4 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          @click="toggleFullscreen"
        >
          取消
        </button>
        <button
          type="button"
          :disabled="disabled || !modelValue.trim()"
          class="px-4 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          @click="handleSubmit"
        >
          {{ disabled ? '发送中...' : (replyTo ? '发送回复' : '发表评论') }}
        </button>
      </div>
    </div>
    
    <!-- 非全屏模式：原始布局 -->
    <template v-else>
      <div class="relative">
        <textarea
          ref="textareaRef"
          :value="modelValue"
          :placeholder="replyTo ? `回复 @${replyTo}...` : placeholder"
          :disabled="disabled"
          :rows="rows"
          class="w-full bg-transparent border-none outline-none text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 resize-none text-sm leading-relaxed"
          @input="handleInput"
          @keydown="handleKeydown"
        />
      </div>
      
      <div 
        v-if="showPreview && modelValue" 
        class="mt-3 p-3 bg-gray-50 dark:bg-dark-100/50 rounded-lg border border-gray-200 dark:border-white/5"
      >
        <div class="text-xs text-gray-500 dark:text-gray-400 mb-2">
          预览
        </div>
        <CommentMarkdownPreview
          :content="previewContent"
          :show-lang-label="true"
        />
      </div>
    </template>
    
    <LinkInserterDialog
      v-model="showLinkInserter"
      @insert="insertLink"
    />
  </div>
</template>

<style scoped>
@media (max-width: 640px) {
  .comment-editor .flex.flex-wrap {
    gap: 0.25rem;
  }
  
  .comment-editor button.px-1\.5,
  .comment-editor button.px-1,
  .comment-editor button.p-1\.5 {
    padding: 0.25rem 0.375rem;
    font-size: 0.6875rem;
  }
  
  .comment-editor .w-px\.h-4 {
    display: none;
  }
}

@media (max-width: 480px) {
  .comment-editor .flex.flex-wrap {
    gap: 0.125rem;
  }
  
  .comment-editor button.px-1\.5,
  .comment-editor button.px-1,
  .comment-editor button.p-1\.5 {
    padding: 0.125rem 0.25rem;
    font-size: 0.625rem;
  }
  
  .comment-editor .lang-selector-container .fixed {
    width: 120px;
    max-height: 150px;
  }
}

@media (max-width: 360px) {
  .comment-editor .flex.flex-wrap {
    gap: 0.0625rem;
  }
  
  .comment-editor button.px-1\.5,
  .comment-editor button.px-1,
  .comment-editor button.p-1\.5 {
    padding: 0.0625rem 0.1875rem;
    font-size: 0.5625rem;
  }
  
  .comment-editor .lang-selector-container .fixed {
    width: 100px;
    left: 0 !important;
  }
}

.action-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 8px;
  background: #ffffff;
  color: #1a1a2e;
  font-size: 12px;
  font-weight: normal;
  border-radius: 4px;
  white-space: nowrap;
  pointer-events: none;
  z-index: 9999;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  animation: tooltip-fade-in 0.15s ease;
}

.dark .action-tooltip {
  background: #0f0f1a;
  color: #f1f5f9;
}

@keyframes tooltip-fade-in {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}
</style>
