<template>
  <div class="page-viewer-container">
    <div class="page-header">
      <h1>{{ $t('pages.pdfViewer') }}</h1>
      <div class="header-actions">
        <router-link
          :to="`/records/${recordId}/pages/${pageId}/edit`"
          class="btn btn-primary"
        >
          {{ $t('common.edit') }}
        </router-link>
        <router-link
          :to="`/records/${recordId}/pages`"
          class="btn btn-secondary"
        >
          {{ $t('common.back') }}
        </router-link>
      </div>
    </div>

    <!-- Loading State -->
    <div
      v-if="loading"
      class="loading"
    >
      {{ $t('common.loading') }}
    </div>

    <!-- Error State -->
    <div
      v-if="error"
      class="alert alert-danger"
    >
      {{ error }}
    </div>

    <!-- Page Content -->
    <div
      v-if="!loading && page"
      class="page-viewer-content"
    >
      <!-- Left Panel: Page Information -->
      <div class="info-panel">
        <div class="info-card">
          <h2>{{ page.name }}</h2>
          
          <!-- Record Information -->
          <div class="info-section">
            <h3>{{ $t('pages.recordInfo') }}</h3>
            <div class="info-item">
              <label>{{ $t('records.title') }}:</label>
              <span>{{ page.record_title || '-' }}</span>
            </div>
            <div class="info-item">
              <label>{{ $t('records.signature') }}:</label>
              <span>{{ page.record_signature || '-' }}</span>
            </div>
          </div>

          <!-- Page Information -->
          <div class="info-section">
            <h3>{{ $t('pages.pageInformation') }}</h3>
            
            <div
              v-if="page.description"
              class="info-item"
            >
              <label>{{ $t('pages.description') }}:</label>
              <div class="info-text">{{ page.description }}</div>
            </div>

            <div
              v-if="page.page"
              class="info-item"
            >
              <label>{{ $t('pages.pageContent') }}:</label>
              <div class="info-text scrollable">{{ page.page }}</div>
            </div>

            <div
              v-if="page.comment"
              class="info-item"
            >
              <label>{{ $t('pages.comment') }}:</label>
              <div class="info-text">{{ page.comment }}</div>
            </div>
          </div>

          <!-- Metadata -->
          <div class="info-section">
            <h3>{{ $t('pages.metadata') }}</h3>
            
            <div class="info-item">
              <label>{{ $t('pages.restriction') }}:</label>
              <span class="badge badge-info">{{ page.restriction || '-' }}</span>
            </div>

            <div
              v-if="page.workstatus"
              class="info-item"
            >
              <label>{{ $t('pages.workstatus') }}:</label>
              <span class="badge badge-secondary">{{ page.workstatus }}</span>
            </div>

            <div
              v-if="page.created_on"
              class="info-item"
            >
              <label>{{ $t('pages.createdOn') }}:</label>
              <span>{{ formatDate(page.created_on) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Panel: PDF Display -->
      <div class="pdf-panel">
        <div
          v-if="!page.location_file"
          class="no-pdf"
        >
          <p>{{ $t('pages.noPdfAvailable') }}</p>
        </div>

        <div
          v-else
          class="pdf-display"
        >
          <!-- Thumbnail -->
          <div class="pdf-thumbnail-section">
            <h3>{{ $t('pages.thumbnail') }}</h3>
            <div class="thumbnail-container">
              <iframe
                :src="pdfThumbnailUrl"
                class="pdf-thumbnail"
                :title="$t('pages.pdfThumbnail')"
              />
              <div class="thumbnail-overlay">
                <a
                  :href="pdfViewerUrl"
                  target="_blank"
                  class="btn btn-sm btn-light"
                >
                  {{ $t('pages.openInNewTab') }}
                </a>
              </div>
            </div>
          </div>

          <!-- Full PDF Viewer -->
          <div class="pdf-viewer-section">
            <h3>{{ $t('pages.pdfDocument') }}</h3>
            <div class="pdf-viewer-controls">
              <button
                type="button"
                class="btn btn-sm btn-primary"
                @click="downloadWatermarkedPdf"
              >
                {{ $t('pages.downloadPdf') }}
              </button>
              <a
                :href="pdfViewerUrl"
                target="_blank"
                class="btn btn-sm btn-secondary"
              >
                {{ $t('pages.openInNewTab') }}
              </a>
            </div>
            <div class="pdf-viewer-container">
              <iframe
                :src="pdfViewerUrl"
                class="pdf-viewer"
                :title="page.name"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { pageService } from '@/services/page'
import { useAppStore } from '@/stores/app'

export default {
  name: 'PageViewer',
  data() {
    return {
      page: null,
      loading: false,
      error: null,
      pdfBlobUrl: null,
      thumbnailBlobUrl: null,
    }
  },
  computed: {
    recordId() {
      return this.$route.params.recordId
    },
    pageId() {
      return this.$route.params.pageId
    },
    pdfThumbnailUrl() {
      return this.thumbnailBlobUrl
    },
    pdfViewerUrl() {
      return this.pdfBlobUrl
    },
  },
  mounted() {
    this.loadPage()
  },
  beforeUnmount() {
    // Clean up blob URLs to avoid memory leaks
    if (this.pdfBlobUrl) {
      URL.revokeObjectURL(this.pdfBlobUrl)
    }
    if (this.thumbnailBlobUrl) {
      URL.revokeObjectURL(this.thumbnailBlobUrl)
    }
  },
  methods: {
    async loadPage() {
      this.loading = true
      this.error = null
      try {
        this.page = await pageService.getPage(this.pageId)
        
        // Load PDF and thumbnail with watermarks if file exists
        if (this.page && this.page.location_file) {
          await Promise.all([
            this.loadPdfBlob(),
            this.loadThumbnailBlob(),
          ])
        }
      } catch (err) {
        console.error('Error loading page:', err)
        this.error = err.message || this.$t('pages.loadError')
      } finally {
        this.loading = false
      }
    },
    async loadPdfBlob() {
      try {
        const blob = await pageService.getViewPdf(this.pageId)
        // Revoke old URL if exists
        if (this.pdfBlobUrl) {
          URL.revokeObjectURL(this.pdfBlobUrl)
        }
        this.pdfBlobUrl = URL.createObjectURL(blob)
      } catch (err) {
        console.error('Error loading PDF blob:', err)
      }
    },
    async loadThumbnailBlob() {
      try {
        const blob = await pageService.getThumbnail(this.pageId, 300)
        // Revoke old URL if exists
        if (this.thumbnailBlobUrl) {
          URL.revokeObjectURL(this.thumbnailBlobUrl)
        }
        this.thumbnailBlobUrl = URL.createObjectURL(blob)
      } catch (err) {
        console.error('Error loading thumbnail blob:', err)
      }
    },
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleDateString(this.$i18n.locale, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    },
    async downloadWatermarkedPdf() {
      if (!this.page) return

      try {
        const { blob, contentDisposition } = await pageService.downloadWatermarkedPdf(this.pageId)
        const fileName = this.extractFilename(contentDisposition)
          || `${(this.page.name || 'page').replace(/\s+/g, '_')}_watermarked.pdf`

        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = fileName
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } catch (err) {
        console.error('Error downloading watermarked PDF:', err)
        const fallbackMessage = this.$t('pages.loadError')
        this.error = err?.detail || err?.message || fallbackMessage
      }
    },
    extractFilename(contentDisposition) {
      if (!contentDisposition) return null
      const match = contentDisposition.match(/filename="?([^";]+)"?/i)
      return match ? match[1] : null
    },
  },
}
</script>

<style scoped>
.page-viewer-container {
  padding: 2rem;
  max-width: 1800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-header h1 {
  margin: 0;
  font-size: 1.8rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.loading {
  text-align: center;
  padding: 3rem;
  font-size: 1.1rem;
  color: #666;
}

.alert {
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
}

.alert-danger {
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
}

.page-viewer-content {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 2rem;
}

/* Left Panel - Info */
.info-panel {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.info-card {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.info-card h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.5rem;
  color: #333;
  padding-bottom: 1rem;
  border-bottom: 2px solid #007bff;
}

.info-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.info-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.info-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #495057;
  font-weight: 600;
}

.info-item {
  margin-bottom: 0.75rem;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-item label {
  display: block;
  font-weight: 600;
  color: #555;
  margin-bottom: 0.25rem;
}

.info-item span {
  color: #333;
}

.info-text {
  white-space: pre-wrap;
  line-height: 1.6;
  color: #333;
  background: #f8f9fa;
  padding: 0.75rem;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.info-text.scrollable {
  max-height: 200px;
  overflow-y: auto;
}

.badge {
  display: inline-block;
  padding: 0.35rem 0.65rem;
  font-size: 0.875rem;
  font-weight: 600;
  line-height: 1;
  color: #fff;
  text-align: center;
  white-space: nowrap;
  vertical-align: baseline;
  border-radius: 0.25rem;
}

.badge-info {
  background-color: #17a2b8;
}

.badge-secondary {
  background-color: #6c757d;
}

/* Right Panel - PDF Display */
.pdf-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.no-pdf {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 3rem;
  text-align: center;
  color: #666;
}

.pdf-display {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.pdf-thumbnail-section,
.pdf-viewer-section {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.pdf-thumbnail-section h3,
.pdf-viewer-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  color: #333;
  font-weight: 600;
}

.thumbnail-container {
  position: relative;
  width: 100%;
  height: 300px;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
  background: #f5f5f5;
}

.pdf-thumbnail {
  width: 100%;
  height: 100%;
  border: none;
  pointer-events: none;
}

.thumbnail-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.thumbnail-container:hover .thumbnail-overlay {
  opacity: 1;
}

.pdf-viewer-controls {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.pdf-viewer-container {
  width: 100%;
  height: 70vh;
  min-height: 520px;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow-y: auto;
  overflow-x: hidden;
  background: #525252;
}

.pdf-viewer {
  width: 100%;
  height: 100%;
  border: none;
}

.btn {
  display: inline-block;
  padding: 0.5rem 1rem;
  font-size: 1rem;
  font-weight: 400;
  text-align: center;
  text-decoration: none;
  vertical-align: middle;
  cursor: pointer;
  user-select: none;
  border: 1px solid transparent;
  border-radius: 0.25rem;
  transition: all 0.15s ease-in-out;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}

.btn-primary {
  color: #fff;
  background-color: #007bff;
  border-color: #007bff;
}

.btn-primary:hover {
  background-color: #0056b3;
  border-color: #004085;
}

.btn-secondary {
  color: #fff;
  background-color: #6c757d;
  border-color: #6c757d;
}

.btn-secondary:hover {
  background-color: #5a6268;
  border-color: #545b62;
}

.btn-light {
  color: #212529;
  background-color: #f8f9fa;
  border-color: #f8f9fa;
}

.btn-light:hover {
  background-color: #e2e6ea;
  border-color: #dae0e5;
}

@media (max-width: 1200px) {
  .page-viewer-content {
    grid-template-columns: 350px 1fr;
  }
}

@media (max-width: 992px) {
  .page-viewer-content {
    grid-template-columns: 1fr;
  }

  .info-panel {
    max-height: none;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .pdf-viewer-container {
    height: 600px;
  }

  .thumbnail-container {
    height: 200px;
  }
}
</style>
