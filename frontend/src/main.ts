import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './assets/main.css'
import { setupLazyLoad } from './directives/lazyLoad'
import { logPerformanceReport } from './utils/performance'

const app = createApp(App)

app.use(createPinia())
app.use(router)

setupLazyLoad(app)

app.mount('#app')

logPerformanceReport()
