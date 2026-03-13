/**
 * Service for User API calls
 */

import api from './api'

export const userService = {
  /**
   * Get current user profile
   */
  async getProfile() {
    try {
      const response = await api.get('/users/profile')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Update user profile
   */
  async updateProfile(data) {
    try {
      const response = await api.put('/users/profile', data)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Change password
   */
  async changePassword(data) {
    try {
      const response = await api.post('/users/password-change', {
        current_password: data.current_password,
        new_password: data.new_password,
        new_password_confirm: data.new_password_confirm,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Change email
   */
  async changeEmail(newEmail) {
    try {
      const response = await api.post('/users/email-change', {
        new_email: newEmail,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Confirm email change
   */
  async confirmEmailChange(verificationCode) {
    try {
      const response = await api.post('/users/email-change/confirm/:token', {
        verification_code: verificationCode,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Enable OTP
   */
  async enableOTP(otpCode) {
    try {
      const response = await api.post('/users/otp/enable', {
        otp_code: otpCode,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Disable OTP
   */
  async disableOTP() {
    try {
      const response = await api.post('/users/otp/disable')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * List users (admin/support)
   */
  async listUsers(skip = 0, limit = 10, filters = {}) {
    try {
      const response = await api.get('/users', {
        params: {
          skip,
          limit,
          ...filters,
        },
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get user details (admin/support)
   */
  async getUserDetail(userId) {
    try {
      const response = await api.get(`/users/${userId}`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Update user (admin/support)
   */
  async updateUser(userId, data) {
    try {
      const response = await api.put(`/users/${userId}`, data)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Start password reset for user (admin/support)
   */
  async startPasswordReset(userId) {
    try {
      const response = await api.put(`/users/${userId}/password-reset`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get user statistics (admin/support)
   */
  async getUserStatistics() {
    try {
      const response = await api.get('/users/statistics')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

    /**
     * Get count of users pending membership number approval (admin/support)
     */
    async getPendingApprovalCount() {
      try {
        const response = await api.get('/users/pending-approval')
        return response.data
      } catch (error) {
        throw error.response?.data || error
      }
    },

  /**
   * Get user roles (admin/support)
   */
  async getUserRoles(userId, includeInactive = false) {
    try {
      const response = await api.get(`/users/${userId}/roles`, {
        params: {
          include_inactive: includeInactive,
        },
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Assign role to user (admin/support)
   */
  async assignRoleToUser(userId, roleId) {
    try {
      const response = await api.post(`/users/${userId}/roles`, {
        role_id: roleId,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Remove role from user (admin/support)
   * Soft delete - cannot be reactivated
   */
  async removeRoleFromUser(userId, roleId) {
    try {
      const response = await api.delete(`/users/${userId}/roles/${roleId}`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },
}

export default userService
