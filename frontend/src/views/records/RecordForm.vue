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
        <label for="signature2">{{ $t('records.signature2') }}</label>
        <input
          id="signature2"
          v-model="form.signature2"
          type="text"
          class="form-control"
          :placeholder="$t('records.signature2Placeholder')"
          :readonly="isReadOnlyMode"
        />
      </div>

      <div class="form-group">
        <label for="subtitle">{{ $t('records.subtitle') }}</label>
        <input
          id="subtitle"
          v-model="form.subtitle"
          type="text"
          class="form-control"
          :placeholder="$t('records.subtitlePlaceholder')"
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

      <div class="form-row three-columns">
        <div class="form-group">
          <label for="year">{{ $t('records.year') }}</label>
          <input
            id="year"
            v-model="form.year"
            type="text"
            class="form-control"
            :placeholder="$t('records.yearPlaceholder')"
            :readonly="isReadOnlyMode"
          />
        </div>

        <div class="form-group">
          <label for="isbn">{{ $t('records.isbn') }}</label>
          <input
            id="isbn"
            v-model="form.isbn"
            type="text"
            class="form-control"
            :placeholder="$t('records.isbnPlaceholder')"
            :readonly="isReadOnlyMode"
          />
        </div>

        <div class="form-group">
          <label for="number_pages">{{ $t('records.numberPages') }}</label>
          <input
            id="number_pages"
            v-model="form.number_pages"
            type="text"
            class="form-control"
            :placeholder="$t('records.numberPagesPlaceholder')"
            :readonly="isReadOnlyMode"
          />
        </div>
      </div>

      <div class="form-row three-columns">
        <div class="form-group">
          <label for="edition">{{ $t('records.edition') }}</label>
          <input
            id="edition"
            v-model="form.edition"
            type="text"
            class="form-control"
            :placeholder="$t('records.editionPlaceholder')"
            :readonly="isReadOnlyMode"
          />
        </div>

        <div class="form-group">
          <label for="reihe">{{ $t('records.reihe') }}</label>
          <input
            id="reihe"
            v-model="form.reihe"
            type="text"
            class="form-control"
            :placeholder="$t('records.reihePlaceholder')"
            :readonly="isReadOnlyMode"
          />
        </div>

        <div class="form-group">
          <label for="volume">{{ $t('records.volume') }}</label>
          <input
            id="volume"
            v-model="form.volume"
            type="text"
            class="form-control"
            :placeholder="$t('records.volumePlaceholder')"
            :readonly="isReadOnlyMode"
          />
        </div>
      </div>

      <div class="form-row two-columns">
        <div class="form-group">
          <label for="jahrgang">{{ $t('records.jahrgang') }}</label>
          <input
            id="jahrgang"
            v-model="form.jahrgang"
            type="text"
            class="form-control"
            :placeholder="$t('records.jahrgangPlaceholder')"
            :readonly="isReadOnlyMode"
          />
        </div>

        <div class="form-group">
          <label for="bibl_nr">{{ $t('records.biblNr') }}</label>
          <input
            id="bibl_nr"
            v-model="form.bibl_nr"
            type="text"
            class="form-control"
            :placeholder="$t('records.biblNrPlaceholder')"
            :readonly="isReadOnlyMode"
          />
        </div>
      </div>

      <div class="form-group">
        <label for="enter_information">{{ $t('records.enterInformation') }}</label>
        <textarea
          id="enter_information"
          v-model="form.enter_information"
          class="form-control"
          :placeholder="$t('records.enterInformationPlaceholder')"
          :readonly="isReadOnlyMode"
          rows="3"
        />
      </div>

      <div class="form-group">
        <label for="indecies">{{ $t('records.indecies') }}</label>
        <textarea
          id="indecies"
          v-model="form.indecies"
          class="form-control"
          :placeholder="$t('records.indeciesPlaceholder')"
          :readonly="isReadOnlyMode"
          rows="3"
        />
      </div>

      <div class="form-row two-columns">
        <div class="form-group">
          <label for="enter_date">{{ $t('records.enterDate') }}</label>
          <input
            id="enter_date"
            v-model="form.enter_date"
            type="date"
            class="form-control"
            :readonly="isReadOnlyMode"
            :disabled="isReadOnlyMode"
          />
        </div>

        <div class="form-group">
          <label for="sort_out_date">{{ $t('records.sortOutDate') }}</label>
          <input
            id="sort_out_date"
            v-model="form.sort_out_date"
            type="date"
            class="form-control"
            :readonly="isReadOnlyMode"
            :disabled="isReadOnlyMode"
          />
        </div>
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

        <div class="form-group">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <label>{{ $t('records.authors') }}</label>
            <button v-if="canEditRecord" type="button" class="btn btn-primary btn-sm" @click="showAuthorDialog = true">
              + {{ $t('records.addAuthor') }}
            </button>
          </div>

          <div v-if="record_authors.length === 0" class="form-text text-muted">
            {{ $t('records.noAuthors') }}
          </div>
          <table v-else class="authors-table">
            <thead>
              <tr>
                <th>#</th>
                <th>{{ $t('records.authorName') }}</th>
                <th>{{ $t('records.authorType') }}</th>
                <th v-if="canEditRecord" style="width: 150px;"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(ra, index) in record_authors" :key="ra.id || `${ra.author_id}-${index}`">
                <td>{{ index + 1 }}</td>
                <td>{{ getAuthorDisplayName(ra) }}</td>
                <td>{{ getAuthorTypeDisplayName(ra) }}</td>
                <td v-if="canEditRecord" class="authors-actions-cell">
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-secondary"
                    @click="moveAuthorUp(index)"
                    :disabled="index === 0"
                    :title="$t('common.moveUp')"
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-secondary"
                    @click="moveAuthorDown(index)"
                    :disabled="index === record_authors.length - 1"
                    :title="$t('common.moveDown')"
                  >
                    ↓
                  </button>
                  <button type="button" class="btn btn-sm btn-danger" @click="removeAuthorRow(index)">
                    {{ $t('common.delete') }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Author Dialog -->
        <div v-if="showAuthorDialog" class="modal-overlay" @click.self="showAuthorDialog = false">
          <div class="modal-dialog">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">{{ $t('records.addAuthor') }}</h5>
                <button type="button" class="btn-close" @click="showAuthorDialog = false"></button>
              </div>
              <div class="modal-body">
                <div class="form-section">
                  <h6 class="mb-3">{{ $t('records.selectAuthor') }}</h6>
                  <select id="select-author" class="form-control mb-3" @change="addAuthorFromDropdown">
                    <option value="">{{ $t('records.selectAuthor') }}</option>
                    <option v-for="author in authors" :key="author.id" :value="String(author.id)">
                      {{ formatAuthorLabel(author) }}
                    </option>
                  </select>
                  <div class="form-group">
                    <label for="select-authortype">{{ $t('records.authorType') }}</label>
                    <select id="select-authortype" v-model="newAuthor.authortype_id" class="form-control">
                      <option value="">{{ $t('records.selectAuthorType') }}</option>
                      <option v-for="item in authorTypes" :key="item.id" :value="String(item.id)">
                        {{ item.authortype }}
                      </option>
                    </select>
                  </div>
                </div>

                <hr />

                <div class="form-section">
                  <h6 class="mb-3">{{ $t('records.createAuthor') }}</h6>
                  <div class="form-group">
                    <label for="author_title">{{ $t('records.authorTitle') }}</label>
                    <input id="author_title" v-model="newAuthor.title" type="text" class="form-control" />
                  </div>
                  <div class="form-group">
                    <label for="author_last_name">{{ $t('records.authorLastName') }} <span class="required">*</span></label>
                    <input id="author_last_name" v-model="newAuthor.last_name" type="text" class="form-control" />
                  </div>
                  <div class="form-group">
                    <label for="author_first_name">{{ $t('records.authorFirstName') }}</label>
                    <input id="author_first_name" v-model="newAuthor.first_name" type="text" class="form-control" />
                  </div>
                </div>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" @click="showAuthorDialog = false">
                  {{ $t('common.cancel') }}
                </button>
                <button type="button" class="btn btn-info" @click="createAuthor" :disabled="creatingAuthor">
                  {{ creatingAuthor ? $t('common.saving') : $t('records.createAuthor') }}
                </button>
              </div>
            </div>
          </div>
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
            <option v-for="restriction in restrictions" :key="restriction.id" :value="String(restriction.id)">
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
            <option v-for="status in workstatuses" :key="status.id" :value="String(status.id)">
              {{ status.status }} {{ status.area ? `(${status.area})` : '' }}
            </option>
          </select>
        </div>
      </div>

      <div class="form-row two-columns">
        <div class="form-group">
          <label for="record_condition">{{ $t('records.recordCondition') }}</label>
          <select
            id="record_condition"
            v-model="form.record_condition_id"
            class="form-control"
            :disabled="isReadOnlyMode"
          >
            <option value="">{{ $t('records.selectRecordCondition') }}</option>
            <option v-for="item in recordConditions" :key="item.id" :value="String(item.id)">
              {{ item.condition }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="loantype">{{ $t('records.loanType') }}</label>
          <select
            id="loantype"
            v-model="form.loantype_id"
            class="form-control"
            :disabled="isReadOnlyMode"
          >
            <option value="">{{ $t('records.selectLoanType') }}</option>
            <option v-for="item in loanTypes" :key="item.id" :value="String(item.id)">
              {{ item.loan }}{{ item.subtype ? ` (${item.subtype})` : '' }}
            </option>
          </select>
        </div>
      </div>

      <div class="form-row three-columns">
        <div class="form-group">
          <label for="lettering">{{ $t('records.lettering') }}</label>
          <select
            id="lettering"
            v-model="form.lettering_id"
            class="form-control"
            :disabled="isReadOnlyMode"
          >
            <option value="">{{ $t('records.selectLettering') }}</option>
            <option v-for="item in letterings" :key="item.id" :value="String(item.id)">
              {{ item.lettering }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="publicationtype">{{ $t('records.publicationType') }}</label>
          <select
            id="publicationtype"
            v-model="form.publicationtype_id"
            class="form-control"
            :disabled="isReadOnlyMode"
          >
            <option value="">{{ $t('records.selectPublicationType') }}</option>
            <option v-for="item in publicationTypes" :key="item.id" :value="String(item.id)">
              {{ item.publicationtype }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="publisher">{{ $t('records.publisher') }}</label>
          <select
            id="publisher"
            v-model="form.publisher_id"
            class="form-control"
            :disabled="isReadOnlyMode"
          >
            <option value="">{{ $t('records.selectPublisher') }}</option>
            <option v-for="item in publishers" :key="item.id" :value="String(item.id)">
              {{ item.companyname }}{{ item.town ? ` (${item.town})` : '' }}
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
        signature2: '',
        subtitle: '',
        description: '',
        comment: '',
        year: '',
        isbn: '',
        number_pages: '',
        edition: '',
        reihe: '',
        volume: '',
        jahrgang: '',
        enter_information: '',
        indecies: '',
        enter_date: '',
        sort_out_date: '',
        bibl_nr: '',
        keywords_names: '',
        keywords_locations: '',
        restriction_id: '',
        workstatus_id: '',
        record_condition_id: '',
        loantype_id: '',
        lettering_id: '',
        publicationtype_id: '',
        publisher_id: '',
      },
      restrictions: [],
      workstatuses: [],
      loanTypes: [],
      recordConditions: [],
      letterings: [],
      publicationTypes: [],
      publishers: [],
      authorTypes: [],
      authors: [],
      loading: false,
      submitting: false,
      creatingAuthor: false,
      error: null,
      successMessage: null,
      showQrCode: false,
      qrLoading: false,
      qrError: null,
      qrData: null,
      record_authors: [],
      newAuthor: {
        title: '',
        last_name: '',
        first_name: '',
        authortype_id: '',
      },
      showAuthorDialog: false,
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
  async mounted() {
    await this.loadMetadata()
    if (this.isEditMode) {
      this.loadRecord()
    }
  },
  methods: {
    async loadMetadata() {
      try {
        const [
          restrictionsResponse,
          workstatusResponse,
          loanTypesResponse,
          recordConditionsResponse,
          letteringsResponse,
          publicationTypesResponse,
          publishersResponse,
        ] = await Promise.all([
          recordService.getRestrictions(),
          recordService.getWorkStatus(),
          recordService.listLoanTypes(),
          recordService.listRecordConditions(),
          recordService.listLetterings(),
          recordService.listPublicationTypes(),
          recordService.listPublishers({ limit: 500 }),
        ])

        this.restrictions = restrictionsResponse.items || []
        this.workstatuses = workstatusResponse.items || []
        this.loanTypes = loanTypesResponse.items || []
        this.recordConditions = recordConditionsResponse.items || []
        this.letterings = letteringsResponse.items || []
        this.publicationTypes = publicationTypesResponse.items || []
        this.publishers = publishersResponse.items || []

        // Load author metadata separately so a failure there does not block other fields.
        try {
          const [authorTypesResponse, authorsResponse] = await Promise.all([
            recordService.listAuthorTypes(),
            recordService.listAuthors({ limit: 200 }),
          ])
          this.authorTypes = authorTypesResponse.items || []
          this.authors = authorsResponse.items || []
        } catch (authorErr) {
          console.error('Error loading author metadata:', authorErr)
          this.authorTypes = []
          this.authors = []
        }

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
          signature2: record.signature2 || '',
          subtitle: record.subtitle || '',
          description: record.description || '',
          comment: record.comment || '',
          year: record.year || '',
          isbn: record.isbn || '',
          number_pages: record.number_pages || '',
          edition: record.edition || '',
          reihe: record.reihe || '',
          volume: record.volume || '',
          jahrgang: record.jahrgang || '',
          enter_information: record.enter_information || '',
          indecies: record.indecies || '',
          enter_date: record.enter_date || '',
          sort_out_date: record.sort_out_date || '',
          bibl_nr: record.bibl_nr || '',
          keywords_names: record.keywords_names || '',
          keywords_locations: record.keywords_locations || '',
          restriction_id: record.restriction_id || '',
          workstatus_id: record.workstatus_id || '',
          record_condition_id: record.record_condition_id || '',
          loantype_id: record.loantype_id || '',
          lettering_id: record.lettering_id || '',
          publicationtype_id: record.publicationtype_id || '',
          publisher_id: record.publisher_id || '',
        }
        this.record_authors = (record.record_authors || []).map((ra, index) => ({
          id: ra.id,
          author_id: ra.author_id || ra.author?.id || '',
          authortype_id: ra.authortype_id || ra.authortype?.id || '',
          order: ra.order ?? index + 1,
          author: ra.author || null,
          authortype: ra.authortype || null,
        }))
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
          signature2: this.form.signature2 || null,
          subtitle: this.form.subtitle || null,
          description: this.form.description || null,
          comment: this.form.comment || null,
          year: this.form.year || null,
          isbn: this.form.isbn || null,
          number_pages: this.form.number_pages || null,
          edition: this.form.edition || null,
          reihe: this.form.reihe || null,
          volume: this.form.volume || null,
          jahrgang: this.form.jahrgang || null,
          enter_information: this.form.enter_information || null,
          indecies: this.form.indecies || null,
          enter_date: this.form.enter_date || null,
          sort_out_date: this.form.sort_out_date || null,
          bibl_nr: this.form.bibl_nr || null,
          keywords_names: this.form.keywords_names || '',
          keywords_locations: this.form.keywords_locations || '',
          restriction_id: this.form.restriction_id,
          workstatus_id: this.form.workstatus_id,
          record_condition_id: this.form.record_condition_id || null,
          loantype_id: this.form.loantype_id || null,
          lettering_id: this.form.lettering_id || null,
          publicationtype_id: this.form.publicationtype_id || null,
          publisher_id: this.form.publisher_id || null,
          record_authors: this.record_authors
            .filter(row => row.author_id)
            .map((row, index) => ({
              author_id: row.author_id,
              authortype_id: row.authortype_id || null,
              order: index + 1,
            })),
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

    moveAuthorUp(index) {
      if (index > 0) {
        const temp = this.record_authors[index]
        this.record_authors[index] = this.record_authors[index - 1]
        this.record_authors[index - 1] = temp
        this.updateAuthorOrders()
      }
    },

    moveAuthorDown(index) {
      if (index < this.record_authors.length - 1) {
        const temp = this.record_authors[index]
        this.record_authors[index] = this.record_authors[index + 1]
        this.record_authors[index + 1] = temp
        this.updateAuthorOrders()
      }
    },

    updateAuthorOrders() {
      this.record_authors.forEach((row, idx) => {
        row.order = idx + 1
      })
    },

    addAuthorFromDropdown(event) {
      const authorId = event.target.value
      if (!authorId) return
      const author = this.authors.find(a => a.id === authorId)
      if (!author) return
      this.record_authors.push({
        author_id: authorId,
        author,
        authortype_id: this.newAuthor.authortype_id || '',
        order: this.record_authors.length + 1,
      })
      event.target.value = ''
      this.newAuthor.authortype_id = ''
    },

    removeAuthorRow(index) {
      this.record_authors.splice(index, 1)
      this.updateAuthorOrders()
    },

    formatAuthorLabel(author) {
      if (!author) {
        return ''
      }
      const base = [author.last_name, author.first_name].filter(Boolean).join(', ')
      return author.title ? `${base} (${author.title})` : base
    },

    getAuthorDisplayName(row) {
      if (row.author) {
        return this.formatAuthorLabel(row.author)
      }
      const author = this.authors.find(item => item.id === row.author_id)
      return this.formatAuthorLabel(author)
    },

    getAuthorTypeDisplayName(row) {
      if (row.authortype?.authortype) {
        return row.authortype.authortype
      }
      const authorType = this.authorTypes.find(item => item.id === row.authortype_id)
      return authorType?.authortype || ''
    },

    async createAuthor() {
      const lastName = this.newAuthor.last_name?.trim()
      if (!lastName) {
        this.error = this.$t('records.authorLastNameRequired')
        return
      }

      this.creatingAuthor = true
      this.error = null
      try {
        const created = await recordService.createAuthor({
          title: this.newAuthor.title?.trim() || null,
          last_name: lastName,
          first_name: this.newAuthor.first_name?.trim() || null,
        })
        this.authors.push(created)
        this.authors.sort((a, b) => this.formatAuthorLabel(a).localeCompare(this.formatAuthorLabel(b)))

          this.record_authors.push({
            author_id: created.id,
            author: created,
            authortype_id: this.newAuthor.authortype_id || '',
            order: this.record_authors.length + 1,
          })

        this.newAuthor = {
          title: '',
          last_name: '',
          first_name: '',
            authortype_id: '',
          }
          this.showAuthorDialog = false
      } catch (err) {
        this.error = err.message || err.detail || this.$t('records.saveError')
      } finally {
        this.creatingAuthor = false
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

  .authors-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }

  .authors-table th,
  .authors-table td {
    border: 1px solid #ddd;
    padding: 6px 10px;
    text-align: left;
  }

  .authors-table th {
    background: #f5f5f5;
    font-weight: 600;
  }

  .authors-table tbody tr:nth-child(even) {
    background: #fafafa;
  }

  .authors-actions-cell {
    width: 1%;
    white-space: nowrap;
  }
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-group {
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.two-columns {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.three-columns {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
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
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.form-section {
  margin-bottom: 16px;
}

.form-section h6 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.d-flex {
  display: flex;
}

.justify-content-between {
  justify-content: space-between;
}

.align-items-center {
  align-items: center;
}

.mb-3 {
  margin-bottom: 12px;
}
</style>
