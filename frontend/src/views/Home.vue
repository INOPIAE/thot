<template>
  <div class="container">
    <div v-if="isAuthenticated" class="page-header text-center">
      <h1>{{ $t('common.home') }}</h1>
      <p>Welcome, {{ authStore.currentUser?.username }}!</p>
    </div>
    <div v-else class="form-container">
      <div class="card form-card">
        <div class="text-center">
          <h1>{{ appName }}</h1>
          <p class="mb-4">Professional Database Management System</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { APP_CONFIG } from '@/config/app'
import { useAppStore } from '@/stores/app'

export default defineComponent({
  name: 'Home',
  setup() {
    const authStore = useAuthStore()
    const appStore = useAppStore()

    return {
      authStore,
      appStore,
    }
  },
  computed: {
    isAuthenticated() {
      return this.authStore.isAuthenticated
    },
    appName() {
      return this.appStore.getConfig('appName', APP_CONFIG.appName)
    },
  },
})
</script>

<style scoped>
.btn {
  display: inline-block;
  margin: 0.5rem;
}
</style>
