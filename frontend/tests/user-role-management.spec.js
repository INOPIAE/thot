import { vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import UserRoleManagement from '@/components/UserRoleManagement.vue'

vi.mock('@/services/user', () => ({
  userService: {
    getUserRoles: vi.fn(() => Promise.resolve([])),
    getUserDetail: vi.fn(),
    assignRoleToUser: vi.fn(),
  }
}))

vi.mock('@/services/role', () => ({
  roleService: {
    listRoles: vi.fn(() => Promise.resolve({ items: [] })),
  },
}))

import { userService } from '@/services/user'
import { roleService } from '@/services/role'

const defaultProps = {
  userId: '1',
  canManageRoles: true,
}


describe('UserRoleManagement.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows OTP error when assigning support/admin role without OTP', async () => {
    userService.getUserRoles.mockResolvedValue([])
    userService.getUserDetail.mockResolvedValue({ otp_enabled: false })
    userService.assignRoleToUser.mockResolvedValue({})
    roleService.listRoles.mockResolvedValue({
      items: [
        { id: '2', name: 'support', active: true },
        { id: '3', name: 'admin', active: true },
      ],
    })
    const wrapper = mount(UserRoleManagement, {
      props: defaultProps,
      global: {
        mocks: {
          $t: (msg, vars) => (vars ? `${msg} ${JSON.stringify(vars)}` : msg),
        },
      },
      data() {
        return {
          allRoles: [
            { id: '2', name: 'support', active: true },
            { id: '3', name: 'admin', active: true },
          ],
          selectedRoleId: '2',
        }
      },
    })
    await flushPromises()
    await wrapper.vm.assignRole()
    expect(wrapper.vm.error).toContain('otpRequiredForRole')
    expect(userService.assignRoleToUser).not.toHaveBeenCalled()
  })

  it('allows assigning support/admin role if OTP enabled', async () => {
    userService.getUserRoles.mockResolvedValue([])
    userService.getUserDetail.mockResolvedValue({ otp_enabled: true })
    userService.assignRoleToUser.mockResolvedValue({})
    roleService.listRoles.mockResolvedValue({
      items: [
        { id: '2', name: 'support', active: true },
        { id: '3', name: 'admin', active: true },
      ],
    })
    const wrapper = mount(UserRoleManagement, {
      props: defaultProps,
      global: {
        mocks: {
          $t: (msg, vars) => (vars ? `${msg} ${JSON.stringify(vars)}` : msg),
        },
      },
      data() {
        return {
          allRoles: [
            { id: '2', name: 'support', active: true },
            { id: '3', name: 'admin', active: true },
          ],
          selectedRoleId: '2',
        }
      },
    })
    await flushPromises()
    await wrapper.vm.assignRole()
    expect(wrapper.vm.error).toBeNull()
    expect(userService.assignRoleToUser).toHaveBeenCalledWith('1', '2')
  })

  it('allows assigning non-support/admin role without OTP', async () => {
    userService.getUserRoles.mockResolvedValue([])
    userService.getUserDetail.mockResolvedValue({ otp_enabled: false })
    userService.assignRoleToUser.mockResolvedValue({})
    roleService.listRoles.mockResolvedValue({
      items: [
        { id: '4', name: 'user', active: true },
      ],
    })
    const wrapper = mount(UserRoleManagement, {
      props: defaultProps,
      global: {
        mocks: {
          $t: (msg, vars) => (vars ? `${msg} ${JSON.stringify(vars)}` : msg),
        },
      },
      data() {
        return {
          allRoles: [
            { id: '4', name: 'user', active: true },
          ],
          selectedRoleId: '4',
        }
      },
    })
    await flushPromises()
    await wrapper.vm.assignRole()
    expect(wrapper.vm.error).toBeNull()
    expect(userService.assignRoleToUser).toHaveBeenCalledWith('1', '4')
  })

  it('allows re-assigning a previously removed role (new entry)', async () => {
    // User had the role before (inactive), should be able to re-assign
    userService.getUserRoles.mockResolvedValue([
      { user_role_id: 'ur1', role_id: '2', role_name: 'support', active: false },
    ])
    userService.getUserDetail.mockResolvedValue({ otp_enabled: true })
    userService.assignRoleToUser.mockResolvedValue({})
    roleService.listRoles.mockResolvedValue({
      items: [
        { id: '2', name: 'support', active: true },
      ],
    })
    const wrapper = mount(UserRoleManagement, {
      props: defaultProps,
      global: {
        mocks: {
          $t: (msg, vars) => (vars ? `${msg} ${JSON.stringify(vars)}` : msg),
        },
      },
      data() {
        return {
          allRoles: [
            { id: '2', name: 'support', active: true },
          ],
          selectedRoleId: '2',
        }
      },
    })
    await flushPromises()
    // Should be able to assign again
    await wrapper.vm.assignRole()
    expect(wrapper.vm.error).toBeNull()
    expect(userService.assignRoleToUser).toHaveBeenCalledWith('1', '2')
  })
})
