<template>
  <div class="page-form-container">
    <div class="form-header">
      <h1>{{ isEditMode ? $t('pages.editPage') : $t('pages.createPage') }}</h1>
      <router-link :to="`/records/${recordId}/pages`" class="btn btn-secondary">
        {{ $t('common.back') }}
      </router-link>
    </div>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <form v-if="!loading" class="page-form" @submit.prevent="handleSubmit">
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
      </div>

      <div class="form-actions">
        <button type="submit" class="btn btn-primary" :disabled="submitting">
          {{ submitting ? $t('common.saving') : $t('common.save') }}
        </button>
        <router-link :to="`/records/${recordId}/pages`" class="btn btn-secondary">
          {{ $t('common.cancel') }}
        </router-link>
      </div>
    </form>
  </div>
</template>

<script>
import { recordService } from '@/services/record'
import { pageService } from '@/services/page'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'PageForm',
  setup() {
    return {
      authStore: useAuthStore(),
    }
  },
  data() {
    return {
      loading: false,
      submitting: false,
      error: null,
      filePageError: null,
      restrictions: [],
      workstatuses: [],
      selectedFile: null,
      selectedFileName: '',
      hasCurrentFile: false,
      form: {
        name: '',
        description: '',
        page: '',
        comment: '',
        restriction_id: '',
        workstatus_id: '',
        order_by: null,
        delete_file: false,
      },
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
    canCreatePage() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_scan')
    },
    canEditPage() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_page')
    },
    canManageFile() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_scan')
    },
    isUploadOnlyMode() {
      return this.isEditMode && !this.canEditPage && this.canManageFile
    },
  },
  mounted() {
    this.loadMetadata()
    if (this.isEditMode) {
      this.loadPage()
    }
  },
  methods: {
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
      } catch (err) {
        this.error = err.message || this.$t('pages.metadataLoadError')
      }
    },
    async loadPage() {
      this.loading = true
      this.error = null
      try {
        const page = await pageService.getPage(this.pageId)
        this.form.name = page.name || ''
        this.form.description = page.description || ''
        this.form.page = page.page || ''
        this.form.comment = page.comment || ''
        this.form.restriction_id = page.restriction_id || ''
        this.form.workstatus_id = page.workstatus_id || ''
        this.form.order_by = page.order_by !== undefined && page.order_by !== null ? page.order_by : null
        this.hasCurrentFile = !!page.location_file
      } catch (err) {
        this.error = err.message || this.$t('pages.loadError')
      } finally {
        this.loading = false
      }
    },
    onFileChange(event) {
      const file = event.target.files?.[0]
      this.selectedFile = file || null
      this.selectedFileName = file?.name || ''
      this.filePageError = null

      if (file && this.isEditMode) {
        const reader = new FileReader()
        reader.onload = (e) => {
          try {
            const bytes = new Uint8Array(e.target.result)
            const text = new TextDecoder('latin1').decode(bytes)
            // Count individual page objects: /Type /Page (not /Pages)
            const matches = text.match(/\/Type\s*\/Page[^s]/g)
            const pageCount = matches ? matches.length : 0
            if (pageCount > 1) {
              this.filePageError = this.$t('pages.uploadSinglePageError')
              this.selectedFile = null
              this.selectedFileName = ''
              event.target.value = ''
            }
          } catch {
            // If we can't parse, let the backend validate
          }
        }
        reader.readAsArrayBuffer(file)
      }
    },
    async handleSubmit() {
      if ((!this.isEditMode && !this.canCreatePage) || (this.isEditMode && !this.canEditPage && !this.canManageFile)) {
        this.error = this.$t('messages.unauthorised')
        return
      }

      if (this.filePageError) {
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
          }
          payload.delete_file = this.form.delete_file
          await pageService.updatePage(this.pageId, payload)
        } else {
          await pageService.createPage(payload)
        }

        this.$router.push(`/records/${this.recordId}/pages`)
      } catch (err) {
        this.error = err.message || this.$t('pages.saveError')
      } finally {
        this.submitting = false
      }
    },
  },
}
</script>

<style scoped>
.page-form-container {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
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
