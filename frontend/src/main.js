/**
 * Main Application Entry Point
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import { useAppStore } from './stores/app'
import { messages, datetimeFormats, numberFormats } from './locales/messages'
import { initializeFavicons } from './utils/favicon'
import './styles/global.css'

// Initialize favicons dynamically from backend
initializeFavicons()

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

const appStore = useAppStore()
const authStore = useAuthStore()

async function bootstrap() {
  try {
    await appStore.initializeConfig()
  } catch (error) {
    console.error('Config initialization failed:', error)
  }

  if (authStore.token) {
    await authStore.fetchUser()
  }

  app.mount('#app')
}

bootstrap()
