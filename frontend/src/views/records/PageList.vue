<template>
  <div class="pages-container">
    <div class="pages-header">
      <div class="header-title">
        <router-link :to="`/records/${recordId}`" class="btn btn-link">
          {{ $t('common.back') }}
        </router-link>
        <h1>{{ $t('pages.pageListTitle') }}: {{ recordTitle }}</h1>
      </div>
      <div class="header-actions">
        <router-link :to="`/records/${recordId}/pages/new`" class="btn btn-primary">
          {{ $t('pages.createNew') }}
        </router-link>
      </div>
    </div>

    <!-- Search and Filter Section -->
    <div class="pages-search">
      <div class="search-fields">
        <div class="form-group">
          <label for="search-name">{{ $t('pages.pageName') }}</label>
          <input
            id="search-name"
            v-model="searchName"
            type="text"
            class="form-control"
            :placeholder="$t('pages.pageNamePlaceholder')"
            @input="handleSearch"
          />
        </div>

        <div class="form-group">
          <label for="page-size">{{ $t('pages.pageSize') }}</label>
          <select
            id="page-size"
            v-model.number="pageSize"
            class="form-control"
            @change="handlePageSizeChange"
          >
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
          </select>
        </div>

        <button class="btn btn-secondary" @click="resetFilters">
          {{ $t('common.reset') }}
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      {{ $t('common.loading') }}
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="alert alert-success" @click="successMessage = ''">
      {{ successMessage }}
    </div>

    <!-- Error Message -->
    <div v-if="error" class="alert alert-danger" @click="error = ''">
      {{ error }}
    </div>

    <!-- Pages List -->
    <div v-if="!loading && pages.length > 0" class="pages-list">
      <div class="pages-grid">
        <div v-for="page in pages" :key="page.id" class="page-card">
          <div class="page-card-header">
            <h3>{{ page.name }}</h3>
            <div class="page-actions">
              <router-link :to="`/records/${recordId}/pages/${page.id}`" class="btn btn-sm btn-info">
                {{ $t('pages.openOverview') }}
              </router-link>
              <router-link :to="`/records/${recordId}/pages/${page.id}/edit`" class="btn btn-sm btn-secondary">
                {{ $t('common.edit') }}
              </router-link>
              <button class="btn btn-sm btn-danger" @click="handleDelete(page.id)">
                {{ $t('common.delete') }}
              </button>
            </div>
          </div>
          <div class="page-card-body">
            <p v-if="page.description" class="page-description">
              <strong>{{ $t('pages.description') }}:</strong> {{ page.description }}
            </p>
            <p v-if="page.page" class="page-content">
              <strong>{{ $t('pages.pageContent') }}:</strong>
              {{ truncateText(page.page, 150) }}
            </p>
            <p v-if="page.comment" class="page-comment">
              <strong>{{ $t('pages.comment') }}:</strong> {{ page.comment }}
            </p>
            <p class="page-file">
              <strong>{{ $t('pages.uploadFile') }}:</strong>
              {{ page.location_file ? $t('common.yes') : $t('common.no') }}
            </p>
            <div class="page-meta">
              <span v-if="page.restriction" class="badge badge-info">
                {{ page.restriction }}
              </span>
              <span v-if="page.workstatus" class="badge badge-secondary">
                {{ page.workstatus }}
              </span>
            </div>
          </div>
          <div class="page-card-footer">
            <small v-if="page.created_on" class="text-muted">
              {{ $t('pages.createdOn') }}: {{ formatDate(page.created_on) }}
            </small>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <button
          :disabled="currentPage === 1"
          class="btn btn-sm"
          @click="currentPage--"
        >
          {{ $t('common.previous') }}
        </button>
        <span class="pagination-info">
          {{ $t('pages.pagingInfo', { current: currentPage, total: totalPages }) }}
        </span>
        <button
          :disabled="currentPage === totalPages"
          class="btn btn-sm"
          @click="currentPage++"
        >
          {{ $t('common.next') }}
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && pages.length === 0" class="empty-state">
      <p>{{ $t('pages.noPages') }}</p>
      <router-link :to="`/records/${recordId}/pages/new`" class="btn btn-primary">
        {{ $t('pages.createNew') }}
      </router-link>
    </div>
  </div>
</template>

<script>
import { useRoute } from 'vue-router'
import { pageService } from '@/services/page'
import { recordService } from '@/services/record'

export default {
  name: 'PageList',
  setup() {
    return {
      route: useRoute(),
    }
  },
  data() {
    return {
      recordId: null,
      recordTitle: '',
      pages: [],
      loading: false,
      error: null,
      successMessage: '',
      searchName: '',
      pageSize: 10,
      currentPage: 1,
      total: 0,
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.total / this.pageSize)
    },
  },
  methods: {
    async loadPages() {
      this.loading = true
      this.error = null
      try {
        const response = await pageService.listPages({
          record_id: this.recordId,
          name: this.searchName || undefined,
          skip: (this.currentPage - 1) * this.pageSize,
          limit: this.pageSize,
        })
        this.pages = response.items || []
        this.total = response.total || 0
      } catch (err) {
        console.error('Error loading pages:', err)
        this.error = this.$t('pages.loadError')
      } finally {
        this.loading = false
      }
    },
    async loadRecordTitle() {
      try {
        const record = await recordService.getRecord(this.recordId)
        this.recordTitle = record.title || this.recordId
      } catch (err) {
        console.error('Error loading record title:', err)
        this.recordTitle = this.recordId
      }
    },
    async handleDelete(pageId) {
      if (confirm(this.$t('pages.confirmDelete'))) {
        try {
          await pageService.deletePage(pageId)
          this.successMessage = this.$t('pages.deleteSuccess')
          await this.loadPages()
        } catch (err) {
          console.error('Error deleting page:', err)
          this.error = this.$t('pages.deleteError')
        }
      }
    },
    handleSearch() {
      this.currentPage = 1
      this.loadPages()
    },
    handlePageSizeChange() {
      this.currentPage = 1
      this.loadPages()
    },
    resetFilters() {
      this.searchName = ''
      this.pageSize = 10
      this.currentPage = 1
      this.loadPages()
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
    truncateText(text, maxLength) {
      if (!text) return ''
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    },
  },
  mounted() {
    this.recordId = this.route.params.recordId
    this.loadRecordTitle()
    this.loadPages()
  },
}
</script>

<style scoped>
.pages-container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.pages-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.header-title h1 {
  margin: 0;
  font-size: 1.8rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.pages-search {
  background: #f5f5f5;
  padding: 1.5rem;
  border-radius: 4px;
  margin-bottom: 2rem;
}

.search-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  align-items: flex-end;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-control {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.pages-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.pages-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
}

.page-card {
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.page-card-header {
  padding: 1rem;
  background: #f9f9f9;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.page-card-header h3 {
  margin: 0;
  word-break: break-word;
  flex: 1;
}

.page-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.page-card-body {
  padding: 1rem;
  flex: 1;
}

.page-description,
.page-content,
.page-comment,
.page-file {
  margin: 0.5rem 0;
  line-height: 1.4;
}

.page-file a {
  color: #007bff;
  text-decoration: none;
}

.page-file a:hover {
  text-decoration: underline;
}

.page-meta {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}

.badge-info {
  background: #e3f2fd;
  color: #1976d2;
}

.badge-secondary {
  background: #f0f0f0;
  color: #666;
}

.page-card-footer {
  padding: 0.75rem 1rem;
  background: #fafafa;
  border-top: 1px solid #eee;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.pagination-info {
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.empty-state p {
  margin-bottom: 1.5rem;
  font-size: 1.1rem;
}

.loading,
.alert {
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 4px;
}

.alert-success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.alert-danger {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  color: #333;
  cursor: pointer;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn:hover {
  background: #f0f0f0;
}

.btn-primary {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
  border-color: #6c757d;
}

.btn-secondary:hover {
  background: #545b62;
}

.btn-info {
  background: #17a2b8;
  color: white;
  border-color: #17a2b8;
}

.btn-info:hover {
  background: #117a8b;
}

.btn-danger {
  background: #dc3545;
  color: white;
  border-color: #dc3545;
}

.btn-danger:hover {
  background: #c82333;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
}

.btn-link {
  background: transparent;
  color: #007bff;
  border: none;
  padding: 0.5rem;
}

.btn-link:hover {
  background: transparent;
  text-decoration: underline;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
