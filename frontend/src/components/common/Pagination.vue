<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'

interface Props {
  currentPage: number
  totalPages: number
  totalItems?: number
  pageSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  pageSize: 12
})

const emit = defineEmits<{
  (e: 'page-change', page: number): void
}>()

const jumpPage = ref<string>('')

const isFirstPage = computed(() => props.currentPage === 1)
const isLastPage = computed(() => props.currentPage === props.totalPages)

const visiblePages = computed(() => {
  const pages: (number | string)[] = []
  const total = props.totalPages
  const current = props.currentPage
  
  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    pages.push(1)
    
    if (current > 3) {
      pages.push('...')
    }
    
    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)
    
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
    
    if (current < total - 2) {
      pages.push('...')
    }
    
    pages.push(total)
  }
  
  return pages
})

const pageStart = computed(() => {
  return (props.currentPage - 1) * props.pageSize + 1
})

const pageEnd = computed(() => {
  return Math.min(props.currentPage * props.pageSize, props.totalItems || 0)
})

const goToPage = (page: number | string) => {
  if (typeof page === 'number' && page !== props.currentPage && page >= 1 && page <= props.totalPages) {
    emit('page-change', page)
  }
}

const goToPrev = () => {
  if (!isFirstPage.value) {
    emit('page-change', props.currentPage - 1)
  }
}

const goToNext = () => {
  if (!isLastPage.value) {
    emit('page-change', props.currentPage + 1)
  }
}

const handleJump = () => {
  const page = parseInt(jumpPage.value)
  if (!isNaN(page) && page >= 1 && page <= props.totalPages) {
    emit('page-change', page)
    jumpPage.value = ''
  }
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'ArrowLeft' && !isFirstPage.value) {
    event.preventDefault()
    goToPrev()
  } else if (event.key === 'ArrowRight' && !isLastPage.value) {
    event.preventDefault()
    goToNext()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

watch(() => props.currentPage, () => {
  jumpPage.value = ''
})
</script>

<template>
  <div class="pagination-container">
    <div class="pagination-info mb-4 text-center text-sm text-gray-500 dark:text-gray-400">
      <span v-if="totalItems">
        第 {{ pageStart }}-{{ pageEnd }} 篇，共 {{ totalItems }} 篇
      </span>
      <span class="mx-2">|</span>
      <span>第 {{ currentPage }} 页，共 {{ totalPages }} 页</span>
    </div>

    <div class="pagination-wrapper flex items-center justify-center gap-1 md:gap-2">
      <button
        @click="goToPrev"
        :disabled="isFirstPage"
        class="pagination-btn pagination-nav"
        :class="{ 'opacity-40 cursor-not-allowed': isFirstPage }"
        :aria-label="'上一页'"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        <span class="hidden md:inline ml-1">上一页</span>
      </button>

      <div class="pagination-pages flex items-center gap-1">
        <template v-for="(page, index) in visiblePages" :key="index">
          <span
            v-if="page === '...'"
            class="pagination-ellipsis"
          >
            ...
          </span>
          <button
            v-else
            @click="goToPage(page)"
            class="pagination-btn pagination-page"
            :class="{ 
              'pagination-active': page === currentPage,
              'hover:bg-gray-100 dark:hover:bg-white/10': page !== currentPage
            }"
          >
            {{ page }}
          </button>
        </template>
      </div>

      <button
        @click="goToNext"
        :disabled="isLastPage"
        class="pagination-btn pagination-nav"
        :class="{ 'opacity-40 cursor-not-allowed': isLastPage }"
        :aria-label="'下一页'"
      >
        <span class="hidden md:inline mr-1">下一页</span>
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>

    <div v-if="totalPages > 7" class="pagination-jump mt-4 flex items-center justify-center gap-2 text-sm">
      <span class="text-gray-500 dark:text-gray-400">跳转至</span>
      <input
        ref="jumpInputRef"
        v-model.number="jumpPage"
        type="number"
        min="1"
        :max="totalPages"
        class="pagination-input"
        placeholder="页码"
        @keyup.enter="handleJump"
      />
      <button
        @click="handleJump"
        class="pagination-jump-btn"
      >
        确定
      </button>
    </div>

    <div class="pagination-hint mt-3 text-center text-xs text-gray-400 dark:text-gray-500">
      <span class="hidden md:inline">使用 ← → 方向键快速翻页</span>
      <span class="md:hidden">点击页码或使用上下页按钮导航</span>
    </div>
  </div>
</template>

<style scoped>
.pagination-container {
  @apply py-6;
}

.pagination-btn {
  @apply relative inline-flex items-center justify-center
         min-w-[36px] h-9 px-3
         text-sm font-medium
         rounded-lg
         transition-all duration-200 ease-out
         focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-900
         select-none;
}

.pagination-page {
  @apply bg-white dark:bg-white/5
         text-gray-700 dark:text-gray-300
         border border-gray-200 dark:border-white/10
         hover:border-primary dark:hover:border-primary
         hover:text-primary dark:hover:text-primary
         active:scale-95;
}

.pagination-active {
  @apply bg-gradient-to-r from-primary to-accent
         text-white
         border-transparent
         shadow-lg shadow-primary/25
         cursor-default;
}

.pagination-nav {
  @apply bg-white dark:bg-white/5
         text-gray-700 dark:text-gray-300
         border border-gray-200 dark:border-white/10
         hover:border-primary dark:hover:border-primary
         hover:text-primary dark:hover:text-primary
         hover:shadow-md
         active:scale-95
         disabled:active:scale-100;
}

.pagination-ellipsis {
  @apply px-2 text-gray-400 dark:text-gray-500 select-none;
}

.pagination-input {
  @apply w-16 h-8 px-2 py-1
         text-center text-sm
         bg-white dark:bg-white/5
         border border-gray-200 dark:border-white/10
         rounded-lg
         text-gray-700 dark:text-gray-300
         focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary
         transition-all duration-200;
}

.pagination-input::-webkit-outer-spin-button,
.pagination-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.pagination-input[type=number] {
  -moz-appearance: textfield;
}

.pagination-jump-btn {
  @apply px-4 h-8
         text-sm font-medium
         bg-gray-100 dark:bg-white/10
         text-gray-700 dark:text-gray-300
         border border-gray-200 dark:border-white/10
         rounded-lg
         hover:bg-gray-200 dark:hover:bg-white/20
         hover:border-primary dark:hover:border-primary
         hover:text-primary dark:hover:text-primary
         transition-all duration-200
         active:scale-95;
}

@media (max-width: 640px) {
  .pagination-btn {
    @apply min-w-[32px] h-8 px-2 text-xs;
  }
  
  .pagination-pages {
    @apply gap-0.5;
  }
  
  .pagination-info {
    @apply text-xs;
  }
  
  .pagination-jump {
    @apply flex-wrap;
  }
  
  .pagination-input {
    @apply w-14 h-7 text-xs;
  }
  
  .pagination-jump-btn {
    @apply px-3 h-7 text-xs;
  }
}
</style>
