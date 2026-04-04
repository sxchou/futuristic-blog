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
const trackRef = ref<HTMLElement | null>(null)

const maxWidth = computed(() => trackWidth.value - buttonWidth)

const sliderStyle = computed(() => ({
  transform: `translateX(${sliderPosition.value}px)`
}))

const progressStyle = computed(() => ({
  width: `${sliderPosition.value + buttonWidth}px`
}))

const updateTrackWidth = () => {
  if (trackRef.value) {
    trackWidth.value = trackRef.value.offsetWidth
  }
}

onMounted(() => {
  updateTrackWidth()
  window.addEventListener('resize', updateTrackWidth)
})

const handleMouseDown = (e: MouseEvent) => {
  if (isVerified.value) return
  isDragging.value = true
  startX.value = e.clientX - sliderPosition.value
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

const handleMouseMove = (e: MouseEvent) => {
  if (!isDragging.value) return
  
  let newPosition = e.clientX - startX.value
  if (newPosition < 0) newPosition = 0
  if (newPosition > maxWidth.value) newPosition = maxWidth.value
  
  sliderPosition.value = newPosition
}

const handleMouseUp = () => {
  if (!isDragging.value) return
  isDragging.value = false
  
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
  
  if (sliderPosition.value >= maxWidth.value - 5) {
    isVerified.value = true
    sliderPosition.value = maxWidth.value
    emit('success')
  } else {
    sliderPosition.value = 0
    emit('fail')
  }
}

const handleTouchStart = (e: TouchEvent) => {
  if (isVerified.value) return
  isDragging.value = true
  startX.value = e.touches[0].clientX - sliderPosition.value
}

const handleTouchMove = (e: TouchEvent) => {
  if (!isDragging.value) return
  
  let newPosition = e.touches[0].clientX - startX.value
  if (newPosition < 0) newPosition = 0
  if (newPosition > maxWidth.value) newPosition = maxWidth.value
  
  sliderPosition.value = newPosition
}

const handleTouchEnd = () => {
  if (!isDragging.value) return
  isDragging.value = false
  
  if (sliderPosition.value >= maxWidth.value - 5) {
    isVerified.value = true
    sliderPosition.value = maxWidth.value
    emit('success')
  } else {
    sliderPosition.value = 0
    emit('fail')
  }
}

const reset = () => {
  isVerified.value = false
  sliderPosition.value = 0
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
      class="slider-track relative h-10 rounded-lg overflow-hidden bg-gray-200 dark:bg-dark-100 border border-gray-300 dark:border-white/10"
      :class="{ 'border-green-500/50 dark:border-green-500/50': isVerified }"
    >
      <div 
        class="slider-progress absolute left-0 top-0 h-full bg-gradient-to-r from-primary/20 to-accent/20 transition-[width] duration-100"
        :style="progressStyle"
      ></div>
      <div 
        class="slider-button absolute left-0 top-0 w-10 h-10 cursor-pointer flex items-center justify-center transition-all duration-100 bg-white dark:bg-dark-100 border-r border-gray-300 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-dark-300 rounded-l-lg"
        :class="{ 
          'border-primary dark:border-primary': isDragging,
          '!bg-gradient-to-r !from-green-500 !to-green-600 !border-green-500 cursor-default rounded-lg': isVerified 
        }"
        :style="sliderStyle"
        @mousedown="handleMouseDown"
        @touchstart="handleTouchStart"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
      >
        <svg v-if="!isVerified" class="w-5 h-5 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
        <svg v-else class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <span 
        v-if="!isVerified" 
        class="slider-text absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-sm text-gray-500 dark:text-gray-400 pointer-events-none z-[1]"
      >向右滑动验证</span>
      <span 
        v-else 
        class="slider-text absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-sm text-green-500 font-medium pointer-events-none z-[1]"
      >验证成功</span>
    </div>
  </div>
</template>

<style scoped>
.slider-captcha {
  user-select: none;
}
</style>
