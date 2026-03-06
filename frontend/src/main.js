/**
 * Main Application Entry Point
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import App from './App.vue'
import router from './router'
import { useAppStore } from './stores/app'
import { messages, datetimeFormats, numberFormats } from './locales/messages'
import './styles/global.css'

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('language') || 'en',
  fallbackLocale: 'en',
  messages,
  datetimeFormats,
  numberFormats,
})

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(i18n)

// Initialize app configuration from backend
const appStore = useAppStore()
app.mount('#app')

// Load config in background so UI is visible even if backend is unavailable.
appStore.initializeConfig().catch((error) => {
  console.error('Background config initialization failed:', error)
})
