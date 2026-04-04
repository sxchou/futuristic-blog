<template>
  <div class="emoji-picker relative inline-block">
    <button
      type="button"
      @click="showPicker = !showPicker"
      class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-white/10 transition-colors"
      title="选择表情"
    >
      <svg class="w-5 h-5 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </button>
    
    <div
      v-if="showPicker"
      :class="[
        'absolute z-[100] bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg shadow-lg p-3 w-72',
        position === 'top' ? 'bottom-full mb-2 left-0' : 'top-full mt-2 left-0'
      ]"
    >
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs text-gray-500 dark:text-gray-400">选择表情</span>
        <button
          @click="showPicker = false"
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div class="flex gap-1 mb-2">
        <button
          v-for="cat in categories"
          :key="cat.name"
          @click="activeCategory = cat.name"
          :class="[
            'px-2 py-1 text-xs rounded transition-colors',
            activeCategory === cat.name
              ? 'bg-primary text-white'
              : 'bg-gray-100 dark:bg-dark-100 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-300'
          ]"
        >
          {{ cat.icon }} {{ cat.label }}
        </button>
      </div>
      
      <div class="grid grid-cols-8 gap-1 max-h-48 overflow-y-auto">
        <button
          v-for="emoji in currentEmojis"
          :key="emoji"
          @click="selectEmoji(emoji)"
          class="w-7 h-7 flex items-center justify-center text-lg hover:bg-gray-100 dark:hover:bg-white/10 rounded transition-colors"
        >
          {{ emoji }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = withDefaults(defineProps<{
  position?: 'top' | 'bottom'
}>(), {
  position: 'top'
})

const emit = defineEmits<{
  select: [emoji: string]
}>()

const showPicker = ref(false)
const activeCategory = ref('smileys')

const categories = [
  { name: 'smileys', icon: '😊', label: '表情' },
  { name: 'gestures', icon: '👋', label: '手势' },
  { name: 'animals', icon: '🐱', label: '动物' },
  { name: 'food', icon: '🍕', label: '食物' },
  { name: 'symbols', icon: '❤️', label: '符号' },
]

const emojis: Record<string, string[]> = {
  smileys: [
    '😊', '😂', '🤣', '😃', '😄', '😅', '😆', '😉', '😊', '😋',
    '😎', '😍', '😘', '🥰', '😗', '😙', '😚', '🙂', '🤗', '🤩',
    '🤔', '🤨', '😐', '😑', '😶', '🙄', '😏', '😣', '😥', '😮',
    '🤐', '😯', '😪', '😫', '😴', '😌', '😛', '😜', '😝', '🤤',
    '😒', '😓', '😔', '😕', '🙃', '🤑', '😲', '🙁', '😖', '😞',
    '😟', '😤', '😢', '😭', '😦', '😧', '😨', '😩', '🤯', '😬',
    '😰', '😱', '🥵', '🥶', '😳', '🤪', '😵', '🥴', '😠', '😡',
    '🤬', '😷', '🤒', '🤕', '🤢', '🤮', '🤧', '🥳', '🥺', '🤥',
  ],
  gestures: [
    '👋', '🤚', '🖐️', '✋', '🖖', '👌', '🤌', '🤏', '✌️', '🤞',
    '🤟', '🤘', '🤙', '👈', '👉', '👆', '🖕', '👇', '☝️', '👍',
    '👎', '✊', '👊', '🤛', '🤜', '👏', '🙌', '👐', '🤲', '🤝',
    '🙏', '✍️', '💪', '🦾', '🦿', '🦵', '🦶', '👂', '🦻', '👃',
  ],
  animals: [
    '🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯',
    '🦁', '🐮', '🐷', '🐸', '🐵', '🙈', '🙉', '🙊', '🐒', '🐔',
    '🐧', '🐦', '🐤', '🐣', '🐥', '🦆', '🦅', '🦉', '🦇', '🐺',
    '🐗', '🐴', '🦄', '🐝', '🐛', '🦋', '🐌', '🐞', '🐜', '🦟',
    '🐢', '🐍', '🦎', '🦖', '🦕', '🐙', '🦑', '🦐', '🦞', '🦀',
    '🐡', '🐠', '🐟', '🐬', '🐳', '🐋', '🦈', '🐊', '🐅', '🐆',
  ],
  food: [
    '🍎', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🫐', '🍈',
    '🍒', '🍑', '🥭', '🍍', '🥥', '🥝', '🍅', '🍆', '🥑', '🥦',
    '🥬', '🥒', '🌶️', '🫑', '🌽', '🥕', '🫒', '🧄', '🧅', '🥔',
    '🍠', '🥐', '🥯', '🍞', '🥖', '🥨', '🧀', '🥚', '🍳', '🧈',
    '🥞', '🧇', '🥓', '🥩', '🍗', '🍖', '🦴', '🌭', '🍔', '🍟',
    '🍕', '🫓', '🥪', '🥙', '🧆', '🌮', '🌯', '🫔', '🥗', '🥘',
  ],
  symbols: [
    '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔',
    '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️',
    '✝️', '☪️', '🕉️', '☸️', '✡️', '🔯', '🕎', '☯️', '☦️', '🛐',
    '⛎', '♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐',
    '♑', '♒', '♓', '🆔', '⚛️', '🉑', '☢️', '☣️', '📴', '📳',
    '🈶', '🈚', '🈸', '🈺', '🈷️', '✴️', '🆚', '💮', '🉐', '㊙️',
  ],
}

const currentEmojis = computed(() => emojis[activeCategory.value] || [])

const selectEmoji = (emoji: string) => {
  emit('select', emoji)
  showPicker.value = false
}

const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.emoji-picker')) {
    showPicker.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
