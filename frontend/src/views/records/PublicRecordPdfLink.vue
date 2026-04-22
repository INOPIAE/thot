<template>
  <div class="public-link-container">
    <div class="public-link-card">
      <h1>{{ $t('records.resolvingPublicLink') }}</h1>
      <p v-if="loading">{{ $t('common.loading') }}</p>
      <p v-else-if="error" class="error-message">{{ error }}</p>
      <router-link v-if="error" to="/" class="btn btn-secondary">
        {{ $t('common.backToHome') }}
      </router-link>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { recordService } from '@/services/record'

export default defineComponent({
  name: 'PublicRecordPdfLink',
  data() {
    return {
      loading: true,
      error: null,
    }
  },
  async mounted() {
    const encodedId = this.$route.params.encodedId
    if (!encodedId) {
      this.error = this.$t('records.publicLinkInvalid')
      this.loading = false
      return
    }

    try {
      const response = await recordService.resolvePublicRecordPdfLink(encodedId)
      this.$router.replace(response.frontend_record_path || '/')
    } catch (err) {
      this.error = err?.detail || this.$t('records.publicLinkInvalid')
      this.loading = false
    }
  },
})
</script>

<style scoped>
.public-link-container {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.public-link-card {
  width: 100%;
  max-width: 520px;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 24px;
  background: #fff;
  text-align: center;
}

.error-message {
  color: #b00020;
  margin-bottom: 16px;
}
</style>
