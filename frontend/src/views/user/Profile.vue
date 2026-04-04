<template>
  <div class="profile-container">
    <div class="profile-card">
      <h2>{{ $t('user.profile') }}</h2>

      <div v-if="successMessage" class="alert alert-success">
        {{ successMessage }}
      </div>
      <div v-if="errorMessage" class="alert alert-error">
        {{ errorMessage }}
      </div>

      <div class="profile-section">
        <h3>{{ $t('auth.accountInfo') }}</h3>

        <div class="form-group">
          <label>{{ $t('common.username') }}</label>
          <input type="text" :value="profileData.username" readonly />
        </div>

        <div class="form-group">
          <label>{{ $t('common.email') }}</label>
          <input type="email" :value="profileData.email" readonly />
        </div>

        <div class="form-group">
          <label>{{ $t('common.corporateNumber') }} ({{ $t('common.optional') }})</label>
          <input type="text" :value="profileData.corporate_number" readonly />
        </div>

        <div class="form-group">
          <label v-if="profileData.corporate_approved" class="badge badge-success">
            ✓ {{ $t('admin.approveCorporate') }}
          </label>
          <label v-else class="badge badge-pending">
            {{ $t('user.pendingApproval') }}
          </label>
        </div>
      </div>

      <div class="profile-section">
        <h3>{{ $t('auth.personalInfo') }}</h3>

        <div class="form-row">
          <div class="form-group">
            <label for="firstName">{{ $t('common.firstName') }}</label>
            <input
              id="firstName"
              v-model="editData.first_name"
              type="text"
              @focus="clearMessages"
            />
          </div>
          <div class="form-group">
            <label for="lastName">{{ $t('common.lastName') }}</label>
            <input
              id="lastName"
              v-model="editData.last_name"
              type="text"
              @focus="clearMessages"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="language">{{ $t('common.language') }}</label>
          <select id="language" v-model="editData.current_language">
            <option value="en">English</option>
            <option value="de">Deutsch</option>
          </select>
        </div>

        <button
          @click="saveProfileChanges"
          :disabled="isLoading || !hasProfileChanges"
          class="btn-primary"
        >
          {{ isLoading ? $t('common.loading') : $t('common.save') }}
        </button>
      </div>

      <div class="profile-section password-section">
        <h3>{{ $t('user.changePassword') }}</h3>

        <div class="form-group">
          <label for="currentPassword">{{ $t('user.currentPassword') }}</label>
          <div class="password-input-wrapper">
            <input
              id="currentPassword"
              v-model="passwordForm.current_password"
              :type="showCurrentPassword ? 'text' : 'password'"
              @focus="clearMessages"
            />
            <button
              type="button"
              class="password-toggle"
              @click="showCurrentPassword = !showCurrentPassword"
              :aria-label="showCurrentPassword ? 'Hide password' : 'Show password'"
            >
              <span v-if="showCurrentPassword">👁️</span>
              <span v-else>👁️‍🗨️</span>
            </button>
          </div>
        </div>

        <div class="password-requirements">
          <p>{{ $t('auth.passwordRequirements') }}</p>
          <ul>
            <li :class="{ valid: passwordValidation.hasMinLength }">
              {{ $t('auth.minLength') }}: 10-60 {{ $t('auth.characters') }}
            </li>
            <li :class="{ valid: passwordValidation.hasUpperLower }">
              {{ $t('auth.upperLowerCase') }}
            </li>
            <li :class="{ valid: passwordValidation.hasDigitOrSpecial }">
              {{ $t('auth.digitOrSpecial') }}
            </li>
            <li :class="{ valid: passwordValidation.passwordsMatch }">
              {{ $t('auth.passwordsMustMatch') }}
            </li>
          </ul>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="newPassword">{{ $t('user.newPassword') }}</label>
            <div class="password-input-wrapper">
              <input
                id="newPassword"
                v-model="passwordForm.new_password"
                :type="showNewPassword ? 'text' : 'password'"
                @input="updatePasswordValidation"
                @focus="clearMessages"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showNewPassword = !showNewPassword"
                :aria-label="showNewPassword ? 'Hide password' : 'Show password'"
              >
                <span v-if="showNewPassword">👁️</span>
                <span v-else>👁️‍🗨️</span>
              </button>
            </div>
          </div>
          <div class="form-group">
            <label for="newPasswordConfirm">{{ $t('user.confirmNewPassword') }}</label>
            <div class="password-input-wrapper">
              <input
                id="newPasswordConfirm"
                v-model="passwordForm.new_password_confirm"
                :type="showConfirmPassword ? 'text' : 'password'"
                @input="updatePasswordValidation"
                @focus="clearMessages"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showConfirmPassword = !showConfirmPassword"
                :aria-label="showConfirmPassword ? 'Hide password' : 'Show password'"
              >
                <span v-if="showConfirmPassword">👁️</span>
                <span v-else>👁️‍🗨️</span>
              </button>
            </div>
          </div>
        </div>

        <button
          @click="changePassword"
          :disabled="isLoading || !isPasswordFormValid"
          class="btn-primary"
        >
          {{ isLoading ? $t('common.loading') : $t('user.changePassword') }}
        </button>
      </div>

      <div class="profile-section otp-section">
        <h3>{{ profileData.otp_enabled ? $t('user.changeOtp') : $t('user.setupOtp') }}</h3>


        <p class="otp-status" :class="profileData.otp_enabled ? 'otp-status-enabled' : 'otp-status-disabled'">
          {{ profileData.otp_enabled ? $t('user.otpStatusEnabled') : $t('user.otpStatusDisabled') }}
        </p>
        <p class="otp-description">{{ $t('user.otpResetDescription') }}</p>

        <button
          @click="startOtpReset"
          :disabled="isOtpResetLoading"
          class="btn-primary"
        >
          {{ isOtpResetLoading ? $t('common.loading') : (profileData.otp_enabled ? $t('user.changeOtp') : $t('user.setupOtp')) }}
        </button>

        <div v-if="hasPendingOtpReset" class="otp-reset-panel">
          <p class="otp-expiry">{{ $t('user.otpResetExpires', { hours: otpResetForm.expires_in_hours }) }}</p>

          <div v-if="otpResetForm.qr_code" class="otp-qr-block">
            <img
              :src="`data:image/png;base64,${otpResetForm.qr_code}`"
              :alt="$t('auth.otpQrAlt')"
              class="otp-qr-image"
            />
          </div>

          <div class="form-group">
            <label for="otpManualEntry">{{ $t('auth.otpManualEntryLabel') }}</label>
            <input id="otpManualEntry" type="text" :value="otpResetForm.manual_entry" readonly />
          </div>

          <p class="otp-description">{{ $t('auth.otpSetupHint') }}</p>

          <div class="form-group">
            <label for="otpResetCode">{{ $t('user.otpResetCodeLabel') }}</label>
            <input
              id="otpResetCode"
              v-model="otpResetForm.otp_code"
              type="text"
              inputmode="numeric"
              maxlength="6"
              @focus="clearMessages"
            />
          </div>

          <div class="otp-reset-actions">
            <button
              @click="confirmOtpReset"
              :disabled="isOtpResetLoading || otpResetForm.otp_code.length !== 6"
              class="btn-primary"
            >
              {{ isOtpResetLoading ? $t('common.loading') : $t('user.otpResetConfirm') }}
            </button>
            <button
              @click="resetOtpResetForm"
              :disabled="isOtpResetLoading"
              class="btn-secondary"
            >
              {{ $t('user.otpResetCancel') }}
            </button>
          </div>
        </div>
      </div>

      <div class="profile-section delete-section">
        <h3>{{ $t('user.deleteAccount') }}</h3>
        <p>{{ $t('user.deleteAccountDesc') }}</p>
        <button @click="confirmDeleteAccount" class="btn-danger">
          {{ $t('user.deleteAccountBtn') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { useAuthStore } from '@/stores/auth'
import userApi from '@/services/user'

export default defineComponent({
  name: 'Profile',
  data() {
    return {
      authStore: useAuthStore(),
      profileData: {
        username: '',
        email: '',
        first_name: '',
        last_name: '',
        current_language: 'en',
        corporate_number: '',
        corporate_approved: false,
        otp_enabled: false,
      },
      editData: {
        first_name: '',
        last_name: '',
        current_language: 'en',
      },
      passwordForm: {
        current_password: '',
        new_password: '',
        new_password_confirm: '',
      },
      otpResetForm: {
        token: '',
        otp_code: '',
        manual_entry: '',
        qr_code: '',
        expires_in_hours: null,
      },
      passwordValidation: {
        hasMinLength: false,
        hasUpperLower: false,
        hasDigitOrSpecial: false,
        passwordsMatch: false,
      },
      successMessage: '',
      errorMessage: '',
      isLoading: false,
      isOtpResetLoading: false,
      showCurrentPassword: false,
      showNewPassword: false,
      showConfirmPassword: false,
    }
  },
  computed: {
    hasProfileChanges() {
      return (
        this.editData.first_name !== this.profileData.first_name ||
        this.editData.last_name !== this.profileData.last_name ||
        this.editData.current_language !== this.profileData.current_language
      )
    },
    isPasswordFormValid() {
      return (
        this.passwordForm.current_password &&
        this.passwordValidation.hasMinLength &&
        this.passwordValidation.hasUpperLower &&
        this.passwordValidation.hasDigitOrSpecial &&
        this.passwordValidation.passwordsMatch
      )
    },
    hasPendingOtpReset() {
      return Boolean(this.otpResetForm.token)
    },
  },
  methods: {
        async confirmDeleteAccount() {
          if (!confirm(this.$t('user.deleteAccountConfirm'))) return
          this.clearMessages()
          this.isLoading = true
          try {
            const result = await userApi.deleteAccount()
            this.successMessage = result.detail?.[this.profileData.current_language] || result.message || this.$t('user.accountDeleted')
            // Optionally log out user after deletion
            setTimeout(() => {
              this.authStore.logout()
              this.$router.push('/auth/login')
            }, 2000)
          } catch (error) {
            this.errorMessage = error.detail || error.message || this.$t('messages.serverError')
          } finally {
            this.isLoading = false
          }
        },
    async loadProfile() {
      try {
        this.isLoading = true
        const response = await userApi.getProfile()

        this.profileData = {
          username: response.username || '',
          email: response.email || '',
          first_name: response.first_name || '',
          last_name: response.last_name || '',
          current_language: response.current_language || 'en',
          corporate_number: response.corporate_number || '',
          corporate_approved: response.corporate_approved || false,
          otp_enabled: response.otp_enabled || false,
        }

        this.editData = {
          first_name: this.profileData.first_name,
          last_name: this.profileData.last_name,
          current_language: this.profileData.current_language,
        }
      } catch (error) {
        this.errorMessage = this.$t('messages.loadingError')
        console.error('Error loading profile:', error)
      } finally {
        this.isLoading = false
      }
    },

    async saveProfileChanges() {
      try {
        this.clearMessages()
        this.isLoading = true

        const response = await userApi.updateProfile({
          first_name: this.editData.first_name,
          last_name: this.editData.last_name,
          current_language: this.editData.current_language,
        })

        this.profileData = {
          ...this.profileData,
          first_name: response.first_name,
          last_name: response.last_name,
          current_language: response.current_language,
          otp_enabled: response.otp_enabled,
        }

        this.successMessage = this.$t('messages.saveSuccess')

        if (this.authStore.user) {
          this.authStore.user.current_language = response.current_language
        }
      } catch (error) {
        this.errorMessage = error.response?.data?.detail || error.detail || this.$t('messages.serverError')
        console.error('Error updating profile:', error)
      } finally {
        this.isLoading = false
      }
    },

    async changePassword() {
      try {
        this.clearMessages()
        this.isLoading = true

        await userApi.changePassword({
          current_password: this.passwordForm.current_password,
          new_password: this.passwordForm.new_password,
          new_password_confirm: this.passwordForm.new_password_confirm,
        })

        this.passwordForm = {
          current_password: '',
          new_password: '',
          new_password_confirm: '',
        }

        this.successMessage = this.$t('user.passwordChanged')
      } catch (error) {
        this.errorMessage = error.response?.data?.detail || error.detail || this.$t('messages.serverError')
        console.error('Error changing password:', error)
      } finally {
        this.isLoading = false
      }
    },

    async startOtpReset() {
      try {
        this.clearMessages()
        this.isOtpResetLoading = true

        const response = await userApi.startOTPReset()
        this.otpResetForm = {
          token: response.token,
          otp_code: '',
          manual_entry: response.otp_setup?.manual_entry || '',
          qr_code: response.otp_setup?.qr_code || '',
          expires_in_hours: response.expires_in_hours,
        }

        this.successMessage = this.$t('user.otpResetStarted')
      } catch (error) {
        this.errorMessage = error.response?.data?.detail || error.detail || this.$t('messages.serverError')
      } finally {
        this.isOtpResetLoading = false
      }
    },

    async confirmOtpReset() {
      try {
        this.clearMessages()
        this.isOtpResetLoading = true

        await userApi.confirmOTPReset({
          token: this.otpResetForm.token,
          otp_code: this.otpResetForm.otp_code,
        })

        this.resetOtpResetForm()
        await this.loadProfile()
        this.successMessage = this.$t('user.otpResetSuccess')
      } catch (error) {
        this.errorMessage = error.response?.data?.detail || error.detail || this.$t('messages.serverError')
      } finally {
        this.isOtpResetLoading = false
      }
    },

    resetOtpResetForm() {
      this.otpResetForm = {
        token: '',
        otp_code: '',
        manual_entry: '',
        qr_code: '',
        expires_in_hours: null,
      }
    },

    updatePasswordValidation() {
      const pwd = this.passwordForm.new_password

      this.passwordValidation.hasMinLength = pwd.length >= 10 && pwd.length <= 60
      this.passwordValidation.hasUpperLower = /[a-z]/.test(pwd) && /[A-Z]/.test(pwd)
      this.passwordValidation.hasDigitOrSpecial = /[0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd)
      this.passwordValidation.passwordsMatch = pwd === this.passwordForm.new_password_confirm
    },

    clearMessages() {
      this.successMessage = ''
      this.errorMessage = ''
    },
  },

  mounted() {
    if (!this.authStore.isAuthenticated) {
      this.$router.push('/auth/login')
      return
    }

    this.loadProfile()
  },
})
</script>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 1rem;
}

.profile-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 2rem;
}

h2 {
  margin-bottom: 1.5rem;
  color: #333;
  border-bottom: 2px solid #f0f0f0;
  padding-bottom: 1rem;
}

.profile-section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #f0f0f0;
}

.profile-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.password-section,
.otp-section {
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 2px solid #f0f0f0;
}

h3 {
  margin-bottom: 1.5rem;
  color: #555;
  font-size: 1.1rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

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

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

input,
select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  font-family: inherit;
  box-sizing: border-box;
}

input:readonly {
  background-color: #f9f9f9;
  color: #666;
  cursor: default;
}

input:focus,
select:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

.password-requirements {
  background-color: #f9f9f9;
  border-left: 4px solid #ddd;
  padding: 1rem;
  margin-bottom: 1.5rem;
  border-radius: 4px;
}

.password-requirements p {
  margin: 0 0 0.75rem 0;
  font-weight: 500;
  color: #333;
}

.password-requirements ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.password-requirements li {
  padding: 0.25rem 0;
  color: #999;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.password-requirements li.valid {
  color: #4CAF50;
  font-weight: 500;
}

button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.otp-status {
  margin: 0 0 1rem;
  font-weight: 600;
}

.otp-status-enabled {
  color: #2e7d32;
}

.otp-status-disabled {
  color: #8a5800;
}

.otp-description,
.otp-expiry {
  color: #4e5d6c;
}

.otp-reset-panel {
  margin-top: 1.5rem;
  padding: 1.5rem;
  border: 1px solid #d8e0e8;
  border-radius: 8px;
  background-color: #fafcfe;
}

.otp-qr-block {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.otp-qr-image {
  width: 220px;
  max-width: 100%;
  border-radius: 8px;
  border: 1px solid #d8e0e8;
  background: white;
  padding: 0.75rem;
}

.otp-reset-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

@media (max-width: 640px) {
  .profile-card {
    padding: 1.5rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  h2 {
    font-size: 1.5rem;
  }

  h3 {
    font-size: 1rem;
  }

  .otp-reset-actions {
    flex-direction: column;
  }
}
</style>
