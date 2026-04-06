<template>
  <div class="role-management">
    <h3>{{ $t('admin.userRoles') }}</h3>
    
    <!-- Loading -->
    <div v-if="loading" class="loading-small">
      {{ $t('common.loading') }}...
    </div>

    <!-- Error Message -->
    <div v-if="error" class="alert alert-danger alert-small" @click="error = ''">
      {{ error }}
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="alert alert-success alert-small" @click="successMessage = ''">
      {{ successMessage }}
    </div>

    <!-- Current Roles -->
    <div v-if="!loading" class="roles-section">
      <h4>{{ $t('admin.activeRoles') }}</h4>
      <div v-if="activeRoles.length === 0" class="empty-roles">
        {{ $t('admin.noActiveRoles') }}
      </div>
      <div v-else class="role-list">
        <div v-for="role in activeRoles" :key="role.user_role_id" class="role-item active-role">
          <div class="role-info">
            <strong>{{ role.role_name }}</strong>
            <span v-if="role.role_description" class="role-description">{{ role.role_description }}</span>
            <small class="role-meta">
              {{ $t('admin.assignedOn') }}: {{ formatDate(role.assigned_on) }}
            </small>
          </div>
          <button 
            v-if="canManageRoles"
            class="btn btn-sm btn-danger"
            @click="removeRole(role.role_id, role.role_name)"
            :disabled="removing"
          >
            {{ $t('common.remove') }}
          </button>
        </div>
      </div>

      <!-- Removed Roles (History) -->
      <div v-if="showInactive && inactiveRoles.length > 0" class="inactive-roles-section">
        <h4>{{ $t('admin.removedRoles') }}</h4>
        <div class="role-list">
          <div v-for="role in inactiveRoles" :key="role.user_role_id" class="role-item inactive-role">
            <div class="role-info">
              <strong>{{ role.role_name }}</strong>
              <small class="role-meta">
                {{ $t('admin.removedOn') }}: {{ formatDate(role.removed_on) }}
              </small>
            </div>
            <span class="badge badge-secondary">{{ $t('admin.removed') }}</span>
          </div>
        </div>
      </div>

      <button 
        v-if="inactiveRoles.length > 0"
        class="btn btn-link btn-sm"
        @click="showInactive = !showInactive"
      >
        {{ showInactive ? $t('admin.hideRemovedRoles') : $t('admin.showRemovedRoles') }}
      </button>
    </div>

    <!-- Add Role Section -->
    <div v-if="canManageRoles && !loading" class="add-role-section">
      <h4>{{ $t('admin.assignRole') }}</h4>
      <div class="add-role-form">
        <select v-model="selectedRoleId" class="form-control" :disabled="adding">
          <option value="">{{ $t('admin.selectRole') }}</option>
          <option 
            v-for="role in availableRoles" 
            :key="role.id" 
            :value="role.id"
          >
            {{ role.name }} - {{ role.description }}
          </option>
        </select>
        <button 
          class="btn btn-primary"
          @click="assignRole"
          :disabled="!selectedRoleId || adding"
        >
          {{ $t('admin.assignRole') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { userService } from '@/services/user'
import { roleService } from '@/services/role'

export default defineComponent({
  name: 'UserRoleManagement',
  props: {
    userId: {
      type: String,
      required: true,
    },
    canManageRoles: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      loading: false,
      adding: false,
      removing: false,
      error: null,
      successMessage: null,
      userRoles: [],
      allRoles: [],
      selectedRoleId: '',
      showInactive: false,
    }
  },
  computed: {
    activeRoles() {
      return this.userRoles.filter(r => r.active)
    },
    inactiveRoles() {
      return this.userRoles.filter(r => !r.active)
    },
    activeRoleIds() {
      return new Set(this.activeRoles.map(r => r.role_id))
    },
    everAssignedRoleIds() {
      return new Set(this.userRoles.map(r => r.role_id))
    },
    availableRoles() {
      // Only exclude roles that are currently active for the user
      return this.allRoles.filter(role => {
        return role.active && !this.activeRoleIds.has(role.id)
      })
    },
  },
  mounted() {
    this.loadUserRoles()
    this.loadAllRoles()
  },
  methods: {
    async loadUserRoles() {
      this.loading = true
      this.error = null

      try {
        this.userRoles = await userService.getUserRoles(this.userId, true) // include inactive
      } catch (err) {
        this.error = err.message || this.$t('admin.rolesLoadError')
        console.error('Error loading user roles:', err)
      } finally {
        this.loading = false
      }
    },

    async loadAllRoles() {
      try {
        const response = await roleService.listRoles()
        this.allRoles = response.items || response || []
      } catch (err) {
        console.error('Error loading all roles:', err)
      }
    },


    async assignRole() {
      if (!this.selectedRoleId) return

      this.adding = true
      this.error = null
      this.successMessage = null

      try {
        const selectedRole = this.availableRoles.find(r => r.id === this.selectedRoleId)
        const roleName = selectedRole?.name || ''

        // OTP enforcement for support/admin
        if (selectedRole && ['support', 'admin'].includes(selectedRole.name.toLowerCase())) {
          // Fetch user details to check OTP status
          const user = await userService.getUserDetail(this.userId)
          if (!user.otp_enabled) {
            this.error = this.$t('admin.otpRequiredForRole', { role: roleName })
            this.adding = false
            return
          }
        }

        await userService.assignRoleToUser(this.userId, this.selectedRoleId)
        this.successMessage = this.$t('admin.roleAssignedSuccess', { roleName })
        this.selectedRoleId = ''
        await this.loadUserRoles()
        this.$emit('roles-updated')
      } catch (err) {
        this.error = err.detail || err.message || this.$t('admin.roleAssignError')
        console.error('Error assigning role:', err)
      } finally {
        this.adding = false
      }
    },

    async removeRole(roleId, roleName) {
      if (!confirm(this.$t('admin.confirmRemoveRole', { role: roleName }))) {
        return
      }

      this.removing = true
      this.error = null
      this.successMessage = null

      try {
        await userService.removeRoleFromUser(this.userId, roleId)
        this.successMessage = this.$t('admin.roleRemovedSuccess', { roleName })
        await this.loadUserRoles()
        this.$emit('roles-updated')
      } catch (err) {
        this.error = err.detail || err.message || this.$t('admin.roleRemoveError')
        console.error('Error removing role:', err)
      } finally {
        this.removing = false
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
.role-management {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 2px solid #eee;
}

.role-management h3 {
  margin-bottom: 1rem;
  font-size: 1.2rem;
}

.role-management h4 {
  margin-bottom: 0.75rem;
  font-size: 1rem;
  font-weight: 600;
  color: #555;
}

.loading-small {
  padding: 1rem;
  text-align: center;
  color: #666;
  font-size: 14px;
}

.alert-small {
  padding: 0.75rem;
  margin-bottom: 1rem;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.roles-section {
  margin-bottom: 1.5rem;
}

.empty-roles {
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 4px;
  color: #666;
  font-style: italic;
  text-align: center;
}

.role-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.role-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-radius: 4px;
  border: 1px solid #ddd;
  background: white;
}

.role-item.active-role {
  border-left: 4px solid #007bff;
}

.role-item.inactive-role {
  border-left: 4px solid #999;
  background: #f9f9f9;
  opacity: 0.7;
}

.role-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.role-info strong {
  color: #333;
  font-size: 14px;
}

.role-description {
  font-size: 12px;
  color: #666;
}

.role-meta {
  font-size: 11px;
  color: #999;
}

.inactive-roles-section {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.add-role-section {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.add-role-form {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.add-role-form .form-control {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

</style>
