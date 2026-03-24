import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart, RadarChart, GaugeChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  VisualMapComponent
} from 'echarts/components'
import { LabelLayout, UniversalTransition } from 'echarts/features'
import VChart from 'vue-echarts'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  RadarChart,
  GaugeChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  VisualMapComponent,
  LabelLayout,
  UniversalTransition
])

const passiveEvents = ['mousewheel', 'wheel', 'touchstart', 'touchmove']

if (typeof window !== 'undefined') {
  const originalAddEventListener = HTMLElement.prototype.addEventListener
  HTMLElement.prototype.addEventListener = function(
    type: string,
    listener: EventListenerOrEventListenerObject,
    options?: boolean | AddEventListenerOptions
  ) {
    if (passiveEvents.includes(type)) {
      if (typeof options === 'boolean') {
        options = { capture: options, passive: true }
      } else if (typeof options === 'object' && options !== null) {
        if (options.passive === undefined) {
          options = { ...options, passive: true }
        }
      } else {
        options = { passive: true }
      }
    }
    return originalAddEventListener.call(this, type, listener, options)
  }
}

export default VChart
