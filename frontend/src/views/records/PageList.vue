<template>
  <div class="pages-container">
    <div class="pages-header">
      <div class="header-title">
        <router-link :to="`/records/${recordId}`" class="btn btn-light">
          {{ $t('common.back') }}
        </router-link>
        <h1>{{ $t('pages.pageListTitle') }}: {{ recordTitle }}</h1>
      </div>
      <div class="header-actions">
        <router-link :to="`/records/${recordId}/pages-gallery`" class="btn btn-info">
          {{ $t('pages.galleryTitle') }}
        </router-link>
        <router-link v-if="canCreatePage" :to="`/records/${recordId}/pages/new`" class="btn btn-primary">
          {{ $t('pages.createNew') }}
        </router-link>
      </div>
    </div>

    <!-- Total Count -->
    <div class="pages-total-count">
      {{ $t('pages.totalCount') }}: {{ total }}
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
        <div v-for="(page, index) in pages" :key="page.id" class="page-card">
          <div class="page-card-header">
            <div class="page-card-heading">
              <div>
                <div v-if="canReorderPages" class="page-position">
                  {{ $t('pages.currentPosition', { position: getPagePosition(page, index) }) }}
                </div>
                <h3>{{ page.name }}</h3>
              </div>
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
              <strong>{{ $t('pages.pdfFileStatus') }}:</strong>
              {{ page.location_file ? $t('common.yes') : $t('common.no') }}
            </p>
            <p v-if="page.page_count" class="page-count">
              <strong>{{ $t('pages.pageCount') }}:</strong> {{ page.page_count }}
            </p>
            <div class="page-meta">
              <span v-if="page.restriction" class="badge badge-info">
                {{ page.restriction }}
              </span>
              <span v-if="page.workstatus" class="badge badge-secondary">
                {{ page.workstatus }}
              </span>
            </div>
            <div v-if="page.ocr_status !== 'completed'" class="ocr-warning mt-2">
              <span class="badge badge-warning">OCR ausstehend</span>
              <button v-if="canManageOcr()" class="btn btn-sm btn-warning ml-2" @click="startOcr(page.id)">
                OCR starten
              </button>
            </div>
            <div v-if="canReorderPages" class="page-reorder-panel">
              <div class="page-reorder-header">
                <div>
                  <div class="page-reorder-title">{{ $t('pages.reorderSectionTitle') }}</div>
                  <small class="page-reorder-help">{{ $t('pages.reorderHelp') }}</small>
                </div>
                <div class="page-order-buttons">
                  <button
                    class="btn btn-sm btn-light"
                    :disabled="isReordering(page.id) || getPagePosition(page, index) === 1"
                    @click="movePageByOffset(page, index, -1)"
                  >
                    {{ $t('pages.moveUp') }}
                  </button>
                  <button
                    class="btn btn-sm btn-light"
                    :disabled="isReordering(page.id) || getPagePosition(page, index) === pageOrderTotal"
                    @click="movePageByOffset(page, index, 1)"
                  >
                    {{ $t('pages.moveDown') }}
                  </button>
                </div>
              </div>
              <label :for="`move-target-${page.id}`" class="page-reorder-label">
                {{ $t('pages.moveToPosition') }}
              </label>
              <div class="page-reorder-controls">
                <input
                  :id="`move-target-${page.id}`"
                  v-model.number="moveTargets[page.id]"
                  type="number"
                  min="1"
                  :max="pageOrderTotal"
                  class="form-control page-reorder-input"
                  :disabled="isReordering(page.id)"
                />
                <button
                  class="btn btn-sm btn-outline-primary"
                  :disabled="isReordering(page.id) || pageOrderTotal < 2"
                  @click="movePageToTarget(page)"
                >
                  {{ $t('pages.moveToPositionAction') }}
                </button>
              </div>
            </div>
          </div>
          <div class="page-card-footer">
            <small v-if="page.created_on" class="text-muted">
              {{ $t('pages.createdOn') }}: {{ formatDate(page.created_on) }}
            </small>
            <div class="page-actions">
              <router-link :to="`/records/${recordId}/pages/${page.id}`" class="btn btn-sm btn-info">
                {{ $t('pages.openOverview') }}
              </router-link>
              <router-link :to="`/records/${recordId}/pages/${page.id}/viewer`" class="btn btn-sm btn-primary">
                {{ $t('pages.openPdfViewer') }}
              </router-link>
              <router-link v-if="canEditPage || canUploadExistingPage" :to="`/records/${recordId}/pages/${page.id}/edit`" class="btn btn-sm btn-secondary">
                {{ canEditPage ? $t('common.edit') : $t('pages.uploadFile') }}
              </router-link>
              <button v-if="canEditPage" class="btn btn-sm btn-danger" @click="handleDelete(page.id)">
                {{ $t('common.delete') }}
              </button>
            </div>
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
      <router-link v-if="canCreatePage" :to="`/records/${recordId}/pages/new`" class="btn btn-primary">
        {{ $t('pages.createNew') }}
      </router-link>
    </div>
  </div>
</template>

<script>
import { useRoute } from 'vue-router'
import { pageService } from '@/services/page'
import { recordService } from '@/services/record'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'PageList',
  setup() {
    return {
      route: useRoute(),
      authStore: useAuthStore(),
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
      currentPage: 1,
      pageSize: 10,
      total: 0,
      pageOrderTotal: 0,
      moveTargets: {},
      pageOrderMap: {},
      movingPageId: null,
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.total / this.pageSize)
    },
    canCreatePage() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_scan')
    },
    canEditPage() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_page')
    },
    canReorderPages() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_page')
    },
    canUploadExistingPage() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_scan')
    },
  },
  watch: {
    currentPage() {
      this.loadPages()
    },
  },
  methods: {
    canManageOcr() {
      // Admins und user_scan dürfen OCR starten
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_scan')
    },
    async startOcr(pageId) {
      try {
        await pageService.startOcr(pageId)
        this.successMessage = 'OCR-Job wurde gestartet.'
        await this.loadPages()
      } catch (err) {
        this.error = err.message || 'Fehler beim Starten des OCR-Jobs.'
      }
    },
    async loadRecordTitle() {
      try {
        const record = await recordService.getRecord(this.recordId)
        this.recordTitle = record?.title || this.$t('pages.unknownRecord')
      } catch (err) {
        this.recordTitle = this.$t('pages.unknownRecord')
      }
    },
    async loadPages() {
      this.loading = true
      this.error = null

      try {
        const params = {
          record_id: this.recordId,
          skip: (this.currentPage - 1) * this.pageSize,
          limit: this.pageSize,
        }

        if (this.searchName) {
          params.name = this.searchName
        }

        const response = await pageService.listPages(params)
        this.pages = response.items || []
        this.total = response.total || 0

        if (this.canReorderPages && this.total > 0) {
          await this.loadPageOrderState()
        } else {
          this.pageOrderTotal = 0
          this.pageOrderMap = {}
          this.moveTargets = {}
        }

        if (this.total > 0 && this.currentPage > this.totalPages) {
          this.currentPage = this.totalPages
        }
      } catch (err) {
        console.error('Error loading pages:', err)
        this.error = err.message || this.$t('pages.loadError')
      } finally {
        this.loading = false
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
      this.currentPage = 1
      this.loadPages()
    },
    getPagePosition(page, index) {
      const mappedIndex = this.pageOrderMap[page.id]

      if (typeof mappedIndex === 'number') {
        return mappedIndex + 1
      }

      return ((this.currentPage - 1) * this.pageSize) + index + 1
    },
    isReordering(pageId) {
      return this.movingPageId === pageId
    },
    async fetchOrderedPages() {
      const initialLimit = Math.max(this.total || 0, this.pageSize, 1)
      let response = await pageService.listPages({
        record_id: this.recordId,
        skip: 0,
        limit: initialLimit,
      })

      const items = response.items || []
      const responseTotal = response.total || items.length

      if (responseTotal > items.length) {
        response = await pageService.listPages({
          record_id: this.recordId,
          skip: 0,
          limit: responseTotal,
        })
      }

      return response.items || []
    },
    async loadPageOrderState() {
      const orderedPages = await this.fetchOrderedPages()
      const pageOrderMap = {}
      const moveTargets = { ...this.moveTargets }

      this.pageOrderTotal = orderedPages.length

      orderedPages.forEach((page, index) => {
        pageOrderMap[page.id] = index
        moveTargets[page.id] = index + 1
      })

      this.pageOrderMap = pageOrderMap
      this.moveTargets = moveTargets
    },
    getReorderError(err, fallback) {
      return err?.message || err?.detail || fallback
    },
    async reorderPages(pageId, targetIndex) {
      this.error = null
      this.successMessage = ''
      this.movingPageId = pageId

      try {
        const orderedPages = await this.fetchOrderedPages()
        const currentIndex = orderedPages.findIndex((page) => page.id === pageId)

        if (currentIndex === -1) {
          throw new Error(this.$t('pages.reorderLoadError'))
        }

        const boundedTargetIndex = Math.min(Math.max(targetIndex, 0), orderedPages.length - 1)

        if (boundedTargetIndex === currentIndex) {
          return
        }

        const [pageToMove] = orderedPages.splice(currentIndex, 1)
        orderedPages.splice(boundedTargetIndex, 0, pageToMove)

        const changedPages = orderedPages
          .map((page, index) => ({
            ...page,
            nextOrder: index + 1,
          }))
          .filter((page) => page.order_by !== page.nextOrder)

        for (const page of changedPages) {
          await pageService.updatePage(page.id, {
            name: page.name,
            description: page.description ?? '',
            page: page.page ?? '',
            comment: page.comment ?? '',
            restriction_id: page.restriction_id,
            workstatus_id: page.workstatus_id ?? '',
            order_by: page.nextOrder,
            rotation: page.rotation ?? 0,
          })
        }

        this.successMessage = this.$t('pages.reorderSuccess')
        await this.loadPages()
      } catch (err) {
        console.error('Error reordering pages:', err)
        this.error = this.getReorderError(err, this.$t('pages.reorderError'))
      } finally {
        this.movingPageId = null
      }
    },
    async movePageByOffset(page, index, offset) {
      const currentPosition = this.getPagePosition(page, index)
      await this.reorderPages(page.id, currentPosition - 1 + offset)
    },
    async movePageToTarget(page) {
      const targetPosition = Number(this.moveTargets[page.id])

      if (!Number.isInteger(targetPosition) || targetPosition < 1 || targetPosition > this.pageOrderTotal) {
        this.error = this.$t('pages.invalidTargetPosition', { total: this.pageOrderTotal })
        return
      }

      await this.reorderPages(page.id, targetPosition - 1)
    },
    async handleDelete(pageId) {
      if (!confirm(this.$t('pages.confirmDelete'))) {
        return
      }

      this.error = null
      this.successMessage = ''

      try {
        await pageService.deletePage(pageId)
        this.successMessage = this.$t('pages.deleteSuccess')
        await this.loadPages()
      } catch (err) {
        console.error('Error deleting page:', err)
        this.error = err.message || this.$t('pages.deleteError')
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

.pages-total-count {
  margin-bottom: 1.5rem;
  padding: 0.75rem;
  background: #e7f3ff;
  border-left: 4px solid #007bff;
  border-radius: 4px;
  font-weight: 500;
  color: #004085;
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
}

.page-card-heading {
  display: flex;
  align-items: flex-start;
}

.page-card-header h3 {
  margin: 0;
  word-break: break-word;
}

.page-position {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 0.35rem;
}

.page-order-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.page-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 0.75rem;
}

.page-card-body {
  padding: 1rem;
  flex: 1;
}

.page-reorder-panel {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.page-reorder-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.page-reorder-title {
  font-weight: 600;
  margin-bottom: 0.2rem;
}

.page-reorder-label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.page-reorder-controls {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.page-reorder-input {
  max-width: 7rem;
}

.page-reorder-help {
  display: block;
  margin-top: 0.5rem;
  color: #666;
}

.page-description,
.page-content,
.page-comment,
.page-file,
.page-count {
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

.page-card-footer {
  padding: 0.75rem 1rem;
  background: #fafafa;
  border-top: 1px solid #eee;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
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

.loading {
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .page-reorder-header,
  .page-reorder-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .page-order-buttons {
    justify-content: flex-start;
  }

  .page-reorder-input {
    max-width: none;
  }
}

</style>
