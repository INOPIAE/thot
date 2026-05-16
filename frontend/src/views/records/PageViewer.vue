<template>
  <div class="page-viewer-container">
    <div class="page-header">
      <h1>{{ $t('pages.pdfViewer') }}</h1>
      <div class="header-actions">
        <router-link
          v-if="canEditPage || canManageFile"
          :to="pageEditRoute"
          class="btn btn-primary"
        >
          {{ canEditPage ? $t('common.edit') : $t('pages.uploadFile') }}
        </router-link>
        <router-link
          :to="backToListUrl"
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
              <img
                v-if="pdfThumbnailUrl"
                :src="pdfThumbnailUrl"
                :style="rotationStyle"
                class="pdf-thumbnail"
                :alt="$t('pages.pdfThumbnail')"
              />
              <span v-else>{{ $t('pages.noThumbnail') }}</span>
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
            <div class="rotation-indicator" v-if="page && typeof page.rotation === 'number'">
              {{ $t('pages.rotation') }}: {{ page.rotation }}°
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
              <PdfJsPageViewer
                v-if="pdfBlobUrl"
                :src="pdfBlobUrl"
                :rotation="page?.rotation || 0"
                style="width:100%;max-width:900px;margin:auto;"
              />
              <div v-else class="no-pdf">
                <p>{{ $t('pages.noPdfAvailable') }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { pageService } from '@/services/page'
import { useAuthStore } from '@/stores/auth'
import PdfJsPageViewer from '@/components/PdfJsPageViewer.vue'

export default {
  name: 'PageViewer',
  components: { PdfJsPageViewer },
  setup() {
    return {
      authStore: useAuthStore(),
    }
  },
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
    pageListQuery() {
      const query = {}
      const routeQuery = this.$route.query || {}

      if (typeof routeQuery.page === 'string' && routeQuery.page) {
        query.page = routeQuery.page
      }

      if (typeof routeQuery.pageSize === 'string' && routeQuery.pageSize) {
        query.pageSize = routeQuery.pageSize
      }

      if (typeof routeQuery.search === 'string' && routeQuery.search) {
        query.search = routeQuery.search
      }

      return query
    },
    pageEditRoute() {
      return {
        path: `/records/${this.recordId}/pages/${this.pageId}/edit`,
        query: this.pageListQuery,
      }
    },
    pdfThumbnailUrl() {
      return this.thumbnailBlobUrl
    },
    pdfViewerUrl() {
      return this.pdfBlobUrl
    },
    rotationStyle() {
      const rotation = this.page?.rotation
      if (typeof rotation !== 'number' || rotation === 0) {
        return ''
      }
      return `transform: rotate(${rotation}deg);`
    },
    canEditPage() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_page')
    },
    canManageFile() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_scan')
    },
    canManagePages() {
      return this.authStore.hasRole('admin')
        || this.authStore.hasRole('user_scan')
        || this.authStore.hasRole('user_page')
    },
    backToListUrl() {
      if (this.canManagePages) {
        return {
          path: `/records/${this.recordId}/pages`,
          query: this.pageListQuery,
        }
      }
      return `/records/${this.recordId}/pages-gallery`
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
