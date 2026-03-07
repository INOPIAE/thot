<template>
  <header class="app-header">
    <div class="header-content">
      <div class="header-left">
        <img :src="appConfig.logoUrl" :alt="appConfig.appName" class="logo" />
        <span class="app-title">{{ appConfig.appName }}</span>
      </div>
      <div class="header-right">
        <select v-model="currentLanguage" @change="changeLanguage" class="language-select">
          <option value="en">🇬🇧 English</option>
          <option value="de">🇩🇪 Deutsch</option>
        </select>
      </div>
    </div>
  </header>
</template>

<script>
import { defineComponent } from 'vue'
import { useAppStore } from '@/stores/app'
import { APP_CONFIG } from '@/config/app'

export default defineComponent({
  name: 'AppHeader',
  setup() {
    const appStore = useAppStore()

    return {
      appStore,
      defaultConfig: APP_CONFIG,
    }
  },
  computed: {
    appConfig() {
      return this.appStore.appConfig || this.defaultConfig
    },
    currentLanguage: {
      get() {
        return this.appStore.currentLanguage
      },
      set(value) {
        this.appStore.setLanguage(value)
        this.$i18n.locale = value
      },
    },
  },
  methods: {
    changeLanguage(event) {
      const language = event.target.value
      this.appStore.setLanguage(language)
      this.$i18n.locale = language
    },
  },
})
</script>

<style scoped>
.app-header {
  background-color: #2c3e50;
  color: white;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo {
  height: 40px;
  width: auto;
}

.app-title {
  font-size: 1.5rem;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.language-select {
  padding: 0.5rem;
  background-color: transparent;
  color: white;
  border: 1px solid white;
  border-radius: 4px;
  cursor: pointer;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
  }
}
</style>
