<template>
  <div class="auth-container">
    <div class="card form-card">
      <h2>{{ $t('auth.loginTitle') }}</h2>
      <p
        v-if="sessionNotice"
        class="info"
      >
        {{ sessionNotice }}
      </p>
      <p
        v-if="error"
        class="error"
      >
        {{ error }}
      </p>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">{{ $t('common.username') }}</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            required
          >
        </div>
        <div class="form-group">
          <label for="password">{{ $t('common.password') }}</label>
          <div class="password-input-wrapper">
            <input
              id="password"
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              required
            >
            <button
              type="button"
              class="password-toggle"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              @click="showPassword = !showPassword"
            >
              <span v-if="showPassword">👁️</span>
              <span v-else>👁️‍🗨️</span>
            </button>
          </div>
        </div>
        <div class="form-group">
          <label for="otp">
            {{ $t('auth.otpCode') }}
            <span>({{ $t('common.optional') }})</span>
          </label>
          <input
            id="otp"
            v-model="form.otpCode"
            type="text"
            placeholder="123456"
            maxlength="6"
          >
          <small>{{ $t('auth.enterOtpFromApp') }}</small>
        </div>
        <button
          type="submit"
          :disabled="isLoading"
        >
          {{ isLoading ? $t('common.loading') : $t('common.login') }}
        </button>
      </form>
      <p class="text-right mt-2">
        <router-link to="/auth/password-reset">
          {{ $t('auth.forgotPassword') }}
        </router-link>
      </p>
      <p class="text-center mt-3">
        {{ $t('auth.noAccount') }}
        <router-link
          v-if="showRegisterLink"
          to="/auth/register"
        >
          {{ $t('common.register') }}
        </router-link>
      </p>
    </div>
  </div>
</template>

<script>
import { computed, defineComponent, reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const TEMPORARY_LOCK_MESSAGE = 'Login temporarily locked. Please try again later'

export default defineComponent({
  name: 'Login',
  setup() {
    const authStore = useAuthStore()
    const appStore = useAppStore()
    const form = reactive({
      username: '',
      password: '',
      otpCode: '',
    })
    const error = ref('')
    const sessionNotice = ref('')
    const isLoading = ref(false)
    const showPassword = ref(false)
    const showRegisterLink = computed(
      () => !(appStore.config?.features?.closedRegistration ?? false)
    )

    return {
      authStore,
      appStore,
      form,
      error,
      sessionNotice,
      isLoading,
      showPassword,
      showRegisterLink,
    }
  },
  mounted() {
    if (this.$route.query.reason === 'session-timeout') {
      this.sessionNotice = this.$t('auth.sessionTimedOut')
    }
  },
  methods: {
    getLoginErrorMessage() {
      if (this.authStore.error === TEMPORARY_LOCK_MESSAGE) {
        return this.$t('auth.loginTemporarilyLocked')
      }

      return this.$t('auth.loginFailed')
    },

    async handleLogin() {
      this.isLoading = true
      this.error = ''
      this.sessionNotice = ''

      const success = await this.authStore.login(
        this.form.username,
        this.form.password,
        this.form.otpCode || null
      )

      if (success) {
        const redirectTarget = typeof this.$route.query.redirect === 'string'
          ? this.$route.query.redirect
          : '/'
        this.$router.push(redirectTarget)
      } else {
        this.error = this.getLoginErrorMessage()
      }

      this.isLoading = false
    },
  },
})
</script>

<style scoped>
.password-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.password-input-wrapper input {
  flex: 1;
  padding-right: 3rem;
}

.password-toggle {
  position: absolute;
  right: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  font-size: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.password-toggle:hover {
  opacity: 1;
}

.password-toggle:focus {
  outline: 2px solid #007bff;
  outline-offset: 2px;
  border-radius: 4px;
}
</style>
