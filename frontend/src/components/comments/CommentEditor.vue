<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import CommentMarkdownPreview from './CommentMarkdownPreview.vue'
import EmojiPicker from '@/components/common/EmojiPicker.vue'

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
  disabled?: boolean
  replyTo?: string
  rows?: number
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

let debounceTimer: ReturnType<typeof setTimeout> | null = null

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

const toolbarActions = [
  { icon: 'B', title: '粗体', action: () => insertText('**', '**') },
  { icon: 'I', title: '斜体', action: () => insertText('*', '*') },
  { icon: 'S', title: '删除线', action: () => insertText('~~', '~~') },
  { icon: '</>', title: '代码', action: () => insertText('`', '`') },
  { icon: '```', title: '代码块', action: () => insertText('\n```\n', '\n```\n') },
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

watch(() => props.modelValue, (newVal) => {
  previewContent.value = newVal
}, { immediate: true })

defineExpose({
  focus: () => textareaRef.value?.focus()
})
</script>

<template>
  <div class="comment-editor">
    <div class="flex justify-between items-center mb-2">
      <div class="flex items-center gap-1">
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
      <CommentMarkdownPreview :content="previewContent" />
    </div>
  </div>
</template>
