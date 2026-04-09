<template>
  <div class="view-wrapper">
    <div class="view-header">
      <h1>{{ $t('common.imprint') }}</h1>
    </div>
    <div class="view-content card">
      <div v-if="loading">{{ $t('common.loading') }}</div>
      <div v-else-if="error">{{ error }}</div>
      <article v-else class="legal-html" v-html="htmlContent"></article>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { fetchLegalHtml, LEGAL_DOCUMENT_TYPES } from '@/services/legal'

export default defineComponent({
  name: 'Imprint',
  data() {
    return {
      htmlContent: '',
      loading: true,
      error: '',
    }
  },
  watch: {
    '$i18n.locale': {
      handler() {
        this.loadLegalContent()
      },
      immediate: true,
    },
  },
  methods: {
    async loadLegalContent() {
      this.loading = true
      this.error = ''
      try {
        const locale = this.$i18n.locale?.value || this.$i18n.locale || 'en'
        this.htmlContent = await fetchLegalHtml(LEGAL_DOCUMENT_TYPES.imprint, locale)
      } catch (error) {
        this.error = error?.response?.data?.detail || this.$t('common.error')
        this.htmlContent = ''
      } finally {
        this.loading = false
      }
    },
  },
})
</script>
