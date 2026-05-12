<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm"
    >
      <div
        class="bg-white dark:bg-dark-100 rounded-2xl shadow-2xl w-full max-w-4xl mx-2 sm:mx-4 max-h-[90vh] overflow-hidden flex flex-col"
        @click.stop
      >
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-white/10">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ title || '裁剪图片' }}
          </h3>
          <button
            type="button"
            class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 transition-colors"
            @click="handleCancel"
          >
            <svg
              class="w-5 h-5 text-gray-500"
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

        <div class="flex-1 overflow-auto p-6">
          <div class="flex gap-6 min-h-0">
            <div class="flex-1 flex flex-col min-h-0">
              <div class="cropper-wrapper bg-gray-100 dark:bg-dark-100 rounded-lg overflow-hidden relative flex-shrink-0">
                <img
                  ref="imageRef"
                  :src="imageSrc"
                  class="cropper-image"
                  alt="裁剪图片"
                >
                <div
                  v-if="isLoading"
                  class="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-dark-100"
                >
                  <div class="flex flex-col items-center gap-3">
                    <div class="w-8 h-8 border-3 border-primary/30 border-t-primary rounded-full animate-spin" />
                    <span class="text-sm text-gray-500">加载中...</span>
                  </div>
                </div>
                <div
                  v-if="loadError"
                  class="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-dark-100"
                >
                  <div class="flex flex-col items-center gap-2">
                    <svg
                      class="w-10 h-10 text-red-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                      />
                    </svg>
                    <span class="text-sm text-red-500">图片加载失败</span>
                  </div>
                </div>
              </div>

              <div class="flex items-center justify-center gap-2 mt-3 flex-wrap flex-shrink-0">
                <button
                  type="button"
                  class="cropper-btn p-2 rounded-lg bg-gray-100 dark:bg-dark-100 hover:bg-gray-200 dark:hover:bg-dark-300 transition-colors relative"
                  :class="{ 'opacity-50 cursor-not-allowed': !cropperReady }"
                  :disabled="!cropperReady"
                  @click="handleZoomIn"
                  @mouseenter="showTooltip('zoomin')"
                  @mouseleave="hideTooltip"
                >
                  <svg
                    class="w-5 h-5 text-gray-600 dark:text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"
                    />
                  </svg>
                  <span
                    v-if="activeTooltip === 'zoomin'"
                    class="action-tooltip"
                  >
                    放大
                  </span>
                </button>
                <button
                  type="button"
                  class="cropper-btn p-2 rounded-lg bg-gray-100 dark:bg-dark-100 hover:bg-gray-200 dark:hover:bg-dark-300 transition-colors relative"
                  :class="{ 'opacity-50 cursor-not-allowed': !cropperReady }"
                  :disabled="!cropperReady"
                  @click="handleZoomOut"
                  @mouseenter="showTooltip('zoomout')"
                  @mouseleave="hideTooltip"
                >
                  <svg
                    class="w-5 h-5 text-gray-600 dark:text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7"
                    />
                  </svg>
                  <span
                    v-if="activeTooltip === 'zoomout'"
                    class="action-tooltip"
                  >
                    缩小
                  </span>
                </button>
                <div class="w-px h-6 bg-gray-200 dark:bg-white/10" />
                <button
                  type="button"
                  class="cropper-btn p-2 rounded-lg bg-gray-100 dark:bg-dark-100 hover:bg-gray-200 dark:hover:bg-dark-300 transition-colors relative"
                  :class="{ 'opacity-50 cursor-not-allowed': !cropperReady }"
                  :disabled="!cropperReady"
                  @click="handleRotateLeft"
                  @mouseenter="showTooltip('rotateleft')"
                  @mouseleave="hideTooltip"
                >
                  <svg
                    class="w-5 h-5 text-gray-600 dark:text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
                    />
                  </svg>
                  <span
                    v-if="activeTooltip === 'rotateleft'"
                    class="action-tooltip"
                  >
                    向左旋转
                  </span>
                </button>
                <button
                  type="button"
                  class="cropper-btn p-2 rounded-lg bg-gray-100 dark:bg-dark-100 hover:bg-gray-200 dark:hover:bg-dark-300 transition-colors relative"
                  :class="{ 'opacity-50 cursor-not-allowed': !cropperReady }"
                  :disabled="!cropperReady"
                  @click="handleRotateRight"
                  @mouseenter="showTooltip('rotateright')"
                  @mouseleave="hideTooltip"
                >
                  <svg
                    class="w-5 h-5 text-gray-600 dark:text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M21 10h-10a8 8 0 00-8 8v2M21 10l-6 6m6-6l-6-6"
                    />
                  </svg>
                  <span
                    v-if="activeTooltip === 'rotateright'"
                    class="action-tooltip"
                  >
                    向右旋转
                  </span>
                </button>
                <div class="w-px h-6 bg-gray-200 dark:bg-white/10" />
                <button
                  type="button"
                  class="cropper-btn p-2 rounded-lg bg-gray-100 dark:bg-dark-100 hover:bg-gray-200 dark:hover:bg-dark-300 transition-colors relative"
                  :class="{ 'opacity-50 cursor-not-allowed': !cropperReady }"
                  :disabled="!cropperReady"
                  @click="handleFlipHorizontal"
                  @mouseenter="showTooltip('fliph')"
                  @mouseleave="hideTooltip"
                >
                  <svg
                    class="w-5 h-5 text-gray-600 dark:text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M7 21h10M12 3v18M17 6l4 6-4 6M7 6l-4 6 4 6"
                    />
                  </svg>
                  <span
                    v-if="activeTooltip === 'fliph'"
                    class="action-tooltip"
                  >
                    水平翻转
                  </span>
                </button>
                <button
                  type="button"
                  class="cropper-btn p-2 rounded-lg bg-gray-100 dark:bg-dark-100 hover:bg-gray-200 dark:hover:bg-dark-300 transition-colors relative"
                  :class="{ 'opacity-50 cursor-not-allowed': !cropperReady }"
                  :disabled="!cropperReady"
                  @click="handleFlipVertical"
                  @mouseenter="showTooltip('flipv')"
                  @mouseleave="hideTooltip"
                >
                  <svg
                    class="w-5 h-5 text-gray-600 dark:text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M3 7v10M21 7v10M6 12h12M6 17l6 4 6-4M6 7l6-4 6 4"
                    />
                  </svg>
                  <span
                    v-if="activeTooltip === 'flipv'"
                    class="action-tooltip"
                  >
                    垂直翻转
                  </span>
                </button>
                <div class="w-px h-6 bg-gray-200 dark:bg-white/10" />
                <button
                  type="button"
                  class="cropper-btn p-2 rounded-lg bg-gray-100 dark:bg-dark-100 hover:bg-gray-200 dark:hover:bg-dark-300 transition-colors relative"
                  :class="{ 'opacity-50 cursor-not-allowed': !cropperReady }"
                  :disabled="!cropperReady"
                  @click="handleReset"
                  @mouseenter="showTooltip('reset')"
                  @mouseleave="hideTooltip"
                >
                  <svg
                    class="w-5 h-5 text-gray-600 dark:text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  <span
                    v-if="activeTooltip === 'reset'"
                    class="action-tooltip"
                  >
                    重置
                  </span>
                </button>
              </div>
            </div>

            <div
              v-if="!isFreeCrop"
              class="w-48 flex-shrink-0 hidden lg:block"
            >
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                预览
              </p>
              <div class="space-y-3">
                <div>
                  <div
                    ref="previewRef"
                    class="preview-container w-48 h-[100px] rounded-lg overflow-hidden bg-gray-100 dark:bg-dark-100 border-2 border-gray-200 dark:border-white/10"
                  />
                  <p class="text-xs text-gray-400 dark:text-gray-500 mt-1 text-center">
                    1200 × 630 px
                  </p>
                </div>
                <div>
                  <div
                    ref="previewSmallRef"
                    class="preview-container w-32 h-[68px] rounded-lg overflow-hidden bg-gray-100 dark:bg-dark-100 border-2 border-gray-200 dark:border-white/10 mx-auto"
                  />
                  <p class="text-xs text-gray-400 dark:text-gray-500 mt-1 text-center">
                    800 × 420 px
                  </p>
                </div>
              </div>

              <div class="mt-4 p-3 bg-gray-50 dark:bg-dark-100/50 rounded-lg">
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  <span class="font-medium text-gray-700 dark:text-gray-300">提示：</span>
                  拖动选择框调整裁剪区域，使用上方按钮进行缩放和旋转。
                </p>
              </div>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-dark-100/50">
          <button
            type="button"
            class="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            @click="handleCancel"
          >
            取消
          </button>
          <button
            type="button"
            :disabled="!cropperReady || isProcessing"
            class="px-6 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            @click="handleConfirm"
          >
            <svg
              v-if="isProcessing"
              class="w-4 h-4 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            {{ isProcessing ? '处理中...' : '确认裁剪' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted, nextTick, computed } from 'vue'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'

const props = defineProps<{
  modelValue: boolean
  imageSrc: string
  aspectRatio?: number
  outputWidth?: number
  outputHeight?: number
  outputQuality?: number
  title?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', blob: Blob): void
  (e: 'cancel'): void
}>()

const imageRef = ref<HTMLImageElement | null>(null)
const previewRef = ref<HTMLDivElement | null>(null)
const previewSmallRef = ref<HTMLDivElement | null>(null)
const cropperInstance = ref<Cropper | null>(null)
const isProcessing = ref(false)
const cropperReady = ref(false)
const isLoading = ref(true)
const loadError = ref(false)
const scaleState = ref({ x: 1, y: 1 })

const activeTooltip = ref<string | null>(null)

const showTooltip = (name: string) => {
  activeTooltip.value = name
}

const hideTooltip = () => {
  activeTooltip.value = null
}

const COVER_ASPECT_RATIO = 1200 / 630
const isFreeCrop = computed(() => isNaN(props.aspectRatio ?? 0))

const loadImage = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (!imageRef.value) {
      reject(new Error('Image ref is null'))
      return
    }

    const img = imageRef.value
    
    if (img.complete && img.naturalWidth > 0) {
      resolve()
      return
    }

    const handleLoad = () => {
      img.removeEventListener('load', handleLoad)
      img.removeEventListener('error', handleError)
      resolve()
    }

    const handleError = () => {
      img.removeEventListener('load', handleLoad)
      img.removeEventListener('error', handleError)
      reject(new Error('Image failed to load'))
    }

    img.addEventListener('load', handleLoad)
    img.addEventListener('error', handleError)
  })
}

const initCropper = async () => {
  if (!imageRef.value) {
    console.warn('Cropper init: image ref is null')
    isLoading.value = false
    loadError.value = true
    return
  }

  if (!isFreeCrop.value && (!previewRef.value || !previewSmallRef.value)) {
    console.warn('Cropper init: preview refs are null')
    isLoading.value = false
    loadError.value = true
    return
  }

  destroyCropper()

  cropperReady.value = false
  scaleState.value = { x: 1, y: 1 }
  loadError.value = false
  isLoading.value = true

  try {
    await loadImage()

    await new Promise(resolve => setTimeout(resolve, 50))

    const cropperOptions: Cropper.Options = {
      viewMode: 1,
      dragMode: 'move',
      autoCropArea: 0.9,
      restore: false,
      guides: true,
      center: true,
      highlight: false,
      cropBoxMovable: true,
      cropBoxResizable: true,
      toggleDragModeOnDblclick: false,
      ready: () => {
        cropperReady.value = true
        isLoading.value = false
      }
    }
    
    if (!isFreeCrop.value) {
      cropperOptions.aspectRatio = props.aspectRatio ?? COVER_ASPECT_RATIO
      if (previewRef.value && previewSmallRef.value) {
        cropperOptions.preview = [previewRef.value, previewSmallRef.value]
      }
    }

    cropperInstance.value = new Cropper(imageRef.value!, cropperOptions)
  } catch (error) {
    console.error('Failed to initialize cropper:', error)
    isLoading.value = false
    loadError.value = true
  }
}

const handleZoomIn = () => {
  if (!cropperInstance.value || !cropperReady.value) return
  cropperInstance.value.zoom(0.1)
}

const handleZoomOut = () => {
  if (!cropperInstance.value || !cropperReady.value) return
  cropperInstance.value.zoom(-0.1)
}

const handleRotateLeft = () => {
  if (!cropperInstance.value || !cropperReady.value) return
  cropperInstance.value.rotate(-90)
}

const handleRotateRight = () => {
  if (!cropperInstance.value || !cropperReady.value) return
  cropperInstance.value.rotate(90)
}

const handleFlipHorizontal = () => {
  if (!cropperInstance.value || !cropperReady.value) return
  const newX = scaleState.value.x === 1 ? -1 : 1
  cropperInstance.value.scaleX(newX)
  scaleState.value.x = newX
}

const handleFlipVertical = () => {
  if (!cropperInstance.value || !cropperReady.value) return
  const newY = scaleState.value.y === 1 ? -1 : 1
  cropperInstance.value.scaleY(newY)
  scaleState.value.y = newY
}

const handleReset = () => {
  if (!cropperInstance.value || !cropperReady.value) return
  cropperInstance.value.reset()
  scaleState.value = { x: 1, y: 1 }
}

const handleConfirm = async () => {
  if (!cropperInstance.value || !cropperReady.value || isProcessing.value) return

  isProcessing.value = true

  try {
    const canvasOptions: Cropper.GetCroppedCanvasOptions = {
      imageSmoothingEnabled: true,
      imageSmoothingQuality: 'high'
    }
    
    if (props.outputWidth && props.outputHeight) {
      canvasOptions.width = props.outputWidth
      canvasOptions.height = props.outputHeight
    }

    const canvas = cropperInstance.value.getCroppedCanvas(canvasOptions)

    if (!canvas) {
      throw new Error('Failed to create canvas')
    }

    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(
        (blob: Blob | null) => {
          if (blob) {
            resolve(blob)
          } else {
            reject(new Error('Failed to create blob'))
          }
        },
        'image/jpeg',
        props.outputQuality || 0.9
      )
    })

    emit('confirm', blob)
    emit('update:modelValue', false)
  } catch (error) {
    console.error('Failed to crop image:', error)
  } finally {
    isProcessing.value = false
  }
}

const handleCancel = () => {
  emit('cancel')
  emit('update:modelValue', false)
}

const destroyCropper = () => {
  if (cropperInstance.value) {
    cropperInstance.value.destroy()
    cropperInstance.value = null
  }
  cropperReady.value = false
  scaleState.value = { x: 1, y: 1 }
}

watch(() => props.modelValue, async (newValue) => {
  if (newValue) {
    cropperReady.value = false
    isLoading.value = true
    loadError.value = false
    
    await nextTick()
    
    requestAnimationFrame(() => {
      setTimeout(initCropper, 100)
    })
  } else {
    destroyCropper()
    isLoading.value = true
    loadError.value = false
  }
})

onUnmounted(() => {
  destroyCropper()
})
</script>

<style scoped>
.cropper-wrapper {
  width: 100%;
  height: 350px;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 768px) {
  .cropper-wrapper {
    height: 280px;
  }
}

.cropper-image {
  display: block;
  max-width: 100%;
  opacity: 0;
}

.cropper-btn {
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.cropper-btn:disabled {
  cursor: not-allowed;
}

.preview-container {
  overflow: hidden;
}

.action-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 8px;
  background: #ffffff;
  color: #1a1a2e;
  font-size: 12px;
  font-weight: normal;
  border-radius: 4px;
  white-space: nowrap;
  pointer-events: none;
  z-index: 9999;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  animation: tooltip-fade-in 0.15s ease;
}

.dark .action-tooltip {
  background: #0f0f1a;
  color: #f1f5f9;
}

@keyframes tooltip-fade-in {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}
</style>

<style>
.cropper-container {
  font-size: 0;
  line-height: 0;
  position: relative;
  touch-action: none;
  user-select: none;
  direction: ltr;
}

.cropper-container .cropper-canvas {
  background-color: transparent;
}

.cropper-container .cropper-modal {
  background-color: rgba(0, 0, 0, 0.5);
}

.cropper-container .cropper-view-box {
  outline: 2px solid var(--color-primary, #00d4ff);
  outline-offset: 0;
}

.cropper-container .cropper-point {
  background-color: var(--color-primary, #00d4ff);
  width: 8px;
  height: 8px;
  opacity: 1;
}

.cropper-container .cropper-point.point-se {
  width: 12px;
  height: 12px;
}

.cropper-container .cropper-line {
  background-color: var(--color-primary, #00d4ff);
}

.cropper-container .cropper-face {
  background-color: transparent;
}

.cropper-bg {
  background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQAQMAAAAlPW0iAAAAA3NCSVQICAjb4U/gAAAABlBMVEXMzMz////TjRV2AAAACXBIWXMAAAs7AAAOzAGDnqGQAAAAHHRFWHRTb2Z0d2FyZQBBZG9iZSBGaXJld29ya3MgQ1MzmGaGAAAAFnRFWHRDcmVhdGlvbiBUaW1lADAxLzA0LzE1O4XJggAAABZ0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC41ZYBSAAAAQklEQVQImWNgQAX8jP/PwMDw////Z2NkZGRkZGQDyLAyiGZgYGBgYGBgYHj4+P8M8f3HwWDHwMDwB6h0ZqCJAAACoQgN9mWmrQAAAABJRU5ErkJggg==");
}

.cropper-preview {
  overflow: hidden;
}
</style>
