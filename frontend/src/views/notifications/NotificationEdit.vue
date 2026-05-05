<template>
  <div class="container">
    <h1>{{ $t('notifications.editTitle') }}</h1>
    <form v-if="notification" @submit.prevent="submitEdit">
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
        <select v-model="form.roles_id" id="role" class="form-select" required :disabled="!isAdmin">
          <option v-for="role in roles" :key="role.id" :value="role.id">
            {{ role.name }}
          </option>
        </select>
      </div>
      <div class="mb-3">
        <label for="active" class="form-label">{{ $t('notifications.activeLabel') }}</label>
        <input type="checkbox" v-model="form.active" id="active" />
      </div>
      <button type="submit" class="btn btn-primary">{{ $t('notifications.saveBtn') }}</button>
      <div v-if="success" class="alert alert-success mt-3">{{ $t('notifications.successEdit') }}</div>
      <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
    </form>
    <div v-else>
      <p>{{ $t('notifications.notFound') }}</p>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { notificationService } from '@/services/notification'
import { roleService } from '@/services/role'
import { useAuthStore } from '@/stores/auth'

export default defineComponent({
  name: 'NotificationEdit',
  data() {
    return {
      notification: null,
      form: {
        title: '',
        notification: '',
        roles_id: '',
        active: true,
      },
      roles: [],
      success: false,
      error: '',
      isAdmin: false,
    }
  },
  async mounted() {
    const authStore = useAuthStore()
    this.isAdmin = authStore.user && authStore.user.roles && authStore.user.roles.includes('admin')
    try {
      const [roles, notif] = await Promise.all([
        roleService.listRoles(),
        notificationService.getNotificationById(this.$route.params.id),
      ])
      this.roles = roles
      this.notification = notif.data
      this.form = { ...notif.data }
    } catch (e) {
      this.error = 'Fehler beim Laden der Notification.'
    }
  },
  methods: {
    async submitEdit() {
      this.success = false
      this.error = ''
      try {
        await notificationService.updateNotification(this.notification.id, this.form)
        this.success = true
      } catch (e) {
        this.error = e?.response?.data?.detail || 'Fehler beim Speichern.'
      }
    },
  },
})
</script>
