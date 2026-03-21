<template>
  <div class="record-form-container">
    <div class="form-header">
      <h1>{{ isReadOnlyMode ? $t('common.view') : (isEditMode ? $t('records.editRecord') : $t('records.createRecord')) }}</h1>
      <div class="header-actions">
        <button v-if="isEditMode" type="button" class="btn btn-info" @click="toggleQrCode" :disabled="qrLoading">
          {{ showQrCode ? $t('records.hideQrCode') : $t('records.showQrCode') }}
        </button>
        <router-link v-if="isEditMode" :to="`/records/${recordId}/pages-gallery`" class="btn btn-primary">
          {{ $t('pages.galleryTitle') }}
        </router-link>
        <router-link v-if="isEditMode" :to="`/records/${recordId}/pages`" class="btn btn-info">
          {{ $t('pages.managePages') }}
        </router-link>
        <router-link to="/records" class="btn btn-secondary">
          {{ $t('common.back') }}
        </router-link>
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

    <div v-if="isEditMode && showQrCode" class="record-qr-section">
      <h2>{{ $t('records.qrCodeTitle') }}</h2>

      <div v-if="qrLoading" class="loading">{{ $t('common.loading') }}</div>
      <div v-else-if="qrError" class="alert alert-danger">{{ qrError }}</div>

      <div v-else-if="qrData" class="qr-content">
        <img
          :src="`data:image/png;base64,${qrData.qr_code}`"
          :alt="$t('records.qrCodeAlt')"
          class="record-qr-image"
        />
        <div class="qr-link">
          <strong>{{ $t('records.publicLinkLabel') }}:</strong>
          <a :href="qrData.public_url" target="_blank" rel="noopener noreferrer">{{ qrData.public_url }}</a>
        </div>
      </div>
    </div>

    <!-- Form -->
    <form v-if="!loading" @submit.prevent="handleSubmit" class="record-form">
      <div class="form-group">
        <label for="title">{{ $t('records.title') }} <span class="required">*</span></label>
        <input
          id="title"
          v-model="form.title"
          type="text"
          class="form-control"
          :placeholder="$t('records.titlePlaceholder')"
          :readonly="isReadOnlyMode"
          required
        />
      </div>

      <div class="form-group">
        <label for="signature">{{ $t('records.signature') }}</label>
        <input
          id="signature"
          v-model="form.signature"
          type="text"
          class="form-control"
          :placeholder="$t('records.signaturePlaceholder')"
          :readonly="isReadOnlyMode"
        />
      </div>

      <div class="form-group">
        <label for="description">{{ $t('records.description') }}</label>
        <textarea
          id="description"
          v-model="form.description"
          class="form-control"
          :placeholder="$t('records.descriptionPlaceholder')"
          :readonly="isReadOnlyMode"
          rows="4"
        />
      </div>

      <div class="form-group">
        <label for="comment">{{ $t('records.comment') }}</label>
        <textarea
          id="comment"
          v-model="form.comment"
          class="form-control"
          :placeholder="$t('records.commentPlaceholder')"
          :readonly="isReadOnlyMode"
          rows="3"
        />
      </div>

      <div class="form-group">
        <label for="keywords_names">{{ $t('records.keywordsNames') }}</label>
        <input
          id="keywords_names"
          v-model="form.keywords_names"
          type="text"
          class="form-control"
          :placeholder="$t('records.keywordsNamesPlaceholder')"
          :readonly="isReadOnlyMode"
        />
        <small class="form-text">{{ $t('records.keywordsHelp') }}</small>
      </div>

      <div class="form-group">
        <label for="keywords_locations">{{ $t('records.keywordsLocations') }}</label>
        <input
          id="keywords_locations"
          v-model="form.keywords_locations"
          type="text"
          class="form-control"
          :placeholder="$t('records.keywordsLocationsPlaceholder')"
          :readonly="isReadOnlyMode"
        />
        <small class="form-text">{{ $t('records.keywordsHelp') }}</small>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="restriction">{{ $t('records.restriction') }} <span class="required">*</span></label>
          <select
            id="restriction"
            v-model="form.restriction_id"
            class="form-control"
            :disabled="isReadOnlyMode"
            required
          >
            <option value="">{{ $t('records.selectRestriction') }}</option>
            <option v-for="restriction in restrictions" :key="restriction.id" :value="restriction.id">
              {{ restriction.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="workstatus">{{ $t('records.workstatus') }} <span class="required">*</span></label>
          <select
            id="workstatus"
            v-model="form.workstatus_id"
            class="form-control"
            :disabled="isReadOnlyMode"
            required
          >
            <option value="">{{ $t('records.selectWorkStatus') }}</option>
            <option v-for="status in workstatuses" :key="status.id" :value="status.id">
              {{ status.status }} {{ status.area ? `(${status.area})` : '' }}
            </option>
          </select>
        </div>
      </div>

      <div class="form-actions">
        <button v-if="canEditRecord" type="submit" class="btn btn-primary" :disabled="submitting">
          {{ submitting ? $t('common.saving') : $t('common.save') }}
        </button>
        <router-link to="/records" class="btn btn-secondary">
          {{ canEditRecord ? $t('common.cancel') : $t('common.back') }}
        </router-link>
      </div>
    </form>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { recordService } from '@/services/record'
import { useAuthStore } from '@/stores/auth'

export default defineComponent({
  name: 'RecordForm',
  setup() {
    const authStore = useAuthStore()
    return { authStore }
  },
  data() {
    return {
      form: {
        title: '',
        signature: '',
        description: '',
        comment: '',
        keywords_names: '',
        keywords_locations: '',
        restriction_id: '',
        workstatus_id: '',
      },
      restrictions: [],
      workstatuses: [],
      loading: false,
      submitting: false,
      error: null,
      successMessage: null,
      showQrCode: false,
      qrLoading: false,
      qrError: null,
      qrData: null,
    }
  },
  computed: {
    isEditMode() {
      return !!this.$route.params.id
    },
    recordId() {
      return this.$route.params.id
    },
    canEditRecord() {
      return this.authStore.hasRole('admin') || this.authStore.hasRole('user_record')
    },
    isReadOnlyMode() {
      return this.isEditMode && !this.canEditRecord
    },
  },
  mounted() {
    this.loadMetadata()
    if (this.isEditMode) {
      this.loadRecord()
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

        // Set default values if creating new record
        if (!this.isEditMode && this.restrictions.length > 0) {
          const noneRestriction = this.restrictions.find(r => r.name === 'none')
          if (noneRestriction) {
            this.form.restriction_id = noneRestriction.id
          }
        }

        if (!this.isEditMode && this.workstatuses.length > 0) {
          const notYetStatus = this.workstatuses.find(w => w.status === 'not yet')
          if (notYetStatus) {
            this.form.workstatus_id = notYetStatus.id
          }
        }
      } catch (err) {
        this.error = err.message || this.$t('records.metadataLoadError')
        console.error('Error loading metadata:', err)
      }
    },

    async loadRecord() {
      this.loading = true
      this.error = null

      try {
        const record = await recordService.getRecord(this.recordId)

        this.form = {
          title: record.title || '',
          signature: record.signature || '',
          description: record.description || '',
          comment: record.comment || '',
          keywords_names: record.keywords_names || '',
          keywords_locations: record.keywords_locations || '',
          restriction_id: record.restriction_id || '',
          workstatus_id: record.workstatus_id || '',
        }
      } catch (err) {
        this.error = err.message || this.$t('records.loadError')
        console.error('Error loading record:', err)
      } finally {
        this.loading = false
      }
    },

    async handleSubmit() {
      if (!this.canEditRecord) {
        return
      }

      this.submitting = true
      this.error = null
      this.successMessage = null

      try {
        const data = {
          title: this.form.title,
          signature: this.form.signature || null,
          description: this.form.description || null,
          comment: this.form.comment || null,
          keywords_names: this.form.keywords_names || '',
          keywords_locations: this.form.keywords_locations || '',
          restriction_id: this.form.restriction_id,
          workstatus_id: this.form.workstatus_id,
        }

        if (this.isEditMode) {
          await recordService.updateRecord(this.recordId, data)
        } else {
          await recordService.createRecord(data)
        }

        // Redirect to record list after successful save
        this.$router.push('/records')
      } catch (err) {
        this.error = err.message || this.$t('records.saveError')
        console.error('Error saving record:', err)
      } finally {
        this.submitting = false
      }
    },

    async toggleQrCode() {
      this.showQrCode = !this.showQrCode
      if (!this.showQrCode || this.qrData || this.qrLoading) {
        return
      }

      this.qrLoading = true
      this.qrError = null
      try {
        this.qrData = await recordService.getRecordQrCode(this.recordId)
      } catch (err) {
        this.qrError = err?.detail || this.$t('records.qrLoadError')
      } finally {
        this.qrLoading = false
      }
    },
  },
})
</script>

<style scoped>
.record-form-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.form-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
}

.loading {
  text-align: center;
  padding: 40px;
  font-size: 16px;
  color: #666;
}

.record-qr-section {
  margin-bottom: 20px;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 16px;
  background: #fff;
}

.record-qr-section h2 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 20px;
}

.qr-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-qr-image {
  width: 35mm;
  height: 35mm;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.qr-link {
  word-break: break-all;
}

.record-form {
  background: white;
  padding: 30px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-weight: 500;
  margin-bottom: 5px;
  font-size: 14px;
}

.required {
  color: #dc3545;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

textarea.form-control {
  resize: vertical;
  min-height: 80px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.form-text {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #6c757d;
  font-style: italic;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .form-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .record-form {
    padding: 20px;
  }
}
</style>
