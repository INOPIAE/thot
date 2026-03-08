<template>
  <div class="pages-gallery-container">
    <!-- Header -->
    <div class="gallery-header">
      <div class="header-title">
        <router-link :to="`/records`" class="btn btn-light">
          {{ $t('common.back') }}
        </router-link>
        <h1>{{ $t('pages.galleryTitle') }}: {{ recordTitle }}</h1>
      </div>
      <div class="header-actions">
        <button
          class="btn btn-secondary"
          @click="toggleThumbnails"
          :title="showThumbnails ? $t('common.close') : $t('common.open')"
        >
          {{ showThumbnails ? '◄ ' : '► ' }}{{ $t('pages.allPages') }}
        </button>
        <router-link v-if="canManagePages" :to="`/records/${recordId}/pages/new`" class="btn btn-primary">
          {{ $t('pages.createNew') }}
        </router-link>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      {{ $t('common.loading') }}
    </div>

    <!-- Error State -->
    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <!-- Gallery Content -->
    <div v-if="!loading && !error" class="gallery-content" :class="{ 'thumbnails-hidden': !showThumbnails }">
      <!-- Left Panel: Thumbnails List -->
      <div v-show="showThumbnails" class="thumbnails-panel">
        <div v-if="pages.length === 0" class="empty-state">
          <p>{{ $t('pages.noPages') }}</p>
          <router-link v-if="canManagePages" :to="`/records/${recordId}/pages/new`" class="btn btn-primary">
            {{ $t('pages.createNew') }}
          </router-link>
        </div>

        <div v-else class="thumbnails-list">
          <div
            v-for="page in pages"
            :key="page.id"
            :class="['thumbnail-item', { active: selectedPageId === page.id }]"
            @click="selectPage(page.id)"
          >
            <div class="thumbnail-wrapper">
              <img
                v-if="page.location_file && thumbnailUrls[page.id]"
                :src="thumbnailUrls[page.id]"
                :alt="page.name"
                class="thumbnail-image"
                @error="handleThumbnailError(page.id)"
              />
              <div v-else class="thumbnail-placeholder">
                <span>{{ $t('pages.noThumbnail') }}</span>
              </div>
              <div v-if="loadingThumbnails[page.id]" class="thumbnail-loading">
                {{ $t('common.loading') }}...
              </div>
            </div>
            <h3 class="thumbnail-title">{{ page.name }}</h3>
          </div>
        </div>
      </div>

      <!-- Right Panel: PDF Viewer (Full Width) -->
      <div class="detail-panel">
        <div v-if="!selectedPageId" class="no-selection">
          <p>{{ $t('pages.selectPageToView') }}</p>
        </div>

        <div v-else-if="selectedPage" class="page-detail">
          <!-- PDF Controls -->
          <div class="pdf-controls">
            <button
              class="btn btn-primary"
              @click="downloadPdf"
              :disabled="!selectedPage.location_file || loadingPdf"
            >
              {{ $t('pages.downloadPdf') }}
            </button>
          </div>

          <!-- PDF Viewer -->
          <div v-if="selectedPage.location_file" class="pdf-viewer-section">
            <div v-if="loadingPdf" class="loading-pdf">
              {{ $t('common.loading') }} PDF...
            </div>

            <div v-else-if="pdfUrl" class="pdf-viewer-container">
              <embed
                :src="pdfUrl"
                type="application/pdf"
                class="pdf-embed"
              />
            </div>

            <div v-else class="no-pdf">
              <p>{{ $t('pages.pdfLoadError') }}</p>
            </div>
          </div>

          <div v-else class="no-pdf">
            <p>{{ $t('pages.noPdfAvailable') }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { pageService } from '@/services/page'
import { recordService } from '@/services/record'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'RecordPagesGallery',
    setup() {
      return {
        authStore: useAuthStore(),
      }
    },
  data() {
    return {
      pages: [],
      selectedPageId: null,
      selectedPage: null,
      recordTitle: '',
      loading: false,
      loadingPdf: false,
      loadingThumbnails: {},
      error: null,
      thumbnailUrls: {},
      pdfUrl: null,
      showThumbnails: true,
    }
  },
  computed: {
    recordId() {
      return this.$route.params.recordId
    },
    canManagePages() {
      return this.authStore.hasRole('admin') ||
             this.authStore.hasRole('user_record') ||
             this.authStore.hasRole('user_scan') ||
             this.authStore.hasRole('user_page')
    },
  },
  mounted() {
    this.loadRecord()
    this.loadPages()
  },
  beforeUnmount() {
    // Clean up all blob URLs
    Object.values(this.thumbnailUrls).forEach(url => {
      if (url) URL.revokeObjectURL(url)
    })
    if (this.pdfUrl) {
      URL.revokeObjectURL(this.pdfUrl)
    }
  },
  methods: {
    async loadRecord() {
      try {
        const record = await recordService.getRecord(this.recordId)
        this.recordTitle = record.title || this.$t('pages.unknownRecord')
      } catch (err) {
        console.error('Error loading record:', err)
        this.recordTitle = this.$t('pages.unknownRecord')
      }
    },

    async loadPages() {
      this.loading = true
      this.error = null
      try {
        const response = await pageService.listPages({
          record_id: this.recordId,
          limit: 100, // Load all pages for gallery
        })
        // Handle both direct array and paginated response
        this.pages = Array.isArray(response) ? response : (response.items || [])
        
        // Load thumbnails for all pages
        this.pages.forEach(page => {
          if (page.location_file) {
            this.loadThumbnail(page.id)
          }
        })

        // Auto-select first page if available
        if (this.pages.length > 0 && !this.selectedPageId) {
          this.selectPage(this.pages[0].id)
        }
      } catch (err) {
        console.error('Error loading pages:', err)
        this.error = err.message || this.$t('pages.loadError')
      } finally {
        this.loading = false
      }
    },

    async loadThumbnail(pageId) {
      if (this.thumbnailUrls[pageId]) {
        return // Already loaded
      }

      this.loadingThumbnails[pageId] = true
      try {
        const blob = await pageService.getThumbnail(pageId, 200)
        const url = URL.createObjectURL(blob)
        this.thumbnailUrls[pageId] = url
      } catch (err) {
        console.error(`Error loading thumbnail for page ${pageId}:`, err)
        this.thumbnailUrls[pageId] = null
      } finally {
        this.loadingThumbnails[pageId] = false
      }
    },

    async selectPage(pageId) {
      if (this.selectedPageId === pageId) {
        return // Already selected
      }

      this.selectedPageId = pageId
      this.selectedPage = this.pages.find(p => p.id === pageId)

      // Clean up old PDF URL
      if (this.pdfUrl) {
        URL.revokeObjectURL(this.pdfUrl)
        this.pdfUrl = null
      }

      // Load PDF for selected page
      if (this.selectedPage && this.selectedPage.location_file) {
        await this.loadPdf(pageId)
      }
    },

    async loadPdf(pageId) {
      this.loadingPdf = true
      try {
        const blob = await pageService.getViewPdf(pageId)
        this.pdfUrl = URL.createObjectURL(blob)
      } catch (err) {
        console.error('Error loading PDF:', err)
        this.pdfUrl = null
      } finally {
        this.loadingPdf = false
      }
    },

    async downloadPdf() {
      if (!this.selectedPageId || !this.selectedPage) {
        return
      }

      try {
        const { blob, contentDisposition } = await pageService.downloadWatermarkedPdf(this.selectedPageId)
        
        // Extract filename from content-disposition or use page name
        let filename = `${(this.selectedPage.name || 'page').replace(/\s+/g, '_')}_watermarked.pdf`
        if (contentDisposition) {
          const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition)
          if (matches && matches[1]) {
            filename = matches[1].replace(/['"]/g, '')
          }
        }

        // Trigger download
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      } catch (err) {
        console.error('Error downloading PDF:', err)
        alert(this.$t('pages.downloadError'))
      }
    },

    handleThumbnailError(pageId) {
      console.error(`Thumbnail error for page ${pageId}`)
      this.thumbnailUrls[pageId] = null
    },

    truncateText(text, maxLength) {
      if (!text) return ''
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    },
  },
}
</script>

<style scoped>
.pages-gallery-container {
  padding: 1rem;
  max-width: 100%;
  margin: 0 auto;
}

.gallery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e0e0e0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-title h1 {
  margin: 0;
  font-size: 1.75rem;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.loading,
.error {
  text-align: center;
  padding: 2rem;
}

/* Gallery Layout */
.gallery-content {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 0;
  min-height: calc(100vh - 200px);
  max-height: calc(100vh - 200px);
}

/* Left Panel - Thumbnails */
.thumbnails-panel {
  border-right: 1px solid #e0e0e0;
  padding: 1rem;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
  background: #f9f9f9;
}

.empty-state {
  text-align: center;
  padding: 2rem 1rem;
}

.thumbnails-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Right Panel - PDF Detail */
.detail-panel {
  overflow-y: auto;
  max-height: calc(100vh - 200px);
  background: white;
  display: flex;
  flex-direction: column;
}

.thumbnail-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.5rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.thumbnail-item:hover {
  border-color: #007bff;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.1);
}

.thumbnail-item.active {
  border-color: #007bff;
  background: #f0f8ff;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.2);
}

.thumbnail-wrapper {
  position: relative;
  width: 100%;
  height: 140px;
  background: #f5f5f5;
  border-radius: 4px;
  overflow: hidden;
}

.thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #f5f5f5;
  color: #999;
  font-size: 0.75rem;
  text-align: center;
  padding: 0.5rem;
}

.thumbnail-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  font-size: 0.75rem;
  color: #666;
}

.thumbnail-title {
  margin: 0;
  font-size: 0.85rem;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
}

/* Thumbnails Bottom Bar */
.thumbnails-bar {
  background: white;
  border-top: 1px solid #e0e0e0;
  padding: 1rem;
  height: auto;
  max-height: 200px;
  overflow-y: auto;
}

.thumbnails-scroll {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
}

.no-selection {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-size: 1.125rem;
}

.page-detail {
  background: white;
  border-radius: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.pdf-controls {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  gap: 0.5rem;
}

/* PDF Viewer Section */
.pdf-viewer-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  min-height: 0;
}

.loading-pdf {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.pdf-viewer-container {
  flex: 1;
  width: 100%;
  border: none;
  border-radius: 0;
  overflow: hidden;
  min-height: 0;
}

.pdf-viewer {
  width: 100%;
  height: 100%;
  border: none;
}

.pdf-embed {
  width: 100%;
  height: 100%;
  border: none;
}

.no-pdf {
  text-align: center;
  padding: 3rem;
  color: #999;
  background: #f9f9f9;
  border-radius: 0;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Badges */
.badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 4px;
  text-transform: uppercase;
}

.badge-info {
  background: #d1ecf1;
  color: #0c5460;
}

.badge-secondary {
  background: #e2e3e5;
  color: #383d41;
}

/* Buttons */
.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  text-decoration: none;
  display: inline-block;
  transition: all 0.2s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.8125rem;
}

.btn-link {
  background: none;
  color: #007bff;
  text-decoration: none;
}

.btn-link:hover {
  text-decoration: underline;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .gallery-content {
    grid-template-columns: 250px 1fr;
  }

  .thumbnails-panel {
    max-height: calc(100vh - 200px);
  }
}

@media (max-width: 768px) {
  .gallery-content {
    grid-template-columns: 200px 1fr;
  }

  .thumbnails-panel {
    padding: 0.75rem;
  }

  .thumbnail-wrapper {
    height: 120px;
  }

  .pdf-viewer-container {
    height: 100%;
  }
}
</style>
