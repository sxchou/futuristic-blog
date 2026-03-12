<template>
  <BaseChart
    :title="title"
    :option="chartOption"
    :height="height"
    :loading="loading"
    :error="error"
    :show-refresh="showRefresh"
    :show-export="showExport"
    :auto-refresh="autoRefresh"
    :refresh-interval="refreshInterval"
    :export-file-name="exportFileName"
    :is-empty="isEmpty"
    @refresh="$emit('refresh')"
    @click="$emit('click', $event)"
  >
    <template #header v-if="$slots.header">
      <slot name="header" />
    </template>
    <template #actions v-if="$slots.actions">
      <slot name="actions" />
    </template>
  </BaseChart>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import type { EChartsOption } from 'echarts'

interface DataItem {
  date: string
  value: number
}

interface Props {
  title?: string
  data: DataItem[]
  height?: number
  loading?: boolean
  error?: string
  showRefresh?: boolean
  showExport?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
  exportFileName?: string
  color?: string
  areaStyle?: boolean
  smooth?: boolean
  showSymbol?: boolean
  yAxisName?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: 300,
  loading: false,
  showRefresh: true,
  showExport: true,
  autoRefresh: false,
  refreshInterval: 60000,
  exportFileName: 'line-chart',
  color: '#00d4ff',
  areaStyle: true,
  smooth: true,
  showSymbol: false,
  yAxisName: ''
})

defineEmits<{
  refresh: []
  click: [params: any]
}>()

const isEmpty = computed(() => !props.data || props.data.length === 0)

const chartOption = computed<EChartsOption>(() => {
  const isDark = document.documentElement.classList.contains('dark')
  
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.95)',
      borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
      textStyle: {
        color: isDark ? '#e5e7eb' : '#374151'
      },
      axisPointer: {
        type: 'cross',
        crossStyle: {
          color: props.color
        }
      }
    },
    grid: {
      left: '50',
      right: '20',
      bottom: '30',
      top: props.yAxisName ? '50' : '30'
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: props.data.map(item => item.date),
      axisLine: {
        lineStyle: {
          color: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
        }
      },
      axisLabel: {
        color: isDark ? '#9ca3af' : '#6b7280',
        fontSize: 11
      }
    },
    yAxis: {
      type: 'value',
      name: props.yAxisName,
      nameTextStyle: {
        color: isDark ? '#9ca3af' : '#6b7280',
        fontSize: 11
      },
      axisLine: {
        show: false
      },
      axisLabel: {
        color: isDark ? '#9ca3af' : '#6b7280',
        fontSize: 11
      },
      splitLine: {
        lineStyle: {
          color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'
        }
      }
    },
    series: [
      {
        type: 'line',
        data: props.data.map(item => item.value),
        smooth: props.smooth,
        showSymbol: props.showSymbol,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 2,
          color: props.color
        },
        areaStyle: props.areaStyle ? {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: props.color + '40' },
              { offset: 1, color: props.color + '05' }
            ]
          }
        } : undefined,
        emphasis: {
          focus: 'series',
          itemStyle: {
            shadowBlur: 10,
            shadowColor: props.color + '80'
          }
        }
      }
    ]
  }
})
</script>
