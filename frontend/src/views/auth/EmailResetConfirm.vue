<template>
  <div class="email-reset-confirm-container">
    <div class="email-reset-confirm-card">
      <h2>{{ $t('emailChange.confirmTitle') }}</h2>
      <div v-if="successMessage" class="alert alert-success">{{ successMessage }}</div>
      <div v-if="errorMessage" class="alert alert-error">{{ errorMessage }}</div>
      <div v-if="!successMessage">
        <label for="token">{{ $t('emailChange.enterToken') }}</label>
        <input id="token" v-model="token" type="text" :placeholder="$t('emailChange.confirmToken')" />
        <button @click="confirmEmailChange" :disabled="isLoading || !token" class="btn-primary">
          {{ isLoading ? $t('common.loading') : $t('emailChange.confirmButton') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import userApi from '@/services/user'

export default {
  name: 'EmailResetConfirm',
  data() {
    return {
      token: this.$route.params.token || '',
      isLoading: false,
      successMessage: '',
      errorMessage: '',
    }
  },
  methods: {
    async confirmEmailChange() {
      this.isLoading = true
      this.successMessage = ''
      this.errorMessage = ''
      try {
        await userApi.confirmEmailChange(this.token)
        this.successMessage = this.$t('emailChange.successConfirm')
      } catch (error) {
        this.errorMessage = error.detail || error.message || this.$t('emailChange.error')
      } finally {
        this.isLoading = false
      }
    },
  },
  mounted() {
    // Auto-confirm if token is present in URL
    if (this.token) {
      this.confirmEmailChange()
    }
  },
}
</script>

<style scoped>
.email-reset-confirm-container {
  max-width: 400px;
  margin: 3rem auto;
  padding: 2rem;
}
.email-reset-confirm-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
  padding: 2rem;
}
.alert {
  margin-bottom: 1rem;
}
</style>
