// Alle Mocks VOR den restlichen Imports!
import { describe, it, expect, vi } from 'vitest'

// Alle Mocks VOR den restlichen Imports!
vi.mock('../src/config/api.js', () => ({
  __esModule: true,
  default: 'http://localhost:8000/api/v1'
}))
vi.mock('../src/services/api.js', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))
vi.mock('@/components/PdfJsPageViewer.vue', () => ({
  default: {
    name: 'PdfJsPageViewer',
    props: ['src', 'rotation'],
    template: '<div class="mock-pdf-viewer">PDF: {{ !!src }} Rot: {{ rotation }}</div>'
  }
}))
vi.mock('../src/services/page', () => ({
  pageService: {
    getPage: vi.fn(),
    getViewPdf: vi.fn(),
    getThumbnail: vi.fn(),
    downloadWatermarkedPdf: vi.fn()
  }
}))

import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { pageService } from '../src/services/page'
import PageViewer from '@/views/records/PageViewer.vue'
import { messages } from '../src/locales/messages'

describe('PageViewer.vue', () => {
  // Setup Pinia, i18n und Router für alle Tests
  const pinia = createPinia()
  setActivePinia(pinia)
  const i18n = createI18n({ legacy: false, locale: 'en', fallbackLocale: 'en', messages })

  function setViewerRoles(roles = ['admin']) {
    const authStore = useAuthStore()
    authStore.user = { roles }
  }

  it('zeigt Fallback wenn keine Datei vorhanden', async () => {
    setViewerRoles()
    pageService.getPage.mockResolvedValue({ name: 'Test', location_file: null })
    const wrapper = mount(PageViewer, {
      global: {
        plugins: [pinia, i18n],
        stubs: {
          RouterLink: {
            name: 'RouterLink',
            props: ['to'],
            template: '<a><slot /></a>',
          },
        },
        mocks: {
          $route: { params: { recordId: 'r1', pageId: '1' }, query: { page: '3', pageSize: '25', search: 'alpha' } }
        }
      }
    })
    await flushPromises()
    expect(wrapper.text()).toContain('No PDF available for this page')
    expect(wrapper.find('.mock-pdf-viewer').exists()).toBe(false)
  })

  it('rendert PdfJsPageViewer mit korrekten Props', async () => {
    setViewerRoles()
    pageService.getPage.mockResolvedValue({ name: 'Test', location_file: 'file.pdf', rotation: 90 })
    pageService.getViewPdf.mockResolvedValue(new Blob(['dummy'], { type: 'application/pdf' }))
    pageService.getThumbnail.mockResolvedValue(new Blob(['thumb'], { type: 'image/png' }))
    const wrapper = mount(PageViewer, {
      global: {
        plugins: [pinia, i18n],
        stubs: {
          RouterLink: {
            name: 'RouterLink',
            props: ['to'],
            template: '<a><slot /></a>',
          },
        },
        mocks: {
          $route: { params: { recordId: 'r1', pageId: '1' }, query: { page: '3', pageSize: '25', search: 'alpha' } }
        }
      }
    })
    await flushPromises()
    expect(wrapper.findComponent({ name: 'PdfJsPageViewer' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'PdfJsPageViewer' }).props('rotation')).toBe(90)
  })

  it('preserves the incoming page list query in back and edit routes', async () => {
    setViewerRoles()
    pageService.getPage.mockResolvedValue({ name: 'Test', location_file: null })
    const wrapper = mount(PageViewer, {
      global: {
        plugins: [pinia, i18n],
        stubs: {
          RouterLink: {
            name: 'RouterLink',
            props: ['to'],
            template: '<a><slot /></a>',
          },
        },
        mocks: {
          $route: { params: { recordId: 'r1', pageId: '1' }, query: { page: '3', pageSize: '25', search: 'alpha' } }
        }
      }
    })
    await flushPromises()

    const links = wrapper.findAllComponents({ name: 'RouterLink' })
    expect(links[0].props('to')).toEqual({
      path: '/records/r1/pages/1/edit',
      query: {
        page: '3',
        pageSize: '25',
        search: 'alpha',
      },
    })
    expect(links[1].props('to')).toEqual({
      path: '/records/r1/pages',
      query: {
        page: '3',
        pageSize: '25',
        search: 'alpha',
      },
    })
  })
})
