import api from './api'

/**
 * Service for User API calls
 */
export const userService = {
  /**
   * Request email change for another user (admin/support)
   */
  async requestSupportEmailChange(userId, email) {
    try {
      const response = await api.post(`/users/email-change/request/support?user_id=${encodeURIComponent(userId)}`, {
        email,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },
    /**
     * Delete own account (soft delete)
     */
    async deleteAccount() {
      try {
        const response = await api.delete('/users/delete-account')
        return response.data
      } catch (error) {
        throw error.response?.data || error
      }
    },
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

  /**
   * Request email change (step 1)
   */
  async changeEmail(newEmail) {
    try {
      const response = await api.post('/users/email-change/request', {
        email: newEmail,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Confirm email change
   */

  /**
   * Confirm email change (step 2)
   */
  async confirmEmailChange(token) {
    try {
      const response = await api.post('/users/email-change/confirm', {
        token,
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
   * Start OTP reset for current user
   */
  async startOTPReset() {
    try {
      const response = await api.post('/users/otp/reset')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Confirm OTP reset for current user
   */
  async confirmOTPReset(data) {
    try {
      const response = await api.post('/users/otp/reset/confirm', {
        token: data.token,
        otp_code: data.otp_code,
      })
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
      let params
      if (typeof skip === 'object' && skip !== null) {
        const options = skip
        params = {
          skip: options.skip ?? 0,
          limit: options.limit ?? 10,
          filter_username: options.filter_username,
          filter_email: options.filter_email,
          include_inactive: options.include_inactive !== undefined ? String(options.include_inactive) : undefined,
        }
      } else {
        params = {
          skip,
          limit,
          ...filters,
        }
        if ('include_inactive' in params) {
          params.include_inactive = String(params.include_inactive)
        }
      }

      const response = await api.get('/users', {
        params,
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
   * Start OTP reset for user (admin/support)
   */
  async startOtpReset(userId) {
    try {
      const response = await api.put(`/users/${userId}/otp-reset`)
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
