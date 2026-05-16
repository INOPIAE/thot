import { describe, it, expect, beforeEach, vi } from 'vitest'
import { RouterLinkStub, mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import RecordForm from '@/views/records/RecordForm.vue'
import { messages } from '../src/locales/messages'
import { useAuthStore } from '@/stores/auth'
import { recordService } from '@/services/record'

vi.mock('@/services/record', () => ({
  recordService: {
    getRestrictions: vi.fn().mockResolvedValue({ items: [] }),
    getWorkStatus: vi.fn().mockResolvedValue({ items: [] }),
    listLoanTypes: vi.fn().mockResolvedValue({ items: [] }),
    listRecordConditions: vi.fn().mockResolvedValue({ items: [] }),
    listLetterings: vi.fn().mockResolvedValue({ items: [] }),
    listPublicationTypes: vi.fn().mockResolvedValue({ items: [] }),
    listPublishers: vi.fn().mockResolvedValue({ items: [] }),
    listAuthorTypes: vi.fn().mockResolvedValue({ items: [] }),
    listAuthors: vi.fn().mockResolvedValue({ items: [] }),
    getRecord: vi.fn().mockResolvedValue({
      title: 'Record One',
      restriction_id: '',
      workstatus_id: '',
      record_authors: [],
    }),
    updateRecord: vi.fn().mockResolvedValue({}),
  },
}))

vi.mock('@/services/page', () => ({
  pageService: {},
}))

function createI18nInstance(locale = 'en') {
  return createI18n({ legacy: false, locale, fallbackLocale: 'en', messages })
}

describe('RecordForm query routing', () => {
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    vi.clearAllMocks()
  })

  it('preserves records list query in header, cancel, and save navigation', async () => {
    const authStore = useAuthStore()
    authStore.user = { roles: ['admin'] }

    const routerPush = vi.fn()

    const wrapper = mount(RecordForm, {
      global: {
        plugins: [pinia, createI18nInstance()],
        stubs: {
          RouterLink: RouterLinkStub,
        },
        mocks: {
          $route: {
            params: { id: 'r1' },
            query: {
              recordsPage: '2',
              recordsPageSize: '20',
              recordsTitle: 'alpha',
              recordsSignature: 'sig',
            },
          },
          $router: { push: routerPush },
        },
      },
    })

    await flushPromises()

    const links = wrapper.findAllComponents(RouterLinkStub)
    expect(links[0].props('to')).toEqual({
      path: '/records/r1/pages-gallery',
      query: {
        recordsPage: '2',
        recordsPageSize: '20',
        recordsTitle: 'alpha',
        recordsSignature: 'sig',
      },
    })
    expect(links[1].props('to')).toEqual({
      path: '/records/r1/pages',
      query: {
        recordsPage: '2',
        recordsPageSize: '20',
        recordsTitle: 'alpha',
        recordsSignature: 'sig',
      },
    })
    expect(links[2].props('to')).toEqual({
      path: '/records',
      query: {
        recordsPage: '2',
        recordsPageSize: '20',
        recordsTitle: 'alpha',
        recordsSignature: 'sig',
      },
    })

    await wrapper.vm.handleSubmit()

    expect(recordService.updateRecord).toHaveBeenCalledWith('r1', expect.objectContaining({ title: 'Record One' }))
    expect(routerPush).toHaveBeenCalledWith({
      path: '/records',
      query: {
        recordsPage: '2',
        recordsPageSize: '20',
        recordsTitle: 'alpha',
        recordsSignature: 'sig',
      },
    })
  })
})