<template>
  <div class="date-time-picker">
    <div class="relative">
      <button
        type="button"
        class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none text-gray-900 dark:text-white flex items-center gap-2 min-w-[180px]"
        @click="togglePicker"
      >
        <svg
          class="w-4 h-4 text-gray-500 dark:text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <span>{{ displayValue }}</span>
      </button>
    </div>

    <Teleport to="body">
      <div
        v-if="showPicker"
        class="fixed inset-0 z-[9999]"
        @click="closePicker"
      >
        <div
          class="fixed bg-white dark:bg-dark-200 rounded-xl shadow-2xl border border-gray-200 dark:border-white/10 p-4 w-[320px]"
          :style="pickerStyle"
          @click.stop
        >
          <div class="flex items-center justify-between mb-4">
            <button
              type="button"
              class="p-1 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors"
              @click="prevMonth"
            >
              <svg
                class="w-5 h-5 text-gray-600 dark:text-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>

            <div class="flex items-center gap-2">
              <select
                v-model="selectedYear"
                class="px-2 py-1 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none text-gray-900 dark:text-white"
                @change="updateCalendar"
              >
                <option
                  v-for="year in years"
                  :key="year"
                  :value="year"
                >
                  {{ year }}年
                </option>
              </select>
              <select
                v-model="selectedMonth"
                class="px-2 py-1 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none text-gray-900 dark:text-white"
                @change="updateCalendar"
              >
                <option
                  v-for="month in 12"
                  :key="month"
                  :value="month - 1"
                >
                  {{ month }}月
                </option>
              </select>
            </div>

            <button
              type="button"
              class="p-1 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors"
              @click="nextMonth"
            >
              <svg
                class="w-5 h-5 text-gray-600 dark:text-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          </div>

          <div class="grid grid-cols-7 gap-1 mb-2">
            <div
              v-for="day in weekDays"
              :key="day"
              class="text-center text-xs font-medium text-gray-500 dark:text-gray-400 py-1"
            >
              {{ day }}
            </div>
          </div>

          <div class="grid grid-cols-7 gap-1 mb-4">
            <button
              v-for="date in calendarDays"
              :key="date.key"
              type="button"
              class="aspect-square flex items-center justify-center text-sm rounded-lg transition-colors"
              :class="[
                date.isCurrentMonth
                  ? date.isSelected
                    ? 'bg-primary text-white'
                    : date.isToday
                    ? 'bg-primary/10 text-primary'
                    : 'text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-white/10'
                  : 'text-gray-300 dark:text-gray-600 cursor-not-allowed',
                date.isDisabled ? 'opacity-50 cursor-not-allowed' : ''
              ]"
              :disabled="date.isDisabled || !date.isCurrentMonth"
              @click="selectDate(date)"
            >
              {{ date.day }}
            </button>
          </div>

          <div class="border-t border-gray-200 dark:border-white/10 pt-4">
            <div class="flex items-center justify-center gap-2">
              <select
                v-model="selectedHour"
                class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none text-gray-900 dark:text-white"
              >
                <option
                  v-for="hour in 24"
                  :key="hour"
                  :value="hour - 1"
                >
                  {{ String(hour - 1).padStart(2, '0') }}时
                </option>
              </select>
              <span class="text-gray-500 dark:text-gray-400">:</span>
              <select
                v-model="selectedMinute"
                class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none text-gray-900 dark:text-white"
              >
                <option
                  v-for="minute in 60"
                  :key="minute"
                  :value="minute - 1"
                >
                  {{ String(minute - 1).padStart(2, '0') }}分
                </option>
              </select>
              <span class="text-gray-500 dark:text-gray-400">:</span>
              <select
                v-model="selectedSecond"
                class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none text-gray-900 dark:text-white"
              >
                <option
                  v-for="second in 60"
                  :key="second"
                  :value="second - 1"
                >
                  {{ String(second - 1).padStart(2, '0') }}秒
                </option>
              </select>
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 mt-4 pt-4 border-t border-gray-200 dark:border-white/10">
            <button
              type="button"
              class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors"
              @click="clearValue"
            >
              清除
            </button>
            <button
              type="button"
              class="px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
              @click="confirmSelection"
            >
              确认
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useDialogStore } from '@/stores/dialog'

const dialog = useDialogStore()

interface Props {
  modelValue?: string
  min?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: string | undefined]
}>()

const showPicker = ref(false)
const selectedYear = ref(new Date().getFullYear())
const selectedMonth = ref(new Date().getMonth())
const selectedDay = ref<number | null>(null)
const selectedHour = ref(0)
const selectedMinute = ref(0)
const selectedSecond = ref(0)

const weekDays = ['日', '一', '二', '三', '四', '五', '六']

const years = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let i = currentYear; i <= currentYear + 5; i++) {
    years.push(i)
  }
  return years
})

const displayValue = computed(() => {
  if (!props.modelValue) {
    return '选择日期时间'
  }
  
  const date = new Date(props.modelValue)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  const second = String(date.getSeconds()).padStart(2, '0')
  
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`
})

const calendarDays = computed(() => {
  const year = selectedYear.value
  const month = selectedMonth.value
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startPadding = firstDay.getDay()
  const daysInMonth = lastDay.getDate()
  
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  const minDate = props.min ? new Date(props.min) : null
  
  const days = []
  
  for (let i = 0; i < startPadding; i++) {
    const date = new Date(year, month, -startPadding + i + 1)
    days.push({
      key: `prev-${i}`,
      day: date.getDate(),
      date: date,
      isCurrentMonth: false,
      isToday: false,
      isSelected: false,
      isDisabled: true
    })
  }
  
  for (let i = 1; i <= daysInMonth; i++) {
    const date = new Date(year, month, i)
    date.setHours(0, 0, 0, 0)
    
    const isToday = date.getTime() === today.getTime()
    const isSelected = selectedYear.value === year && selectedMonth.value === month && selectedDay.value === i
    
    // 只禁用今天之前的日期，今天和未来的日期都可以选择
    // 时间验证在confirmSelection时进行
    const isDisabled = minDate ? date < today : false
    
    days.push({
      key: `current-${i}`,
      day: i,
      date: date,
      isCurrentMonth: true,
      isToday,
      isSelected,
      isDisabled
    })
  }
  
  const remainingDays = 42 - days.length
  for (let i = 1; i <= remainingDays; i++) {
    const date = new Date(year, month + 1, i)
    days.push({
      key: `next-${i}`,
      day: date.getDate(),
      date: date,
      isCurrentMonth: false,
      isToday: false,
      isSelected: false,
      isDisabled: true
    })
  }
  
  return days
})

const pickerStyle = ref({})

const togglePicker = () => {
  showPicker.value = !showPicker.value
  if (showPicker.value) {
    updatePickerPosition()
    
    if (props.modelValue) {
      const date = new Date(props.modelValue)
      selectedYear.value = date.getFullYear()
      selectedMonth.value = date.getMonth()
      selectedDay.value = date.getDate()
      selectedHour.value = date.getHours()
      selectedMinute.value = date.getMinutes()
      selectedSecond.value = date.getSeconds()
    } else {
      const now = new Date()
      now.setMinutes(now.getMinutes() + 5)
      if (now.getSeconds() > 0 || now.getMilliseconds() > 0) {
        now.setMinutes(now.getMinutes() + 1)
      }
      now.setSeconds(0)
      now.setMilliseconds(0)
      
      selectedYear.value = now.getFullYear()
      selectedMonth.value = now.getMonth()
      selectedDay.value = now.getDate()
      selectedHour.value = now.getHours()
      selectedMinute.value = now.getMinutes()
      selectedSecond.value = 0
    }
  }
}

const closePicker = () => {
  showPicker.value = false
}

const updatePickerPosition = () => {
  const button = document.querySelector('.date-time-picker button')
  if (!button) return
  
  const rect = button.getBoundingClientRect()
  const viewportHeight = window.innerHeight
  const viewportWidth = window.innerWidth
  
  let top = rect.bottom + 8
  let left = rect.left
  
  if (top + 450 > viewportHeight) {
    top = rect.top - 450 - 8
  }
  
  if (left + 320 > viewportWidth) {
    left = viewportWidth - 320 - 16
  }
  
  pickerStyle.value = {
    top: `${top}px`,
    left: `${left}px`
  }
}

const prevMonth = () => {
  if (selectedMonth.value === 0) {
    selectedMonth.value = 11
    selectedYear.value--
  } else {
    selectedMonth.value--
  }
}

const nextMonth = () => {
  if (selectedMonth.value === 11) {
    selectedMonth.value = 0
    selectedYear.value++
  } else {
    selectedMonth.value++
  }
}

const updateCalendar = () => {
  // Calendar will automatically update through computed property
}

const selectDate = (date: any) => {
  if (!date.isCurrentMonth || date.isDisabled) return
  
  selectedDay.value = date.day
}

const confirmSelection = async () => {
  if (selectedDay.value === null) {
    const today = new Date()
    selectedDay.value = today.getDate()
  }
  
  const selectedDate = new Date(
    selectedYear.value,
    selectedMonth.value,
    selectedDay.value,
    selectedHour.value,
    selectedMinute.value,
    selectedSecond.value
  )
  
  const now = new Date()
  const minTime = new Date(now.getTime() + 5 * 60 * 1000)
  
  if (selectedDate < minTime) {
    showPicker.value = false
    await dialog.showError(
      '定时发布时间必须至少距离当前时间5分钟',
      '时间无效'
    )
    return
  }
  
  const isoString = selectedDate.toISOString()
  emit('update:modelValue', isoString)
  
  showPicker.value = false
}

const clearValue = () => {
  emit('update:modelValue', undefined)
  showPicker.value = false
}

const handleEscape = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && showPicker.value) {
    showPicker.value = false
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscape)
  window.addEventListener('resize', updatePickerPosition)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
  window.removeEventListener('resize', updatePickerPosition)
})

watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    const date = new Date(newValue)
    selectedYear.value = date.getFullYear()
    selectedMonth.value = date.getMonth()
    selectedDay.value = date.getDate()
    selectedHour.value = date.getHours()
    selectedMinute.value = date.getMinutes()
    selectedSecond.value = date.getSeconds()
  }
}, { immediate: true })
</script>
