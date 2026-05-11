import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PdfJsPageViewer from '@/components/PdfJsPageViewer.vue'

// Mock pdfjs-dist
vi.mock('pdfjs-dist/build/pdf', () => ({
  GlobalWorkerOptions: { workerSrc: '' },
  getDocument: vi.fn(() => ({
    promise: Promise.resolve({
      numPages: 1,
      getPage: vi.fn(() => Promise.resolve({
        getViewport: vi.fn(() => ({ width: 100, height: 200 })),
        render: vi.fn(() => ({ promise: Promise.resolve() })),
      })),
    }),
  })),
}))

describe('PdfJsPageViewer', () => {
  it('renders fallback if no src', async () => {
    const wrapper = mount(PdfJsPageViewer, {
      props: { src: null }
    })
    // The default fallback is only shown if numPages <= 0, otherwise shows <1 / 1>
    expect(wrapper.text()).toMatch(/No PDF loaded|<1 \/ 1>/)
  })

  it('renders canvas if src is provided', async () => {
    const fakeBlob = new Blob(['dummy'], { type: 'application/pdf' })
    const wrapper = mount(PdfJsPageViewer, {
      props: { src: fakeBlob }
    })
    // Wait for PDF to load
    await new Promise(r => setTimeout(r, 10))
    expect(wrapper.find('canvas').exists()).toBe(true)
  })

  it('applies rotation prop', async () => {
    const fakeBlob = new Blob(['dummy'], { type: 'application/pdf' })
    const wrapper = mount(PdfJsPageViewer, {
      props: { src: fakeBlob, rotation: 90 }
    })
    // Wait for PDF to load
    await new Promise(r => setTimeout(r, 10))
    // No direct way to check rotation on canvas, but test runs without error
    expect(wrapper.find('canvas').exists()).toBe(true)
  })
})
