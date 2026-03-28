<template>
  <div class="record-import-container">
    <div class="record-import-header">
      <h1>{{ $t('admin.recordImport') }}</h1>
      <p class="description">{{ $t('admin.recordImportDescription') }}</p>
    </div>

    <div class="card import-form">
      <label class="form-label" for="xlsx-file">{{ $t('admin.selectImportFile') }}</label>
      <input
        id="xlsx-file"
        type="file"
        accept=".xlsx"
        class="form-control"
        @change="onFileChange"
      />
      <p class="hint">{{ $t('admin.importHint') }}</p>

      <div class="actions">
        <button class="btn btn-primary" :disabled="isImporting" @click="startImport">
          {{ isImporting ? $t('admin.importInProgress') : $t('admin.runImport') }}
        </button>
      </div>

      <div v-if="errorMessage" class="alert alert-danger">
        {{ errorMessage }}
      </div>
    </div>

    <div v-if="importResult" class="card result-card">
      <h2>{{ $t('admin.importSummary') }}</h2>
      <div class="summary-row">
        <strong>{{ $t('admin.importedCount') }}:</strong>
        <span>{{ importResult.imported }}</span>
      </div>
      <div class="summary-row">
        <strong>{{ $t('admin.skippedCount') }}:</strong>
        <span>{{ importResult.skipped }}</span>
      </div>

      <h3>{{ $t('admin.errorReport') }}</h3>
      <div v-if="!importResult.errors || importResult.errors.length === 0" class="text-muted">
        {{ $t('admin.noErrors') }}
      </div>
      <table v-else class="error-table">
        <thead>
          <tr>
            <th>{{ $t('admin.row') }}</th>
            <th>{{ $t('admin.message') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in importResult.errors" :key="index">
            <td>{{ item.row }}</td>
            <td>{{ item.message }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { recordService } from '@/services/record'

export default defineComponent({
  name: 'RecordImport',
  data() {
    return {
      selectedFile: null,
      isImporting: false,
      errorMessage: '',
      importResult: null,
    }
  },
  methods: {
    onFileChange(event) {
      const file = event.target.files?.[0] || null
      this.selectedFile = file
      this.errorMessage = ''
    },
    async startImport() {
      this.errorMessage = ''
      this.importResult = null

      if (!this.selectedFile || !this.selectedFile.name.toLowerCase().endsWith('.xlsx')) {
        this.errorMessage = this.$t('admin.fileRequired')
        return
      }

      this.isImporting = true
      try {
        this.importResult = await recordService.importRecordsXlsx(this.selectedFile)
      } catch (error) {
        const detail = error?.detail
        this.errorMessage = typeof detail === 'string' ? detail : this.$t('common.error')
      } finally {
        this.isImporting = false
      }
    },
  },
})
</script>

<style scoped>
.record-import-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 1rem;
}

.record-import-header {
  margin-bottom: 1rem;
}

.description {
  color: #666;
  margin-top: 0.4rem;
}

.card {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.form-label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.hint {
  margin-top: 0.75rem;
  color: #666;
  font-size: 0.95rem;
}

.actions {
  margin-top: 1rem;
}

.summary-row {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.error-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.75rem;
}

.error-table th,
.error-table td {
  border: 1px solid #ddd;
  padding: 0.5rem;
  text-align: left;
}

.error-table th {
  background: #f6f6f6;
}
</style>
