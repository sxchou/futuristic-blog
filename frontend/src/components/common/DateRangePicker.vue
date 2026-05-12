<template>
  <div class="date-range-picker">
    <div class="flex items-center gap-1.5">
      <div class="relative">
        <button
          type="button"
          class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none text-gray-900 dark:text-white flex items-center gap-1.5 min-w-[110px]"
          @click="toggleCalendar('start', $event)"
        >
          <svg
            class="w-3.5 h-3.5 text-gray-500 dark:text-gray-400"
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
          <span>{{ startDateDisplay }}</span>
        </button>
      </div>

      <span class="text-gray-500 dark:text-gray-400 text-xs">至</span>

      <div class="relative">
        <button
          type="button"
          class="px-2.5 py-1 text-xs bg-gray-100 dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-lg focus:border-primary focus:outline-none text-gray-900 dark:text-white flex items-center gap-1.5 min-w-[110px]"
          @click="toggleCalendar('end', $event)"
        >
          <svg
            class="w-3.5 h-3.5 text-gray-500 dark:text-gray-400"
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
          <span>{{ endDateDisplay }}</span>
        </button>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="showCalendar"
        class="fixed inset-0 z-[9999]"
        @click="closeCalendar"
      >
        <div
          class="fixed bg-white dark:bg-dark-200 rounded-xl shadow-2xl border border-gray-200 dark:border-white/10 p-4 w-[320px] max-h-[450px] overflow-y-auto"
          :style="calendarStyle"
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

          <div class="grid grid-cols-7 gap-1">
            <button
              v-for="date in calendarDays"
              :key="date.key"
              type="button"
              :class="[
                'text-sm rounded-lg transition-colors relative',
                date.isCurrentMonth
                  ? 'text-gray-900 dark:text-white'
                  : 'text-gray-400 dark:text-gray-600',
                date.isToday ? 'font-bold' : '',
                date.isInRange ? 'bg-primary/10' : '',
                date.isStart || date.isEnd
                  ? 'bg-primary text-white hover:bg-primary/90'
                  : 'hover:bg-gray-100 dark:hover:bg-white/10',
                date.isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
              ]"
              :style="date.isInRange && !date.isStart && !date.isEnd ? { borderRadius: '0' } : {}"
              :disabled="date.isDisabled"
              @click="selectDate(date.date)"
              @dblclick="selectDateAndApply(date.date)"
            >
              {{ date.day }}
            </button>
          </div>

          <div class="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-white/10">
            <div class="flex gap-2">
              <button
                type="button"
                class="px-2 py-1 text-xs bg-gray-100 dark:bg-dark-100 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-white/10 transition-colors"
                @click="selectToday"
              >
                今天
              </button>
              <button
                type="button"
                class="px-2 py-1 text-xs bg-gray-100 dark:bg-dark-100 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-white/10 transition-colors"
                @click="selectLast7Days"
              >
                最近7天
              </button>
              <button
                type="button"
                class="px-2 py-1 text-xs bg-gray-100 dark:bg-dark-100 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-white/10 transition-colors"
                @click="selectLast30Days"
              >
                最近30天
              </button>
            </div>
            <button
              type="button"
              class="px-3 py-1 text-xs bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
              @click="applySelection"
            >
              确定
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Props {
  startDate?: string
  endDate?: string
}

interface Emits {
  (e: 'update:startDate', value: string): void
  (e: 'update:endDate', value: string): void
}

const props = withDefaults(defineProps<Props>(), {
  startDate: '',
  endDate: ''
})

const emit = defineEmits<Emits>()

const showCalendar = ref(false)
const activeInput = ref<'start' | 'end'>('start')
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth())
const selectedYear = ref(new Date().getFullYear())
const selectedMonth = ref(new Date().getMonth())

const tempStartDate = ref('')
const tempEndDate = ref('')

const calendarStyle = ref({})

const weekDays = ['日', '一', '二', '三', '四', '五', '六']

const years = computed(() => {
  const currentYearValue = new Date().getFullYear()
  const yearsArray = []
  for (let i = currentYearValue - 5; i <= currentYearValue + 1; i++) {
    yearsArray.push(i)
  }
  return yearsArray
})

const startDateDisplay = computed(() => {
  return props.startDate || '开始日期'
})

const endDateDisplay = computed(() => {
  return props.endDate || '结束日期'
})

interface CalendarDay {
  key: string
  date: Date
  day: number
  isCurrentMonth: boolean
  isToday: boolean
  isStart: boolean
  isEnd: boolean
  isInRange: boolean
  isDisabled: boolean
}

const calendarDays = computed(() => {
  const days: CalendarDay[] = []
  const firstDay = new Date(currentYear.value, currentMonth.value, 1)
  const lastDay = new Date(currentYear.value, currentMonth.value + 1, 0)
  const startDayOfWeek = firstDay.getDay()
  const daysInMonth = lastDay.getDate()

  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const startDate = tempStartDate.value ? new Date(tempStartDate.value) : null
  const endDate = tempEndDate.value ? new Date(tempEndDate.value) : null

  if (startDate) startDate.setHours(0, 0, 0, 0)
  if (endDate) endDate.setHours(0, 0, 0, 0)

  for (let i = 0; i < startDayOfWeek; i++) {
    const prevDate = new Date(currentYear.value, currentMonth.value, -startDayOfWeek + i + 1)
    days.push({
      key: `prev-${i}`,
      date: prevDate,
      day: prevDate.getDate(),
      isCurrentMonth: false,
      isToday: false,
      isStart: startDate ? prevDate.getTime() === startDate.getTime() : false,
      isEnd: endDate ? prevDate.getTime() === endDate.getTime() : false,
      isInRange: startDate && endDate ? prevDate > startDate && prevDate < endDate : false,
      isDisabled: prevDate > today
    })
  }

  for (let i = 1; i <= daysInMonth; i++) {
    const date = new Date(currentYear.value, currentMonth.value, i)
    days.push({
      key: `current-${i}`,
      date: date,
      day: i,
      isCurrentMonth: true,
      isToday: date.getTime() === today.getTime(),
      isStart: startDate ? date.getTime() === startDate.getTime() : false,
      isEnd: endDate ? date.getTime() === endDate.getTime() : false,
      isInRange: startDate && endDate ? date > startDate && date < endDate : false,
      isDisabled: date > today
    })
  }

  const remainingDays = 42 - days.length
  for (let i = 1; i <= remainingDays; i++) {
    const nextDate = new Date(currentYear.value, currentMonth.value + 1, i)
    days.push({
      key: `next-${i}`,
      date: nextDate,
      day: nextDate.getDate(),
      isCurrentMonth: false,
      isToday: false,
      isStart: startDate ? nextDate.getTime() === startDate.getTime() : false,
      isEnd: endDate ? nextDate.getTime() === endDate.getTime() : false,
      isInRange: startDate && endDate ? nextDate > startDate && nextDate < endDate : false,
      isDisabled: nextDate > today
    })
  }

  return days
})

const toggleCalendar = (input: 'start' | 'end', event?: Event) => {
  activeInput.value = input
  tempStartDate.value = props.startDate
  tempEndDate.value = props.endDate
  
  if (tempStartDate.value) {
    const date = new Date(tempStartDate.value)
    selectedYear.value = date.getFullYear()
    selectedMonth.value = date.getMonth()
    currentYear.value = date.getFullYear()
    currentMonth.value = date.getMonth()
  }
  
  showCalendar.value = !showCalendar.value
  
  if (showCalendar.value && event) {
    updateCalendarPosition(event)
  }
}

const closeCalendar = () => {
  showCalendar.value = false
}

const updateCalendarPosition = (event: Event) => {
  const target = event.currentTarget as HTMLElement
  if (!target) return
  
  const rect = target.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  
  let left = rect.left
  let top = rect.bottom + 8

  if (left + 320 > viewportWidth) {
    left = viewportWidth - 320 - 16
  }

  if (left < 16) {
    left = 16
  }

  if (top + 450 > viewportHeight) {
    top = rect.top - 450 - 8
  }

  if (top < 16) {
    top = 16
  }

  calendarStyle.value = {
    left: `${left}px`,
    top: `${top}px`
  }
}

const prevMonth = () => {
  if (currentMonth.value === 0) {
    currentMonth.value = 11
    currentYear.value--
  } else {
    currentMonth.value--
  }
  selectedYear.value = currentYear.value
  selectedMonth.value = currentMonth.value
}

const nextMonth = () => {
  if (currentMonth.value === 11) {
    currentMonth.value = 0
    currentYear.value++
  } else {
    currentMonth.value++
  }
  selectedYear.value = currentYear.value
  selectedMonth.value = currentMonth.value
}

const updateCalendar = () => {
  currentYear.value = selectedYear.value
  currentMonth.value = selectedMonth.value
}

const selectDate = (date: Date) => {
  const dateStr = formatDateToString(date)
  
  if (activeInput.value === 'start') {
    tempStartDate.value = dateStr
    if (tempEndDate.value && new Date(dateStr) > new Date(tempEndDate.value)) {
      tempEndDate.value = ''
    }
  } else {
    tempEndDate.value = dateStr
    if (tempStartDate.value && new Date(dateStr) < new Date(tempStartDate.value)) {
      tempStartDate.value = dateStr
    }
  }
}

const selectDateAndApply = (date: Date) => {
  const dateStr = formatDateToString(date)
  
  if (activeInput.value === 'start') {
    tempStartDate.value = dateStr
    if (tempEndDate.value && new Date(dateStr) > new Date(tempEndDate.value)) {
      tempEndDate.value = ''
    }
  } else {
    tempEndDate.value = dateStr
    if (tempStartDate.value && new Date(dateStr) < new Date(tempStartDate.value)) {
      tempStartDate.value = dateStr
    }
  }
  
  if (tempStartDate.value && tempEndDate.value) {
    applySelection()
  } else if (tempStartDate.value || tempEndDate.value) {
    if (activeInput.value === 'start') {
      activeInput.value = 'end'
    } else {
      applySelection()
    }
  }
}

const formatDateToString = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const selectToday = () => {
  const today = new Date()
  const dateStr = formatDateToString(today)
  tempStartDate.value = dateStr
  tempEndDate.value = dateStr
}

const selectLast7Days = () => {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 6)
  tempStartDate.value = formatDateToString(start)
  tempEndDate.value = formatDateToString(end)
}

const selectLast30Days = () => {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 29)
  tempStartDate.value = formatDateToString(start)
  tempEndDate.value = formatDateToString(end)
}

const applySelection = () => {
  emit('update:startDate', tempStartDate.value)
  emit('update:endDate', tempEndDate.value)
  closeCalendar()
}

const handleEscapeKey = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && showCalendar.value) {
    closeCalendar()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscapeKey)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscapeKey)
})
</script>

<style scoped>
.date-range-picker {
  position: relative;
}
</style>
