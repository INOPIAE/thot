import { describe, it, expect, beforeEach, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import Profile from '@/views/user/Profile.vue'
import userApi from '@/services/user'
import { useAuthStore } from '@/stores/auth'

// Mock the user API
vi.mock('@/services/user', () => ({
  default: {
    getProfile: vi.fn(),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
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
    },
    user: {
      profile: 'User Profile',
      changePassword: 'Change Password',
      currentPassword: 'Current Password',
      newPassword: 'New Password',
      confirmNewPassword: 'Confirm New Password',
      passwordChanged: 'Password changed successfully',
      pendingApproval: 'Pending Approval',
    },
    admin: {
      approveCorporate: 'Approve Membership Number',
    },
    messages: {
      loadingError: 'Error loading data',
      saveSuccess: 'Changes saved successfully',
    },
  },
}

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages,
})

describe('Profile.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('renders profile component', () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.user = {
      id: '123',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['user'],
    }

    userApi.getProfile.mockResolvedValue({
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      current_language: 'en',
      corporate_number: '12345',
      corporate_approved: false,
    })

    const wrapper = mount(Profile, {
      global: {
        plugins: [i18n],
        stubs: ['router-link'],
        mocks: {
          $router: { push: vi.fn() },
          $route: { path: '/user/profile' },
        },
      },
    })

    expect(wrapper.find('h2').text()).toContain('User Profile')
  })

  it('loads profile data on mount', async () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.user = {
      id: '123',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['user'],
    }

    userApi.getProfile.mockResolvedValue({
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      current_language: 'en',
      corporate_number: '12345',
      corporate_approved: true,
    })

    const wrapper = mount(Profile, {
      global: {
        plugins: [i18n],
        stubs: ['router-link'],
        mocks: {
          $router: { push: vi.fn() },
          $route: { path: '/user/profile' },
        },
      },
    })

    await wrapper.vm.$nextTick()
    expect(userApi.getProfile).toHaveBeenCalled()
  })

  it('redirects to login if not authenticated', () => {
    const authStore = useAuthStore()
    authStore.token = null

    const mockPush = vi.fn()
    const wrapper = mount(Profile, {
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
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.user = {
      id: '123',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['user'],
    }

    userApi.getProfile.mockResolvedValue({
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      current_language: 'en',
      corporate_number: '12345',
      corporate_approved: false,
    })

    const wrapper = mount(Profile, {
      global: {
        plugins: [i18n],
        stubs: ['router-link'],
        mocks: {
          $router: { push: vi.fn() },
          $route: { path: '/user/profile' },
        },
      },
    })

    await wrapper.vm.$nextTick()

    // Test password validation
    wrapper.vm.passwordForm.new_password = 'ValidPass123!@'
    wrapper.vm.passwordForm.new_password_confirm = 'ValidPass123!@'
    wrapper.vm.updatePasswordValidation()

    expect(wrapper.vm.passwordValidation.hasMinLength).toBe(true)
    expect(wrapper.vm.passwordValidation.hasUpperLower).toBe(true)
    expect(wrapper.vm.passwordValidation.hasDigitOrSpecial).toBe(true)
    expect(wrapper.vm.passwordValidation.passwordsMatch).toBe(true)
  })

  it('rejects password that is too short', async () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.user = {
      id: '123',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['user'],
    }

    userApi.getProfile.mockResolvedValue({
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      current_language: 'en',
      corporate_number: '12345',
      corporate_approved: false,
    })

    const wrapper = mount(Profile, {
      global: {
        plugins: [i18n],
        stubs: ['router-link'],
        mocks: {
          $router: { push: vi.fn() },
          $route: { path: '/user/profile' },
        },
      },
    })

    await wrapper.vm.$nextTick()

    wrapper.vm.passwordForm.new_password = 'Short1!'
    wrapper.vm.updatePasswordValidation()

    expect(wrapper.vm.passwordValidation.hasMinLength).toBe(false)
  })

  it('detects when passwords do not match', async () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.user = {
      id: '123',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['user'],
    }

    userApi.getProfile.mockResolvedValue({
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      current_language: 'en',
      corporate_number: '12345',
      corporate_approved: false,
    })

    const wrapper = mount(Profile, {
      global: {
        plugins: [i18n],
        stubs: ['router-link'],
        mocks: {
          $router: { push: vi.fn() },
          $route: { path: '/user/profile' },
        },
      },
    })

    await wrapper.vm.$nextTick()

    wrapper.vm.passwordForm.new_password = 'ValidPass123!@'
    wrapper.vm.passwordForm.new_password_confirm = 'DifferentPass123!@'
    wrapper.vm.updatePasswordValidation()

    expect(wrapper.vm.passwordValidation.passwordsMatch).toBe(false)
  })

  it('saves profile changes successfully', async () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.user = {
      id: '123',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['user'],
      current_language: 'en',
    }

    userApi.getProfile.mockResolvedValue({
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      current_language: 'en',
      corporate_number: '12345',
      corporate_approved: false,
    })

    userApi.updateProfile.mockResolvedValue({
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Updated',
      last_name: 'User',
      current_language: 'de',
    })

    const wrapper = mount(Profile, {
      global: {
        plugins: [i18n],
        stubs: ['router-link'],
        mocks: {
          $router: { push: vi.fn() },
          $route: { path: '/user/profile' },
        },
      },
    })

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
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.user = {
      id: '123',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['user'],
    }

    userApi.getProfile.mockResolvedValue({
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      current_language: 'en',
      corporate_number: '12345',
      corporate_approved: false,
    })

    userApi.changePassword.mockResolvedValue({
      message: 'Password changed successfully',
    })

    const wrapper = mount(Profile, {
      global: {
        plugins: [i18n],
        stubs: ['router-link'],
        mocks: {
          $router: { push: vi.fn() },
          $route: { path: '/user/profile' },
        },
      },
    })

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
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.user = {
      id: '123',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['user'],
    }

    userApi.getProfile.mockResolvedValue({
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      current_language: 'en',
      corporate_number: '12345',
      corporate_approved: false,
    })

    userApi.changePassword.mockRejectedValue({
      response: {
        data: {
          detail: 'Current password is incorrect',
        },
      },
    })

    const wrapper = mount(Profile, {
      global: {
        plugins: [i18n],
        stubs: ['router-link'],
        mocks: {
          $router: { push: vi.fn() },
          $route: { path: '/user/profile' },
        },
      },
    })

    await wrapper.vm.$nextTick()

    wrapper.vm.passwordForm.current_password = 'WrongPassword!'
    wrapper.vm.passwordForm.new_password = 'NewPassword123!@'
    wrapper.vm.passwordForm.new_password_confirm = 'NewPassword123!@'

    await wrapper.vm.changePassword()

    expect(wrapper.vm.errorMessage).toContain('Current password is incorrect')
  })
})
