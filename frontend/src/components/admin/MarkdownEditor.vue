<script setup lang="ts">
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from 'vue'
import MarkdownPreview from './MarkdownPreview.vue'

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
const hasUnsavedChanges = ref(false)
const originalValue = ref('')

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
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    previewContent.value = value
  }, 300)
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

const insertText = (before: string, after: string = '') => {
  if (!editorRef.value) return
  
  const textarea = editorRef.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selectedText = props.modelValue.substring(start, end)
  const newText = props.modelValue.substring(0, start) + before + selectedText + after + props.modelValue.substring(end)
  
  emit('update:modelValue', newText)
  
  nextTick(() => {
    textarea.focus()
    const newCursorPos = start + before.length + selectedText.length
    textarea.selectionStart = textarea.selectionEnd = newCursorPos
  })
}

const insertCodeBlock = (lang: string) => {
  showLangSelector.value = false
  
  if (!editorRef.value) return
  
  const textarea = editorRef.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selectedText = props.modelValue.substring(start, end)
  const codeBlock = `\`\`\`${lang}\n${selectedText || 'code here'}\n\`\`\``
  
  const newText = props.modelValue.substring(0, start) + codeBlock + props.modelValue.substring(end)
  emit('update:modelValue', newText)
  
  nextTick(() => {
    textarea.focus()
    const cursorPos = start + 3 + lang.length + 1 + (selectedText ? selectedText.length : 10)
    textarea.selectionStart = textarea.selectionEnd = cursorPos
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
  { icon: 'H1', title: '标题1', action: () => insertText('# ') },
  { icon: 'H2', title: '标题2', action: () => insertText('## ') },
  { icon: 'H3', title: '标题3', action: () => insertText('### ') },
  { divider: true },
  { icon: '•', title: '无序列表', action: () => insertText('- ') },
  { icon: '1.', title: '有序列表', action: () => insertText('1. ') },
  { icon: '□', title: '任务列表', action: () => insertText('- [ ] ') },
  { divider: true },
  { icon: '🔗', title: '链接', action: () => insertText('[', '](url)') },
  { icon: '🖼', title: '图片', action: () => insertText('![alt](', ')') },
  { icon: '</>', title: '行内代码', action: () => insertText('`', '`') },
  { divider: true },
  { icon: '|', title: '表格', action: () => insertText('\n| 列1 | 列2 | 列3 |\n| --- | --- | --- |\n| 内容 | 内容 | 内容 |\n') },
  { icon: '—', title: '分割线', action: () => insertText('\n---\n') },
  { icon: '>', title: '引用', action: () => insertText('> ') },
]

watch(() => props.modelValue, (newVal) => {
  previewContent.value = newVal
}, { immediate: true })

const editorContainerStyle = computed(() => ({
  height: isFullscreen.value ? 'calc(100vh - 120px)' : '400px'
}))

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
    <div class="flex items-center justify-between px-3 py-2 bg-gray-100 dark:bg-dark-100 border-b border-gray-200 dark:border-white/10">
      <div class="flex items-center gap-1 flex-wrap">
        <template v-for="(item, index) in toolbarActions" :key="index">
          <button
            v-if="!item.divider"
            type="button"
            @click="item.action"
            :title="item.title"
            class="px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/5 rounded transition-colors"
          >
            {{ item.icon }}
          </button>
          <div v-else class="w-px h-4 bg-gray-300 dark:bg-white/10 mx-1" />
        </template>
        
        <div class="lang-selector-container relative">
          <button
            type="button"
            @click="showLangSelector = !showLangSelector"
            title="代码块"
            class="px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/5 rounded transition-colors"
          >
            { }
          </button>
          
          <div
            v-if="showLangSelector"
            class="absolute z-50 top-full mt-1 left-0 bg-white dark:bg-dark-200 border border-gray-200 dark:border-white/10 rounded-lg shadow-lg py-1 w-40 max-h-60 overflow-y-auto"
          >
            <div class="px-2 py-1 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10">
              选择语言
            </div>
            <button
              v-for="lang in programmingLanguages"
              :key="lang.code"
              type="button"
              @click="insertCodeBlock(lang.code)"
              class="w-full px-2 py-1 text-xs text-left text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
            >
              {{ lang.label }}
            </button>
          </div>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          @click="togglePreview"
          class="px-2 py-1 text-xs font-medium rounded transition-colors"
          :class="showPreview ? 'text-primary bg-primary/10' : 'text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/5'"
        >
          {{ showPreview ? '隐藏预览' : '显示预览' }}
        </button>
        <button
          type="button"
          @click="toggleFullscreen"
          class="px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/5 rounded transition-colors"
        >
          {{ isFullscreen ? '退出全屏' : '全屏' }}
        </button>
      </div>
    </div>
    
    <div class="flex" :style="editorContainerStyle">
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
          @input="handleInput"
          @keydown="handleKeydown"
          @scroll="handleEditorScroll"
          :placeholder="placeholder"
          :disabled="disabled"
          class="flex-1 w-full p-3 text-sm bg-white dark:bg-dark-200 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 resize-none focus:outline-none font-mono leading-relaxed"
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
  .markdown-editor-container .flex {
    flex-direction: column;
  }
  
  .editor-pane,
  .preview-pane {
    max-width: 100% !important;
    flex: none;
  }
  
  .editor-pane {
    height: 200px;
  }
  
  .preview-pane {
    height: 200px;
    border-left: none !important;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
}
</style>
