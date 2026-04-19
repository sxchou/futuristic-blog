<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

const emit = defineEmits<{
  (e: 'success'): void
  (e: 'fail'): void
}>()

const isDragging = ref(false)
const sliderPosition = ref(0)
const startX = ref(0)
const trackWidth = ref(0)
const buttonWidth = 40
const isVerified = ref(false)
const hasFailed = ref(false)
const trackRef = ref<HTMLElement | null>(null)

const targetPosition = ref(0)
const tolerance = 15

const maxWidth = computed(() => trackWidth.value - buttonWidth)

const sliderStyle = computed(() => ({
  transform: `translateX(${sliderPosition.value}px)`,
  transition: isDragging.value ? 'none' : 'transform 0.15s ease-out'
}))

const targetStyle = computed(() => ({
  transform: `translateX(${targetPosition.value}px)`
}))

const updateTrackWidth = () => {
  if (trackRef.value) {
    trackWidth.value = trackRef.value.offsetWidth
    if (targetPosition.value === 0) {
      generateTarget()
    }
  }
}

const generateTarget = () => {
  const textWidth = 220
  const minPos = Math.max(textWidth, trackWidth.value * 0.35)
  const maxPos = trackWidth.value - buttonWidth - 10
  targetPosition.value = Math.floor(Math.random() * (maxPos - minPos) + minPos)
}

onMounted(() => {
  updateTrackWidth()
  window.addEventListener('resize', updateTrackWidth)
})

const handleMouseDown = (e: MouseEvent) => {
  if (isVerified.value) return
  e.preventDefault()
  hasFailed.value = false
  isDragging.value = true
  startX.value = e.clientX - sliderPosition.value
  document.addEventListener('mousemove', handleMouseMove, { passive: false })
  document.addEventListener('mouseup', handleMouseUp)
}

const handleMouseMove = (e: MouseEvent) => {
  if (!isDragging.value) return
  e.preventDefault()
  
  let newPosition = e.clientX - startX.value
  if (newPosition < 0) newPosition = 0
  if (newPosition > maxWidth.value) newPosition = maxWidth.value
  
  const distance = Math.abs(newPosition - targetPosition.value)
  if (distance <= tolerance) {
    newPosition = targetPosition.value
  }
  
  sliderPosition.value = newPosition
}

const handleMouseUp = () => {
  if (!isDragging.value) return
  isDragging.value = false
  
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
  
  const distance = Math.abs(sliderPosition.value - targetPosition.value)
  
  if (distance <= tolerance) {
    isVerified.value = true
    sliderPosition.value = targetPosition.value
    emit('success')
  } else {
    hasFailed.value = true
    sliderPosition.value = 0
    generateTarget()
    emit('fail')
    setTimeout(() => {
      hasFailed.value = false
    }, 800)
  }
}

const handleTouchStart = (e: TouchEvent) => {
  if (isVerified.value) return
  e.preventDefault()
  hasFailed.value = false
  isDragging.value = true
  startX.value = e.touches[0].clientX - sliderPosition.value
}

const handleTouchMove = (e: TouchEvent) => {
  if (!isDragging.value) return
  e.preventDefault()
  
  let newPosition = e.touches[0].clientX - startX.value
  if (newPosition < 0) newPosition = 0
  if (newPosition > maxWidth.value) newPosition = maxWidth.value
  
  const distance = Math.abs(newPosition - targetPosition.value)
  if (distance <= tolerance) {
    newPosition = targetPosition.value
  }
  
  sliderPosition.value = newPosition
}

const handleTouchEnd = () => {
  if (!isDragging.value) return
  isDragging.value = false
  
  const distance = Math.abs(sliderPosition.value - targetPosition.value)
  
  if (distance <= tolerance) {
    isVerified.value = true
    sliderPosition.value = targetPosition.value
    emit('success')
  } else {
    hasFailed.value = true
    sliderPosition.value = 0
    generateTarget()
    emit('fail')
    setTimeout(() => {
      hasFailed.value = false
    }, 800)
  }
}

const reset = () => {
  isVerified.value = false
  hasFailed.value = false
  sliderPosition.value = 0
  generateTarget()
}

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
  window.removeEventListener('resize', updateTrackWidth)
})

defineExpose({ reset })
</script>

<template>
  <div class="slider-captcha w-full select-none">
    <div 
      ref="trackRef"
      class="slider-track relative h-10 rounded-lg transition-colors duration-200"
      :class="[
        isVerified 
          ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800' 
          : hasFailed
            ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
            : 'bg-gray-100 dark:bg-dark-200 border border-gray-200 dark:border-white/10'
      ]"
    >
      <div 
        v-if="!isVerified"
        class="slider-target absolute left-0 w-10 h-9 pointer-events-none rounded-md border-2 border-dashed"
        :class="hasFailed ? 'border-red-400 bg-red-400/10' : 'border-primary bg-primary/10'"
        :style="{ ...targetStyle, top: '1px' }"
      />

      <div 
        class="slider-button absolute left-0 top-0 w-10 h-10 flex items-center justify-center cursor-pointer rounded-lg"
        :class="[
          isVerified 
            ? 'bg-green-500 cursor-default' 
            : hasFailed
              ? 'bg-red-400'
              : isDragging
                ? 'bg-primary shadow-md'
                : 'bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 hover:border-primary'
        ]"
        :style="sliderStyle"
        @mousedown="handleMouseDown"
        @touchstart.prevent="handleTouchStart"
        @touchmove.prevent="handleTouchMove"
        @touchend="handleTouchEnd"
      >
        <template v-if="!isVerified">
          <svg
            v-if="!hasFailed"
            class="w-4 h-4 transition-colors"
            :class="isDragging ? 'text-white' : 'text-gray-400 dark:text-gray-500'"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5l7 7-7 7"
            />
          </svg>
          <svg
            v-else
            class="w-4 h-4 text-white"
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
        </template>
        <svg
          v-else
          class="w-4 h-4 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>
      
      <span 
        v-if="!isVerified" 
        class="slider-text absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-xs pointer-events-none z-10"
        :class="hasFailed ? 'text-red-500' : 'text-gray-400 dark:text-gray-500'"
      >
        {{ hasFailed ? '安全验证失败' : '拖动滑块对准目标' }}
      </span>
      <span 
        v-else 
        class="slider-text absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-xs text-green-600 dark:text-green-400 font-medium pointer-events-none z-10"
      >
        安全验证成功
      </span>
    </div>
  </div>
</template>

<style scoped>
.slider-captcha {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

.slider-track {
  touch-action: none;
  -webkit-tap-highlight-color: transparent;
}

.slider-button {
  touch-action: none;
  will-change: transform;
  -webkit-tap-highlight-color: transparent;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.slider-button:active {
  transform: scale(0.95);
}

.slider-target {
  will-change: transform;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.slider-captcha:has(.slider-button.bg-red-400) .slider-track {
  animation: shake 0.25s ease-in-out;
}

@keyframes pulse-target {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.slider-target {
  animation: pulse-target 2s ease-in-out infinite;
}
</style>
