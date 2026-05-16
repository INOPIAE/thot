import { mount, flushPromises } from '@vue/test-utils'
import NotificationCreate from '@/views/notifications/NotificationCreate.vue'
import { vi, describe, it, expect, beforeEach } from 'vitest'

vi.mock('@/services/notification', () => ({
  notificationService: {
    createNotification: vi.fn(),
  },
}))
vi.mock('@/services/role', () => ({
  roleService: {
    listRoles: vi.fn(),
  },
}))
import { notificationService } from '@/services/notification'
import { roleService } from '@/services/role'

describe('NotificationCreate.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders roles and submits notification', async () => {
    roleService.listRoles.mockResolvedValue([{ id: 1, name: 'admin' }])
    notificationService.createNotification.mockResolvedValue({})
    const wrapper = mount(NotificationCreate, {
      global: {
        mocks: { $t: (msg) => msg },
      },
    })
    await flushPromises()
    const input = wrapper.find('input#title')
    const textarea = wrapper.find('textarea#notification')
    const select = wrapper.find('select#role')
    expect(input.exists()).toBe(true)
    expect(textarea.exists()).toBe(true)
    expect(select.exists()).toBe(true)
    wrapper.vm.form = { title: 'TestTitle', notification: 'TestBody', roles_id: '1' }
    await wrapper.vm.$nextTick()
    await flushPromises()
    expect(wrapper.vm.form).toEqual({ title: 'TestTitle', notification: 'TestBody', roles_id: '1' })
    await wrapper.vm.submitNotification()
    await flushPromises()
    const call = notificationService.createNotification.mock.calls[0][0]
    expect(call).toEqual({ title: 'TestTitle', notification: 'TestBody', roles_id: '1' })
    expect(wrapper.text()).toContain('notifications.success')
  })

  it('shows error if role loading fails', async () => {
    roleService.listRoles.mockRejectedValue(new Error('fail'))
    const wrapper = mount(NotificationCreate, {
      global: {
        mocks: { $t: (msg) => msg },
      },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Fehler beim Laden der Rollen.')
  })

  it('shows error if creation fails', async () => {
    roleService.listRoles.mockResolvedValue([{ id: 1, name: 'admin' }])
    notificationService.createNotification.mockRejectedValue(new Error('fail'))
    const wrapper = mount(NotificationCreate, {
      global: {
        mocks: { $t: (msg) => msg },
      },
    })
    await flushPromises()
    const input = wrapper.find('input#title')
    const textarea = wrapper.find('textarea#notification')
    const select = wrapper.find('select#role')
    expect(input.exists()).toBe(true)
    expect(textarea.exists()).toBe(true)
    expect(select.exists()).toBe(true)
    wrapper.vm.form = { title: 'TestTitle', notification: 'TestBody', roles_id: '1' }
    await wrapper.vm.$nextTick()
    await flushPromises()
    expect(wrapper.vm.form).toEqual({ title: 'TestTitle', notification: 'TestBody', roles_id: '1' })
    await wrapper.vm.submitNotification()
    await flushPromises()
    expect(wrapper.text()).toContain('Fehler beim Erstellen.')
  })
})