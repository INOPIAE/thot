<template>
  <div class="page-detail-container">
    <div class="page-header">
      <h1>{{ $t('pages.pageDetail') }}</h1>
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

export default {
  name: 'PageDetail',
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
