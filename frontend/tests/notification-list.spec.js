import { mount } from '@vue/test-utils'
import NotificationList from '@/views/notifications/NotificationList.vue'
import { vi, describe, it, expect, beforeEach } from 'vitest'

vi.mock('@/services/notification', () => ({
  notificationService: {
    getUserNotifications: vi.fn(),
  },
}))
import { notificationService } from '@/services/notification'

describe('NotificationList.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders notifications from API', async () => {
    notificationService.getUserNotifications.mockResolvedValue({
      data: [
        { id: 1, title: 'Test', notification: 'Test body', created_on: '2024-01-01T12:00:00Z', role: { name: 'admin' } },
      ],
    })
    const wrapper = mount(NotificationList, {
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
        mocks: {
          $t: (msg) => msg,
          $d: (date) => date.toISOString(),
          $store: { state: { auth: { user: { roles: ['admin'] } } } },
        },
      },
    })
    for (let i = 0; i < 20; i++) {
      if (wrapper.vm.notifications && wrapper.vm.notifications.length > 0) break
      await wrapper.vm.$nextTick()
    }
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.notifications.length).toBeGreaterThan(0)
    expect(wrapper.text()).toContain('Test')
    expect(wrapper.text()).toContain('Test body')
    expect(wrapper.text()).toContain('admin')
  })

  it('shows message if no notifications', async () => {
    notificationService.getUserNotifications.mockResolvedValue({ data: [] })
    const wrapper = mount(NotificationList, {
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
        mocks: {
          $t: (msg) => msg,
          $d: (date) => date.toISOString(),
          $store: { state: { auth: { user: { roles: ['user'] } } } },
        },
      },
    })
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('notifications.none')
  })

  it('handles API error gracefully', async () => {
    notificationService.getUserNotifications.mockRejectedValue(new Error('fail'))
    const wrapper = mount(NotificationList, {
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
        mocks: {
          $t: (msg) => msg,
          $d: (date) => date.toISOString(),
          $store: { state: { auth: { user: { roles: ['user'] } } } },
        },
      },
    })
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('notifications.none')
  })
})