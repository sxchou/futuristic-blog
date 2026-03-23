<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import CommentMarkdownPreview from './CommentMarkdownPreview.vue'
import EmojiPicker from '@/components/common/EmojiPicker.vue'

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
  disabled?: boolean
  replyTo?: string
  rows?: number
  storageKey?: string
}>(), {
  placeholder: '写下你的想法...',
  rows: 4
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'submit'): void
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const showPreview = ref(false)
const previewContent = ref('')
const showLangSelector = ref(false)
const hasUnsavedChanges = ref(false)
const originalValue = ref('')

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
  updatePreview(newValue)
  
  nextTick(() => {
    textarea.focus()
    textarea.selectionStart = textarea.selectionEnd = start + emoji.length
  })
}

const insertText = (before: string, after: string = '') => {
  if (!textareaRef.value) return
  
  const textarea = textareaRef.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selectedText = props.modelValue.substring(start, end)
  const newValue = props.modelValue.substring(0, start) + before + selectedText + after + props.modelValue.substring(end)
  
  emit('update:modelValue', newValue)
  updatePreview(newValue)
  
  nextTick(() => {
    textarea.focus()
    const newCursorPos = start + before.length + selectedText.length
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
  const codeBlock = `\`\`\`${lang}\n${selectedText || 'code here'}\n\`\`\``
  
  const newValue = props.modelValue.substring(0, start) + codeBlock + props.modelValue.substring(end)
  emit('update:modelValue', newValue)
  updatePreview(newValue)
  
  nextTick(() => {
    textarea.focus()
    const cursorPos = start + 3 + lang.length + 1 + (selectedText ? selectedText.length : 10)
    textarea.selectionStart = textarea.selectionEnd = cursorPos
  })
}

const toolbarActions = [
  { icon: 'B', title: '粗体', action: () => insertText('**', '**') },
  { icon: 'I', title: '斜体', action: () => insertText('*', '*') },
  { icon: 'S', title: '删除线', action: () => insertText('~~', '~~') },
  { icon: '</>', title: '行内代码', action: () => insertText('`', '`') },
  { icon: '🔗', title: '链接', action: () => insertText('[', '](url)') },
  { icon: '•', title: '列表', action: () => insertText('- ') },
  { icon: '>', title: '引用', action: () => insertText('> ') },
]

const togglePreview = () => {
  showPreview.value = !showPreview.value
  if (showPreview.value) {
    previewContent.value = props.modelValue
  }
}

const toggleLangSelector = () => {
  showLangSelector.value = !showLangSelector.value
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

watch(() => props.modelValue, (newVal) => {
  previewContent.value = newVal
}, { immediate: true })

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
  focus: () => textareaRef.value?.focus(),
  markAsSaved,
  clearDraft
})
</script>

<template>
  <div class="comment-editor">
    <div class="flex justify-between items-center mb-2">
      <div class="flex items-center gap-1 flex-wrap">
        <button
          v-for="item in toolbarActions"
          :key="item.icon"
          type="button"
          @click="item.action"
          :title="item.title"
          class="px-1.5 py-0.5 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/10 rounded transition-colors"
        >
          {{ item.icon }}
        </button>
        
        <div class="lang-selector-container relative">
          <button
            type="button"
            @click="toggleLangSelector"
            title="代码块"
            class="px-1.5 py-0.5 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/10 rounded transition-colors"
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
        <EmojiPicker @select="insertEmoji" />
        <button
          type="button"
          @click="togglePreview"
          class="px-2 py-0.5 text-xs font-medium rounded transition-colors"
          :class="showPreview ? 'text-primary bg-primary/10' : 'text-gray-500 dark:text-gray-400 hover:text-primary hover:bg-gray-200 dark:hover:bg-white/10'"
        >
          {{ showPreview ? '隐藏预览' : '预览' }}
        </button>
      </div>
    </div>
    
    <div class="relative">
      <textarea
        ref="textareaRef"
        :value="modelValue"
        @input="handleInput"
        @keydown="handleKeydown"
        :placeholder="replyTo ? `回复 @${replyTo}...` : placeholder"
        :disabled="disabled"
        :rows="rows"
        class="w-full bg-transparent border-none outline-none text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 resize-none text-sm leading-relaxed"
      />
    </div>
    
    <div 
      v-if="showPreview && modelValue" 
      class="mt-3 p-3 bg-gray-50 dark:bg-dark-200/50 rounded-lg border border-gray-200 dark:border-white/5"
    >
      <div class="text-xs text-gray-500 dark:text-gray-400 mb-2">预览</div>
      <CommentMarkdownPreview :content="previewContent" :show-lang-label="true" />
    </div>
  </div>
</template>
