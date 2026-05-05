import { mount, flushPromises } from '@vue/test-utils'
import NotificationEdit from './NotificationEdit.vue'
import { vi, describe, it, expect, beforeEach } from 'vitest'

vi.mock('@/services/notification', () => ({
  notificationService: {
    getNotificationById: vi.fn(),
    updateNotification: vi.fn(),
  },
}))
vi.mock('@/services/role', () => ({
  roleService: {
    listRoles: vi.fn(),
  },
}))
vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({ user: { roles: ['admin'] } }),
}))
import { notificationService } from '@/services/notification'
import { roleService } from '@/services/role'

describe('NotificationEdit.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders notification for editing', async () => {
    notificationService.getNotificationById.mockResolvedValue({
      data: { id: 1, title: 'EditTitle', notification: 'EditBody', roles_id: 2, active: true },
    })
    roleService.listRoles.mockResolvedValue([
      { id: 2, name: 'admin' },
    ])
    const wrapper = mount(NotificationEdit, {
      global: {
        mocks: {
          $t: (msg) => msg,
          $route: { params: { id: 1 } },
        },
      },
    })
    await flushPromises()
    // Warte explizit auf notification und Input-Element (max. 20 Ticks)
    let input
    for (let i = 0; i < 20; i++) {
      if (wrapper.vm.notification) {
        input = wrapper.find('input#title')
        if (input.exists()) break
      }
      await wrapper.vm.$nextTick()
    }
    expect(wrapper.vm.notification).toBeTruthy()
    expect(input && input.exists()).toBe(true)
    expect(input.element.value).toBe('EditTitle')
    let textarea = wrapper.find('textarea#notification')
    expect(textarea.exists()).toBe(true)
    expect(textarea.element.value).toBe('EditBody')
  })

  it('shows not found if notification missing', async () => {
    notificationService.getNotificationById.mockResolvedValue({ data: null })
    roleService.listRoles.mockResolvedValue([])
    const wrapper = mount(NotificationEdit, {
      global: {
        mocks: {
          $t: (msg) => msg,
          $route: { params: { id: 1 } },
        },
      },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('notifications.notFound')
  })

  it('shows error on update failure', async () => {
    notificationService.getNotificationById.mockResolvedValue({
      data: { id: 1, title: 'EditTitle', notification: 'EditBody', roles_id: 2, active: true },
    })
    roleService.listRoles.mockResolvedValue([{ id: 2, name: 'admin' }])
    notificationService.updateNotification.mockRejectedValue(new Error('fail'))
    const wrapper = mount(NotificationEdit, {
      global: {
        mocks: {
          $t: (msg) => msg,
          $route: { params: { id: 1 } },
        },
      },
    })
    await flushPromises()
    // Warte explizit auf notification und Formular (max. 20 Ticks)
    let form
    for (let i = 0; i < 20; i++) {
      if (wrapper.vm.notification) {
        form = wrapper.find('form')
        if (form.exists()) break
      }
      await wrapper.vm.$nextTick()
    }
    expect(wrapper.vm.notification).toBeTruthy()
    expect(form && form.exists()).toBe(true)
    await form.trigger('submit.prevent')
    await flushPromises()
    expect(wrapper.text()).toContain('Fehler beim Speichern.')
  })
})
