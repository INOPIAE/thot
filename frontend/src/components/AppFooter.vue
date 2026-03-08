<template>
  <footer class="app-footer">
    <div class="footer-content">
      <div class="footer-left">
        <span v-if="authStore.isAuthenticated">
          {{ $t('common.user') }}: {{ authStore.currentUser?.username }} ({{ authStore.currentUser?.roles?.join(', ') }})
        </span>
        <span v-else>
          {{ $t('common.user') }}: {{ $t('common.notLoggedIn') }}
        </span>
      </div>
      <div class="footer-right">
        <span>
          {{ $t('common.copyright', { year: footerYearLabel, company: 'NLF Database Contributors' }) }}
          {{ $t('common.poweredBy', { company: footerCompany }) }}
        </span>
      </div>
    </div>
  </footer>
</template>

<script>
import { computed, defineComponent } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { APP_CONFIG } from '@/config/app'
import { useAppStore } from '@/stores/app'

export default defineComponent({
  name: 'AppFooter',
  setup() {
    const authStore = useAuthStore()
    const appStore = useAppStore()
    const footerCompany = computed(() => appStore.getConfig('companyName', APP_CONFIG.companyName))
    const footerYear = computed(() => Number(appStore.getConfig('copyrightYear', APP_CONFIG.copyrightYear)))
    const footerYearLabel = computed(() => {
      const currentYear = new Date().getFullYear()

      if (!Number.isFinite(footerYear.value)) {
        return String(currentYear)
      }

      if (footerYear.value < currentYear) {
        return `${footerYear.value}-${currentYear}`
      }

      return String(footerYear.value)
    })

    return {
      authStore,
      footerCompany,
      footerYearLabel,
    }
  },
})
</script>

<style scoped>
.app-footer {
  background-color: var(--color-header-footer-bg);
  color: var(--color-header-footer-text);
  padding: 1rem;
  text-align: center;
  border-top: 1px solid #ddd;
  margin-top: auto;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
}
</style>
