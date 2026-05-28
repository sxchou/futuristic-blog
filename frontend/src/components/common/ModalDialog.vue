<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useDialogStore } from '@/stores'

const dialogStore = useDialogStore()
const promptValue = ref('')

watch(() => dialogStore.isVisible.value, (val) => {
  if (val && dialogStore.dialogOptions.value.type === 'prompt') {
    promptValue.value = dialogStore.dialogOptions.value.inputValue || ''
    nextTick(() => {
      const input = document.querySelector<HTMLInputElement>('#dialog-prompt-input')
      if (input) input.focus()
    })
  }
})

const handleConfirmClick = () => {
  dialogStore.confirm()
}

const handleCancelClick = () => {
  dialogStore.cancel()
}

const handlePromptConfirm = () => {
  dialogStore.confirmPrompt(promptValue.value)
}

const handlePromptCancel = () => {
  dialogStore.cancelPrompt()
}

const handlePromptKeyup = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    handlePromptConfirm()
  }
}

const handleOverlayClick = () => {
  const type = dialogStore.dialogOptions.value.type
  if (type === 'alert' || type === 'success' || type === 'error' || type === 'warning') {
    dialogStore.cancel()
  }
}

const getIconClass = () => {
  const type = dialogStore.dialogOptions.value.type
  switch (type) {
    case 'confirm':
      return 'text-yellow-400'
    case 'success':
      return 'text-green-400'
    case 'error':
      return 'text-red-400'
    case 'warning':
      return 'text-amber-400'
    case 'prompt':
      return 'text-primary'
    default:
      return 'text-primary'
  }
}

const getIconPath = () => {
  const type = dialogStore.dialogOptions.value.type
  switch (type) {
    case 'confirm':
      return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
    case 'success':
      return 'M5 13l4 4L19 7'
    case 'error':
      return 'M6 18L18 6M6 6l12 12'
    case 'warning':
      return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
    case 'prompt':
      return 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z'
    default:
      return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }
}

const isConfirmType = () => {
  return dialogStore.dialogOptions.value.type === 'confirm'
}

const isPromptType = () => {
  return dialogStore.dialogOptions.value.type === 'prompt'
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
        v-if="dialogStore.isVisible.value"
        class="fixed inset-0 z-[9999] flex items-center justify-center"
      >
        <div
          class="absolute inset-0 bg-black/60 backdrop-blur-sm"
          @click="handleOverlayClick"
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
            v-if="dialogStore.isVisible.value"
            class="relative bg-white dark:bg-gray-900 border border-gray-200 dark:border-white/10 rounded-xl shadow-2xl w-full max-w-sm mx-4 overflow-hidden"
          >
            <div class="p-6">
              <div class="flex items-start gap-4">
                <div :class="['flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-gray-100 dark:bg-gray-800', getIconClass()]">
                  <svg
                    class="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      :d="getIconPath()"
                    />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <h3
                    v-if="dialogStore.dialogOptions.value.title"
                    class="text-lg font-semibold text-gray-900 dark:text-white mb-2"
                  >
                    {{ dialogStore.dialogOptions.value.title }}
                  </h3>
                  <p
                    v-if="dialogStore.dialogOptions.value.message"
                    class="text-gray-600 dark:text-gray-300 text-sm leading-relaxed"
                  >
                    {{ dialogStore.dialogOptions.value.message }}
                  </p>
                  <div
                    v-if="isPromptType()"
                    class="mt-3"
                  >
                    <label
                      v-if="dialogStore.dialogOptions.value.inputLabel"
                      class="block text-sm text-gray-600 dark:text-gray-400 mb-1"
                    >
                      {{ dialogStore.dialogOptions.value.inputLabel }}
                    </label>
                    <input
                      id="dialog-prompt-input"
                      v-model="promptValue"
                      :type="dialogStore.dialogOptions.value.inputType || 'text'"
                      :placeholder="dialogStore.dialogOptions.value.inputPlaceholder || ''"
                      :min="dialogStore.dialogOptions.value.inputMin"
                      :max="dialogStore.dialogOptions.value.inputMax"
                      class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-white/20 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
                      @keyup="handlePromptKeyup"
                    >
                  </div>
                </div>
              </div>
            </div>

            <div class="flex border-t border-gray-200 dark:border-white/10">
              <button
                v-if="isConfirmType()"
                type="button"
                class="flex-1 px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                @click="handleCancelClick"
              >
                {{ dialogStore.dialogOptions.value.cancelText || '取消' }}
              </button>
              <button
                v-if="isConfirmType()"
                type="button"
                class="flex-1 px-4 py-3 text-sm font-medium text-primary hover:text-primary/80 hover:bg-primary/10 transition-colors"
                @click="handleConfirmClick"
              >
                {{ dialogStore.dialogOptions.value.confirmText || '确定' }}
              </button>
              <template v-if="isPromptType()">
                <button
                  type="button"
                  class="flex-1 px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  @click="handlePromptCancel"
                >
                  {{ dialogStore.dialogOptions.value.cancelText || '取消' }}
                </button>
                <button
                  type="button"
                  class="flex-1 px-4 py-3 text-sm font-medium text-primary hover:text-primary/80 hover:bg-primary/10 transition-colors"
                  @click="handlePromptConfirm"
                >
                  {{ dialogStore.dialogOptions.value.confirmText || '确定' }}
                </button>
              </template>
              <button
                v-if="!isConfirmType() && !isPromptType()"
                type="button"
                :class="[
                  'flex-1 px-4 py-3 text-sm font-medium transition-colors',
                  dialogStore.dialogOptions.value.type === 'error'
                    ? 'text-red-500 dark:text-red-400 hover:text-red-600 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-500/10'
                    : dialogStore.dialogOptions.value.type === 'success'
                      ? 'text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 hover:bg-green-50 dark:hover:bg-green-500/10'
                      : dialogStore.dialogOptions.value.type === 'warning'
                        ? 'text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 hover:bg-amber-50 dark:hover:bg-amber-500/10'
                        : 'text-primary hover:text-primary/80 hover:bg-primary/10'
                ]"
                @click="handleCancelClick"
              >
                关闭
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
