<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const progress = ref(0)

const updateProgress = () => {
  if (route.name !== 'Article') {
    progress.value = 0
    return
  }
  
  const scrollTop = window.scrollY
  const docHeight = document.documentElement.scrollHeight - window.innerHeight
  progress.value = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0
}

onMounted(() => {
  window.addEventListener('scroll', updateProgress)
  updateProgress()
})

onUnmounted(() => {
  window.removeEventListener('scroll', updateProgress)
})
</script>

<template>
  <div
    v-if="progress > 0"
    class="fixed top-0 left-0 right-0 h-1 z-[60] bg-dark-100"
  >
    <div
      class="h-full bg-gradient-to-r from-primary to-accent transition-all duration-150"
      :style="{ width: `${progress}%` }"
    />
  </div>
</template>
