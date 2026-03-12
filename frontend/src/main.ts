import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './assets/main.css'

const SCROLL_POSITION_KEY = 'scroll_position'

window.addEventListener('beforeunload', () => {
  const scrollTop = window.scrollY || document.documentElement.scrollTop || 0
  if (scrollTop > 0) {
    sessionStorage.setItem(SCROLL_POSITION_KEY, JSON.stringify({
      path: window.location.pathname,
      scrollTop: scrollTop
    }))
  } else {
    sessionStorage.removeItem(SCROLL_POSITION_KEY)
  }
})

const restoreScrollPosition = () => {
  const savedPosition = sessionStorage.getItem(SCROLL_POSITION_KEY)
  if (!savedPosition) return
  
  try {
    const { path, scrollTop } = JSON.parse(savedPosition)
    
    if (path === window.location.pathname && scrollTop > 0) {
      const maxAttempts = 30
      let attempts = 0
      
      const tryScroll = () => {
        const docHeight = document.documentElement.scrollHeight
        const viewportHeight = window.innerHeight
        
        if (docHeight >= scrollTop + viewportHeight) {
          window.scrollTo(0, scrollTop)
          sessionStorage.removeItem(SCROLL_POSITION_KEY)
        } else if (attempts < maxAttempts) {
          attempts++
          requestAnimationFrame(tryScroll)
        } else {
          sessionStorage.removeItem(SCROLL_POSITION_KEY)
        }
      }
      
      requestAnimationFrame(tryScroll)
    } else {
      sessionStorage.removeItem(SCROLL_POSITION_KEY)
    }
  } catch (e) {
    sessionStorage.removeItem(SCROLL_POSITION_KEY)
  }
}

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

if (document.readyState === 'complete') {
  setTimeout(restoreScrollPosition, 50)
} else {
  window.addEventListener('load', () => {
    setTimeout(restoreScrollPosition, 50)
  })
}
