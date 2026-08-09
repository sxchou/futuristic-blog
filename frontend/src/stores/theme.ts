import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(true)

  const toggleTheme = () => {
    isDark.value = !isDark.value
  }

  const initTheme = () => {
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      isDark.value = savedTheme === 'dark'
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      // 无保存偏好时，跟随系统设置
      isDark.value = true
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      isDark.value = false
    } else {
      // 系统未指定时，根据时间判断（18:00-06:00 为夜间）
      const hour = new Date().getHours()
      isDark.value = hour < 6 || hour >= 18
    }

    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }

    // 监听系统主题变化（仅当用户未手动选择时生效）
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
          isDark.value = e.matches
        }
      })
    }
  }

  watch(isDark, (newValue) => {
    localStorage.setItem('theme', newValue ? 'dark' : 'light')
    if (newValue) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  })

  initTheme()

  return {
    isDark,
    toggleTheme
  }
})
