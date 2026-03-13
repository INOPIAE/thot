<template>
  <div class="auth-container">
    <div class="card form-card">
      <div v-if="loading" class="loading">
        <p>{{ $t('common.loading') }}</p>
      </div>

      <div v-else-if="tokenError" class="error-message">
        <h2>{{ $t('auth.otpResetTitle') }}</h2>
        <p>{{ tokenError }}</p>
        <router-link to="/auth/login" class="btn btn-primary">
          {{ $t('common.backToLogin') }}
        </router-link>
      </div>

      <form v-else @submit.prevent="handleSubmit">
        <h2>{{ $t('auth.otpResetTitle') }}</h2>
        <p class="info-text">{{ $t('auth.otpResetDescription') }}</p>

        <div v-if="qrCode" class="qr-container">
          <img :src="`data:image/png;base64,${qrCode}`" :alt="$t('auth.otpQrAlt')" class="qr-image">
        </div>

        <div class="manual-entry">
          <label for="manualEntry">{{ $t('auth.otpManualEntryLabel') }}</label>
          <input id="manualEntry" type="text" :value="manualEntry" readonly>
        </div>

        <p class="hint-text">{{ $t('auth.otpSetupHint') }}</p>

        <div class="form-group">
          <label for="otpCode">{{ $t('user.otpResetCodeLabel') }}</label>
          <input
            id="otpCode"
            v-model="otpCode"
            type="text"
            inputmode="numeric"
            maxlength="6"
            required
          >
        </div>

        <button
          type="submit"
          class="btn btn-primary"
          :disabled="isLoading || otpCode.length !== 6"
        >
          {{ isLoading ? $t('common.loading') : $t('user.otpResetConfirm') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import authService from '@/services/auth'

export default defineComponent({
  name: 'OTPResetConfirm',
  data() {
    return {
      token: '',
      loading: true,
      isLoading: false,
      tokenError: '',
      qrCode: '',
      manualEntry: '',
      otpCode: '',
    }
  },
  async mounted() {
    this.token = this.$route.params.token
    await this.validateToken()
  },
  methods: {
    async validateToken() {
      try {
        this.loading = true
        const response = await authService.validateOtpResetToken(this.token)
        this.qrCode = response?.otp_setup?.qr_code || ''
        this.manualEntry = response?.otp_setup?.manual_entry || ''
      } catch (error) {
        this.tokenError = error?.detail || this.$t('auth.invalidOrExpiredLink')
      } finally {
        this.loading = false
      }
    },
    async handleSubmit() {
      try {
        this.isLoading = true
        await authService.confirmOtpResetToken(this.token, this.otpCode)
        alert(this.$t('user.otpResetSuccess'))
        this.$router.push('/auth/login')
      } catch (error) {
        const message = error?.detail || this.$t('messages.serverError')
        alert(message)
      } finally {
        this.isLoading = false
      }
    },
  },
})
</script>

<style scoped>
.form-card {
  width: 100%;
  max-width: 520px;
}

.info-text {
  margin-bottom: 16px;
}

.qr-container {
  display: flex;
  justify-content: center;
  margin: 12px 0 18px;
}

.qr-image {
  width: 220px;
  height: 220px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fff;
  object-fit: contain;
}

.manual-entry {
  margin-bottom: 12px;
}

.manual-entry label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
}

.manual-entry input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: #f5f5f5;
  font-family: monospace;
}

.hint-text {
  font-size: 0.95rem;
  color: #555;
  margin-bottom: 16px;
}
</style>
