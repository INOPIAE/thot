<template>
  <div class="container">
    <h1>{{ $t('notifications.title') }}</h1>
    <ul v-if="notifications.length">
      <li v-for="n in notifications" :key="n.id">
        <strong>
          {{ n.title }}
          <span v-if="n.role && n.role.name"> ({{ n.role.name }})</span>
        </strong>
        <p>{{ n.notification }}</p>
        <small>{{ $d(new Date(n.created_on), 'short') }}</small>
        <router-link
          v-if="isAdmin"
          :to="{ name: 'NotificationEdit', params: { id: n.id } }"
          class="btn btn-sm btn-secondary ms-2"
        >
          {{ $t('notifications.editBtn') }}
        </router-link>
      </li>
    </ul>
    <div v-else>
      <p>{{ $t('notifications.none') }}</p>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { notificationService } from '@/services/notification'

export default defineComponent({
  name: 'NotificationList',
  data() {
    return {
      notifications: [],
      isAdmin: false,
    }
  },
  async mounted() {
    try {
      const res = await notificationService.getUserNotifications()
      this.notifications = res.data
      const user = this.$store?.state?.auth?.user || (this.$pinia && this.$pinia._s.get('auth')?.user)
      this.isAdmin = user && user.roles && user.roles.includes('admin')
    } catch (e) {
      this.notifications = []
    }
  },
})
</script>
