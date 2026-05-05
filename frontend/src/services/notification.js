import api from './api'

export const notificationService = {
  async getUserNotifications() {
    return api.get('/notifications')
  },
  async getRecentNotifications() {
    return api.get('/notifications/recent')
  },
  async createNotification(data) {
    return api.post('/notifications', data)
  },
  async getNotificationById(id) {
    return api.get(`/notifications/${id}`)
  },
  async updateNotification(id, data) {
    return api.put(`/notifications/${id}`, data)
  },
}
