<template>
  <div class="chart-container">
    <div class="chart-header" v-if="title || $slots.header">
      <slot name="header">
        <h3 class="chart-title">{{ title }}</h3>
      </slot>
      <div class="chart-actions">
        <button
          v-if="showRefresh"
          @click="handleRefresh"
          class="chart-action-btn"
          :disabled="loading"
          title="刷新数据"
        >
          <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
        <div class="export-dropdown" v-if="showExport">
          <button class="chart-action-btn" title="导出图表">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>
          <div class="export-menu">
            <button @click="exportChart('png')" class="export-menu-item">导出 PNG</button>
            <button @click="exportChart('svg')" class="export-menu-item">导出 SVG</button>
            <button @click="exportData('csv')" class="export-menu-item">导出 CSV</button>
          </div>
        </div>
        <slot name="actions" />
      </div>
    </div>
    
    <div class="chart-content" :style="{ height: height + 'px' }">
      <div v-if="loading" class="chart-loading">
        <div class="loading-spinner"></div>
        <span class="loading-text">加载中...</span>
      </div>
      
      <div v-else-if="error" class="chart-error">
        <svg class="w-12 h-12 text-red-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span class="error-text">{{ error }}</span>
        <button @click="handleRefresh" class="retry-btn">重试</button>
      </div>
      
      <div v-else-if="isEmpty" class="chart-empty">
        <svg class="w-12 h-12 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <span class="empty-text">暂无数据</span>
      </div>
      
      <v-chart
        v-else
        ref="chartRef"
        :option="chartOption"
        :theme="chartTheme"
        :autoresize="true"
        :init-options="initOptions"
        class="chart"
        @click="handleClick"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import VChart from './echarts'
import type { EChartsOption } from 'echarts'
import { useAdminCheck } from '@/composables/useAdminCheck'

const { requireAdmin } = useAdminCheck()

interface Props {
  title?: string
  option: EChartsOption
  height?: number
  loading?: boolean
  error?: string
  showRefresh?: boolean
  showExport?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
  exportFileName?: string
  isEmpty?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: 300,
  loading: false,
  showRefresh: true,
  showExport: true,
  autoRefresh: false,
  refreshInterval: 60000,
  exportFileName: 'chart'
})

const emit = defineEmits<{
  refresh: []
  click: [params: any]
  'export-complete': [type: string]
}>()

const chartRef = ref<InstanceType<typeof VChart> | null>(null)

const chartTheme = computed(() => {
  const isDark = document.documentElement.classList.contains('dark')
  return isDark ? 'dark' : 'light'
})

const initOptions = computed(() => ({
  renderer: 'canvas' as const,
  devicePixelRatio: window.devicePixelRatio || 1
}))

const chartOption = computed(() => {
  const isDark = document.documentElement.classList.contains('dark')
  const baseOption = { ...props.option }
  
  if (isDark) {
    return {
      backgroundColor: 'transparent',
      textStyle: {
        color: '#e5e7eb'
      },
      ...baseOption
    }
  }
  
  return baseOption
})

let refreshTimer: number | null = null

const startAutoRefresh = () => {
  if (props.autoRefresh && props.refreshInterval > 0) {
    refreshTimer = window.setInterval(() => {
      emit('refresh')
    }, props.refreshInterval)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const handleRefresh = () => {
  emit('refresh')
}

const handleClick = (params: any) => {
  emit('click', params)
}

const exportChart = async (type: 'png' | 'svg') => {
  if (!await requireAdmin('导出图表')) return
  if (!chartRef.value) return
  
  const chartInstance = chartRef.value
  const url = chartInstance.getDataURL({
    type,
    pixelRatio: 2,
    backgroundColor: '#fff'
  })
  
  const link = document.createElement('a')
  link.download = `${props.exportFileName}.${type}`
  link.href = url
  link.click()
  
  emit('export-complete', type)
}

const exportData = async (type: 'csv') => {
  if (!await requireAdmin('导出数据')) return
  if (!props.option) return
  
  let csvContent = ''
  const option = props.option as any
  
  if (option.series) {
    const series = Array.isArray(option.series) ? option.series : [option.series]
    
    series.forEach((s: any, index: number) => {
      if (s.data) {
        csvContent += `Series ${index + 1}\n`
        if (Array.isArray(s.data[0])) {
          csvContent += 'X,Value\n'
          s.data.forEach((item: any) => {
            csvContent += `${item[0]},${item[1]}\n`
          })
        } else if (typeof s.data[0] === 'object') {
          csvContent += 'Name,Value\n'
          s.data.forEach((item: any) => {
            csvContent += `${item.name},${item.value}\n`
          })
        } else {
          csvContent += 'Value\n'
          s.data.forEach((item: any) => {
            csvContent += `${item}\n`
          })
        }
        csvContent += '\n'
      }
    })
  }
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.download = `${props.exportFileName}.csv`
  link.href = URL.createObjectURL(blob)
  link.click()
  
  emit('export-complete', type)
}

watch(() => props.autoRefresh, (newVal) => {
  if (newVal) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
})

onMounted(() => {
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.chart-container {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px;
  backdrop-filter: blur(10px);
}

.dark .chart-container {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.05);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.dark .chart-title {
  color: #f3f4f6;
}

.chart-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.chart-action-btn {
  padding: 6px;
  border-radius: 6px;
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.1);
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.chart-action-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #374151;
}

.dark .chart-action-btn {
  border-color: rgba(255, 255, 255, 0.1);
  color: #9ca3af;
}

.dark .chart-action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #e5e7eb;
}

.chart-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.export-dropdown {
  position: relative;
}

.export-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  opacity: 0;
  visibility: hidden;
  transform: translateY(-4px);
  transition: all 0.2s;
  z-index: 10;
  min-width: 120px;
}

.dark .export-menu {
  background: #1f2937;
  border-color: rgba(255, 255, 255, 0.1);
}

.export-dropdown:hover .export-menu {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.export-menu-item {
  display: block;
  width: 100%;
  padding: 8px 12px;
  text-align: left;
  font-size: 13px;
  color: #374151;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}

.dark .export-menu-item {
  color: #e5e7eb;
}

.export-menu-item:hover {
  background: rgba(0, 0, 0, 0.05);
}

.dark .export-menu-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.chart-content {
  position: relative;
}

.chart {
  width: 100%;
  height: 100%;
}

.chart-loading,
.chart-error,
.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(0, 212, 255, 0.2);
  border-top-color: #00d4ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text,
.error-text,
.empty-text {
  margin-top: 8px;
  font-size: 14px;
  color: #6b7280;
}

.dark .loading-text,
.dark .error-text,
.dark .empty-text {
  color: #9ca3af;
}

.retry-btn {
  margin-top: 12px;
  padding: 6px 16px;
  font-size: 13px;
  color: white;
  background: linear-gradient(135deg, #00d4ff, #7c3aed);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.retry-btn:hover {
  opacity: 0.9;
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
