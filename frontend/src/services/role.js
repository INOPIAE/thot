/**
 * Service for Role API calls
 */

import api from './api'

export const roleService = {
  /**
   * List all roles (admin only)
   */
  async listRoles() {
    try {
      const response = await api.get('/roles')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Create a new role (admin only)
   */
  async createRole(data) {
    try {
      const response = await api.post('/roles', {
        name: data.name,
        description: data.description || null,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Update a role (admin only)
   */
  async updateRole(roleId, data) {
    try {
      const response = await api.put(`/roles/${roleId}`, {
        name: data.name,
        description: data.description,
        active: data.active,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Delete a role (soft delete, admin only)
   */
  async deleteRole(roleId) {
    try {
      await api.delete(`/roles/${roleId}`)
      return true
    } catch (error) {
      throw error.response?.data || error
    }
  },
}

export default roleService
