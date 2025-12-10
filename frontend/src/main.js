import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { FrappeUI, setConfig, frappeRequest } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import './index.css'

// Configure frappe-ui
setConfig('resourceFetcher', frappeRequest)

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(FrappeUI)

app.mount('#app')
