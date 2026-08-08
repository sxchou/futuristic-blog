import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './assets/main.css'
import 'katex/dist/katex.min.css'
import { setupLazyLoad } from './directives/lazyLoad'
import { permission, permissionTooltip } from './directives/permission'
import resizableTable from './directives/resizableTable'
import { logPerformanceReport } from './utils/performance'

const app = createApp(App)

app.use(createPinia())
app.use(router)

setupLazyLoad(app)

app.directive('permission', permission)
app.directive('permission-tooltip', permissionTooltip)
app.directive('resizable-table', resizableTable)

app.mount('#app')

logPerformanceReport()
