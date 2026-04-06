import { describe, it, expect, beforeEach, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import Profile from '@/views/user/Profile.vue'
import userApi from '@/services/user'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/services/user', () => ({
  default: {
    getProfile: vi.fn(),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
    startOTPReset: vi.fn(),
    confirmOTPReset: vi.fn(),
  },
}))

const messages = {
  en: {
    common: {
      username: 'Username',
      email: 'Email',
      firstName: 'First Name',
      lastName: 'Last Name',
      corporateNumber: 'Membership Number',
      language: 'Language',
      save: 'Save',
      loading: 'Loading...',
      optional: 'optional',
    },
    auth: {
      accountInfo: 'Account Information',
      personalInfo: 'Personal Information',
      passwordInfo: 'Password',
      passwordRequirements: 'Password Requirements',
      minLength: 'Minimum Length',
      upperLowerCase: 'Upper and Lower Case',
      digitOrSpecial: 'Digit or Special Character',
      characters: 'characters',
      passwordsMustMatch: 'Passwords must match',
      otpQrAlt: 'QR code for OTP setup',
      otpManualEntryLabel: 'Manual setup key',
      otpSetupHint: 'Enter the manual key in your app and confirm a code.',
    },
    user: {
      profile: 'User Profile',
      changePassword: 'Change Password',
      currentPassword: 'Current Password',
      newPassword: 'New Password',
      confirmNewPassword: 'Confirm New Password',
      passwordChanged: 'Password changed successfully',
      pendingApproval: 'Pending Approval',
      otpStatusEnabled: '2FA authentication is active',
      otpStatusDisabled: '2FA authentication is not active',
      setupOtp: 'Set up two-factor authentication',
      changeOtp: 'Change two-factor authentication',
      otpResetDescription: 'Temporary OTP reset description',
      otpResetStarted: 'Temporary OTP setup created.',
      otpResetConfirm: 'Confirm new two-factor authentication',
      otpResetCodeLabel: 'Authenticator code',
      otpResetSuccess: 'Two-factor authentication updated successfully',
      otpResetCancel: 'Cancel temporary setup',
      otpResetExpires: 'Temporary setup expires in {hours} hour(s).',
    },
    admin: {
      approveCorporate: 'Approved Membership Number',
    },
    messages: {
      loadingError: 'Error loading data',
      saveSuccess: 'Changes saved successfully',
      serverError: 'Server error',
    },
  },
}

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages,
})

function authenticatedStore() {
  const authStore = useAuthStore()
  authStore.token = 'test-token'
  authStore.user = {
    id: '123',
    username: 'testuser',
    email: 'test@example.com',
    roles: ['user'],
    current_language: 'en',
  }
  return authStore
}

function buildProfile(overrides = {}) {
  return {
    username: 'testuser',
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
    current_language: 'en',
    corporate_number: '12345',
    corporate_approved: false,
    otp_enabled: false,
    ...overrides,
  }
}

function mountProfile() {
  return mount(Profile, {
    global: {
      plugins: [i18n],
      stubs: ['router-link'],
      mocks: {
        $router: { push: vi.fn() },
        $route: { path: '/user/profile' },
      },
    },
  })
}

describe('Profile.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('renders profile component', () => {
    authenticatedStore()
    userApi.getProfile.mockResolvedValue(buildProfile({ otp_enabled: true }))

    const wrapper = mountProfile()
    expect(wrapper.find('h2').text()).toContain('User Profile')
  })

  it('loads profile data on mount', async () => {
    authenticatedStore()
    userApi.getProfile.mockResolvedValue(buildProfile({ corporate_approved: true, otp_enabled: true }))

    const wrapper = mountProfile()
    await wrapper.vm.$nextTick()

    expect(userApi.getProfile).toHaveBeenCalled()
  })

  it('redirects to login if not authenticated', () => {
    const authStore = useAuthStore()
    authStore.token = null

    const mockPush = vi.fn()
    mount(Profile, {
      global: {
        plugins: [i18n],
        stubs: ['router-link'],
        mocks: {
          $router: { push: mockPush },
          $route: { path: '/user/profile' },
        },
      },
    })

    expect(mockPush).toHaveBeenCalledWith('/auth/login')
  })

  it('validates password requirements', async () => {
    authenticatedStore()
    userApi.getProfile.mockResolvedValue(buildProfile())

    const wrapper = mountProfile()
    await wrapper.vm.$nextTick()

    wrapper.vm.passwordForm.new_password = 'ValidPass123!@'
    wrapper.vm.passwordForm.new_password_confirm = 'ValidPass123!@'
    wrapper.vm.updatePasswordValidation()

    expect(wrapper.vm.passwordValidation.hasMinLength).toBe(true)
    expect(wrapper.vm.passwordValidation.hasUpperLower).toBe(true)
    expect(wrapper.vm.passwordValidation.hasDigitOrSpecial).toBe(true)
    expect(wrapper.vm.passwordValidation.passwordsMatch).toBe(true)
  })

  it('rejects password that is too short', async () => {
    authenticatedStore()
    userApi.getProfile.mockResolvedValue(buildProfile())

    const wrapper = mountProfile()
    await wrapper.vm.$nextTick()

    wrapper.vm.passwordForm.new_password = 'Short1!'
    wrapper.vm.updatePasswordValidation()

    expect(wrapper.vm.passwordValidation.hasMinLength).toBe(false)
  })

  it('detects when passwords do not match', async () => {
    authenticatedStore()
    userApi.getProfile.mockResolvedValue(buildProfile())

    const wrapper = mountProfile()
    await wrapper.vm.$nextTick()

    wrapper.vm.passwordForm.new_password = 'ValidPass123!@'
    wrapper.vm.passwordForm.new_password_confirm = 'DifferentPass123!@'
    wrapper.vm.updatePasswordValidation()

    expect(wrapper.vm.passwordValidation.passwordsMatch).toBe(false)
  })

  it('saves profile changes successfully', async () => {
    authenticatedStore()
    userApi.getProfile.mockResolvedValue(buildProfile())
    userApi.updateProfile.mockResolvedValue(buildProfile({ first_name: 'Updated', current_language: 'de' }))

    const wrapper = mountProfile()
    await flushPromises()

    wrapper.vm.editData.first_name = 'Updated'
    wrapper.vm.editData.current_language = 'de'

    await wrapper.vm.saveProfileChanges()

    expect(userApi.updateProfile).toHaveBeenCalledWith({
      first_name: 'Updated',
      last_name: 'User',
      current_language: 'de',
    })
  })

  it('changes password successfully', async () => {
    authenticatedStore()
    userApi.getProfile.mockResolvedValue(buildProfile())
    userApi.changePassword.mockResolvedValue({ message: 'Password changed successfully' })

    const wrapper = mountProfile()
    await wrapper.vm.$nextTick()

    wrapper.vm.passwordForm.current_password = 'OldPassword123!'
    wrapper.vm.passwordForm.new_password = 'NewPassword123!@'
    wrapper.vm.passwordForm.new_password_confirm = 'NewPassword123!@'

    await wrapper.vm.changePassword()

    expect(userApi.changePassword).toHaveBeenCalledWith({
      current_password: 'OldPassword123!',
      new_password: 'NewPassword123!@',
      new_password_confirm: 'NewPassword123!@',
    })
    expect(wrapper.vm.passwordForm.current_password).toBe('')
    expect(wrapper.vm.passwordForm.new_password).toBe('')
    expect(wrapper.vm.passwordForm.new_password_confirm).toBe('')
  })

  it('displays error message on change password failure', async () => {
    authenticatedStore()
    userApi.getProfile.mockResolvedValue(buildProfile())
    userApi.changePassword.mockRejectedValue({
      response: {
        data: {
          detail: 'Current password is incorrect',
        },
      },
    })

    const wrapper = mountProfile()
    await wrapper.vm.$nextTick()

    wrapper.vm.passwordForm.current_password = 'WrongPassword!'
    wrapper.vm.passwordForm.new_password = 'NewPassword123!@'
    wrapper.vm.passwordForm.new_password_confirm = 'NewPassword123!@'

    await wrapper.vm.changePassword()

    expect(wrapper.vm.errorMessage).toContain('Current password is incorrect')
  })

  it('starts otp reset successfully', async () => {
    authenticatedStore()
    userApi.getProfile.mockResolvedValue(buildProfile({ otp_enabled: true }))
    userApi.startOTPReset.mockResolvedValue({
      token: 'temporary-token',
      expires_in_hours: 1,
      otp_setup: {
        manual_entry: 'ABCDEF123456',
        qr_code: 'ZmFrZS1xcg==',
      },
    })

    const wrapper = mountProfile()
    await flushPromises()
    await wrapper.vm.startOtpReset()

    expect(userApi.startOTPReset).toHaveBeenCalled()
    expect(wrapper.vm.otpResetForm.token).toBe('temporary-token')
    expect(wrapper.text()).toContain('Temporary OTP setup created.')
  })

  it('confirms otp reset successfully', async () => {
    authenticatedStore()
    userApi.getProfile
      .mockResolvedValueOnce(buildProfile({ otp_enabled: false }))
      .mockResolvedValueOnce(buildProfile({ otp_enabled: true }))
    userApi.confirmOTPReset.mockResolvedValue({
      message: 'Two-factor authentication updated successfully',
    })

    const wrapper = mountProfile()
    await flushPromises()

    wrapper.vm.otpResetForm = {
      token: 'temporary-token',
      otp_code: '123456',
      manual_entry: 'ABCDEF123456',
      qr_code: 'ZmFrZS1xcg==',
      expires_in_hours: 1,
    }

    await wrapper.vm.confirmOtpReset()

    expect(userApi.confirmOTPReset).toHaveBeenCalledWith({
      token: 'temporary-token',
      otp_code: '123456',
    })
    expect(wrapper.vm.otpResetForm.token).toBe('')
    expect(wrapper.vm.profileData.otp_enabled).toBe(true)
  })
})
