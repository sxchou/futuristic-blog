<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: boolean
  title?: string
  message: string
  type?: 'confirm' | 'alert' | 'success' | 'error'
  confirmText?: string
  cancelText?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const isVisible = ref(props.modelValue)

watch(() => props.modelValue, (val) => {
  isVisible.value = val
})

watch(isVisible, (val) => {
  emit('update:modelValue', val)
})

const handleConfirm = () => {
  emit('confirm')
  isVisible.value = false
}

const handleCancel = () => {
  emit('cancel')
  isVisible.value = false
}

const getIconClass = () => {
  switch (props.type) {
    case 'confirm':
      return 'text-yellow-400'
    case 'success':
      return 'text-green-400'
    case 'error':
      return 'text-red-400'
    default:
      return 'text-primary'
  }
}

const getIconPath = () => {
  switch (props.type) {
    case 'confirm':
      return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
    case 'success':
      return 'M5 13l4 4L19 7'
    case 'error':
      return 'M6 18L18 6M6 6l12 12'
    default:
      return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isVisible"
        class="fixed inset-0 z-[9999] flex items-center justify-center"
      >
        <div
          class="absolute inset-0 bg-black/60 backdrop-blur-sm"
          @click="type === 'alert' || type === 'success' || type === 'error' ? handleCancel : null"
        />
        <Transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="isVisible"
            class="relative bg-gray-900 dark:bg-dark-50 border border-gray-700 dark:border-white/10 rounded-xl shadow-2xl w-full max-w-sm mx-4 overflow-hidden"
          >
            <div class="p-6">
              <div class="flex items-start gap-4">
                <div :class="['flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-gray-800', getIconClass()]">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getIconPath()" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <h3 v-if="title" class="text-lg font-semibold text-white mb-2">
                    {{ title }}
                  </h3>
                  <p class="text-gray-300 text-sm leading-relaxed">
                    {{ message }}
                  </p>
                </div>
              </div>
            </div>
            
            <div class="flex border-t border-gray-700 dark:border-white/10">
              <button
                v-if="type === 'confirm'"
                @click="handleCancel"
                class="flex-1 px-4 py-3 text-sm font-medium text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
              >
                {{ cancelText || '取消' }}
              </button>
              <button
                @click="type === 'confirm' ? handleConfirm : handleCancel"
                :class="[
                  'flex-1 px-4 py-3 text-sm font-medium transition-colors',
                  type === 'error' 
                    ? 'text-red-400 hover:text-red-300 hover:bg-red-500/10'
                    : type === 'success'
                    ? 'text-green-400 hover:text-green-300 hover:bg-green-500/10'
                    : 'text-primary hover:text-primary/80 hover:bg-primary/10'
                ]"
              >
                {{ type === 'confirm' ? (confirmText || '确定') : '关闭' }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
