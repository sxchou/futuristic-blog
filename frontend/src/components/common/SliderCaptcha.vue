<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'

const emit = defineEmits<{
  (e: 'success'): void
  (e: 'fail'): void
}>()

const isDragging = ref(false)
const sliderPosition = ref(0)
const startX = ref(0)
const maxWidth = ref(280)
const isVerified = ref(false)

const sliderStyle = computed(() => ({
  transform: `translateX(${sliderPosition.value}px)`
}))

const progressStyle = computed(() => ({
  width: `${sliderPosition.value + 40}px`
}))

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
  
  if (sliderPosition.value >= maxWidth.value - 10) {
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
  
  if (sliderPosition.value >= maxWidth.value - 10) {
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
})

defineExpose({ reset })
</script>

<template>
  <div class="slider-captcha">
    <div 
      class="slider-track"
      :class="{ 'verified': isVerified }"
    >
      <div class="slider-progress" :style="progressStyle"></div>
      <div 
        class="slider-button"
        :class="{ 'verified': isVerified, 'dragging': isDragging }"
        :style="sliderStyle"
        @mousedown="handleMouseDown"
        @touchstart="handleTouchStart"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
      >
        <svg v-if="!isVerified" class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
        <svg v-else class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <span v-if="!isVerified" class="slider-text">向右滑动验证</span>
      <span v-else class="slider-text verified-text">验证成功</span>
    </div>
  </div>
</template>

<style scoped>
.slider-captcha {
  width: 100%;
  user-select: none;
}

.slider-track {
  position: relative;
  height: 40px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  overflow: hidden;
}

.slider-track.verified {
  border-color: rgba(34, 197, 94, 0.5);
}

.slider-progress {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(90deg, rgba(0, 212, 255, 0.2) 0%, rgba(124, 58, 237, 0.2) 100%);
  transition: width 0.1s ease;
}

.slider-button {
  position: absolute;
  left: 0;
  top: 0;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #2a2a4e 0%, #1a1a3e 100%);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.1s ease, background 0.3s ease, border-color 0.3s ease;
  z-index: 2;
}

.slider-button:hover {
  background: linear-gradient(135deg, #3a3a5e 0%, #2a2a4e 100%);
}

.slider-button.dragging {
  border-color: rgba(0, 212, 255, 0.6);
}

.slider-button.verified {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border-color: rgba(34, 197, 94, 0.6);
  cursor: default;
}

.slider-text {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-size: 14px;
  color: #9ca3af;
  pointer-events: none;
  z-index: 1;
}

.verified-text {
  color: #22c55e;
  font-weight: 500;
}
</style>
