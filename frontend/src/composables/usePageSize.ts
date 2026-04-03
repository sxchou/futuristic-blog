import { ref, onMounted, onUnmounted } from 'vue'

export function usePageSize() {
  const pageSize = ref(6)
  let resizeTimeout: ReturnType<typeof setTimeout> | null = null

  const calculatePageSize = () => {
    const width = window.innerWidth
    
    if (width >= 1280) {
      pageSize.value = 8
    } else if (width >= 1024) {
      pageSize.value = 6
    } else if (width >= 768) {
      pageSize.value = 6
    } else {
      pageSize.value = 6
    }
  }

  const debouncedCalculate = () => {
    if (resizeTimeout) {
      clearTimeout(resizeTimeout)
    }
    resizeTimeout = setTimeout(() => {
      calculatePageSize()
    }, 150)
  }

  onMounted(() => {
    calculatePageSize()
    window.addEventListener('resize', debouncedCalculate)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', debouncedCalculate)
    if (resizeTimeout) {
      clearTimeout(resizeTimeout)
    }
  })

  return {
    pageSize
  }
}
