import { describe, it, expect, beforeEach, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import PageForm from '@/views/records/PageForm.vue'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/services/record', () => ({
  recordService: {
    getRestrictions: vi.fn().mockResolvedValue({ items: [{ id: 'r1', name: 'none' }] }),
    getWorkStatus: vi.fn().mockResolvedValue({ items: [] }),
  },
}))

vi.mock('@/services/page', () => ({
  pageService: {
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
      uploadSinglePageError: 'The selected PDF has multiple pages. Please upload a single-page PDF.',
      noFileSelected: 'No file selected',
      noThumbnail: 'No thumbnail',
      currentFile: 'Current file',
      removeCurrentFile: 'Remove current file',
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

  return mount(PageForm, {
    global: {
      plugins: [i18n, pinia],
      mocks: {
        $route: { params: routeParams },
        $router: { push: vi.fn() },
      },
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
      },
    },
  })
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('PageForm – file upload hints', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows multi-page hint in create mode', async () => {
    const wrapper = mountPageForm({ isEditMode: false })
    await flushPromises()
    expect(wrapper.text()).toContain(
      'Multi-page PDFs will be split into individual page entries automatically.',
    )
  })

  it('does not show single-page-only note in create mode', async () => {
    const wrapper = mountPageForm({ isEditMode: false })
    await flushPromises()
    expect(wrapper.text()).not.toContain(
      'Only single-page PDFs are allowed when replacing a file on an existing page.',
    )
  })

  it('shows single-page-only note in edit mode', async () => {
    const wrapper = mountPageForm({ isEditMode: true })
    await flushPromises()
    expect(wrapper.text()).toContain(
      'Only single-page PDFs are allowed when replacing a file on an existing page.',
    )
  })

  it('does not show multi-page hint in edit mode', async () => {
    const wrapper = mountPageForm({ isEditMode: true })
    await flushPromises()
    expect(wrapper.text()).not.toContain(
      'Multi-page PDFs will be split into individual page entries automatically.',
    )
  })
})

describe('PageForm – file page count validation in edit mode', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows error and clears file when multi-page PDF selected in edit mode', async () => {
    const wrapper = mountPageForm({ isEditMode: true })
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
    const wrapper = mountPageForm({ isEditMode: true })
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
    const wrapper = mountPageForm({ isEditMode: false })
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
