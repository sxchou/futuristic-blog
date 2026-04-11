<script setup lang="ts">
</script>

<template>
  <div class="article-card-skeleton bg-white dark:bg-dark-200 rounded-xl overflow-hidden border border-gray-200 dark:border-white/10 p-4 flex flex-col sm:flex-row gap-3">
    <div class="relative flex-shrink-0 overflow-hidden rounded-lg h-28 sm:w-40 sm:h-24">
      <SkeletonLoader
        height="100%"
        radius="0.5rem"
      />
    </div>
    <div class="flex-1 min-w-0 flex flex-col">
      <div class="flex items-center gap-2 mb-2">
        <SkeletonLoader
          width="3rem"
          height="0.875rem"
          radius="0.25rem"
        />
      </div>
      <SkeletonLoader
        height="1.125rem"
        class="mb-1"
      />
      <SkeletonLoader
        :lines="2"
        height="0.875rem"
        class="mb-2"
      />
      <div class="flex items-center gap-1 mb-2">
        <SkeletonLoader
          width="2.5rem"
          height="1.25rem"
          radius="9999px"
        />
        <SkeletonLoader
          width="3rem"
          height="1.25rem"
          radius="9999px"
        />
      </div>
      <div class="flex items-center justify-between mt-auto pt-1.5 border-t border-gray-100 dark:border-white/5">
        <SkeletonLoader
          width="4rem"
          height="0.75rem"
        />
        <div class="flex items-center gap-2">
          <SkeletonLoader
            width="2rem"
            height="0.75rem"
          />
          <SkeletonLoader
            width="2rem"
            height="0.75rem"
          />
          <SkeletonLoader
            width="2rem"
            height="0.75rem"
          />
        </div>
      </div>
    </div>
  </div>
</template>
