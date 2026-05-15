import { describe, it, expect, beforeEach, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import PageForm from '@/views/records/PageForm.vue'
import { useAuthStore } from '@/stores/auth'
import { pageService } from '@/services/page'

vi.mock('@/services/record', () => ({
  recordService: {
    getRestrictions: vi.fn().mockResolvedValue({ items: [{ id: 'r1', name: 'none' }] }),
    getWorkStatus: vi.fn().mockResolvedValue({ items: [] }),
  },
}))

vi.mock('@/services/page', () => ({
  pageService: {
    listPages: vi.fn().mockResolvedValue({
      items: [
        { id: 'p-1', name: 'Test Page' },
        { id: 'p-2', name: 'Second Page' },
      ],
      total: 2,
    }),
    getPage: vi.fn().mockResolvedValue({
      name: 'Test Page',
      description: '',
      page: '',
      comment: '',
      restriction_id: 'r1',
      workstatus_id: null,
      location_file: 'some/file.pdf',
    }),
    createPage: vi.fn().mockResolvedValue({}),
    updatePage: vi.fn().mockResolvedValue({}),
    getThumbnail: vi.fn().mockResolvedValue(new Blob(['thumbnail'], { type: 'image/png' })),
    getViewPdf: vi.fn().mockResolvedValue(new Blob(['pdf'], { type: 'application/pdf' })),
    getRestrictionViewPdf: vi.fn().mockResolvedValue(new Blob(['pdf'], { type: 'application/pdf' })),
  },
}))

const messages = {
  en: {
    common: {
      back: 'Back',
      cancel: 'Cancel',
      save: 'Save',
      saving: 'Saving...',
      loading: 'Loading...',
      yes: 'Yes',
      no: 'No',
    },
    pages: {
      createPage: 'Create Page',
      editPage: 'Edit Page',
      rotation: 'Rotation',
      pageName: 'Name',
      pageNamePlaceholder: 'Enter name',
      description: 'Description',
      descriptionPlaceholder: 'Enter description',
      comment: 'Comment',
      commentPlaceholder: 'Enter comment',
      pageContent: 'Content',
      pageContentPlaceholder: 'Enter content',
      orderBy: 'Sort Order',
      orderByPlaceholder: 'Sort order',
      orderByHelp: 'Lower values are shown first.',
      restriction: 'Restriction',
      selectRestriction: 'Select restriction...',
      workstatus: 'Work Status',
      selectWorkStatus: 'Select work status...',
      uploadFile: 'Upload PDF File',
      uploadMultiPageHint: 'Multi-page PDFs will be split into individual page entries automatically.',
      uploadSinglePageOnly: 'Only single-page PDFs are allowed when replacing a file on an existing page.',
      restrictionUploadSinglePageOnly: 'Restriction files must always be uploaded as a single-page PDF.',
      uploadSinglePageError: 'The selected PDF has multiple pages. Please upload a single-page PDF.',
      restrictionRotation: 'Restriction rotation',
      previousPage: 'Previous page',
      nextPage: 'Next page',
      pageNavigationPosition: 'Page {current} of {total}',
      unsavedChangesTitle: 'Unsaved changes',
      unsavedChangesMessage: 'There are unsaved changes on this page. Do you want to save them before leaving edit mode?',
      saveAndContinue: 'Save and continue',
      discardChanges: 'Discard changes',
      noFileSelected: 'No file selected',
      noRestrictionFileSelected: 'No restriction file selected',
      noThumbnail: 'No thumbnail',
      pdfThumbnail: 'PDF thumbnail',
      currentFile: 'Current file',
      removeCurrentFile: 'Remove current file',
      restrictionFile: 'Restriction file',
      removeRestrictionFile: 'Remove restriction file',
      uploadRestrictionFile: 'Upload restriction PDF',
      restrictionPdfDocument: 'Restriction PDF',
      currentPdfDocument: 'Current PDF',
      downloadCurrentPdf: 'Download current PDF',
      downloadRestrictionPdf: 'Download restriction PDF',
      loadError: 'Failed to load page',
      metadataLoadError: 'Failed to load metadata',
      saveError: 'Failed to save page',
    },
    records: {
      title: 'Record',
    },
    messages: {
      unauthorised: 'Unauthorised',
    },
  },
}

function createI18nInstance() {
  return createI18n({ legacy: false, locale: 'en', fallbackLocale: 'en', messages })
}

/**
 * Helper: build a minimal PDF-like ArrayBuffer.
 * The FileReader in onFileChange decodes via latin1 and searches for
 * /Type /Page (not followed by 's'). We embed the right strings.
 */
function makePdfBuffer(pageCount) {
  // Insert the right number of /Type /Page objects and one /Type /Pages root
  let content = '%PDF-1.4\n/Type /Pages count=' + pageCount + '\n'
  for (let i = 0; i < pageCount; i++) {
    content += '/Type /Page\n'
  }
  const encoder = new TextEncoder()
  return encoder.encode(content).buffer
}

function makeMockFile(name, pageCount) {
  const buffer = makePdfBuffer(pageCount)
  const blob = new Blob([buffer], { type: 'application/pdf' })
  const file = new File([blob], name, { type: 'application/pdf' })
  return file
}

function mountPageForm({ isEditMode = false, roles = ['admin'] } = {}) {
  const i18n = createI18nInstance()
  const pinia = createPinia()
  setActivePinia(pinia)

  const authStore = useAuthStore()
  // hasRole getter checks state.user?.roles.includes(role) — roles must be plain string array
  authStore.user = { roles }

  const routeParams = isEditMode
    ? { recordId: 'rec-1', pageId: 'p-1' }
    : { recordId: 'rec-1' }

  const routerPush = vi.fn()

  const wrapper = mount(PageForm, {
    global: {
      plugins: [i18n, pinia],
      mocks: {
        $route: { params: routeParams },
        $router: { push: routerPush },
      },
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
        PdfJsPageViewer: { template: '<div class="pdfjs-page-viewer-stub" />' },
      },
    },
  })

  return { wrapper, routerPush }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('PageForm – file upload hints', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.URL.createObjectURL = vi.fn(() => 'blob:thumbnail')
    global.URL.revokeObjectURL = vi.fn()
  })

  it('shows multi-page hint in create mode', async () => {
    const { wrapper } = mountPageForm({ isEditMode: false })
    await flushPromises()
    expect(wrapper.text()).toContain(
      'Multi-page PDFs will be split into individual page entries automatically.',
    )
  })

  it('does not show single-page-only note in create mode', async () => {
    const { wrapper } = mountPageForm({ isEditMode: false })
    await flushPromises()
    expect(wrapper.text()).not.toContain(
      'Only single-page PDFs are allowed when replacing a file on an existing page.',
    )
  })

  it('shows single-page-only note in edit mode', async () => {
    const { wrapper } = mountPageForm({ isEditMode: true })
    await flushPromises()
    expect(wrapper.text()).toContain(
      'Only single-page PDFs are allowed when replacing a file on an existing page.',
    )
  })

  it('does not show multi-page hint in edit mode', async () => {
    const { wrapper } = mountPageForm({ isEditMode: true })
    await flushPromises()
    expect(wrapper.text()).not.toContain(
      'Multi-page PDFs will be split into individual page entries automatically.',
    )
  })
})

describe('PageForm – file page count validation in edit mode', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.URL.createObjectURL = vi.fn(() => 'blob:thumbnail')
    global.URL.revokeObjectURL = vi.fn()
  })

  it('shows error and clears file when multi-page PDF selected in edit mode', async () => {
    const { wrapper } = mountPageForm({ isEditMode: true })
    await flushPromises()

    const multiPageFile = makeMockFile('multi.pdf', 3)

    // Spy on FileReader to provide synchronous onload
    const originalFileReader = window.FileReader
    const readAsArrayBufferSpy = vi.fn().mockImplementation(function () {
      const buffer = makePdfBuffer(3)
      this.result = buffer
      this.onload({ target: { result: buffer } })
    })
    window.FileReader = vi.fn().mockImplementation(() => ({
      readAsArrayBuffer: readAsArrayBufferSpy,
      onload: null,
    }))

    const input = wrapper.find('#file')
    Object.defineProperty(input.element, 'files', {
      value: [multiPageFile],
      configurable: true,
    })
    await input.trigger('change')
    await flushPromises()

    window.FileReader = originalFileReader

    const vm = wrapper.vm
    expect(vm.filePageError).toBeTruthy()
    expect(vm.selectedFile).toBeNull()
    expect(wrapper.text()).toContain(
      'The selected PDF has multiple pages. Please upload a single-page PDF.',
    )
  })

  it('clears error and accepts single-page PDF in edit mode', async () => {
    const { wrapper } = mountPageForm({ isEditMode: true })
    await flushPromises()

    const singlePageFile = makeMockFile('single.pdf', 1)

    const originalFileReader = window.FileReader
    window.FileReader = vi.fn().mockImplementation(() => ({
      readAsArrayBuffer: vi.fn().mockImplementation(function () {
        const buffer = makePdfBuffer(1)
        this.result = buffer
        this.onload({ target: { result: buffer } })
      }),
      onload: null,
    }))

    const input = wrapper.find('#file')
    Object.defineProperty(input.element, 'files', {
      value: [singlePageFile],
      configurable: true,
    })
    await input.trigger('change')
    await flushPromises()

    window.FileReader = originalFileReader

    const vm = wrapper.vm
    expect(vm.filePageError).toBeNull()
    expect(vm.selectedFile).toBeTruthy()
  })

  it('does not validate page count in create mode for multi-page PDF', async () => {
    const { wrapper } = mountPageForm({ isEditMode: false })
    await flushPromises()

    const multiPageFile = makeMockFile('multi.pdf', 3)

    // FileReader should NOT be called because create mode skips validation
    const readSpy = vi.fn()
    const originalFileReader = window.FileReader
    window.FileReader = vi.fn().mockImplementation(() => ({
      readAsArrayBuffer: readSpy,
      onload: null,
    }))

    const input = wrapper.find('#file')
    Object.defineProperty(input.element, 'files', {
      value: [multiPageFile],
      configurable: true,
    })
    await input.trigger('change')
    await flushPromises()

    window.FileReader = originalFileReader

    expect(readSpy).not.toHaveBeenCalled()
    expect(wrapper.vm.filePageError).toBeNull()
    expect(wrapper.vm.selectedFile).toBeTruthy()
  })
})

describe('PageForm – restriction file controls', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.URL.createObjectURL = vi.fn(() => 'blob:preview')
    global.URL.revokeObjectURL = vi.fn()
  })

  it('rotates and deletes an existing restriction file before submit', async () => {
    pageService.getPage.mockResolvedValueOnce({
      name: 'Restricted Page',
      description: '',
      page: '',
      comment: '',
      restriction_id: 'r1',
      workstatus_id: null,
      location_file: 'some/file.pdf',
      current_file: 'some/current.pdf',
      restriction_file: 'some/restriction.pdf',
      rotation: 0,
      rotation_restriction: 90,
      record_title: 'Record Title',
      record_signature: 'REC-1',
      order_by: 1,
    })

    const { wrapper } = mountPageForm({ isEditMode: true })
    await flushPromises()

    expect(wrapper.text()).toContain('Remove restriction file')
    expect(wrapper.text()).toContain('Restriction rotation: 90°')

    const restrictionRotationButtons = wrapper.findAll('.restriction-rotation-group button')
    await restrictionRotationButtons[1].trigger('click')

    const restrictionDeleteLabel = wrapper
      .findAll('label.checkbox-label')
      .find((label) => label.text().includes('Remove restriction file'))

    await restrictionDeleteLabel.find('input').setValue(true)
    await wrapper.find('form.page-form').trigger('submit.prevent')
    await flushPromises()

    expect(pageService.updatePage).toHaveBeenCalledWith(
      'p-1',
      expect.objectContaining({
        rotation_restriction: 180,
        delete_restriction_file: true,
      }),
    )
  })
})

describe('PageForm – edit navigation and unsaved changes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.URL.createObjectURL = vi.fn(() => 'blob:thumbnail')
    global.URL.revokeObjectURL = vi.fn()
  })

  it('renders previous/next navigation both above and below the form in edit mode', async () => {
    const { wrapper } = mountPageForm({ isEditMode: true })
    await flushPromises()

    const previousButtons = wrapper.findAll('button').filter((button) => button.text() === 'Previous page')
    const nextButtons = wrapper.findAll('button').filter((button) => button.text() === 'Next page')

    expect(previousButtons).toHaveLength(2)
    expect(nextButtons).toHaveLength(2)
    expect(wrapper.text()).toContain('Page 1 of 2')
  })

  it('navigates to the next page immediately when there are no unsaved changes', async () => {
    const { wrapper, routerPush } = mountPageForm({ isEditMode: true })
    await flushPromises()

    await wrapper.vm.navigateToAdjacentPage(1)

    expect(routerPush).toHaveBeenCalledWith('/records/rec-1/pages/p-2/edit')
    expect(wrapper.vm.showUnsavedChangesDialog).toBe(false)
  })

  it('prompts for save or discard before switching pages when the form is dirty', async () => {
    const { wrapper, routerPush } = mountPageForm({ isEditMode: true })
    await flushPromises()

    await wrapper.find('#name').setValue('Changed Page Name')
    await wrapper.vm.navigateToAdjacentPage(1)

    expect(routerPush).not.toHaveBeenCalled()
    expect(wrapper.vm.showUnsavedChangesDialog).toBe(true)
    expect(wrapper.vm.pendingNavigationTarget).toBe('/records/rec-1/pages/p-2/edit')
    expect(wrapper.text()).toContain('There are unsaved changes on this page. Do you want to save them before leaving edit mode?')
  })

  it('saves and continues when the user confirms the unsaved changes dialog', async () => {
    const { wrapper, routerPush } = mountPageForm({ isEditMode: true })
    await flushPromises()

    await wrapper.find('#name').setValue('Changed Page Name')
    await wrapper.vm.navigateToAdjacentPage(1)
    await wrapper.vm.saveAndContinueNavigation()

    expect(pageService.updatePage).toHaveBeenCalledTimes(1)
    expect(pageService.updatePage).toHaveBeenCalledWith(
      'p-1',
      expect.objectContaining({
        name: 'Changed Page Name',
      }),
    )
    expect(routerPush).toHaveBeenCalledWith('/records/rec-1/pages/p-2/edit')
    expect(wrapper.vm.showUnsavedChangesDialog).toBe(false)
  })

  it('discards changes and continues when requested', async () => {
    const { wrapper, routerPush } = mountPageForm({ isEditMode: true })
    await flushPromises()

    await wrapper.find('#name').setValue('Changed Page Name')
    await wrapper.vm.navigateToAdjacentPage(1)
    await wrapper.vm.discardPendingNavigation()
    await flushPromises()

    expect(pageService.updatePage).not.toHaveBeenCalled()
    expect(routerPush).toHaveBeenCalledWith('/records/rec-1/pages/p-2/edit')
    expect(wrapper.vm.showUnsavedChangesDialog).toBe(false)
  })
})
