<template>
  <BaseChart
    :title="title"
    :option="chartOption"
    :height="height"
    :loading="loading"
    :error="error"
    :show-refresh="showRefresh"
    :show-export="showExport"
    :show-expand="showExpand"
    :auto-refresh="autoRefresh"
    :refresh-interval="refreshInterval"
    :export-file-name="exportFileName"
    :is-empty="isEmpty"
    @refresh="$emit('refresh')"
    @click="$emit('click', $event)"
    @expand="$emit('expand')"
  >
    <template
      v-if="$slots.header"
      #header
    >
      <slot name="header" />
    </template>
    <template
      v-if="$slots.actions"
      #actions
    >
      <slot name="actions" />
    </template>
  </BaseChart>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import type { EChartsOption } from 'echarts'

interface DataItem {
  name: string
  value: number
  color?: string
}

interface Props {
  title?: string
  data: DataItem[]
  height?: number
  loading?: boolean
  error?: string
  showRefresh?: boolean
  showExport?: boolean
  showExpand?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
  exportFileName?: string
  colors?: string[]
  radius?: string[]
  center?: string[]
  showLegend?: boolean
  legendPosition?: 'top' | 'bottom' | 'left' | 'right'
  doughnut?: boolean
  roseType?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: 300,
  loading: false,
  showRefresh: true,
  showExport: true,
  showExpand: false,
  autoRefresh: false,
  refreshInterval: 60000,
  exportFileName: 'pie-chart',
  colors: () => ['#00d4ff', '#7c3aed', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#06b6d4', '#8b5cf6'],
  radius: () => ['40%', '70%'],
  center: () => ['50%', '50%'],
  showLegend: true,
  legendPosition: 'bottom',
  doughnut: true,
  roseType: false
})

defineEmits<{
  refresh: []
  click: [params: any]
  expand: []
}>()

const isEmpty = computed(() => !props.data || props.data.length === 0)

const legendPositions = {
  top: { top: '5%', left: 'center' },
  bottom: { bottom: '5%', left: 'center' },
  left: { left: '5%', top: 'middle' },
  right: { right: '5%', top: 'middle' }
}

const chartOption = computed<EChartsOption>(() => {
  const isDark = document.documentElement.classList.contains('dark')
  
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.95)',
      borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
      textStyle: {
        color: isDark ? '#e5e7eb' : '#374151'
      },
      formatter: '{b}: {c} ({d}%)'
    },
    legend: props.showLegend ? {
      type: 'scroll',
      orient: props.legendPosition === 'left' || props.legendPosition === 'right' ? 'vertical' : 'horizontal',
      ...legendPositions[props.legendPosition],
      textStyle: {
        color: isDark ? '#9ca3af' : '#6b7280',
        fontSize: 11
      },
      pageTextStyle: {
        color: isDark ? '#9ca3af' : '#6b7280'
      },
      pageIconColor: isDark ? '#e5e7eb' : '#374151',
      pageIconInactiveColor: isDark ? '#4b5563' : '#d1d5db'
    } : undefined,
    series: [
      {
        type: 'pie',
        radius: props.doughnut ? props.radius : '70%',
        center: props.center,
        roseType: props.roseType ? 'area' : undefined,
        itemStyle: {
          borderRadius: 6,
          borderColor: isDark ? 'rgba(0, 0, 0, 0.5)' : 'rgba(255, 255, 255, 0.8)',
          borderWidth: 2
        },
        label: {
          show: true,
          color: isDark ? '#e5e7eb' : '#374151',
          fontSize: 11,
          formatter: '{b}\n{d}%'
        },
        labelLine: {
          show: true,
          lineStyle: {
            color: isDark ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.2)'
          }
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 13,
            fontWeight: 'bold'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          }
        },
        data: props.data.map((item, index) => ({
          name: item.name,
          value: item.value,
          itemStyle: {
            color: item.color || props.colors[index % props.colors.length]
          }
        }))
      }
    ]
  }
})
</script>
