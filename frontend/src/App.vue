<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useBlogStore } from '@/stores'
import Navbar from '@/components/common/Navbar.vue'
import Footer from '@/components/common/Footer.vue'
import GlobalSearch from '@/components/common/GlobalSearch.vue'
import ReadingProgress from '@/components/common/ReadingProgress.vue'

const route = useRoute()
const blogStore = useBlogStore()

const isAdminPage = computed(() => route.path.startsWith('/admin'))

onMounted(() => {
  blogStore.fetchCategories()
  blogStore.fetchTags()
})

const handleKeydown = (e: KeyboardEvent) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    const searchModal = document.querySelector('[data-search-modal]') as HTMLElement
    if (searchModal) {
      searchModal.click()
    }
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-dark flex flex-col">
    <template v-if="!isAdminPage">
      <ReadingProgress />
      <Navbar />
    </template>
    <main class="flex-1" :class="{ 'pt-16': !isAdminPage }">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <Footer v-if="!isAdminPage" />
    <GlobalSearch v-if="!isAdminPage" />
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
