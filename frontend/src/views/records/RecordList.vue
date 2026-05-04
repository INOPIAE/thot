<template>
  <div class="records-container">
    <div class="records-header">
      <h1>{{ $t('nav.records') }}</h1>
      <div class="header-actions">
        <router-link v-if="!defaultListMode && canCreateRecord" to="/records/new" class="btn btn-primary">
          {{ $t('records.createNew') }}
        </router-link>
      </div>
    </div>

    <!-- Search and Filter Section -->
    <div class="records-search">
      <div class="search-fields">
        <div class="form-group">
          <label for="search-title">{{ $t('records.searchByTitle') }}</label>
          <input
            id="search-title"
            v-model="searchTitle"
            type="text"
            class="form-control"
            :placeholder="$t('records.titlePlaceholder')"
            @input="handleSearch"
          />
        </div>

        <div class="form-group">
          <label for="search-signature">{{ $t('records.searchBySignature') }}</label>
          <input
            id="search-signature"
            v-model="searchSignature"
            type="text"
            class="form-control"
            :placeholder="$t('records.signaturePlaceholder')"
            @input="handleSearch"
          />
        </div>

        <div class="form-group">
          <label for="search-keywords-names">{{ $t('records.searchByKeywordsNames') }}</label>
          <input
            id="search-keywords-names"
            v-model="searchKeywordsNames"
            type="text"
            class="form-control"
            :placeholder="$t('records.keywordsNamesSearchPlaceholder')"
            @input="handleSearch"
          />
          <small class="form-text">{{ $t('records.keywordsSearchHelp') }}</small>
        </div>

        <div class="form-group">
          <label for="search-keywords-locations">{{ $t('records.searchByKeywordsLocations') }}</label>
          <input
            id="search-keywords-locations"
            v-model="searchKeywordsLocations"
            type="text"
            class="form-control"
            :placeholder="$t('records.keywordsLocationsSearchPlaceholder')"
            @input="handleSearch"
          />
          <small class="form-text">{{ $t('records.keywordsSearchHelp') }}</small>
        </div>

        <div class="form-group">
          <label for="page-size">{{ $t('records.pageSize') }}</label>
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

    <!-- Success State -->
    <div v-if="successMessage" class="alert alert-success">
      {{ successMessage }}
    </div>

    <!-- Error State -->
    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <!-- Records Table -->
    <div v-if="!loading && records.length > 0" class="records-table-container">
      <table class="records-table">
        <thead>
          <tr>
            <th>{{ $t('records.columnTitle') }}</th>
            <th>{{ $t('records.signature') }}</th>
            <th>{{ $t('records.authors') }}</th>
            <th>{{ $t('records.publisher') }}</th>
            <th>{{ $t('records.keywordsNames') }}</th>
            <th>{{ $t('records.keywordsLocations') }}</th>
            <th>{{ $t('records.loantype') }}</th>
            <!-- <th v-if="!defaultListMode && (authStore.hasRole('admin') || authStore.hasRole('user_bibl'))">{{ $t('records.loantypeSubtype') }}</th> -->
            <th v-if="!defaultListMode">{{ $t('records.restriction') }}</th>
            <th v-if="!defaultListMode">{{ $t('records.workstatus') }}</th>
            <th>{{ $t('pages.totalCount') }}</th>
            <th v-if="!defaultListMode">{{ $t('records.createdOn') }}</th>
            <th>{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="record in records" :key="record.id">
            <td>{{ record.title }}</td>
            <td>{{ record.signature || '-' }}</td>
            <td class="authors-cell">{{ record.authors || '-' }}</td>
            <td class="publisher-cell">{{ record.publisher || '-' }}</td>
            <td class="keywords-cell">
              <span v-if="record.keywords_names" class="keywords-tag">
                {{ record.keywords_names }}
              </span>
              <span v-else>-</span>
            </td>
            <td class="keywords-cell">
              <span v-if="record.keywords_locations" class="keywords-tag">
                {{ record.keywords_locations }}
              </span>
              <span v-else>-</span>
            </td>
            <td>
              <span v-if="!defaultListMode && (authStore.hasRole('admin') || authStore.hasRole('user_bibl'))">
                {{ record.loantype ? (record.loantype + (record.loantype_subtype ? ' - ' + record.loantype_subtype : '')) : '-' }}
              </span>
              <span v-else>
                {{ record.loantype || '-' }}
              </span>
            </td>
            <td v-if="!defaultListMode">{{ record.restriction || '-' }}</td>
            <td v-if="!defaultListMode">{{ record.workstatus || '-' }}</td>
            <td class="pages-count">{{ record.page_count || 0 }}</td>
            <td v-if="!defaultListMode">{{ formatDate(record.entered_on) }}</td>
            <td class="actions-cell">
              <router-link
                v-if="record.page_count > 0"
                :to="`/records/${record.id}/pages-gallery`"
                class="btn btn-sm btn-secondary"
              >
                {{ $t('pages.title') }}
              </router-link>
              <router-link
                v-if="!defaultListMode"
                :to="`/records/${record.id}`"
                class="btn btn-sm btn-info"
              >
                {{ canEditRecord ? $t('common.edit') : $t('common.view') }}
              </router-link>
              <button
                v-if="!defaultListMode && canEditRecord"
                class="btn btn-sm btn-danger"
                @click="deleteRecord(record.id)"
              >
                {{ $t('common.delete') }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div class="pagination">
        <button
          class="btn btn-secondary"
          @click="previousPage"
          :disabled="currentPage === 0"
        >
          {{ $t('common.previous') }}
        </button>

        <span class="pagination-info">
          {{ $t('records.pagingInfo', { current: currentPage + 1, total: totalPages }) }}
        </span>

        <button
          class="btn btn-secondary"
          @click="nextPage"
          :disabled="currentPage >= totalPages - 1"
        >
          {{ $t('common.next') }}
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && records.length === 0" class="empty-state">
      <p>{{ $t('records.noRecords') }}</p>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { fetchRecords } from '@/services/records'
import { useAuthStore } from '@/stores/auth'

export default defineComponent({
  name: 'RecordList',
  props: {
    defaultListMode: {
      type: Boolean,
      default: false,
    },
  },
  setup() {
    const authStore = useAuthStore()
    return { authStore }
  },
  data() {
    return {
      records: [],
      loading: false,
      error: null,
      successMessage: null,
      searchTitle: '',
      searchSignature: '',
      searchKeywordsNames: '',
      searchKeywordsLocations: '',
      currentPage: 0,
      pageSize: 10,
      totalRecords: 0,
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.totalRecords / this.pageSize)
    },
    canCreateRecord() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_bibl')
    },
    canEditRecord() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_bibl')
    },
    canManagePages() {
      return this.authStore.hasRole('admin') || 
             this.authStore.hasRole('user_bibl') || 
             this.authStore.hasRole('user_scan') || 
             this.authStore.hasRole('user_page')
    },
  },
  mounted() {
    this.loadRecords()
  },
  methods: {
    getPagesUrl(recordId) {
      // Users with management roles go to pages list, others to gallery
      if (this.canManagePages) {
        return `/records/${recordId}/pages`
      }
      return `/records/${recordId}/pages-gallery`
    },
    async loadRecords() {
      this.loading = true
      this.error = null
      this.successMessage = null

      try {
        let params = {
          skip: this.currentPage * this.pageSize,
          limit: this.pageSize,
        }
        if (this.searchTitle) params.title = this.searchTitle
        if (this.searchSignature) params.signature = this.searchSignature
        if (this.searchKeywordsNames) params.keywords_names = this.searchKeywordsNames
        if (this.searchKeywordsLocations) params.keywords_locations = this.searchKeywordsLocations
        if (this.defaultListMode) {
          params.endpoint = '/api/v1/records/defaultlist'
        }
        const data = await fetchRecords(params)
        if (Array.isArray(data)) {
          this.records = data
          this.totalRecords = data.length
        } else {
          this.records = data.items || []
          this.totalRecords = data.total || 0
        }
      } catch (err) {
        this.error = err.message || this.$t('records.loadError')
        console.error('Error loading records:', err)
      } finally {
        this.loading = false
      }
    },

    handleSearch() {
      this.currentPage = 0
      this.loadRecords()
    },

    handlePageSizeChange() {
      this.currentPage = 0
      this.loadRecords()
    },

    resetFilters() {
      this.searchTitle = ''
      this.searchSignature = ''
      this.searchKeywordsNames = ''
      this.searchKeywordsLocations = ''
      this.currentPage = 0
      this.loadRecords()
    },

    previousPage() {
      if (this.currentPage > 0) {
        this.currentPage--
        this.loadRecords()
      }
    },

    nextPage() {
      if (this.currentPage < this.totalPages - 1) {
        this.currentPage++
        this.loadRecords()
      }
    },

    async deleteRecord(recordId) {
      if (!confirm(this.$t('records.confirmDelete'))) {
        return
      }

      this.error = null
      this.successMessage = null

      try {
        await recordService.deleteRecord(recordId)
        this.successMessage = this.$t('records.deleteSuccess')
        this.loadRecords()
      } catch (err) {
        this.error = err.message || this.$t('records.deleteError')
      }
    },

    formatDate(dateString) {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return date.toLocaleDateString(this.$i18n.locale, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      })
    },
  },
})
</script>

<style scoped>
.records-container {
  padding: 5px;
.records-table thead th {
  position: sticky;
  top: 0;
  background: #f9f9f9;
  z-index: 2;
}
}

.records-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.records-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.records-search {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.search-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 500;
  margin-bottom: 5px;
  font-size: 14px;
}

.form-text {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #6c757d;
  font-style: italic;
}

/* Ensure all search fields have the same height */
.form-control {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  height: 38px;
  box-sizing: border-box;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.loading {
  text-align: center;
  padding: 40px;
  font-size: 16px;
  color: #666;
}

.records-table-container {
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow-x: auto;
  max-height: 70vh;
  overflow-y: auto;
  max-width: 80vw;
}

.records-table {
  border-collapse: collapse;
  min-width: 1000px;
}

.records-table thead {
  background-color: #f9f9f9;
  border-bottom: 2px solid #ddd;
}

.records-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
}

.records-table td {
  padding: 12px;
  border-bottom: 1px solid #eee;
}

.records-table tbody tr:hover {
  background-color: #f5f5f5;
}

.keywords-cell {
  max-width: 200px;
}

.authors-cell {
  max-width: 250px;
  word-break: break-word;
}

.publisher-cell {
  max-width: 180px;
  word-break: break-word;
}

.keywords-tag {
  display: inline-block;
  font-size: 12px;
  color: #495057;
  background-color: #e9ecef;
  padding: 2px 6px;
  border-radius: 3px;
  word-break: break-word;
}

.pages-count {
  text-align: center;
  font-weight: 500;
}

.actions-cell {
  display: flex;
  gap: 8px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.pagination-info {
  font-size: 14px;
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
  font-size: 16px;
}

@media (max-width: 1200px) {
  .records-table {
    font-size: 13px;
  }
  
  .records-table th,
  .records-table td {
    padding: 8px;
  }
  
  .keywords-cell {
    max-width: 150px;
    font-size: 11px;
  }
}

@media (max-width: 768px) {
  .search-fields {
    grid-template-columns: 1fr;
  }
  
  .records-table-container {
    overflow-x: auto;
  }
  
  .records-table {
    min-width: 800px;
  }
}
</style>
