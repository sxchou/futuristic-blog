<template>
  <div class="icon-picker relative inline-block">
    <div
      ref="triggerRef"
      class="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg cursor-pointer hover:border-primary/50 transition-colors"
      @click.stop="togglePicker"
    >
      <div
        v-if="modelValue"
        class="w-6 h-6 flex items-center justify-center text-lg"
      >
        {{ modelValue }}
      </div>
      <div
        v-else
        class="w-6 h-6 flex items-center justify-center text-gray-400"
      >
        <svg
          class="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      </div>
      <span class="text-sm text-gray-600 dark:text-gray-300 flex-1">
        {{ modelValue || '选择图标' }}
      </span>
      <svg
        class="w-4 h-4 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 9l-7 7-7-7"
        />
      </svg>
    </div>

    <Teleport to="body">
      <div
        v-if="showPicker"
        class="fixed z-[9999] bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg shadow-2xl p-4 w-80"
        :style="pickerStyle"
        @click.stop
      >
        <div class="flex items-center justify-between mb-3 cursor-move select-none" @mousedown="handleDragStart">
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">选择图标</span>
          <button
            type="button"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 cursor-pointer"
            @click.stop="showPicker = false"
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

        <div class="flex gap-1 mb-3 flex-wrap">
          <button
            v-for="cat in emojiCategories"
            :key="cat.name"
            type="button"
            :class="[
              'px-2 py-1 text-xs rounded transition-colors',
              activeEmojiCategory === cat.name
                ? 'bg-primary/20 text-primary'
                : 'bg-gray-100 dark:bg-dark-200 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-300'
            ]"
            @click.stop="activeEmojiCategory = cat.name"
          >
            {{ cat.icon }} {{ cat.label }}
          </button>
        </div>

        <div class="grid grid-cols-8 gap-1 max-h-64 overflow-y-auto">
          <button
            v-for="emoji in categoryEmojis"
            :key="emoji"
            type="button"
            :class="[
              'w-8 h-8 flex items-center justify-center text-lg hover:bg-primary/10 rounded transition-colors',
              modelValue === emoji ? 'bg-primary/20 ring-2 ring-primary' : ''
            ]"
            @click.stop="selectIcon(emoji)"
          >
            {{ emoji }}
          </button>
        </div>

        <div class="flex items-center justify-between mt-3 pt-3 border-t border-gray-200 dark:border-white/10">
          <button
            type="button"
            class="text-xs text-gray-500 hover:text-red-400 transition-colors"
            @click.stop="clearIcon"
          >
            清除图标
          </button>
          <button
            type="button"
            class="px-3 py-1.5 text-xs bg-primary text-white rounded hover:bg-primary/80 transition-colors"
            @click.stop="showPicker = false"
          >
            确定
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  modelValue?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | undefined]
}>()

const showPicker = ref(false)
const activeEmojiCategory = ref('smileys')
const triggerRef = ref<HTMLElement | null>(null)
const pickerPosition = ref({ top: 0, left: 0 })
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0, top: 0, left: 0 })

const emojiCategories = [
  { name: 'smileys', icon: '😊', label: '表情' },
  { name: 'gestures', icon: '👋', label: '手势' },
  { name: 'animals', icon: '🐱', label: '动物' },
  { name: 'food', icon: '🍕', label: '食物' },
  { name: 'symbols', icon: '❤️', label: '符号' },
  { name: 'objects', icon: '💡', label: '物品' },
  { name: 'nature', icon: '🌸', label: '自然' },
  { name: 'tech', icon: '💻', label: '科技' },
]

const emojis: Record<string, string[]> = {
  smileys: [
    '😊', '😂', '🤣', '😃', '😄', '😅', '😆', '😉', '😋', '😎',
    '😍', '😘', '🥰', '😗', '😙', '😚', '🙂', '🤗', '🤩', '🤔',
    '🤨', '😐', '😑', '😶', '🙄', '😏', '😣', '😥', '😮', '🤐',
    '😯', '😪', '😫', '😴', '😌', '😛', '😜', '😝', '🤤', '😒',
    '😓', '😔', '😕', '🙃', '🤑', '😲', '🙁', '😖', '😞', '😟',
    '😤', '😢', '😭', '😦', '😧', '😨', '😩', '🤯', '😬', '😰',
    '😱', '🥵', '🥶', '😳', '🤪', '😵', '🥴', '😠', '😡', '🤬',
    '😷', '🤒', '🤕', '🤢', '🤮', '🤧', '🥳', '🥺', '🤥', '🤫',
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
  objects: [
    '💡', '🔦', '🏮', '📱', '💻', '🖥️', '🖨️', '⌨️', '🖱️', '🖲️',
    '💽', '💾', '💿', '📀', '📼', '📷', '📸', '📹', '🎥', '📽️',
    '🎬', '📺', '📻', '🎙️', '🎚️', '🎛️', '🎤', '🎧', '🎼', '🎵',
    '🎶', '🎹', '🥁', '🎷', '🎺', '🎸', '🪕', '🎻', '🪗', '🥁',
    '⌚', '📱', '📲', '💻', '⌨️', '🖥️', '🖨️', '🖱️', '🖲️', '🕹️',
    '🗜️', '💽', '💾', '💿', '📀', '📼', '📷', '📸', '📹', '🎥',
  ],
  nature: [
    '🌸', '🌺', '🌻', '🌹', '🥀', '🌷', '🌱', '🌲', '🌳', '🌴',
    '🌵', '🌾', '🌿', '☘️', '🍀', '🍁', '🍂', '🍃', '🌊', '💧',
    '💦', '☔', '🌈', '⭐', '🌟', '✨', '⚡', '☄️', '💥', '🔥',
    '🌪️', '🌈', '☀️', '🌤️', '⛅', '🌥️', '☁️', '🌦️', '🌧️', '🌨️',
    '❄️', '☃️', '⛄', '🌬️', '💨', '🌪️', '🌫️', '🌊', '💧', '💦',
    '☔', '🌈', '⭐', '🌟', '✨', '⚡', '☄️', '💥', '🔥', '🌙',
  ],
  tech: [
    '💻', '🖥️', '📱', '⌨️', '🖱️', '🖨️', '💾', '💿', '📀', '📼',
    '📷', '📹', '🎥', '📺', '📻', '🎧', '🎤', '🔊', '🔔', '📡',
    '🔋', '🔌', '💡', '🔦', '🔧', '🔨', '⚙️', '🛠️', '🔩', '🔧',
    '📡', '🌐', '🔒', '🔓', '🔑', '🗝️', '🛡️', '📧', '📨', '📩',
    '💬', '💭', '📝', '📄', '📃', '📑', '📊', '📈', '📉', '📋',
    '📁', '📂', '🗂️', '📅', '📆', '🗓️', '📇', '🗃️', '🗄️', '🗑️',
    '🤖', '🧠', '🔬', '🔭', '🚀', '🛸', '✈️', '🛩️', '🚁', '🛰️',
    '🌐', '🌍', '🌎', '🌏', '🗺️', '🧭', '📍', '🚩', '🏁', '🎯',
  ],
}

const categoryEmojis = computed(() => {
  return emojis[activeEmojiCategory.value] || []
})

const pickerStyle = computed(() => {
  return {
    top: `${pickerPosition.value.top}px`,
    left: `${pickerPosition.value.left}px`
  }
})

const updatePickerPosition = () => {
  if (!triggerRef.value) return
  
  const rect = triggerRef.value.getBoundingClientRect()
  const viewportHeight = window.innerHeight
  const viewportWidth = window.innerWidth
  const pickerHeight = 400
  const pickerWidth = 320
  const margin = 8
  
  let top = rect.bottom + margin
  let left = rect.left
  
  if (top + pickerHeight > viewportHeight) {
    top = rect.top - pickerHeight - margin
  }
  
  if (top < margin) {
    top = margin
  }
  
  if (left + pickerWidth > viewportWidth) {
    left = viewportWidth - pickerWidth - margin
  }
  
  if (left < margin) {
    left = margin
  }
  
  pickerPosition.value = { top, left }
}

const togglePicker = () => {
  if (!showPicker.value) {
    updatePickerPosition()
  }
  showPicker.value = !showPicker.value
}

const selectIcon = (icon: string) => {
  emit('update:modelValue', icon)
}

const clearIcon = () => {
  emit('update:modelValue', undefined)
  showPicker.value = false
}

const handleClickOutside = (event: MouseEvent) => {
  if (showPicker.value) {
    const target = event.target as HTMLElement
    const picker = document.querySelector('.icon-picker .fixed')
    if (picker && !picker.contains(target) && !triggerRef.value?.contains(target)) {
      showPicker.value = false
    }
  }
}

const handleDragStart = (event: MouseEvent) => {
  isDragging.value = true
  dragStart.value = {
    x: event.clientX,
    y: event.clientY,
    top: pickerPosition.value.top,
    left: pickerPosition.value.left
  }
  event.preventDefault()
}

const handleDragMove = (event: MouseEvent) => {
  if (!isDragging.value) return
  
  const deltaX = event.clientX - dragStart.value.x
  const deltaY = event.clientY - dragStart.value.y
  
  pickerPosition.value = {
    top: dragStart.value.top + deltaY,
    left: dragStart.value.left + deltaX
  }
}

const handleDragEnd = () => {
  isDragging.value = false
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('mousemove', handleDragMove)
  document.addEventListener('mouseup', handleDragEnd)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('mousemove', handleDragMove)
  document.removeEventListener('mouseup', handleDragEnd)
})
</script>
