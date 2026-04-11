<template>
  <div id="app-layout">
    <AppHeader />

    <div class="app-main">
      <AppNavbar />

      <main class="app-content">
        <slot></slot>
      </main>
    </div>

    <AppFooter />
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import AppNavbar from '@/components/AppNavbar.vue'
import AppFooter from '@/components/AppFooter.vue'

export default defineComponent({
  name: 'DefaultLayout',
  components: {
    AppHeader,
    AppNavbar,
    AppFooter,
  },
})
</script>

<style scoped>

#app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-main {
  display: flex;
  flex: 1;
  width: 100%;
}

.app-content {
  flex: 1;
  padding: 2rem;
}

@media (max-width: 768px) {
  .app-main {
    flex-direction: column;
  }
}
</style>
