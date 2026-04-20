<script setup lang="ts">
import { onMounted, onUnmounted, computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useSessionManager, useActivityTracker } from '@/composables/useSessionManager'
import { useInitStore } from '@/stores'
import Navbar from '@/components/common/Navbar.vue'
import Footer from '@/components/common/Footer.vue'
import GlobalSearch from '@/components/common/GlobalSearch.vue'
import ReadingProgress from '@/components/common/ReadingProgress.vue'
import ModalDialog from '@/components/common/ModalDialog.vue'
import AppSkeleton from '@/components/common/AppSkeleton.vue'

const route = useRoute()
const initStore = useInitStore()

useSessionManager()
useActivityTracker()

const isAdminPage = computed(() => route.path.startsWith('/admin'))
const isAppReady = ref(false)

const handleKeydown = (e: KeyboardEvent) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    const searchModal = document.querySelector('[data-search-modal]') as HTMLElement
    if (searchModal) {
      searchModal.click()
    }
  }
}

onMounted(async () => {
  document.addEventListener('keydown', handleKeydown)
  
  await initStore.initializeCore()
  
  isAppReady.value = true
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
    
    <Transition name="skeleton-fade">
      <AppSkeleton v-if="!isAppReady && !isAdminPage" />
    </Transition>
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

.skeleton-fade-enter-active,
.skeleton-fade-leave-active {
  transition: opacity 0.2s ease;
}

.skeleton-fade-enter-from,
.skeleton-fade-leave-to {
  opacity: 0;
}
</style>
