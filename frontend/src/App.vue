<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useBlogStore, useSiteConfigStore } from '@/stores'
import { useSessionManager, useActivityTracker } from '@/composables/useSessionManager'
import Navbar from '@/components/common/Navbar.vue'
import Footer from '@/components/common/Footer.vue'
import GlobalSearch from '@/components/common/GlobalSearch.vue'
import ReadingProgress from '@/components/common/ReadingProgress.vue'
import ModalDialog from '@/components/common/ModalDialog.vue'

const route = useRoute()
const blogStore = useBlogStore()
const siteConfigStore = useSiteConfigStore()

useSessionManager()
useActivityTracker()

const isAdminPage = computed(() => route.path.startsWith('/admin'))

onMounted(async () => {
  await siteConfigStore.fetchConfigs()
  blogStore.fetchCategories()
  blogStore.fetchTags()
  blogStore.fetchAnnouncements()
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
  <div class="min-h-screen bg-white dark:bg-dark-100 flex flex-col transition-colors duration-300">
    <template v-if="!isAdminPage">
      <ReadingProgress />
      <Navbar />
    </template>
    <main
      class="flex-1"
      :class="{ 'pt-16': !isAdminPage }"
    >
      <div
        v-if="!isAdminPage"
        class="blog-container py-8"
      >
        <router-view v-slot="{ Component }">
          <transition
            name="fade"
            mode="out-in"
          >
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
      <router-view
        v-else
        v-slot="{ Component }"
      >
        <transition
          name="fade"
          mode="out-in"
        >
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <Footer v-if="!isAdminPage" />
    <GlobalSearch v-if="!isAdminPage" />
    <ModalDialog />
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
