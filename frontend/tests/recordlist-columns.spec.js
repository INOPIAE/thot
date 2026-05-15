import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import RecordList from '../src/views/records/RecordList.vue'
vi.mock('../src/services/record', () => ({
  recordService: {
    getRecords: vi.fn(() => Promise.resolve({ data: [], total: 0 })),
    deleteRecord: vi.fn(() => Promise.resolve()),
  },
}))
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { messages } from '../src/locales/messages'
import { useAuthStore } from '../src/stores/auth'

function createI18nInstance(locale = 'en') {
  return createI18n({
    legacy: false,
    locale,
    fallbackLocale: 'en',
    messages,
  })
}

describe('RecordList.vue role-based columns', () => {
  let pinia
  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    localStorage.clear()
    vi.clearAllMocks()
  })

  function mountWithRole(role, defaultListMode = false) {
    const authStore = useAuthStore()
    authStore.user = { roles: [role] }
    authStore.token = 'token'
    const wrapper = mount(RecordList, {
      global: {
        plugins: [pinia, createI18nInstance()],
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
        mocks: {
          $t: (msg, vars) => (vars ? `${msg} ${JSON.stringify(vars)}` : msg),
        },
      },
      props: {
        defaultListMode,
      },
    })
    wrapper.vm.records = [
      { id: 1, title: 'Test', loantype: 'Book', loantype_subtype: 'Short', restriction: 'None' },
    ]
    wrapper.vm.loading = false
    return wrapper
  }

  it('shows only loantype for normal user', async () => {
    const wrapper = mountWithRole('user', true)
    await flushPromises()
//    console.log('USER:', wrapper.html())
    expect(wrapper.html()).toContain('Book')
    expect(wrapper.html()).not.toContain('Book - Short')
  })

  it('shows loantype and subtype combined for admin', async () => {
    const wrapper = mountWithRole('admin', false)
    await flushPromises()
//    console.log('ADMIN:', wrapper.html())
    expect(wrapper.html()).toContain('Book - Short')
  })

  it('shows loantype and subtype combined for user_bibl', async () => {
    const wrapper = mountWithRole('user_bibl', false)
    await flushPromises()
//    console.log('USER_BIBL:', wrapper.html())
    expect(wrapper.html()).toContain('Book - Short')
  })
})
