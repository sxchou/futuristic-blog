<script setup lang="ts">
</script>

<template>
  <div class="article-card-skeleton bg-white dark:bg-dark-200 rounded-xl overflow-hidden border border-gray-200 dark:border-white/10">
    <div class="aspect-video relative">
      <SkeletonLoader height="100%" radius="0" />
    </div>
    <div class="p-4">
      <div class="flex items-center gap-2 mb-3">
        <SkeletonLoader width="3rem" height="1.25rem" radius="0.25rem" />
        <SkeletonLoader width="4rem" height="1.25rem" radius="0.25rem" />
      </div>
      <SkeletonLoader height="1.5rem" class="mb-2" />
      <SkeletonLoader :lines="2" height="0.875rem" class="mb-3" />
      <div class="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-white/5">
        <div class="flex items-center gap-2">
          <SkeletonLoader width="2rem" height="2rem" circle />
          <SkeletonLoader width="5rem" height="0.875rem" />
        </div>
        <SkeletonLoader width="4rem" height="0.875rem" />
      </div>
    </div>
  </div>
</template>
