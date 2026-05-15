<template>
  <div class="pdfjs-viewer-wrapper">
    <canvas
      v-if="numPages > 0"
      ref="pdfCanvas"
      class="pdfjs-canvas"
    ></canvas>
    <div v-else class="pdf-fallback">No PDF loaded (numPages: {{ numPages }})</div>
    <div class="pdfjs-controls">
      <button @click="prevPage" :disabled="pageNum <= 1">&lt;</button>
      <span>{{ pageNum }} / {{ numPages }}</span>
      <button @click="nextPage" :disabled="pageNum >= numPages">&gt;</button>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted, nextTick } from 'vue'
import * as pdfjsLib from 'pdfjs-dist/build/pdf'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
// Use ESM worker for Vite compatibility
pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl

export default {
  name: 'PdfJsPageViewer',
  props: {
    src: { type: [String, Blob, ArrayBuffer], required: false, default: null },
    rotation: { type: Number, default: 0 }
  },
  setup(props) {
    let pdfDoc = null
    const pageNum = ref(1)
    const numPages = ref(0)
    const pdfCanvas = ref(null)
    let loadId = 0

    const renderPage = async () => {
      const myLoadId = loadId
      let docAtStart = pdfDoc
      if (!docAtStart) return
      let page
      try {
        page = await docAtStart.getPage(pageNum.value)
      } catch (err) {
        console.log('renderPage: getPage failed', err)
        return
      }
      if (myLoadId !== loadId || !pdfDoc || pdfDoc !== docAtStart) {
        console.log('renderPage: aborted due to doc change')
        return
      }
      const canvas = pdfCanvas.value
      if (!canvas) {
        console.log('renderPage: pdfCanvas.value is null')
        return
      }
      try {
        const viewport = page.getViewport({ scale: 1, rotation: props.rotation })
        const context = canvas.getContext('2d')
        if (!context) {
          return
        }
        canvas.width = viewport.width
        canvas.height = viewport.height
        context.clearRect(0, 0, canvas.width, canvas.height)
        // console.log('renderPage: set canvas size', canvas.width, canvas.height, 'DOM:', pdfCanvas.value?.width, pdfCanvas.value?.height)
        await page.render({ canvasContext: context, viewport }).promise
          .then(() => {
            // console.log('renderPage: render promise resolved for page', pageNum.value)
          })
          .catch((err) => {
            console.error('renderPage: render promise rejected', err)
          })
      } catch (err) {
        console.log('renderPage: rendered page', pageNum.value)
        // eslint-disable-next-line no-console
        console.error('PDF render error:', err)
      }
    }

    const loadPdf = async () => {
      try {
        if (!props.src) {
          numPages.value = 0
          return
        }
        loadId++
        pdfDoc = null // Reset before loading new doc
        pageNum.value = 1
        let loadingTask
        if (typeof props.src === 'string') {
          // Try to fetch as URL (could be a remote URL or object URL)
          // For object URLs, fetch and convert to ArrayBuffer
          if (props.src.startsWith('blob:')) {
            const response = await fetch(props.src)
            const blob = await response.blob()
            const arrayBuffer = await blob.arrayBuffer()
            loadingTask = pdfjsLib.getDocument({ data: arrayBuffer })
          } else {
            loadingTask = pdfjsLib.getDocument({ url: props.src })
          }
        } else if (props.src instanceof Blob) {
          const arrayBuffer = await props.src.arrayBuffer()
          loadingTask = pdfjsLib.getDocument({ data: arrayBuffer })
        } else if (props.src instanceof ArrayBuffer) {
          loadingTask = pdfjsLib.getDocument({ data: props.src })
        } else {
          throw new Error('Unsupported src type for PDF viewer')
        }
        pdfDoc = await loadingTask.promise
        numPages.value = pdfDoc.numPages
        // console.log('loadPdf: loaded PDF with', numPages.value, 'pages')
        await nextTick()
        await renderPage()
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('PDF load error:', err)
        pdfDoc = null
      }
    }

    // Watchers for src, rotation, and pageNum
    watch(() => props.src, loadPdf)
    watch(() => props.rotation, renderPage)
    watch(pageNum, renderPage)

    const prevPage = async () => {
      if (pageNum.value > 1) {
        pageNum.value--
        await renderPage()
      }
    }
    const nextPage = async () => {
      if (pageNum.value < numPages.value) {
        pageNum.value++
        await renderPage()
      }
    }

    onMounted(loadPdf)

    return { pdfCanvas, pageNum, numPages, prevPage, nextPage }
  }
}
</script>

<style scoped>
.pdfjs-viewer-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #222;
}
.pdfjs-canvas {
  background: #fff;
  max-width: 100vw;
  max-height: 80vh;
  margin-bottom: 0.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}
.pdfjs-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
  color: #fff;
}
</style>
