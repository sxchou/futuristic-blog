<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  fileType: string
  mimeType: string
  size?: 'sm' | 'md' | 'lg'
}>()

const size = computed(() => props.size || 'md')

const sizeClasses = computed(() => {
  switch (size.value) {
    case 'sm': return 'w-5 h-5'
    case 'lg': return 'w-10 h-10'
    default: return 'w-6 h-6'
  }
})

const iconData = computed(() => {
  const { fileType, mimeType } = props
  
  if (fileType === 'image') {
    return {
      type: 'image',
      bg: 'bg-emerald-500',
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <circle cx="8.5" cy="8.5" r="1.5"/>
        <polyline points="21 15 16 10 5 21"/>
      </svg>`
    }
  }
  
  if (mimeType.includes('pdf')) {
    return {
      type: 'pdf',
      bg: 'bg-red-500',
      icon: `<svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM8.5 13h1c.83 0 1.5.67 1.5 1.5S10.33 16 9.5 16h-.5v1.5H8V13h.5zm3 0h1c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5h-.5v1.5H11V13h.5zm3.5 0h2v.5h-1.5v1h1v.5h-1v2H14v-4z"/>
        <circle cx="9" cy="14.5" r="0"/>
        <text x="9" y="15" font-size="4" font-weight="bold" text-anchor="middle" fill="currentColor">PDF</text>
      </svg>`
    }
  }
  
  if (mimeType.includes('excel') || mimeType.includes('spreadsheet') || mimeType.includes('sheet')) {
    return {
      type: 'excel',
      bg: 'bg-green-600',
      icon: `<svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM8 13h2l1.5 2.5L13 13h2l-2.5 3L15 19h-2l-1.5-2.5L10 19H8l2.5-3L8 13z"/>
      </svg>`
    }
  }
  
  if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) {
    return {
      type: 'powerpoint',
      bg: 'bg-orange-500',
      icon: `<svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM9 13h2.5c1.38 0 2.5 1.12 2.5 2.5S12.88 18 11.5 18H10v2H9v-7zm1.5 3.5c.83 0 1.5-.67 1.5-1.5s-.67-1.5-1.5-1.5H10v3h.5z"/>
      </svg>`
    }
  }
  
  if (mimeType.includes('word') || mimeType.includes('wordprocessing')) {
    return {
      type: 'word',
      bg: 'bg-blue-600',
      icon: `<svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM8 13h1.5l1.5 4.5L12.5 13H14l-2 6h-2l-2-6z"/>
      </svg>`
    }
  }
  
  if (mimeType.includes('zip') || mimeType.includes('rar') || mimeType.includes('7z') || mimeType.includes('compressed')) {
    return {
      type: 'archive',
      bg: 'bg-yellow-500',
      icon: `<svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 6h-8l-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-2 6h-2v2h2v2h-2v2h-2v-2h2v-2h-2v-2h2v-2h-2V8h2v2h2v2z"/>
      </svg>`
    }
  }
  
  if (mimeType.includes('text/plain') || mimeType.includes('text/markdown')) {
    return {
      type: 'text',
      bg: 'bg-gray-500',
      icon: `<svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM8 12h8v2H8v-2zm0 4h8v2H8v-2z"/>
      </svg>`
    }
  }
  
  return {
    type: 'file',
    bg: 'bg-gray-400',
    icon: `<svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4z"/>
    </svg>`
  }
})
</script>

<template>
  <div 
    :class="[sizeClasses, iconData.bg]" 
    class="rounded flex items-center justify-center text-white flex-shrink-0"
    v-html="iconData.icon"
  />
</template>
