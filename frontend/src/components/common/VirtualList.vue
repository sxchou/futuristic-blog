<script setup lang="ts" generic="T">
import { ref, computed, onMounted, onUnmounted, watch, type CSSProperties } from 'vue'

const props = withDefaults(defineProps<{
  items: T[]
  itemHeight: number
  buffer?: number
  width?: string | number
  height?: string | number
}>(), {
  buffer: 5,
  width: '100%',
  height: '100%'
})

const emit = defineEmits<{
  (e: 'scroll', scrollTop: number): void
}>()

const containerRef = ref<HTMLElement | null>(null)
const scrollTop = ref(0)
const containerHeight = ref(0)

const visibleCount = computed(() => {
  return Math.ceil(containerHeight.value / props.itemHeight) + props.buffer * 2
})

const startIndex = computed(() => {
  const start = Math.floor(scrollTop.value / props.itemHeight) - props.buffer
  return Math.max(0, start)
})

const endIndex = computed(() => {
  return Math.min(props.items.length, startIndex.value + visibleCount.value)
})

const visibleItems = computed(() => {
  return props.items.slice(startIndex.value, endIndex.value).map((item, index) => ({
    item,
    index: startIndex.value + index
  }))
})

const totalHeight = computed(() => props.items.length * props.itemHeight)

const offsetY = computed(() => startIndex.value * props.itemHeight)

const containerStyle = computed<CSSProperties>(() => ({
  width: typeof props.width === 'number' ? `${props.width}px` : props.width,
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
  overflow: 'auto',
  position: 'relative'
}))

const contentStyle = computed<CSSProperties>(() => ({
  height: `${totalHeight.value}px`,
  position: 'relative'
}))

const itemsStyle = computed<CSSProperties>(() => ({
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  transform: `translateY(${offsetY.value}px)`
}))

const handleScroll = (event: Event) => {
  const target = event.target as HTMLElement
  scrollTop.value = target.scrollTop
  emit('scroll', scrollTop.value)
}

const resizeObserver = new ResizeObserver((entries) => {
  for (const entry of entries) {
    containerHeight.value = entry.contentRect.height
  }
})

onMounted(() => {
  if (containerRef.value) {
    containerHeight.value = containerRef.value.clientHeight
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  resizeObserver.disconnect()
})

watch(() => props.height, () => {
  if (containerRef.value) {
    containerHeight.value = containerRef.value.clientHeight
  }
})

defineExpose({
  scrollToIndex: (index: number) => {
    if (containerRef.value) {
      containerRef.value.scrollTop = index * props.itemHeight
    }
  },
  scrollToTop: () => {
    if (containerRef.value) {
      containerRef.value.scrollTop = 0
    }
  }
})
</script>

<template>
  <div
    ref="containerRef"
    class="virtual-list"
    :style="containerStyle"
    @scroll="handleScroll"
  >
    <div :style="contentStyle">
      <div :style="itemsStyle">
        <div
          v-for="{ item, index } in visibleItems"
          :key="index"
          class="virtual-list-item"
          :style="{ height: `${itemHeight}px` }"
        >
          <slot :item="item" :index="index" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.virtual-list {
  will-change: transform;
}

.virtual-list-item {
  box-sizing: border-box;
}
</style>
