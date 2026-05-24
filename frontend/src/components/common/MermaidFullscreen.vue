<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

const isOpen = ref(false)
const svgContent = ref('')
const mermaidCode = ref('')
const scale = ref(100)
const isCopied = ref(false)
const scrollRef = ref<HTMLElement>()
const isDragging = ref(false)

const dragState = { startX: 0, startY: 0, scrollLeft: 0, scrollTop: 0 }

const MIN_SCALE = 20
const MAX_SCALE = 300
const BTN_STEP = 20
const WHEEL_STEP = 10

const open = async (svg: string, code: string) => {
  svgContent.value = svg
  mermaidCode.value = code
  scale.value = 100
  isCopied.value = false
  isOpen.value = true
  document.body.style.overflow = 'hidden'

  await nextTick()
  autoFit()
}

const autoFit = () => {
  const container = scrollRef.value
  if (!container) return

  const svg = container.querySelector('svg') as SVGSVGElement | null
  if (!svg) return

  const vb = svg.viewBox?.baseVal
  if (!vb || vb.width === 0 || vb.height === 0) return

  const padding = 64
  const availH = container.clientHeight - padding

  const svgHeightAt100 = container.clientWidth * (vb.height / vb.width)
  const scaleX = 100
  const scaleY = (availH / svgHeightAt100) * 100

  const fitScale = Math.min(scaleX, scaleY)
  scale.value = Math.max(MIN_SCALE, Math.round(fitScale / 5) * 5)
}

const close = () => {
  isOpen.value = false
  isDragging.value = false
  document.body.style.overflow = ''
}

const zoomIn = () => {
  scale.value = Math.min(MAX_SCALE, scale.value + BTN_STEP)
}

const zoomOut = () => {
  scale.value = Math.max(MIN_SCALE, scale.value - BTN_STEP)
}

const resetZoom = () => {
  autoFit()
  if (scrollRef.value) {
    scrollRef.value.scrollTo({ top: 0, left: 0, behavior: 'smooth' })
  }
}

const copySource = async () => {
  try {
    await navigator.clipboard.writeText(decodeURIComponent(mermaidCode.value))
    isCopied.value = true
    setTimeout(() => { isCopied.value = false }, 2000)
  } catch { /* ignore */ }
}

const onWheel = (e: WheelEvent) => {
  const delta = e.deltaY > 0 ? -WHEEL_STEP : WHEEL_STEP
  const newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scale.value + delta))
  if (newScale === scale.value) return

  const container = scrollRef.value
  if (!container) return

  const rect = container.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top

  const ratioX = (mouseX + container.scrollLeft) / container.scrollWidth
  const ratioY = (mouseY + container.scrollTop) / container.scrollHeight

  scale.value = newScale

  nextTick(() => {
    container.scrollLeft = ratioX * container.scrollWidth - mouseX
    container.scrollTop = ratioY * container.scrollHeight - mouseY
  })
}

const onDragStart = (e: MouseEvent) => {
  if (e.button !== 0) return
  const container = scrollRef.value
  if (!container) return
  isDragging.value = true
  dragState.startX = e.clientX
  dragState.startY = e.clientY
  dragState.scrollLeft = container.scrollLeft
  dragState.scrollTop = container.scrollTop
}

const onDragMove = (e: MouseEvent) => {
  if (!isDragging.value) return
  const container = scrollRef.value
  if (!container) return
  const dx = e.clientX - dragState.startX
  const dy = e.clientY - dragState.startY
  container.scrollLeft = dragState.scrollLeft - dx
  container.scrollTop = dragState.scrollTop - dy
}

const onDragEnd = () => {
  isDragging.value = false
}

const handleKeydown = (e: KeyboardEvent) => {
  if (!isOpen.value) return
  if (e.key === 'Escape') close()
  else if (e.key === '+' || e.key === '=') { e.preventDefault(); zoomIn() }
  else if (e.key === '-') { e.preventDefault(); zoomOut() }
  else if (e.key === '0') { e.preventDefault(); resetZoom() }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
  if (isOpen.value) document.body.style.overflow = ''
})

defineExpose({ open })
</script>

<template>
  <Teleport to="body">
    <Transition name="mfs">
      <div v-if="isOpen" class="mfs-overlay">
        <div class="mfs-layout">
          <div class="mfs-toolbar">
            <button class="mfs-btn" @click="copySource" :title="isCopied ? '已复制' : '复制源码'">
              <svg v-if="!isCopied" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="text-green-400"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
            </button>
            <div class="mfs-sep"></div>
            <button class="mfs-btn" @click="zoomOut" :disabled="scale <= MIN_SCALE" title="缩小 (-)">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" /></svg>
            </button>
            <span class="mfs-scale">{{ scale }}%</span>
            <button class="mfs-btn" @click="zoomIn" :disabled="scale >= MAX_SCALE" title="放大 (+)">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" /></svg>
            </button>
            <div class="mfs-sep"></div>
            <button class="mfs-btn" @click="resetZoom" title="重置缩放 (0)">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
            </button>
            <div class="mfs-sep"></div>
            <button class="mfs-btn" @click="close" title="关闭 (Esc)">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
          <div class="mfs-viewer" @wheel.prevent="onWheel">
            <div
              class="mfs-scroll"
              ref="scrollRef"
              :class="{ 'mfs-dragging': isDragging }"
              :style="{ '--mfs-scale': scale + '%' }"
              @mousedown="onDragStart"
            >
              <div class="mfs-content" v-html="svgContent"></div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.mfs-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

.mfs-layout {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

.mfs-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 8px 12px;
  gap: 4px;
  flex-shrink: 0;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  z-index: 1;
}

:root.dark .mfs-toolbar {
  background: #1a1a2e;
  border-bottom-color: rgba(255, 255, 255, 0.1);
}

.mfs-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s ease;
  padding: 0;
}

.mfs-btn:hover:not(:disabled) {
  background: #f3f4f6;
  color: #111827;
}

:root.dark .mfs-btn {
  color: #9ca3af;
}

:root.dark .mfs-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: #f3f4f6;
}

.mfs-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.mfs-btn svg {
  width: 20px;
  height: 20px;
}

.mfs-sep {
  width: 1px;
  height: 20px;
  background: #e5e7eb;
  margin: 0 4px;
}

:root.dark .mfs-sep {
  background: rgba(255, 255, 255, 0.1);
}

.mfs-scale {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  min-width: 40px;
  text-align: center;
  user-select: none;
  font-variant-numeric: tabular-nums;
}

:root.dark .mfs-scale {
  color: #9ca3af;
}

.mfs-viewer {
  flex: 1;
  overflow: hidden;
  position: relative;
  min-width: 0;
}

.mfs-scroll {
  width: 100%;
  height: 100%;
  overflow: auto;
  background: #f9fafb;
  cursor: grab;
}

.mfs-scroll.mfs-dragging {
  cursor: grabbing;
  user-select: none;
}

:root.dark .mfs-scroll {
  background: #0f0f1a;
}

.mfs-content {
  display: inline-flex;
  min-width: 100%;
  min-height: 100%;
  padding: 2rem;
  box-sizing: border-box;
}

.mfs-content :deep(svg) {
  width: var(--mfs-scale) !important;
  max-width: none !important;
  height: auto !important;
  display: block !important;
  flex-shrink: 0;
  pointer-events: none;
  margin: auto;
}

.mfs-enter-active,
.mfs-leave-active {
  transition: opacity 0.2s ease;
}

.mfs-enter-from,
.mfs-leave-to {
  opacity: 0;
}
</style>
