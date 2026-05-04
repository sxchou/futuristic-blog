<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const isVisible = ref(false)
const scrollThreshold = 300

const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

const handleScroll = () => {
  isVisible.value = window.scrollY > scrollThreshold
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    scrollToTop()
  }
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  handleScroll()
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <Transition name="fade-up">
    <button
      v-show="isVisible"
      class="fixed z-40 flex items-center justify-center
             w-10 h-10 md:w-11 md:h-11
             bottom-20 right-4 md:bottom-24 md:right-5
             rounded-full bg-white/90 dark:bg-dark-200/80
             shadow-lg shadow-slate-200/50 dark:shadow-none
             border border-slate-200/50 dark:border-white/10
             text-slate-600 dark:text-white/80
             hover:bg-slate-50 dark:hover:bg-white/10
             hover:-translate-y-0.5 hover:scale-105
             active:scale-95
             transition-all duration-200 cursor-pointer"
      aria-label="回到顶部"
      tabindex="0"
      @click="scrollToTop"
      @keydown="handleKeydown"
    >
      <svg
        class="w-5 h-5"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M5 15l7-7 7 7"
        />
      </svg>
    </button>
  </Transition>
</template>

<style scoped>
.fade-up-enter-active,
.fade-up-leave-active {
  transition: all 0.25s ease-out;
}

.fade-up-enter-from,
.fade-up-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
