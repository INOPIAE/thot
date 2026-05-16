<template>
  <div class="page-detail-container">
    <div class="page-header">
      <h1>{{ $t('pages.pageDetail') }}</h1>
      <div class="header-actions">
        <router-link
          :to="pageViewerRoute"
          class="btn btn-secondary"
        >
          {{ $t('pages.openPdfViewer') }}
        </router-link>
        <router-link
          v-if="canEditPage"
          :to="pageEditRoute"
          class="btn btn-primary"
        >
          {{ $t('common.edit') }}
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

    <!-- Page Details -->
    <div
      v-if="!loading && page"
      class="page-details"
    >
      <div class="detail-card">
        <div class="card-header">
          <h2>{{ page.name }}</h2>
        </div>
        
        <div class="card-body">
          <!-- Record Information -->
          <div class="detail-section">
            <h3>{{ $t('pages.recordInfo') }}</h3>
            <div class="detail-row">
              <label>{{ $t('records.title') }}:</label>
              <span>{{ page.record_title || '-' }}</span>
            </div>
            <div class="detail-row">
              <label>{{ $t('records.signature') }}:</label>
              <span>{{ page.record_signature || '-' }}</span>
            </div>
          </div>

          <!-- Page Information -->
          <div class="detail-section">
            <h3>{{ $t('pages.pageInformation') }}</h3>
            
            <div
              v-if="page.description"
              class="detail-row"
            >
              <label>{{ $t('pages.description') }}:</label>
              <div class="detail-text">{{ page.description }}</div>
            </div>

            <div
              v-if="page.page"
              class="detail-row"
            >
              <label>{{ $t('pages.pageContent') }}:</label>
              <div class="detail-text detail-content">{{ page.page }}</div>
            </div>

            <div
              v-if="page.comment"
              class="detail-row"
            >
              <label>{{ $t('pages.comment') }}:</label>
              <div class="detail-text">{{ page.comment }}</div>
            </div>
          </div>

          <!-- File Information -->
          <div class="detail-section">
            <h3>{{ $t('pages.fileInformation') }}</h3>
            <div class="detail-row">
              <label>{{ $t('pages.pdfFile') }}:</label>
              <span>{{ page.location_file ? $t('common.yes') : $t('common.no') }}</span>
            </div>
            <div
              v-if="page.location_file"
              class="detail-row"
            >
              <label>{{ $t('pages.filePath') }}:</label>
              <span class="file-path">{{ page.location_file }}</span>
            </div>
          </div>

          <!-- Metadata -->
          <div class="detail-section">
            <h3>{{ $t('pages.metadata') }}</h3>
            
            <div class="detail-row">
              <label>{{ $t('pages.restriction') }}:</label>
              <span class="badge badge-info">{{ page.restriction || '-' }}</span>
            </div>

            <div
              v-if="page.workstatus"
              class="detail-row"
            >
              <label>{{ $t('pages.workstatus') }}:</label>
              <span class="badge badge-secondary">{{ page.workstatus }}</span>
            </div>

            <div
              v-if="page.created_on"
              class="detail-row"
            >
              <label>{{ $t('pages.createdOn') }}:</label>
              <span>{{ formatDate(page.created_on) }}</span>
            </div>

            <div
              v-if="page.last_modified_on"
              class="detail-row"
            >
              <label>{{ $t('pages.modifiedOn') }}:</label>
              <span>{{ formatDate(page.last_modified_on) }}</span>
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

export default {
  name: 'PageDetail',
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
    pageViewerRoute() {
      return {
        path: `/records/${this.recordId}/pages/${this.pageId}/viewer`,
        query: this.pageListQuery,
      }
    },
    pageEditRoute() {
      return {
        path: `/records/${this.recordId}/pages/${this.pageId}/edit`,
        query: this.pageListQuery,
      }
    },
    canEditPage() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_page')
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
  methods: {
    async loadPage() {
      this.loading = true
      this.error = null
      try {
        this.page = await pageService.getPage(this.pageId)
      } catch (err) {
        console.error('Error loading page:', err)
        this.error = err.message || this.$t('pages.loadError')
      } finally {
        this.loading = false
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
  },
}
</script>

<style scoped>
.page-detail-container {
  padding: 2rem;
  max-width: 1000px;
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

.page-details {
  margin-top: 1.5rem;
}

.detail-card {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card-header {
  background: #f8f9fa;
  padding: 1.5rem;
  border-bottom: 1px solid #ddd;
}

.card-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
}

.card-body {
  padding: 1.5rem;
}

.detail-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #eee;
}

.detail-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.detail-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  color: #495057;
  font-weight: 600;
}

.detail-row {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
  align-items: start;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-row label {
  font-weight: 600;
  color: #555;
}

.detail-row span {
  color: #333;
}

.detail-text {
  white-space: pre-wrap;
  line-height: 1.6;
  color: #333;
}

.detail-content {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  max-height: 400px;
  overflow-y: auto;
}

.file-path {
  font-family: monospace;
  background: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .detail-row {
    grid-template-columns: 1fr;
  }

  .detail-row label {
    margin-bottom: 0.25rem;
  }
}
</style>
