<template>
  <div class="record-form-container">
    <div class="form-header">
      <h1>{{ isEditMode ? $t('records.editRecord') : $t('records.createRecord') }}</h1>
      <router-link to="/records" class="btn btn-secondary">
        {{ $t('common.back') }}
      </router-link>
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
        />
      </div>

      <div class="form-group">
        <label for="description">{{ $t('records.description') }}</label>
        <textarea
          id="description"
          v-model="form.description"
          class="form-control"
          :placeholder="$t('records.descriptionPlaceholder')"
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
        <button type="submit" class="btn btn-primary" :disabled="submitting">
          {{ submitting ? $t('common.saving') : $t('common.save') }}
        </button>
        <router-link to="/records" class="btn btn-secondary">
          {{ $t('common.cancel') }}
        </router-link>
      </div>
    </form>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { recordService } from '@/services/record'

export default defineComponent({
  name: 'RecordForm',
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
    }
  },
  computed: {
    isEditMode() {
      return !!this.$route.params.id
    },
    recordId() {
      return this.$route.params.id
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

.alert {
  padding: 12px 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.alert-success {
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  color: #155724;
}

.alert-danger {
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
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

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  text-decoration: none;
  display: inline-block;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
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
