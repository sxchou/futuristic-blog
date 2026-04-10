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
  colors?: string[]
  horizontal?: boolean
  showBackground?: boolean
  yAxisName?: string
  xAxisName?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: 300,
  loading: false,
  showRefresh: true,
  showExport: true,
  autoRefresh: false,
  refreshInterval: 60000,
  exportFileName: 'bar-chart',
  colors: () => ['#00d4ff', '#7c3aed', '#10b981', '#f59e0b', '#ef4444'],
  horizontal: false,
  showBackground: false,
  yAxisName: '',
  xAxisName: ''
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
        type: 'shadow'
      }
    },
    grid: {
      left: '50',
      right: '20',
      bottom: '30',
      top: props.yAxisName || props.xAxisName ? '50' : '30'
    },
    xAxis: {
      type: props.horizontal ? 'value' : 'category',
      name: props.horizontal ? props.xAxisName : '',
      data: props.horizontal ? undefined : props.data.map(item => item.name),
      nameTextStyle: {
        color: isDark ? '#9ca3af' : '#6b7280',
        fontSize: 11
      },
      axisLine: {
        lineStyle: {
          color: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
        }
      },
      axisLabel: {
        color: isDark ? '#9ca3af' : '#6b7280',
        fontSize: 11,
        rotate: props.horizontal ? 0 : (props.data.length > 6 ? 30 : 0)
      }
    },
    yAxis: {
      type: props.horizontal ? 'category' : 'value',
      name: props.horizontal ? '' : props.yAxisName,
      data: props.horizontal ? props.data.map(item => item.name) : undefined,
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
        type: 'bar',
        data: props.data.map((item, index) => ({
          value: item.value,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: props.horizontal ? 1 : 0,
              y2: props.horizontal ? 0 : 1,
              colorStops: [
                { offset: 0, color: props.colors[index % props.colors.length] },
                { offset: 1, color: props.colors[index % props.colors.length] + '80' }
              ]
            },
            borderRadius: props.horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]
          }
        })),
        barWidth: '60%',
        showBackground: props.showBackground,
        backgroundStyle: {
          color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
          borderRadius: 4
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          }
        }
      }
    ]
  }
})
</script>
