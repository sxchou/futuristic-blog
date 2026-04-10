<script setup lang="ts">
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from 'vue'
import MarkdownPreview from './MarkdownPreview.vue'
import EmojiPicker from '@/components/common/EmojiPicker.vue'
import LinkInserterDialog from '@/components/comments/LinkInserterDialog.vue'

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
  disabled?: boolean
  storageKey?: string
}>(), {
  placeholder: '请输入内容...'
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const editorRef = ref<HTMLTextAreaElement | null>(null)
const previewComponentRef = ref<InstanceType<typeof MarkdownPreview> | null>(null)
const showPreview = ref(true)
const isSyncingScroll = ref(false)
const previewContent = ref('')
const isFullscreen = ref(false)
const showLangSelector = ref(false)
const showMarkdownHelp = ref(false)
const hasUnsavedChanges = ref(false)
const originalValue = ref('')
const showLinkInserter = ref(false)

const programmingLanguages = [
  { code: 'javascript', label: 'JavaScript' },
  { code: 'typescript', label: 'TypeScript' },
  { code: 'python', label: 'Python' },
  { code: 'java', label: 'Java' },
  { code: 'cpp', label: 'C++' },
  { code: 'csharp', label: 'C#' },
  { code: 'go', label: 'Go' },
  { code: 'rust', label: 'Rust' },
  { code: 'ruby', label: 'Ruby' },
  { code: 'php', label: 'PHP' },
  { code: 'swift', label: 'Swift' },
  { code: 'kotlin', label: 'Kotlin' },
  { code: 'bash', label: 'Bash/Shell' },
  { code: 'sql', label: 'SQL' },
  { code: 'html', label: 'HTML' },
  { code: 'css', label: 'CSS' },
  { code: 'json', label: 'JSON' },
  { code: 'yaml', label: 'YAML' },
  { code: 'markdown', label: 'Markdown' },
  { code: 'plaintext', label: 'Plain Text' },
]

let debounceTimer: ReturnType<typeof setTimeout> | null = null
let autoSaveTimer: ReturnType<typeof setTimeout> | null = null

const getStorageKey = () => {
  return props.storageKey ? `admin_draft_${props.storageKey}` : null
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
  previewContent.value = value
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
    
    const textarea = editorRef.value
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

const handleEditorScroll = () => {
  if (isSyncingScroll.value) return
  
  const editor = editorRef.value
  const previewEl = previewComponentRef.value?.$el
  if (!editor || !previewEl) return
  
  const editorScrollRatio = editor.scrollTop / (editor.scrollHeight - editor.clientHeight || 1)
  const previewScrollTop = editorScrollRatio * (previewEl.scrollHeight - previewEl.clientHeight || 0)
  
  isSyncingScroll.value = true
  previewEl.scrollTop = previewScrollTop
  
  setTimeout(() => {
    isSyncingScroll.value = false
  }, 50)
}

const handlePreviewScroll = (scrollTop: number) => {
  if (isSyncingScroll.value) return
  
  const editor = editorRef.value
  const previewEl = previewComponentRef.value?.$el
  if (!editor || !previewEl) return
  
  const previewScrollRatio = scrollTop / (previewEl.scrollHeight - previewEl.clientHeight || 1)
  const editorScrollTop = previewScrollRatio * (editor.scrollHeight - editor.clientHeight || 0)
  
  isSyncingScroll.value = true
  editor.scrollTop = editorScrollTop
  
  setTimeout(() => {
    isSyncingScroll.value = false
  }, 50)
}

const togglePreview = () => {
  showPreview.value = !showPreview.value
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
}

const insertText = (before: string, after: string = '', needsNewLine: boolean = false) => {
  if (!editorRef.value) return
  
  const textarea = editorRef.value
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
  
  const newText = props.modelValue.substring(0, start) + prefix + before + selectedText + after + props.modelValue.substring(end)
  emit('update:modelValue', newText)
  
  nextTick(() => {
    textarea.focus({ preventScroll: true })
    const newCursorPos = start + prefix.length + before.length + selectedText.length
    textarea.selectionStart = textarea.selectionEnd = newCursorPos
  })
}

const insertEmoji = (emoji: string) => {
  insertText(emoji)
}

const insertCodeBlock = (lang: string) => {
  showLangSelector.value = false
  
  if (!editorRef.value) return
  
  const textarea = editorRef.value
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
  
  const newText = props.modelValue.substring(0, start) + prefix + codeBlock + props.modelValue.substring(end)
  emit('update:modelValue', newText)
  
  nextTick(() => {
    textarea.focus({ preventScroll: true })
    const cursorPos = start + prefix.length + 3 + lang.length + 1
    textarea.selectionStart = textarea.selectionEnd = cursorPos
  })
}

const openLinkDialog = () => {
  showLinkInserter.value = true
}

const insertLink = (markdown: string) => {
  if (!editorRef.value) return
  
  const textarea = editorRef.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  
  const newText = props.modelValue.substring(0, start) + markdown + props.modelValue.substring(end)
  emit('update:modelValue', newText)
  
  nextTick(() => {
    textarea.focus({ preventScroll: true })
    textarea.selectionStart = textarea.selectionEnd = start + markdown.length
  })
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

const toolbarActions = [
  { icon: 'B', title: '粗体', action: () => insertText('**', '**') },
  { icon: 'I', title: '斜体', action: () => insertText('*', '*') },
  { icon: 'S', title: '删除线', action: () => insertText('~~', '~~') },
  { divider: true },
  { icon: 'H1', title: '标题1', action: () => insertText('# ', '', true) },
  { icon: 'H2', title: '标题2', action: () => insertText('## ', '', true) },
  { icon: 'H3', title: '标题3', action: () => insertText('### ', '', true) },
  { divider: true },
  { icon: '•', title: '无序列表', action: () => insertText('- ', '', true) },
  { icon: '1.', title: '有序列表', action: () => insertText('1. ', '', true) },
  { icon: '□', title: '任务列表', action: () => insertText('- [ ] ', '', true) },
  { divider: true },
  { icon: '🔗', title: '链接', action: openLinkDialog },
  { icon: '🖼', title: '图片', action: () => insertText('![alt](', ')') },
  { icon: '</>', title: '行内代码', action: () => insertText('`', '`') },
  { divider: true },
  { icon: '|', title: '表格', action: () => insertText('\n| 列1 | 列2 | 列3 |\n| --- | --- | --- |\n| 内容 | 内容 | 内容 |\n') },
  { icon: '—', title: '分割线', action: () => insertText('\n---\n') },
  { icon: '>', title: '引用', action: () => insertText('> ', '', true) },
]

watch(() => props.modelValue, (newVal) => {
  previewContent.value = newVal
}, { immediate: true })

const editorContainerStyle = computed(() => ({
  height: isFullscreen.value ? 'calc(100vh - 120px)' : '400px'
}))

const langSelectorStyle = ref({
  top: '0px',
  left: '0px'
})

const updateLangSelectorPosition = () => {
  nextTick(() => {
    const container = document.querySelector('.lang-selector-container')
    if (container) {
      const rect = container.getBoundingClientRect()
      langSelectorStyle.value = {
        top: `${rect.bottom + 4}px`,
        left: `${rect.left}px`
      }
    }
  })
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  loadDraft()
  originalValue.value = props.modelValue
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (debounceTimer) clearTimeout(debounceTimer)
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
})

defineExpose({
  markAsSaved,
  clearDraft
})
</script>

<template>
  <div 
    class="markdown-editor-container rounded-lg border border-gray-200 dark:border-white/10 overflow-hidden"
    :class="{ 'fixed inset-4 z-50 bg-gray-900 dark:bg-dark-100': isFullscreen }"
  >
    <div class="flex flex-wrap items-center gap-1 px-3 py-2 bg-gray-100 dark:bg-dark-100 border-b border-gray-200 dark:border-white/10">
      <template
        v-for="(item, index) in toolbarActions"
        :key="index"
      >
        <button
          v-if="!item.divider"
          type="button"
          :title="item.title"
          class="px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/5 rounded transition-colors"
          @click="item.action"
        >
          {{ item.icon }}
        </button>
        <div
          v-else
          class="w-px h-4 bg-gray-300 dark:bg-white/10 mx-0.5 hidden sm:block"
        />
      </template>
      
      <div class="lang-selector-container relative">
        <button
          type="button"
          title="代码块"
          class="px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/5 rounded transition-colors"
          @click="showLangSelector = !showLangSelector; if (showLangSelector) updateLangSelectorPosition()"
        >
          { }
        </button>
        
        <div
          v-if="showLangSelector"
          class="fixed z-[200] bg-white dark:bg-dark-200 border border-gray-200 dark:border-white/10 rounded-lg shadow-lg py-1 w-40 max-h-60 overflow-y-auto"
          :style="langSelectorStyle"
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
      
      <div class="w-px h-4 bg-gray-300 dark:bg-white/10 mx-0.5 hidden sm:block" />
      
      <EmojiPicker
        position="bottom"
        @select="insertEmoji"
      />
      
      <div class="w-px h-4 bg-gray-300 dark:bg-white/10 mx-0.5 hidden sm:block" />
      
      <button
        type="button"
        title="Markdown 语法帮助"
        class="px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/5 rounded transition-colors"
        @click="showMarkdownHelp = !showMarkdownHelp"
      >
        ?
      </button>
      <button
        type="button"
        :title="showPreview ? '隐藏预览' : '显示预览'"
        class="px-2 py-1 text-xs font-medium rounded transition-colors"
        :class="showPreview ? 'text-primary bg-primary/10' : 'text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/5'"
        @click="togglePreview"
      >
        👁
      </button>
      <button
        type="button"
        :title="isFullscreen ? '退出全屏' : '全屏'"
        class="px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/5 rounded transition-colors"
        @click="toggleFullscreen"
      >
        ⛶
      </button>
    </div>
    
    <div 
      v-if="showMarkdownHelp" 
      class="mb-2 p-3 bg-gray-50 dark:bg-dark-200/50 border border-gray-200 dark:border-white/10 rounded-lg text-xs text-gray-600 dark:text-gray-400"
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
      <div class="mt-3 pt-2 border-t border-gray-200 dark:border-white/10">
        <a 
          href="https://markdown.com.cn/basic-syntax/" 
          target="_blank" 
          rel="noopener noreferrer"
          class="inline-flex items-center gap-1 text-primary hover:underline"
        >
          <span>查看完整 Markdown 语法文档</span>
          <svg
            class="w-3 h-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
        </a>
      </div>
    </div>
    
    <div
      class="editor-container flex"
      :style="editorContainerStyle"
    >
      <div 
        class="editor-pane flex-1 flex flex-col min-w-0"
        :class="{ 'max-w-[50%]': showPreview }"
      >
        <div class="flex items-center px-3 py-1.5 bg-gray-50 dark:bg-dark-200 border-b border-gray-200 dark:border-white/5">
          <span class="text-xs font-medium text-gray-500 dark:text-gray-400">编辑</span>
        </div>
        <textarea
          ref="editorRef"
          :value="modelValue"
          :placeholder="placeholder"
          :disabled="disabled"
          class="flex-1 w-full p-3 text-sm bg-white dark:bg-dark-200 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 resize-none focus:outline-none font-mono leading-relaxed"
          @input="handleInput"
          @keydown="handleKeydown"
          @scroll="handleEditorScroll"
        />
      </div>
      
      <div 
        v-if="showPreview" 
        class="preview-pane flex-1 border-l border-gray-200 dark:border-white/10 min-w-0"
      >
        <MarkdownPreview
          ref="previewComponentRef"
          :content="previewContent"
          @scroll="handlePreviewScroll"
        />
      </div>
    </div>
    
    <LinkInserterDialog
      v-model="showLinkInserter"
      @insert="insertLink"
    />
  </div>
</template>

<style scoped>
.markdown-editor-container {
  background: var(--bg-color, #1a1a2e);
}

.editor-pane textarea {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
}

.editor-pane textarea::-webkit-scrollbar,
.preview-pane :deep(.preview-content)::-webkit-scrollbar {
  width: 6px;
}

.editor-pane textarea::-webkit-scrollbar-track,
.preview-pane :deep(.preview-content)::-webkit-scrollbar-track {
  background: transparent;
}

.editor-pane textarea::-webkit-scrollbar-thumb,
.preview-pane :deep(.preview-content)::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.editor-pane textarea::-webkit-scrollbar-thumb:hover,
.preview-pane :deep(.preview-content)::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

@media (max-width: 768px) {
  .markdown-editor-container .editor-container {
    flex-direction: column;
  }
  
  .editor-pane,
  .preview-pane {
    max-width: 100% !important;
    flex: none;
  }
  
  .editor-pane {
    height: 180px;
    min-height: 150px;
  }
  
  .preview-pane {
    height: 180px;
    min-height: 150px;
    border-left: none !important;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .editor-pane textarea {
    font-size: 14px;
    padding: 12px;
  }
  
  .markdown-editor-container > div:first-child {
    padding: 0.5rem 0.75rem;
    gap: 0.25rem;
  }
  
  .markdown-editor-container > div:first-child button {
    padding: 0.25rem 0.5rem;
    font-size: 0.6875rem;
  }
}

@media (max-width: 480px) {
  .markdown-editor-container {
    border-radius: 8px;
  }
  
  .editor-pane,
  .preview-pane {
    height: 160px;
    min-height: 120px;
  }
  
  .editor-pane textarea {
    font-size: 13px;
    padding: 10px;
    line-height: 1.5;
  }
  
  .preview-pane :deep(.preview-content) {
    padding: 10px;
  }
  
  .markdown-editor-container > div:first-child {
    padding: 0.375rem 0.5rem;
    gap: 0.125rem;
  }
  
  .markdown-editor-container > div:first-child button {
    padding: 0.125rem 0.375rem;
    font-size: 0.625rem;
  }
  
  .markdown-editor-container .lang-selector-container .fixed {
    width: 120px;
    max-height: 150px;
  }
}

@media (max-width: 360px) {
  .editor-pane,
  .preview-pane {
    height: 140px;
    min-height: 100px;
  }
  
  .editor-pane textarea {
    font-size: 12px;
    padding: 8px;
  }
  
  .preview-pane :deep(.preview-content) {
    padding: 8px;
  }
  
  .markdown-editor-container > div:first-child {
    padding: 0.25rem 0.375rem;
    gap: 0.0625rem;
  }
  
  .markdown-editor-container > div:first-child button {
    padding: 0.0625rem 0.25rem;
    font-size: 0.5625rem;
  }
  
  .markdown-editor-container .lang-selector-container .fixed {
    width: 100px;
    left: 0 !important;
  }
}
</style>
