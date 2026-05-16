import { describe, it, expect, beforeEach, vi } from 'vitest'
import { RouterLinkStub, mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

const mockRoute = {
  query: {},
}

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
}))

vi.mock('@/services/records', () => ({
  fetchRecords: vi.fn(),
}))

import RecordList from '@/views/records/RecordList.vue'
import { fetchRecords } from '@/services/records'
import { messages } from '../src/locales/messages'
import { useAuthStore } from '@/stores/auth'

function createI18nInstance(locale = 'en') {
  return createI18n({ legacy: false, locale, fallbackLocale: 'en', messages })
}

describe('RecordList query routing', () => {
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    vi.clearAllMocks()
    mockRoute.query = {}
  })

  it('restores records list query and forwards it to record routes', async () => {
    mockRoute.query = {
      recordsPage: '2',
      recordsPageSize: '20',
      recordsTitle: 'alpha',
      recordsSignature: 'sig',
    }

    fetchRecords.mockResolvedValue({
      items: [{ id: 'r1', title: 'Record One', page_count: 3 }],
      total: 50,
    })

    const authStore = useAuthStore()
    authStore.user = { roles: ['admin'] }

    const wrapper = mount(RecordList, {
      global: {
        plugins: [pinia, createI18nInstance()],
        stubs: {
          RouterLink: RouterLinkStub,
        },
        mocks: {
          $t: (msg, vars) => (vars ? `${msg} ${JSON.stringify(vars)}` : msg),
        },
      },
    })

    await flushPromises()

    expect(wrapper.vm.currentPage).toBe(2)
    expect(wrapper.vm.pageSize).toBe(20)
    expect(wrapper.vm.searchTitle).toBe('alpha')
    expect(wrapper.vm.searchSignature).toBe('sig')

    const links = wrapper.findAllComponents(RouterLinkStub)
    expect(links[0].props('to')).toEqual({
      path: '/records/new',
      query: {
        recordsPage: '2',
        recordsPageSize: '20',
        recordsTitle: 'alpha',
        recordsSignature: 'sig',
      },
    })
    expect(links[1].props('to')).toEqual({
      path: '/records/r1/pages-gallery',
      query: {
        recordsPage: '2',
        recordsPageSize: '20',
        recordsTitle: 'alpha',
        recordsSignature: 'sig',
      },
    })
    expect(links[2].props('to')).toEqual({
      path: '/records/r1',
      query: {
        recordsPage: '2',
        recordsPageSize: '20',
        recordsTitle: 'alpha',
        recordsSignature: 'sig',
      },
    })
  })
})