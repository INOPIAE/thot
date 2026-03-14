import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

import Login from '@/views/auth/Login.vue'
import { messages } from '@/locales/messages'
import { useAppStore } from '@/stores/app'

function createI18nInstance() {
  return createI18n({
    legacy: false,
    locale: 'en',
    fallbackLocale: 'en',
    messages,
  })
}

describe('Login view register link visibility', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('shows register link when closed registration is disabled', () => {
    const appStore = useAppStore()
    appStore.appConfig = {
      features: {
        closedRegistration: false,
      },
    }

    const wrapper = mount(Login, {
      global: {
        plugins: [createI18nInstance()],
        mocks: {
          $route: { query: {} },
          $router: { push: vi.fn() },
        },
        stubs: {
          RouterLink: {
            template: '<a><slot /></a>',
          },
        },
      },
    })

    expect(wrapper.text()).toContain('Register')
  })

  it('hides register link when closed registration is enabled', () => {
    const appStore = useAppStore()
    appStore.appConfig = {
      features: {
        closedRegistration: true,
      },
    }

    const wrapper = mount(Login, {
      global: {
        plugins: [createI18nInstance()],
        mocks: {
          $route: { query: {} },
          $router: { push: vi.fn() },
        },
        stubs: {
          RouterLink: {
            template: '<a><slot /></a>',
          },
        },
      },
    })

    expect(wrapper.text()).not.toContain('Register')
  })
})
