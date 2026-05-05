<template>
  <div class="container">
    <h1>{{ $t('notifications.createTitle') }}</h1>
    <form @submit.prevent="submitNotification">
      <div class="mb-3">
        <label for="title" class="form-label">{{ $t('notifications.titleLabel') }}</label>
        <input v-model="form.title" id="title" class="form-control" required />
      </div>
      <div class="mb-3">
        <label for="notification" class="form-label">{{ $t('notifications.notificationLabel') }}</label>
        <textarea v-model="form.notification" id="notification" class="form-control" required></textarea>
      </div>
      <div class="mb-3">
        <label for="role" class="form-label">{{ $t('notifications.roleLabel') }}</label>
        <select v-model="form.roles_id" id="role" class="form-select" required>
          <option v-for="role in roles" :key="role.id" :value="role.id">
            {{ role.name }}
          </option>
        </select>
      </div>
      <button type="submit" class="btn btn-primary">{{ $t('notifications.createBtn') }}</button>
      <div v-if="success" class="alert alert-success mt-3">{{ $t('notifications.success') }}</div>
      <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
    </form>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { notificationService } from '@/services/notification'
import { roleService } from '@/services/role'

export default defineComponent({
  name: 'NotificationCreate',
  data() {
    return {
      form: {
        title: '',
        notification: '',
        roles_id: '',
      },
      roles: [],
      success: false,
      error: '',
    }
  },
  async mounted() {
    try {
      const roles = await roleService.listRoles()
      this.roles = roles
    } catch (e) {
      this.error = 'Fehler beim Laden der Rollen.'
    }
  },
  methods: {
    async submitNotification() {
      this.success = false
      this.error = ''
      try {
        await notificationService.createNotification({ ...this.form })
        this.success = true
        this.form.title = ''
        this.form.notification = ''
        this.form.roles_id = ''
      } catch (e) {
        this.error = e?.response?.data?.detail || 'Fehler beim Erstellen.'
      }
    },
  },
})
</script>
