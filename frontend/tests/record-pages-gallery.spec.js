import { describe, it, expect, beforeEach, vi } from 'vitest'
import { RouterLinkStub, flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import RecordPagesGallery from '@/views/records/RecordPagesGallery.vue'
import { useAuthStore } from '@/stores/auth'
import { recordService } from '@/services/record'
import { pageService } from '@/services/page'

vi.mock('@/services/record', () => ({
  recordService: {
    getRecord: vi.fn().mockResolvedValue({ title: 'Record One' }),
    downloadCombinedPdf: vi.fn().mockResolvedValue({
      blob: new Blob(['combined'], { type: 'application/pdf' }),
      contentDisposition: 'attachment; filename="record.pdf"',
    }),
  },
}))

vi.mock('@/services/page', () => ({
  pageService: {
    listPages: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'p-1',
          name: 'Restricted Page',
          location_file: 'record/origin/Seite_1.pdf',
          current_file: 'record/current/Seite_1_current.pdf',
          restriction_file: 'record/restriction/Seite_1_restricted.pdf',
          rotation: 90,
          rotation_restriction: 180,
          pdf_public_url: 'https://example.test/public/current.pdf',
          order_by: 1,
        },
      ],
      total: 1,
    }),
    getThumbnail: vi.fn().mockResolvedValue(new Blob(['thumb'], { type: 'image/jpeg' })),
    getViewPdf: vi.fn().mockResolvedValue(new Blob(['current'], { type: 'application/pdf' })),
    getRestrictionViewPdf: vi.fn().mockResolvedValue(new Blob(['restricted'], { type: 'application/pdf' })),
    downloadWatermarkedPdf: vi.fn().mockResolvedValue({
      blob: new Blob(['current'], { type: 'application/pdf' }),
      contentDisposition: 'attachment; filename="current.pdf"',
    }),
    downloadRestrictionPdf: vi.fn().mockResolvedValue({
      blob: new Blob(['restricted'], { type: 'application/pdf' }),
      contentDisposition: 'attachment; filename="restricted.pdf"',
    }),
  },
}))

const messages = {
  en: {
    common: {
      back: 'Back',
      close: 'Close',
      open: 'Open',
      loading: 'Loading',
      copied: 'Copied',
      copyError: 'Copy failed',
    },
    pages: {
      downloadAllPagesAsPdf: 'Download all pages as PDF',
      downloadCombinedPdf: 'Download combined PDF',
      galleryTitle: 'Gallery',
      allPages: 'All pages',
      createNew: 'Create new',
      noPages: 'No pages',
      noThumbnail: 'No thumbnail',
      rotation: 'Rotation',
      selectPageToView: 'Select page to view',
      downloadPdf: 'Download PDF',
      pdfLoadError: 'Failed to load PDF',
      unknownRecord: 'Unknown record',
      downloadError: 'Download failed',
      downloadCombinedError: 'Combined download failed',
    },
    records: {
      citationLink: 'Citation link',
      citationLinkCopy: 'Copy citation link',
    },
  },
}

function createI18nInstance() {
  return createI18n({ legacy: false, locale: 'en', fallbackLocale: 'en', messages })
}

function mountGallery() {
  const i18n = createI18nInstance()
  const pinia = createPinia()
  setActivePinia(pinia)

  const authStore = useAuthStore()
  authStore.user = { roles: ['admin'] }

  return mount(RecordPagesGallery, {
    global: {
      plugins: [i18n, pinia],
      mocks: {
        $route: {
          params: { recordId: 'rec-1' },
          query: {
            recordsPage: '2',
            recordsPageSize: '20',
            recordsTitle: 'alpha',
          },
        },
      },
      stubs: {
        RouterLink: RouterLinkStub,
        PdfJsPageViewer: { template: '<div class="pdf-viewer-stub" />' },
      },
    },
  })
}

describe('RecordPagesGallery', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.URL.createObjectURL = vi.fn(() => 'blob:gallery')
    global.URL.revokeObjectURL = vi.fn()
  })

  it('prefers the restriction PDF in gallery thumbnails, viewer, and download', async () => {
    const wrapper = mountGallery()
    await flushPromises()

    const links = wrapper.findAllComponents(RouterLinkStub)
    expect(links[0].props('to')).toEqual({
      path: '/records',
      query: {
        recordsPage: '2',
        recordsPageSize: '20',
        recordsTitle: 'alpha',
      },
    })

    expect(pageService.getThumbnail).toHaveBeenCalledWith('p-1', 200, true)
    expect(pageService.getRestrictionViewPdf).toHaveBeenCalledWith('p-1')
    expect(pageService.getViewPdf).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Rotation: 180°')
    expect(wrapper.html()).not.toContain('https://example.test/public/current.pdf')

    await wrapper.vm.downloadPdf()

    expect(pageService.downloadRestrictionPdf).toHaveBeenCalledWith('p-1')
    expect(pageService.downloadWatermarkedPdf).not.toHaveBeenCalled()
    expect(recordService.downloadCombinedPdf).not.toHaveBeenCalled()
  })
})