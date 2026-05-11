<template>
  <div class="pages-gallery-container">
    <!-- Header -->
    <div class="gallery-header">
      <div class="header-title">
        <router-link :to="`/records`" class="btn btn-light">
          {{ $t('common.back') }}
        </router-link>
        <button
          class="btn btn-success"
          @click="downloadCombinedPdf"
          :disabled="loadingCombinedPdf || pages.length === 0"
          :title="$t('pages.downloadAllPagesAsPdf')"
        >
          {{ loadingCombinedPdf ? $t('common.loading') + '...' : $t('pages.downloadCombinedPdf') }}
        </button>
        <div>
          <h1>{{ $t('pages.galleryTitle') }}: {{ recordTitle }}</h1>
          <div v-if="selectedPage && selectedPage.pdf_public_url" class="citation-link citation-link-row">
            <span style="margin-right: 0.5rem;">{{ $t('records.citationLink') }}</span>
            <a
              :href="selectedPage.pdf_public_url"
              target="_blank"
              rel="noopener"
              class="citation-link-url"
            >
              {{ selectedPage.pdf_public_url }}
            </a>
            <button class="btn btn-secondary btn-sm" @click="copyCitationLink" style="margin-left: 0.5rem;">
              {{ $t('records.citationLinkCopy') }}
            </button>
          </div>
        </div>
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
                :style="rotationStyle(page)"
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
            <div class="rotation-indicator" v-if="typeof page.rotation === 'number'">
              {{ $t('pages.rotation') }}: {{ page.rotation }}°
            </div>
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

            <div v-else-if="pdfBlob" class="pdf-viewer-container">
              <PdfJsPageViewer :src="pdfBlob" :rotation="selectedPage.rotation || 0" />
            </div>
          </div>
          <div v-else class="no-pdf">
            <p>{{ $t('pages.pdfLoadError') }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


<script>
import PdfJsPageViewer from '@/components/PdfJsPageViewer.vue'
import { useAuthStore } from '@/stores/auth'
import { recordService } from '@/services/record'
import { pageService } from '@/services/page'

export default {
  name: 'RecordPagesGallery',
  components: { PdfJsPageViewer },
  data() {
    return {
      authStore: useAuthStore(),
      pages: [],
      selectedPageId: null,
      selectedPage: null,
      recordTitle: '',
      loading: false,
      loadingPdf: false,
      loadingCombinedPdf: false,
      loadingThumbnails: {},
      error: null,
      thumbnailUrls: {},
      pdfBlob: null,
      showThumbnails: true,
    }
  },
  computed: {
    recordId() {
      return this.$route.params.recordId
    },
    canManagePages() {
      return this.authStore.hasRole('admin') ||
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
    this.pdfBlob = null
  },
  beforeUnmount() {
    // Clean up all blob URLs
    Object.values(this.thumbnailUrls).forEach(url => {
      if (url) URL.revokeObjectURL(url)
    })
    this.pdfBlob = null
  },
  methods: {
    rotationStyle(page) {
      if (page && typeof page.rotation === 'number' && [0,90,180,270].includes(page.rotation) && page.rotation !== 0) {
        return `transform: rotate(${page.rotation}deg); transition: transform 0.2s;`;
      }
      return '';
    },
    copyCitationLink() {
      if (this.selectedPage && this.selectedPage.pdf_public_url) {
        navigator.clipboard.writeText(this.selectedPage.pdf_public_url)
          .then(() => {
            this.$toast?.success?.(this.$t('common.copied')) || alert(this.$t('common.copied'))
          })
          .catch(() => {
            this.$toast?.error?.(this.$t('common.copyError')) || alert(this.$t('common.copyError'))
          })
      }
    },
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
        // Use backend-configured default limit if available
        let limit = 100;
        if (this.$pinia?.state?.app?.appConfig?.itemsPerPageDefault) {
          limit = this.$pinia.state.app.appConfig.itemsPerPageDefault;
        }
        const response = await pageService.listPages({
          record_id: this.recordId,
          limit,
        })
        // Handle both direct array and paginated response
        let pages = Array.isArray(response) ? response : (response.items || [])
        // Sort by order_by (ascending, fallback to name)
        this.pages = pages.slice().sort((a, b) => {
          if (a.order_by != null && b.order_by != null) {
            return a.order_by - b.order_by
          } else if (a.order_by != null) {
            return -1
          } else if (b.order_by != null) {
            return 1
          } else {
            return (a.name || '').localeCompare(b.name || '')
          }
        })
        
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
      this.pdfBlob = null

      // Load PDF for selected page
      if (this.selectedPage && this.selectedPage.location_file) {
        await this.loadPdf(pageId)
      }
    },

    async loadPdf(pageId) {
      this.loadingPdf = true
      try {
        const blob = await pageService.getViewPdf(pageId)
        this.pdfBlob = blob
      } catch (err) {
        console.error('Error loading PDF:', err)
        this.pdfBlob = null
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
        let filename = `${(this.selectedPage.name || 'page').replace(/\s+/g, '_')}.pdf`
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

    async downloadCombinedPdf() {
      if (!this.recordId) {
        return
      }

      this.loadingCombinedPdf = true
      try {
        const { blob, contentDisposition } = await recordService.downloadCombinedPdf(this.recordId)
        
        // Extract filename from content-disposition or use record title
        let filename = `${(this.recordTitle || 'record').replace(/\s+/g, '_')}.pdf`
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
        console.error('Error downloading combined PDF:', err)
        alert(this.$t('pages.downloadCombinedError'))
      } finally {
        this.loadingCombinedPdf = false
      }
    },

    toggleThumbnails() {
      this.showThumbnails = !this.showThumbnails
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
  .citation-link {
    margin-top: 0.5rem;
  }

  .citation-link-row {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
  }

  .citation-link-url {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: left;
  }
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
  .pdf-viewer-rotated {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: auto;
    background: #222;
  }
  .pdf-embed {
    width: 100%;
    height: 100%;
    max-width: 100vw;
    max-height: 100vh;
    object-fit: contain;
    background: #fff;
  }
</style>
