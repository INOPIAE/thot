<template>
  <div class="roles-container">
    <div class="roles-header">
      <h1>{{ $t('admin.roles') }}</h1>
      <button class="btn btn-primary" @click="startCreateRole">
        {{ $t('admin.newRole') }}
      </button>
    </div>

    <div v-if="successMessage" class="alert alert-success" @click="successMessage = ''">
      {{ successMessage }}
    </div>
    <div v-if="error" class="alert alert-danger" @click="error = ''">
      {{ error }}
    </div>

    <div class="card form-card" v-if="showForm">
      <h2>{{ editingRole ? $t('admin.editRole') : $t('admin.newRole') }}</h2>

      <div class="form-group">
        <label for="role-name">{{ $t('admin.roleName') }}</label>
        <input
          id="role-name"
          v-model.trim="form.name"
          type="text"
          class="form-control"
          :disabled="loading"
        />
      </div>

      <div class="form-group">
        <label for="role-description">{{ $t('admin.roleDescription') }}</label>
        <textarea
          id="role-description"
          v-model.trim="form.description"
          class="form-control"
          rows="3"
          :disabled="loading"
        ></textarea>
      </div>

      <div class="form-group" v-if="editingRole">
        <label>
          <input
            v-model="form.active"
            type="checkbox"
            :disabled="loading"
          />
          {{ $t('common.active') }}
        </label>
      </div>

      <div class="form-actions">
        <button class="btn btn-primary" :disabled="loading" @click="saveRole">
          {{ $t('common.save') }}
        </button>
        <button class="btn btn-secondary" :disabled="loading" @click="cancelEdit">
          {{ $t('common.cancel') }}
        </button>
      </div>
    </div>

    <div v-if="loading && !roles.length" class="loading">
      {{ $t('common.loading') }}
    </div>

    <div v-if="!loading && roles.length" class="card table-card">
      <table class="roles-table">
        <thead>
          <tr>
            <th>{{ $t('admin.roleName') }}</th>
            <th>{{ $t('admin.roleDescription') }}</th>
            <th>{{ $t('admin.roleStatus') }}</th>
            <th>{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="role in roles" :key="role.id">
            <td>{{ role.name }}</td>
            <td>{{ role.description || '-' }}</td>
            <td>
              {{ role.active ? $t('common.active') : $t('common.inactive') }}
            </td>
            <td class="actions-cell">
              <button class="btn btn-sm btn-warning" @click="startEditRole(role)">
                {{ $t('common.edit') }}
              </button>
              <button
                class="btn btn-sm btn-danger"
                :disabled="isSystemRole(role.name)"
                @click="deleteRole(role)"
              >
                {{ $t('common.delete') }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!loading && !roles.length" class="empty-state">
      <p>{{ $t('admin.noRoles') }}</p>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { roleService } from '@/services/role'

export default defineComponent({
  name: 'RoleManagement',
  data() {
    return {
      roles: [],
      loading: false,
      error: null,
      successMessage: null,
      showForm: false,
      editingRole: null,
      form: {
        name: '',
        description: '',
        active: true,
      },
    }
  },
  mounted() {
    this.loadRoles()
  },
  methods: {
    async loadRoles() {
      this.loading = true
      this.error = null

      try {
        this.roles = await roleService.listRoles()
      } catch (err) {
        this.error = err.detail || this.$t('admin.rolesLoadError')
      } finally {
        this.loading = false
      }
    },

    isSystemRole(roleName) {
      return ['admin', 'support', 'user'].includes(roleName)
    },

    startCreateRole() {
      this.editingRole = null
      this.form = {
        name: '',
        description: '',
        active: true,
      }
      this.showForm = true
      this.error = null
    },

    startEditRole(role) {
      this.editingRole = role
      this.form = {
        name: role.name,
        description: role.description || '',
        active: role.active,
      }
      this.showForm = true
      this.error = null
    },

    cancelEdit() {
      this.showForm = false
      this.editingRole = null
      this.form = {
        name: '',
        description: '',
        active: true,
      }
    },

    async saveRole() {
      if (!this.form.name) {
        this.error = this.$t('validation.required', { field: this.$t('admin.roleName') })
        return
      }

      this.loading = true
      this.error = null

      try {
        if (this.editingRole) {
          await roleService.updateRole(this.editingRole.id, {
            name: this.form.name,
            description: this.form.description,
            active: this.form.active,
          })
          this.successMessage = this.$t('admin.roleUpdateSuccess')
        } else {
          await roleService.createRole({
            name: this.form.name,
            description: this.form.description,
          })
          this.successMessage = this.$t('admin.roleCreateSuccess')
        }

        this.cancelEdit()
        await this.loadRoles()
      } catch (err) {
        this.error = err.detail || this.$t('admin.roleSaveError')
      } finally {
        this.loading = false
      }
    },

    async deleteRole(role) {
      if (this.isSystemRole(role.name)) {
        this.error = this.$t('admin.systemRoleCannotDelete')
        return
      }

      if (!confirm(this.$t('admin.confirmRoleDelete', { role: role.name }))) {
        return
      }

      this.loading = true
      this.error = null

      try {
        await roleService.deleteRole(role.id)
        this.successMessage = this.$t('admin.roleDeleteSuccess')
        await this.loadRoles()
      } catch (err) {
        this.error = err.detail || this.$t('admin.roleDeleteError')
      } finally {
        this.loading = false
      }
    },
  },
})
</script>

<style scoped>
.roles-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.roles-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.form-card,
.table-card {
  padding: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.35rem;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
}

.roles-table {
  width: 100%;
  border-collapse: collapse;
}

.roles-table th,
.roles-table td {
  padding: 0.65rem;
  border-bottom: 1px solid #e3e3e3;
  text-align: left;
}

.actions-cell {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.empty-state {
  padding: 1.5rem;
  text-align: center;
  color: #666;
}

@media (max-width: 768px) {
  .roles-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
