<template>
  <div class="page-form-container">
    <div class="form-header">
      <div class="form-header-main">
        <h1>{{ isEditMode ? $t('pages.editPage') : $t('pages.createPage') }}</h1>
        <div v-if="isEditMode && pageSequence.length > 0" class="page-navigation-toolbar">
          <button
            type="button"
            class="btn btn-light"
            :disabled="!hasPreviousPage || submitting || loading"
            @click="navigateToAdjacentPage(-1)"
          >
            {{ $t('pages.previousPage') }}
          </button>
          <span class="page-navigation-status">
            {{ $t('pages.pageNavigationPosition', { current: currentPagePosition, total: pageSequence.length }) }}
          </span>
          <button
            type="button"
            class="btn btn-light"
            :disabled="!hasNextPage || submitting || loading"
            @click="navigateToAdjacentPage(1)"
          >
            {{ $t('pages.nextPage') }}
          </button>
        </div>
      </div>
      <router-link :to="`/records/${recordId}/pages`" class="btn btn-secondary">
        {{ $t('common.back') }}
      </router-link>
    </div>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-if="isEditMode && isOcrPending" class="alert alert-warning ocr-pending-alert">
      {{ $t('pages.ocrPending') }}
    </div>

    <form v-if="!loading" class="page-form" @submit.prevent="handleSubmit">

      <div v-if="(isEditMode || (!isEditMode && (pageRecordTitle || pageRecordSignature)))" class="form-group">
        <label>{{ $t('records.title') }}:</label>
        <span>
          <template v-if="pageRecordSignature && pageRecordTitle">{{ pageRecordSignature }} - </template>{{ pageRecordTitle }}
        </span>
      </div>

      <div class="form-group">
        <label for="name">{{ $t('pages.pageName') }} *</label>
        <input
          id="name"
          v-model="form.name"
          type="text"
          class="form-control"
          :placeholder="$t('pages.pageNamePlaceholder')"
          :disabled="isUploadOnlyMode"
          required
        />
      </div>

      <div class="form-group">
        <label for="description">{{ $t('pages.description') }}</label>
        <textarea
          id="description"
          v-model="form.description"
          class="form-control"
          :placeholder="$t('pages.descriptionPlaceholder')"
          :disabled="isUploadOnlyMode"
          rows="3"
        />
      </div>

      <div class="form-group">
        <label for="page">{{ $t('pages.pageContent') }}</label>
        <textarea
          id="page"
          v-model="form.page"
          class="form-control"
          :placeholder="$t('pages.pageContentPlaceholder')"
          :disabled="isUploadOnlyMode"
          rows="8"
        />
      </div>


      <div class="form-group">
        <label for="comment">{{ $t('pages.comment') }}</label>
        <textarea
          id="comment"
          v-model="form.comment"
          class="form-control"
          :placeholder="$t('pages.commentPlaceholder')"
          :disabled="isUploadOnlyMode"
          rows="3"
        />
      </div>

      <div class="form-group" v-if="canEditPage">
        <label for="order_by">{{ $t('pages.orderBy') }}</label>
        <input
          id="order_by"
          v-model.number="form.order_by"
          type="number"
          min="1"
          class="form-control"
          :placeholder="$t('pages.orderByPlaceholder')"
        />
        <small class="form-text text-muted">{{ $t('pages.orderByHelp') }}</small>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="restriction">{{ $t('pages.restriction') }} *</label>
          <select id="restriction" v-model="form.restriction_id" class="form-control" :disabled="isUploadOnlyMode" required>
            <option value="">{{ $t('pages.selectRestriction') }}</option>
            <option v-for="restriction in restrictions" :key="restriction.id" :value="restriction.id">
              {{ restriction.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="workstatus">{{ $t('pages.workstatus') }}</label>
          <select id="workstatus" v-model="form.workstatus_id" class="form-control" :disabled="isUploadOnlyMode">
            <option value="">{{ $t('pages.selectWorkStatus') }}</option>
            <option v-for="status in workstatuses" :key="status.id" :value="status.id">
              {{ status.status }} {{ status.area ? `(${status.area})` : '' }}
            </option>
          </select>
        </div>
      </div>

      <div class="form-group" v-if="canManageFile">
        <label for="file">{{ $t('pages.uploadFile') }}</label>
        <input id="file" type="file" class="form-control" accept="application/pdf,.pdf" @change="onFileChange" />
        <small class="form-text">
          {{ selectedFileName || $t('pages.noFileSelected') }}
        </small>
        <small v-if="!isEditMode" class="form-text text-info">
          {{ $t('pages.uploadMultiPageHint') }}
        </small>
        <small v-if="isEditMode && !filePageError" class="form-text text-warning">
          {{ $t('pages.uploadSinglePageOnly') }}
        </small>
        <small v-if="filePageError" class="form-text text-danger">{{ filePageError }}</small>
        <small v-if="isEditMode" class="form-text">
          {{ $t('pages.currentFile') }}: {{ hasCurrentFile ? $t('common.yes') : $t('common.no') }}
        </small>
        <label v-if="isEditMode && hasCurrentFile" class="checkbox-label">
          <input v-model="form.delete_file" type="checkbox" /> {{ $t('pages.removeCurrentFile') }}
        </label>

        <!-- Thumbnail und Rotation -->
        <div v-if="isEditMode && hasCurrentFile" class="rotation-thumbnail-group">
          <div class="thumbnail-rotation-row">
            <button type="button" class="btn btn-light btn-sm" @click="rotateLeft" :disabled="submitting">
              ⟲
            </button>
            <div class="thumbnail-preview-wrapper">
              <img
                v-if="thumbnailUrl"
                :src="thumbnailUrl"
                :style="rotationStyle"
                class="thumbnail-preview"
                :alt="$t('pages.pdfThumbnail')"
              />
              <span v-else>{{ $t('pages.noThumbnail') }}</span>
            </div>
            <button type="button" class="btn btn-light btn-sm" @click="rotateRight" :disabled="submitting">
              ⟳
            </button>
          </div>
          <div class="rotation-indicator">
            {{ $t('pages.rotation') }}: {{ form.rotation }}°
          </div>
        </div>
      </div>

      <div class="form-group" v-if="isEditMode && canManageFile">
        <label for="restriction-file">{{ $t('pages.uploadRestrictionFile') }}</label>
        <input id="restriction-file" type="file" class="form-control" accept="application/pdf,.pdf" @change="onRestrictionFileChange" />
        <small class="form-text">
          {{ selectedRestrictionFileName || $t('pages.noRestrictionFileSelected') }}
        </small>
        <small v-if="!restrictionFilePageError" class="form-text text-warning">
          {{ $t('pages.restrictionUploadSinglePageOnly') }}
        </small>
        <small v-if="restrictionFilePageError" class="form-text text-danger">{{ restrictionFilePageError }}</small>
        <small class="form-text">
          {{ $t('pages.restrictionFile') }}: {{ hasRestrictionFile ? $t('common.yes') : $t('common.no') }}
        </small>
        <label v-if="hasRestrictionFile" class="checkbox-label">
          <input v-model="form.delete_restriction_file" type="checkbox" /> {{ $t('pages.removeRestrictionFile') }}
        </label>

        <div v-if="hasRestrictionFile" class="rotation-thumbnail-group restriction-rotation-group">
          <div class="thumbnail-rotation-row">
            <button type="button" class="btn btn-light btn-sm" @click="rotateRestrictionLeft" :disabled="submitting">
              ⟲
            </button>
            <span class="rotation-preview-label">{{ $t('pages.restrictionPdfDocument') }}</span>
            <button type="button" class="btn btn-light btn-sm" @click="rotateRestrictionRight" :disabled="submitting">
              ⟳
            </button>
          </div>
          <div class="rotation-indicator">
            {{ $t('pages.restrictionRotation') }}: {{ form.rotation_restriction }}°
          </div>
        </div>
      </div>

      <div v-if="isEditMode && canViewManagedFiles && (hasCurrentFile || hasRestrictionFile)" class="pdf-preview-grid">
        <section v-if="hasCurrentFile" class="pdf-preview-card">
          <div class="pdf-preview-header">
            <h2>{{ $t('pages.currentPdfDocument') }}</h2>
            <div class="pdf-preview-actions">
              <button type="button" class="btn btn-sm btn-primary" @click="downloadCurrentPdf">
                {{ $t('pages.downloadCurrentPdf') }}
              </button>
            </div>
          </div>
          <div class="pdf-preview-viewer">
            <PdfJsPageViewer
              v-if="currentPdfBlobUrl"
              :src="currentPdfBlobUrl"
              :rotation="form.rotation || 0"
            />
            <div v-else class="pdf-preview-placeholder">
              {{ $t('common.loading') }}
            </div>
          </div>
        </section>

        <section v-if="hasRestrictionFile" class="pdf-preview-card">
          <div class="pdf-preview-header">
            <h2>{{ $t('pages.restrictionPdfDocument') }}</h2>
            <div class="pdf-preview-actions">
              <button type="button" class="btn btn-sm btn-primary" @click="downloadRestrictionPdf">
                {{ $t('pages.downloadRestrictionPdf') }}
              </button>
            </div>
          </div>
          <div class="pdf-preview-viewer">
            <PdfJsPageViewer
              v-if="restrictionPdfBlobUrl"
              :src="restrictionPdfBlobUrl"
              :rotation="form.rotation_restriction || 0"
            />
            <div v-else class="pdf-preview-placeholder">
              {{ $t('common.loading') }}
            </div>
          </div>
        </section>
      </div>

      <div class="form-actions">
        <button type="submit" class="btn btn-primary" :disabled="submitting">
          {{ submitting ? $t('common.saving') : $t('common.save') }}
        </button>
        <router-link :to="`/records/${recordId}/pages`" class="btn btn-secondary">
          {{ $t('common.cancel') }}
        </router-link>
      </div>

      <div v-if="isEditMode && pageSequence.length > 0" class="page-navigation-toolbar page-navigation-toolbar-bottom">
        <button
          type="button"
          class="btn btn-light"
          :disabled="!hasPreviousPage || submitting || loading"
          @click="navigateToAdjacentPage(-1)"
        >
          {{ $t('pages.previousPage') }}
        </button>
        <span class="page-navigation-status">
          {{ $t('pages.pageNavigationPosition', { current: currentPagePosition, total: pageSequence.length }) }}
        </span>
        <button
          type="button"
          class="btn btn-light"
          :disabled="!hasNextPage || submitting || loading"
          @click="navigateToAdjacentPage(1)"
        >
          {{ $t('pages.nextPage') }}
        </button>
      </div>
    </form>

    <div v-if="showUnsavedChangesDialog" class="modal-overlay" @click.self="closeUnsavedChangesDialog">
      <div class="modal-dialog unsaved-changes-dialog" role="dialog" :aria-label="$t('pages.unsavedChangesTitle')">
        <div class="modal-content">
          <div class="modal-header">
            <h2 class="modal-title">{{ $t('pages.unsavedChangesTitle') }}</h2>
            <button type="button" class="btn-close" :disabled="submitting" @click="closeUnsavedChangesDialog">&times;</button>
          </div>
          <div class="modal-body">
            <p>{{ $t('pages.unsavedChangesMessage') }}</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" :disabled="submitting" @click="closeUnsavedChangesDialog">
              {{ $t('common.cancel') }}
            </button>
            <button type="button" class="btn btn-danger" :disabled="submitting" @click="discardPendingNavigation">
              {{ $t('pages.discardChanges') }}
            </button>
            <button type="button" class="btn btn-primary" :disabled="submitting" @click="saveAndContinueNavigation">
              {{ submitting ? $t('common.saving') : $t('pages.saveAndContinue') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

import { recordService } from '@/services/record'
import { pageService } from '@/services/page'
import { useAuthStore } from '@/stores/auth'
import PdfJsPageViewer from '@/components/PdfJsPageViewer.vue'


export default {
  name: 'PageForm',
  components: {
    PdfJsPageViewer,
  },
  beforeRouteLeave(to, from, next) {
    if (this.shouldBlockNavigation(to.fullPath)) {
      this.openUnsavedChangesDialog(to.fullPath)
      next(false)
      return
    }
    next()
  },
  beforeRouteUpdate(to, from, next) {
    if (this.shouldBlockNavigation(to.fullPath)) {
      this.openUnsavedChangesDialog(to.fullPath)
      next(false)
      return
    }
    next()
  },
  data() {
    return {
      authStore: useAuthStore(),
      loading: false,
      submitting: false,
      error: null,
      filePageError: null,
      restrictionFilePageError: null,
      restrictions: [],
      workstatuses: [],
      selectedFile: null,
      selectedFileName: '',
      selectedRestrictionFile: null,
      selectedRestrictionFileName: '',
      hasCurrentFile: false,
      hasRestrictionFile: false,
      pageRecordTitle: '',
      pageRecordSignature: '',
      pageSequence: [],
      initialFormSnapshot: null,
      showUnsavedChangesDialog: false,
      pendingNavigationTarget: null,
      bypassUnsavedChangesGuard: false,
      ocrStatus: 'not-applicable',
      form: {
        name: '',
        description: '',
        page: '',
        comment: '',
        restriction_id: '',
        workstatus_id: '',
        order_by: null,
        delete_file: false,
        delete_restriction_file: false,
        rotation: 0,
        rotation_restriction: 0,
      },
      thumbnailUrl: null,
      currentPdfBlobUrl: null,
      restrictionPdfBlobUrl: null,
    }
  },
  computed: {
    isEditMode() {
      return !!this.$route.params.pageId
    },
    recordId() {
      return this.$route.params.recordId
    },
    pageId() {
      return this.$route.params.pageId
    },
    currentPageIndex() {
      return this.pageSequence.findIndex((page) => page.id === this.pageId)
    },
    currentPagePosition() {
      return this.currentPageIndex >= 0 ? this.currentPageIndex + 1 : null
    },
    hasPreviousPage() {
      return this.currentPageIndex > 0
    },
    hasNextPage() {
      return this.currentPageIndex >= 0 && this.currentPageIndex < this.pageSequence.length - 1
    },
    canCreatePage() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_scan')
    },
    canEditPage() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_page')
    },
    canManageFile() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_scan')
    },
    canViewManagedFiles() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_page') || this.authStore.hasRole('user_scan')
    },
    isUploadOnlyMode() {
      return this.isEditMode && !this.canEditPage && this.canManageFile
    },
    isOcrPending() {
      return this.ocrStatus === 'pending'
    },
    rotationStyle() {
      return this.form.rotation ? `transform: rotate(${this.form.rotation}deg);` : ''
    },
    isDirty() {
      if (!this.initialFormSnapshot) {
        return false
      }
      return this.initialFormSnapshot !== JSON.stringify(this.buildFormSnapshot())
    },
  },
  watch: {
    pageId(newPageId, oldPageId) {
      if (newPageId && newPageId !== oldPageId) {
        this.handleRouteContextChange()
      }
    },
    recordId(newRecordId, oldRecordId) {
      if (newRecordId && newRecordId !== oldRecordId) {
        this.handleRouteContextChange()
      }
    },
  },
  mounted() {
    if (!this.recordId) {
      this.error = this.$t('pages.loadError') + ': recordId missing in URL.'
      return
    }
    window.addEventListener('beforeunload', this.handleBeforeUnload)
    this.loadMetadata()
    this.handleRouteContextChange()
  },
  methods: {
    buildFormSnapshot() {
      return {
        name: this.form.name,
        description: this.form.description,
        page: this.form.page,
        comment: this.form.comment,
        restriction_id: this.form.restriction_id,
        workstatus_id: this.form.workstatus_id,
        order_by: this.form.order_by !== undefined && this.form.order_by !== null ? this.form.order_by : null,
        delete_file: !!this.form.delete_file,
        delete_restriction_file: !!this.form.delete_restriction_file,
        rotation: this.form.rotation || 0,
        rotation_restriction: this.form.rotation_restriction || 0,
        selected_file: this.selectedFile
          ? {
              name: this.selectedFile.name,
              size: this.selectedFile.size,
              lastModified: this.selectedFile.lastModified,
            }
          : null,
        selected_restriction_file: this.selectedRestrictionFile
          ? {
              name: this.selectedRestrictionFile.name,
              size: this.selectedRestrictionFile.size,
              lastModified: this.selectedRestrictionFile.lastModified,
            }
          : null,
      }
    },
    captureInitialFormSnapshot() {
      this.initialFormSnapshot = JSON.stringify(this.buildFormSnapshot())
    },
    resetSelectedFileState() {
      this.selectedFile = null
      this.selectedFileName = ''
      this.filePageError = null
    },
    resetSelectedRestrictionFileState() {
      this.selectedRestrictionFile = null
      this.selectedRestrictionFileName = ''
      this.restrictionFilePageError = null
    },
    revokePdfUrls() {
      if (this.currentPdfBlobUrl) {
        URL.revokeObjectURL(this.currentPdfBlobUrl)
        this.currentPdfBlobUrl = null
      }
      if (this.restrictionPdfBlobUrl) {
        URL.revokeObjectURL(this.restrictionPdfBlobUrl)
        this.restrictionPdfBlobUrl = null
      }
    },
    async handleRouteContextChange() {
      if (!this.recordId) {
        this.error = this.$t('pages.loadError') + ': recordId missing in URL.'
        return
      }

      if (this.isEditMode) {
        await Promise.all([this.loadPageSequence(), this.loadPage()])
        return
      }

      this.pageSequence = []
      this.resetSelectedFileState()
      this.resetSelectedRestrictionFileState()
      this.ocrStatus = 'not-applicable'
      this.hasCurrentFile = false
      this.hasRestrictionFile = false
      this.revokePdfUrls()
      this.form.delete_file = false
      this.form.delete_restriction_file = false
      this.captureInitialFormSnapshot()
      this.loadRecordInfo()
    },
    async loadRecordInfo() {
      if (!this.recordId) {
        this.error = this.$t('pages.loadError') + ': recordId missing in URL.'
        return
      }
      try {
        const record = await recordService.getRecord(this.recordId)
        this.pageRecordTitle = record.title || ''
        this.pageRecordSignature = record.signature || ''
      } catch (err) {
        // Fehler ignorieren, falls Record nicht geladen werden kann
      }
    },
    async loadMetadata() {
      try {
        const [restrictionsResponse, workstatusResponse] = await Promise.all([
          recordService.getRestrictions(),
          recordService.getWorkStatus(),
        ])

        this.restrictions = restrictionsResponse.items || []
        this.workstatuses = workstatusResponse.items || []

        if (!this.form.restriction_id) {
          const noneRestriction = this.restrictions.find((item) => item.name === 'none')
          if (noneRestriction) {
            this.form.restriction_id = noneRestriction.id
          }
        }

        if (
          !this.isEditMode &&
          !this.form.name &&
          !this.form.description &&
          !this.form.page &&
          !this.form.comment &&
          !this.form.workstatus_id &&
          this.form.order_by === null &&
          !this.selectedFile &&
          !this.form.delete_file
        ) {
          this.captureInitialFormSnapshot()
        }
      } catch (err) {
        this.error = err.message || this.$t('pages.metadataLoadError')
      }
    },
    async loadPageSequence() {
      const limit = 100
      let skip = 0
      const orderedPages = []

      try {
        while (true) {
          const response = await pageService.listPages({
            record_id: this.recordId,
            skip,
            limit,
          })

          const items = response.items || []
          orderedPages.push(...items.map((page) => ({ id: page.id, name: page.name })))

          if (!items.length || orderedPages.length >= (response.total || 0)) {
            break
          }

          skip += limit
        }

        this.pageSequence = orderedPages
      } catch (err) {
        this.error = err.message || this.$t('pages.loadError')
      }
    },
    async loadPage() {
      this.loading = true
      this.error = null
      try {
        this.resetSelectedFileState()
        this.resetSelectedRestrictionFileState()
        this.revokePdfUrls()
        this.form.delete_file = false
        this.form.delete_restriction_file = false
        const page = await pageService.getPage(this.pageId)
        this.form.name = page.name || ''
        this.form.description = page.description || ''
        this.form.page = page.page || ''
        this.form.comment = page.comment || ''
        this.form.restriction_id = page.restriction_id || ''
        this.form.workstatus_id = page.workstatus_id || ''
        this.form.order_by = page.order_by !== undefined && page.order_by !== null ? page.order_by : null
        this.form.rotation = typeof page.rotation === 'number' ? page.rotation : 0
        this.form.rotation_restriction = typeof page.rotation_restriction === 'number' ? page.rotation_restriction : 0
        this.ocrStatus = page.ocr_status || 'not-applicable'
        this.hasCurrentFile = !!(page.current_file || page.location_file)
        this.hasRestrictionFile = !!page.restriction_file
        this.pageRecordTitle = page.record_title || ''
        this.pageRecordSignature = page.record_signature || ''
        // Lade Thumbnail
        if (this.hasCurrentFile) {
          try {
            const blob = await pageService.getThumbnail(this.pageId, 200)
            if (this.thumbnailUrl) URL.revokeObjectURL(this.thumbnailUrl)
            this.thumbnailUrl = URL.createObjectURL(blob)
          } catch {
            this.thumbnailUrl = null
          }
        }
        if (this.canViewManagedFiles) {
          await Promise.all([
            this.loadCurrentPdfPreview(),
            this.loadRestrictionPdfPreview(),
          ])
        }
        this.captureInitialFormSnapshot()
      } catch (err) {
        this.error = err.message || this.$t('pages.loadError')
      } finally {
        this.loading = false
      }
    },
    handleBeforeUnload(event) {
      if (!this.isDirty) {
        return
      }
      event.preventDefault()
      event.returnValue = ''
    },
    shouldBlockNavigation(targetPath) {
      return !!targetPath && !this.bypassUnsavedChangesGuard && this.isDirty && targetPath !== this.$route.fullPath
    },
    openUnsavedChangesDialog(targetPath) {
      this.pendingNavigationTarget = targetPath
      this.showUnsavedChangesDialog = true
    },
    closeUnsavedChangesDialog() {
      this.showUnsavedChangesDialog = false
      this.pendingNavigationTarget = null
    },
    async proceedWithPendingNavigation() {
      if (!this.pendingNavigationTarget) {
        return
      }

      const targetPath = this.pendingNavigationTarget
      this.showUnsavedChangesDialog = false
      this.pendingNavigationTarget = null
      this.bypassUnsavedChangesGuard = true

      try {
        await this.$router.push(targetPath)
      } finally {
        this.$nextTick(() => {
          this.bypassUnsavedChangesGuard = false
        })
      }
    },
    async discardPendingNavigation() {
      await this.proceedWithPendingNavigation()
    },
    async saveAndContinueNavigation() {
      if (!this.pendingNavigationTarget) {
        this.closeUnsavedChangesDialog()
        return
      }

      await this.handleSubmit({ redirectTo: this.pendingNavigationTarget })
    },
    async navigateToAdjacentPage(offset) {
      const targetIndex = this.currentPageIndex + offset
      const targetPage = this.pageSequence[targetIndex]

      if (!targetPage) {
        return
      }

      const targetPath = `/records/${this.recordId}/pages/${targetPage.id}/edit`
      if (this.shouldBlockNavigation(targetPath)) {
        this.openUnsavedChangesDialog(targetPath)
        return
      }

      await this.$router.push(targetPath)
    },
    onFileChange(event) {
      const file = event.target.files?.[0]
      this.selectedFile = file || null
      this.selectedFileName = file?.name || ''
      this.filePageError = null

      if (file && this.isEditMode) {
        this.validateSinglePagePdfSelection(file, event, {
          setError: (message) => {
            this.filePageError = message
          },
          clearSelection: () => {
            this.selectedFile = null
            this.selectedFileName = ''
          },
        })
      }
    },
    onRestrictionFileChange(event) {
      const file = event.target.files?.[0]
      this.selectedRestrictionFile = file || null
      this.selectedRestrictionFileName = file?.name || ''
      this.restrictionFilePageError = null

      if (file) {
        this.validateSinglePagePdfSelection(file, event, {
          setError: (message) => {
            this.restrictionFilePageError = message
          },
          clearSelection: () => {
            this.selectedRestrictionFile = null
            this.selectedRestrictionFileName = ''
          },
        })
      }
    },
    validateSinglePagePdfSelection(file, event, handlers) {
      const reader = new FileReader()
      reader.onload = (loadEvent) => {
        try {
          const bytes = new Uint8Array(loadEvent.target.result)
          const text = new TextDecoder('latin1').decode(bytes)
          const matches = text.match(/\/Type\s*\/Page[^s]/g)
          const pageCount = matches ? matches.length : 0
          if (pageCount > 1) {
            handlers.setError(this.$t('pages.uploadSinglePageError'))
            handlers.clearSelection()
            event.target.value = ''
          }
        } catch {
          // If we can't parse, let the backend validate
        }
      }
      reader.readAsArrayBuffer(file)
    },
    async loadCurrentPdfPreview() {
      if (!this.pageId || !this.hasCurrentFile) {
        return
      }
      try {
        const blob = await pageService.getViewPdf(this.pageId)
        if (this.currentPdfBlobUrl) {
          URL.revokeObjectURL(this.currentPdfBlobUrl)
        }
        this.currentPdfBlobUrl = URL.createObjectURL(blob)
      } catch {
        this.currentPdfBlobUrl = null
      }
    },
    async loadRestrictionPdfPreview() {
      if (!this.pageId || !this.hasRestrictionFile) {
        return
      }
      try {
        const blob = await pageService.getRestrictionViewPdf(this.pageId)
        if (this.restrictionPdfBlobUrl) {
          URL.revokeObjectURL(this.restrictionPdfBlobUrl)
        }
        this.restrictionPdfBlobUrl = URL.createObjectURL(blob)
      } catch {
        this.restrictionPdfBlobUrl = null
      }
    },
    async downloadCurrentPdf() {
      try {
        const { blob, contentDisposition } = await pageService.downloadWatermarkedPdf(this.pageId)
        this.triggerBlobDownload(blob, contentDisposition, `${(this.form.name || 'page').replace(/\s+/g, '_')}.pdf`)
      } catch (err) {
        this.error = err.message || this.$t('pages.loadError')
      }
    },
    async downloadRestrictionPdf() {
      try {
        const { blob, contentDisposition } = await pageService.downloadRestrictionPdf(this.pageId)
        this.triggerBlobDownload(blob, contentDisposition, `${(this.form.name || 'page').replace(/\s+/g, '_')}_restricted.pdf`)
      } catch (err) {
        this.error = err.message || this.$t('pages.loadError')
      }
    },
    triggerBlobDownload(blob, contentDisposition, fallbackName) {
      const fileName = this.extractFilename(contentDisposition) || fallbackName
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    },
    extractFilename(contentDisposition) {
      if (!contentDisposition) return null
      const match = contentDisposition.match(/filename="?([^";]+)"?/i)
      return match ? match[1] : null
    },
    async handleSubmit(options = {}) {
      if ((!this.isEditMode && !this.canCreatePage) || (this.isEditMode && !this.canEditPage && !this.canManageFile)) {
        this.error = this.$t('messages.unauthorised')
        return
      }

      if (this.filePageError || this.restrictionFilePageError) {
        return
      }

      this.submitting = true
      this.error = null
      try {
        const payload = {
          name: this.form.name,
          description: this.form.description || null,
          page: this.form.page || null,
          comment: this.form.comment || null,
          record_id: this.recordId,
          restriction_id: this.form.restriction_id,
          workstatus_id: this.form.workstatus_id || null,
          order_by: this.form.order_by,
          file: this.selectedFile,
          restriction_file: this.selectedRestrictionFile,
          rotation: this.form.rotation,
          rotation_restriction: this.form.rotation_restriction,
        }

        if (this.isEditMode) {
          // user_scan can upload/remove files on existing pages but cannot edit metadata fields
          if (this.isUploadOnlyMode) {
            const page = await pageService.getPage(this.pageId)
            payload.name = page.name
            payload.description = page.description || null
            payload.page = page.page || null
            payload.comment = page.comment || null
            payload.restriction_id = page.restriction_id
            payload.workstatus_id = page.workstatus_id || null
            payload.rotation = typeof page.rotation === 'number' ? page.rotation : 0
            payload.rotation_restriction = typeof page.rotation_restriction === 'number' ? page.rotation_restriction : 0
          }
          payload.delete_file = this.form.delete_file
          payload.delete_restriction_file = this.form.delete_restriction_file
          await pageService.updatePage(this.pageId, payload)
        } else {
          await pageService.createPage(payload)
        }

        this.resetSelectedFileState()
        this.resetSelectedRestrictionFileState()
        this.form.delete_file = false
        this.form.delete_restriction_file = false
        this.captureInitialFormSnapshot()

        const redirectTarget = options.redirectTo || `/records/${this.recordId}/pages`
        this.showUnsavedChangesDialog = false
        this.pendingNavigationTarget = null
        await this.$router.push(redirectTarget)
      } catch (err) {
        this.error = err.message || this.$t('pages.saveError')
      } finally {
        this.submitting = false
      }
    },

    rotateLeft() {
      this.form.rotation = (this.form.rotation + 270) % 360
      if (![0, 90, 180, 270].includes(this.form.rotation)) {
        this.form.rotation = 0
      }
    },
    rotateRight() {
      this.form.rotation = (this.form.rotation + 90) % 360
      if (![0, 90, 180, 270].includes(this.form.rotation)) {
        this.form.rotation = 0
      }
    },
    rotateRestrictionLeft() {
      this.form.rotation_restriction = (this.form.rotation_restriction + 270) % 360
      if (![0, 90, 180, 270].includes(this.form.rotation_restriction)) {
        this.form.rotation_restriction = 0
      }
    },
    rotateRestrictionRight() {
      this.form.rotation_restriction = (this.form.rotation_restriction + 90) % 360
      if (![0, 90, 180, 270].includes(this.form.rotation_restriction)) {
        this.form.rotation_restriction = 0
      }
    },
  },
  // ...
  beforeUnmount() {
    window.removeEventListener('beforeunload', this.handleBeforeUnload)
    if (this.thumbnailUrl) URL.revokeObjectURL(this.thumbnailUrl)
    this.revokePdfUrls()
  },
}
</script>

<style scoped>
.page-form-container {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.ocr-pending-alert {
  margin-bottom: 1rem;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.form-header-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.page-navigation-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.page-navigation-toolbar-bottom {
  margin-top: 16px;
}

.page-navigation-status {
  font-size: 0.95rem;
  color: #555;
}

.rotation-preview-label {
  min-width: 180px;
  text-align: center;
  font-size: 0.95rem;
  color: #555;
}

.unsaved-changes-dialog {
  max-width: 560px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-dialog {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: min(560px, 90vw);
}

.modal-content {
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-title {
  margin: 0;
  font-size: 1.125rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  line-height: 1;
  color: #666;
  cursor: pointer;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
}

.page-form {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 24px;
}

.form-group {
  margin-bottom: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.form-control {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-text {
  display: block;
  margin-top: 4px;
  color: #666;
  font-size: 12px;
}

.form-text.text-info {
  color: #0d6efd;
}

.form-text.text-warning {
  color: #856404;
}

.form-text.text-danger {
  color: #dc3545;
}

.checkbox-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.pdf-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
  margin-top: 24px;
}

.pdf-preview-card {
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 16px;
  background: #fafafa;
}

.pdf-preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.pdf-preview-header h2 {
  margin: 0;
  font-size: 1rem;
}

.pdf-preview-actions {
  display: flex;
  gap: 8px;
}

.pdf-preview-viewer {
  min-height: 280px;
  border: 1px solid #e0e0e0;
  background: #fff;
}

.pdf-preview-placeholder {
  min-height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.loading {
  text-align: center;
  padding: 20px;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
