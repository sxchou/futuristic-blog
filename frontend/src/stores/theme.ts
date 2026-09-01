import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(true)
  // 标记是否为用户手动选择：只有手动切换才持久化，默认始终跟随系统
  let userPreference = false

  const applyTheme = (dark: boolean) => {
    if (dark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  const getSystemDark = (): boolean => {
    if (window.matchMedia) {
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return true
      }
      if (window.matchMedia('(prefers-color-scheme: light)').matches) {
        return false
      }
    }
    // 系统未指定时，根据时间判断（18:00-06:00 为夜间）
    const hour = new Date().getHours()
    return hour < 6 || hour >= 18
  }

  const toggleTheme = () => {
    userPreference = true
    isDark.value = !isDark.value
  }

  const initTheme = () => {
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      // 用户曾手动选择过，使用保存的偏好
      userPreference = true
      isDark.value = savedTheme === 'dark'
    } else {
      // 无保存偏好时，跟随系统设置
      isDark.value = getSystemDark()
    }

    applyTheme(isDark.value)

    // 监听系统主题变化（仅当用户未手动选择时生效）
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addEventListener('change', (e) => {
        if (!userPreference && !localStorage.getItem('theme')) {
          isDark.value = e.matches
        }
      })
    }
  }

  watch(isDark, (newValue) => {
    // 仅用户手动切换时持久化；初始化/跟随系统造成的变更不写入，保证默认跟随系统
    if (userPreference) {
      localStorage.setItem('theme', newValue ? 'dark' : 'light')
    }
    applyTheme(newValue)
  })

  initTheme()

  return {
    isDark,
    toggleTheme
  }
})
