import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import PageDetail from '@/views/records/PageDetail.vue'
import { messages } from '../src/locales/messages'

vi.mock('@/services/page', () => ({
  pageService: {
    getPage: vi.fn(),
  },
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    hasRole: (role) => ['admin', 'user_page'].includes(role),
  }),
}))

import { pageService } from '@/services/page'

describe('PageDetail.vue', () => {
  const pinia = createPinia()
  setActivePinia(pinia)
  const i18n = createI18n({ legacy: false, locale: 'en', fallbackLocale: 'en', messages })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('preserves the incoming page list query in viewer, edit, and back routes', async () => {
    pageService.getPage.mockResolvedValue({
      name: 'Test Page',
      location_file: 'file.pdf',
      restriction: 'none',
      record_title: 'Record',
      record_signature: 'SIG-1',
    })

    const wrapper = mount(PageDetail, {
      global: {
        plugins: [pinia, i18n],
        stubs: {
          RouterLink: RouterLinkStub,
        },
        mocks: {
          $route: {
            params: { recordId: 'r1', pageId: '1' },
            query: { page: '3', pageSize: '25', search: 'alpha' },
          },
        },
      },
    })

    await flushPromises()

    const links = wrapper.findAllComponents(RouterLinkStub)
    expect(links[0].props('to')).toEqual({
      path: '/records/r1/pages/1/viewer',
      query: {
        page: '3',
        pageSize: '25',
        search: 'alpha',
      },
    })
    expect(links[1].props('to')).toEqual({
      path: '/records/r1/pages/1/edit',
      query: {
        page: '3',
        pageSize: '25',
        search: 'alpha',
      },
    })
    expect(links[2].props('to')).toEqual({
      path: '/records/r1/pages',
      query: {
        page: '3',
        pageSize: '25',
        search: 'alpha',
      },
    })
  })
})