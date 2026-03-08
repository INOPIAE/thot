<template>
  <div class="users-container">
    <div class="users-header">
      <h1>{{ $t('admin.userManagement') }}</h1>
    </div>

    <!-- User Statistics -->
    <div class="user-statistics" v-if="!loading">
      <div class="stat-card">
        <div class="stat-value">{{ totalUsers }}</div>
        <div class="stat-label">{{ $t('admin.totalUsers') }}</div>
      </div>
      <div class="stat-card stat-success">
        <div class="stat-value">{{ statistics.active || 0 }}</div>
        <div class="stat-label">{{ $t('admin.activeUsers') }}</div>
      </div>
      <div class="stat-card stat-danger">
        <div class="stat-value">{{ statistics.inactive || 0 }}</div>
        <div class="stat-label">{{ $t('admin.inactiveUsers') }}</div>
      </div>
    </div>

    <!-- Search and Filter Section -->
    <div class="users-search">
      <div class="search-fields">
        <div class="form-group">
          <label for="search-username">{{ $t('admin.filterUsername') }}</label>
          <input
            id="search-username"
            v-model="search.username"
            type="text"
            class="form-control"
            :placeholder="$t('admin.usernamePlaceholder')"
            @input="handleSearch"
          />
        </div>

        <div class="form-group">
          <label for="search-email">{{ $t('admin.filterEmail') }}</label>
          <input
            id="search-email"
            v-model="search.email"
            type="text"
            class="form-control"
            :placeholder="$t('admin.emailPlaceholder')"
            @input="handleSearch"
          />
        </div>

        <div class="form-group">
          <label for="page-size">{{ $t('common.itemsPerPage') }}</label>
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

    <!-- Users Table -->
    <div v-if="!loading && users.length > 0" class="users-table-container">
      <table class="users-table">
        <thead>
          <tr>
            <th>{{ $t('common.username') }}</th>
            <th>{{ $t('common.firstName') }}</th>
            <th>{{ $t('common.lastName') }}</th>
            <th>{{ $t('common.email') }}</th>
            <th>{{ $t('admin.corporateNumber') }}</th>
            <th>{{ $t('admin.corporateApproved') }}</th>
            <th>{{ $t('common.active') }}</th>
            <th>{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.first_name }}</td>
            <td>{{ user.last_name }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.corporate_number || '-' }}</td>
            <td>
              <div class="checkbox-cell">
                <input
                  type="checkbox"
                  :checked="user.corporate_approved"
                  @change="handleCorporateApprovedChange(user.id, user.username, $event)"
                  class="form-checkbox"
                />
              </div>
            </td>
            <td>
              <div class="checkbox-cell">
                <input
                  type="checkbox"
                  :checked="user.active"
                  @change="handleActiveChange(user.id, user.username, $event)"
                  class="form-checkbox"
                />
              </div>
            </td>
            <td class="actions-cell">
              <button class="btn btn-sm btn-info" @click="viewUserDetails(user.id)">
                {{ $t('common.view') }}
              </button>
              <button class="btn btn-sm btn-warning" @click="startPasswordReset(user.id, user.username)">
                {{ $t('admin.resetPassword') }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <button
          :disabled="currentPage === 1"
          class="btn btn-sm"
          @click="previousPage"
        >
          {{ $t('common.previous') }}
        </button>
        <span class="pagination-info">
          {{ $t('common.pagingInfo', { current: currentPage, total: totalPages }) }}
        </span>
        <button
          :disabled="currentPage === totalPages"
          class="btn btn-sm"
          @click="nextPage"
        >
          {{ $t('common.next') }}
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && users.length === 0" class="empty-state">
      <p>{{ $t('admin.noUsers') }}</p>
    </div>

    <!-- User Details Modal -->
    <div v-if="showDetailsModal" class="modal-overlay" @click.self="closeDetailsModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ $t('admin.userDetails') }}</h2>
          <button class="btn-close" @click="closeDetailsModal">&times;</button>
        </div>
        <div class="modal-body" v-if="selectedUserDetails">
          <div class="detail-field">
            <label>{{ $t('common.username') }}</label>
            <div>{{ selectedUserDetails.username }}</div>
          </div>
          <div class="detail-field">
            <label>{{ $t('common.firstName') }}</label>
            <div>{{ selectedUserDetails.first_name }}</div>
          </div>
          <div class="detail-field">
            <label>{{ $t('common.lastName') }}</label>
            <div>{{ selectedUserDetails.last_name }}</div>
          </div>
          <div class="detail-field">
            <label>{{ $t('common.email') }}</label>
            <div>{{ selectedUserDetails.email }}</div>
          </div>
          <div class="detail-field">
            <label>{{ $t('admin.corporateNumber') }}</label>
            <div>{{ selectedUserDetails.corporate_number || '-' }}</div>
          </div>
          <div class="detail-field">
            <label>{{ $t('admin.corporateApproved') }}</label>
            <div>{{ selectedUserDetails.corporate_approved ? $t('common.yes') : $t('common.no') }}</div>
          </div>
          <div class="detail-field">
            <label>{{ $t('common.active') }}</label>
            <div>{{ selectedUserDetails.active ? $t('common.yes') : $t('common.no') }}</div>
          </div>
          <div class="detail-field">
            <label>{{ $t('common.createdOn') }}</label>
            <div>{{ formatDate(selectedUserDetails.created_on) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { userService } from '@/services/user'

export default defineComponent({
  name: 'UserManagement',
  setup() {
    const authStore = useAuthStore()

    return {
      authStore,
    }
  },
  data() {
    return {
      users: [],
      loading: false,
      error: null,
      successMessage: null,
      search: {
        username: '',
        email: '',
      },
      currentPage: 1,
      pageSize: 10,
      totalUsers: 0,
      statistics: {
        active: 0,
        inactive: 0,
      },
      showDetailsModal: false,
      selectedUserDetails: null,
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.totalUsers / this.pageSize)
    },
  },
  mounted() {
    this.loadUsers()
  },
  methods: {
    async loadUsers() {
      this.loading = true
      this.error = null

      try {
        const response = await userService.listUsers({
          skip: (this.currentPage - 1) * this.pageSize,
          limit: this.pageSize,
          filter_username: this.search.username || undefined,
          filter_email: this.search.email || undefined,
        })

        this.users = response.items || []
        this.totalUsers = response.total || 0
        
        // Load statistics
        await this.loadStatistics()
      } catch (err) {
        this.error = err.message || this.$t('admin.usersLoadError')
        console.error('Error loading users:', err)
      } finally {
        this.loading = false
      }
    },

    async loadStatistics() {
      try {
        const stats = await userService.getUserStatistics()
        this.statistics = stats
      } catch (err) {
        console.error('Error loading user statistics:', err)
        // Don't show error to user, statistics are optional
      }
    },

    async handleCorporateApprovedChange(userId, username, event) {
      const approved = event.target.checked

      if (!confirm(this.$t('admin.confirmCorporateApprovedChange', { username, status: this.$t(approved ? 'common.yes' : 'common.no') }))) {
        event.target.checked = !approved
        return
      }

      try {
        await userService.updateUser(userId, {
          corporate_approved: approved,
        })

        this.successMessage = this.$t('admin.userUpdatedWithName', { username })
        this.loadUsers()
      } catch (err) {
        this.error = err.message || this.$t('admin.updateUserError')
        this.loadUsers()
      }
    },

    async handleActiveChange(userId, username, event) {
      const active = event.target.checked

      if (!confirm(this.$t('admin.confirmActiveChange', { username, status: this.$t(active ? 'admin.activate' : 'admin.deactivate') }))) {
        event.target.checked = !active
        return
      }

      try {
        await userService.updateUser(userId, {
          active: active,
        })

        this.successMessage = this.$t('admin.userUpdatedWithName', { username })
        this.loadUsers()
      } catch (err) {
        this.error = err.message || this.$t('admin.updateUserError')
        this.loadUsers()
      }
    },

    async viewUserDetails(userId) {
      try {
        this.selectedUserDetails = await userService.getUserDetail(userId)
        this.showDetailsModal = true
      } catch (err) {
        this.error = err.message || this.$t('admin.userLoadError')
      }
    },

    closeDetailsModal() {
      this.showDetailsModal = false
      this.selectedUserDetails = null
    },

    async startPasswordReset(userId, username) {
      if (!confirm(this.$t('admin.confirmPasswordReset', { username }))) {
        return
      }

      try {
        const response = await userService.startPasswordReset(userId)
        this.successMessage = this.$t('admin.passwordResetEmailSentWithName', { username })
      } catch (err) {
        this.error = err.message || this.$t('admin.passwordResetError')
      }
    },

    handleSearch() {
      this.currentPage = 1
      this.loadUsers()
    },

    handlePageSizeChange() {
      this.currentPage = 1
      this.loadUsers()
    },

    resetFilters() {
      this.search.username = ''
      this.search.email = ''
      this.currentPage = 1
      this.loadUsers()
    },

    previousPage() {
      if (this.currentPage > 1) {
        this.currentPage--
        this.loadUsers()
      }
    },

    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++
        this.loadUsers()
      }
    },

    formatDate(dateString) {
      if (!dateString) return '-'
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
})
</script>

<style scoped>
.users-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.users-header {
  margin-bottom: 2rem;
}

.users-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
}

.user-statistics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.stat-card.stat-success {
  border-left: 4px solid #28a745;
}

.stat-card.stat-danger {
  border-left: 4px solid #dc3545;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 0.3rem;
}

.stat-success .stat-value {
  color: #28a745;
}

.stat-danger .stat-value {
  color: #dc3545;
}

.stat-label {
  font-size: 0.85rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.users-search {
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

.form-group label {
  font-weight: 500;
  font-size: 14px;
}

.form-control {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
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

.alert {
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 4px;
  cursor: pointer;
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

.users-table-container {
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow-x: auto;
  margin-bottom: 2rem;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table thead {
  background-color: #f9f9f9;
  border-bottom: 2px solid #ddd;
}

.users-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
}

.users-table td {
  padding: 12px;
  border-bottom: 1px solid #eee;
}

.users-table tbody tr:hover {
  background-color: #f5f5f5;
}

.checkbox-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.badge-success {
  background-color: #d4edda;
  color: #155724;
}

.badge-danger {
  background-color: #f8d7da;
  color: #721c24;
}

.actions-cell {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  color: #333;
  cursor: pointer;
  font-size: 13px;
  text-decoration: none;
  display: inline-block;
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

.btn-warning {
  background: #ffc107;
  color: #333;
  border-color: #ffc107;
}

.btn-warning:hover {
  background: #e0a800;
}

.btn-sm {
  padding: 6px 10px;
  font-size: 12px;
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

/* Modal Styles */
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

.modal-content {
  background: white;
  border-radius: 4px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
}

.btn-close {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #666;
}

.btn-close:hover {
  color: #000;
}

.modal-body {
  padding: 1.5rem;
}

.detail-field {
  margin-bottom: 1rem;
}

.detail-field label {
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 0.5rem;
}

.detail-field div {
  padding: 0.75rem;
  background: #f9f9f9;
  border-radius: 4px;
  border-left: 3px solid #007bff;
}

@media (max-width: 768px) {
  .search-fields {
    grid-template-columns: 1fr;
  }

  .users-table {
    font-size: 13px;
  }

  .actions-cell {
    flex-direction: column;
  }

  .btn-sm {
    width: 100%;
  }
}
</style>
