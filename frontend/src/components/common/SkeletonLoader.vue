<script setup lang="ts">
defineProps<{
  width?: string
  height?: string
  radius?: string
  circle?: boolean
  lines?: number
  animated?: boolean
}>()
</script>

<template>
  <div
    v-if="!lines"
    class="skeleton-item"
    :class="{ 'skeleton-animated': animated !== false }"
    :style="{
      width: width || '100%',
      height: height || '1rem',
      borderRadius: circle ? '50%' : radius || '0.375rem'
    }"
  />
  <div
    v-else
    class="skeleton-lines"
  >
    <div
      v-for="i in lines"
      :key="i"
      class="skeleton-item"
      :class="{ 'skeleton-animated': animated !== false }"
      :style="{
        width: i === lines ? '70%' : '100%',
        height: height || '0.875rem',
        borderRadius: radius || '0.25rem'
      }"
    />
  </div>
</template>

<style scoped>
.skeleton-item {
  background: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0.06) 25%,
    rgba(0, 0, 0, 0.1) 50%,
    rgba(0, 0, 0, 0.06) 75%
  );
  background-size: 200% 100%;
}

.dark .skeleton-item {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.05) 25%,
    rgba(255, 255, 255, 0.08) 50%,
    rgba(255, 255, 255, 0.05) 75%
  );
  background-size: 200% 100%;
}

.skeleton-animated {
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.skeleton-lines {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}
</style>
