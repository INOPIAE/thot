/**
 * Service for Authentication API calls
 */

import api from './api'

export const authService = {
  /**
   * Register new user
   */
  async register(username, email, tosAgreed) {
    try {
      const response = await api.post('/auth/register', {
        username,
        email,
        tos_agreed: tosAgreed,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get registration confirmation data (validate token)
   */
  async getRegistrationConfirm(token) {
    try {
      const response = await api.get(`/auth/register/confirm/${token}`)
      return response
    } catch (error) {
      throw error
    }
  },

  /**
   * Complete registration with password
   */
  async confirmRegistration(token, data) {
    try {
      const response = await api.post(`/auth/register/confirm/${token}`, {
        first_name: data.first_name,
        last_name: data.last_name,
        password: data.password,
        password_confirm: data.password_confirm,
        corporate_number: data.corporate_number,
        enable_otp: data.enable_otp || false,
        tos_agreed: data.tos_agreed || false,
        current_language: data.current_language,
      })
      return response
    } catch (error) {
      throw error
    }
  },

  /**
   * Login user
   */
  async login(username, password, otpCode = null) {
    try {
      const response = await api.post('/auth/login', {
        username,
        password,
        otp_code: otpCode,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Logout user
   */
  async logout() {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    }
  },

  /**
   * Refresh access token
   */
  async refreshToken() {
    try {
      const response = await api.post('/auth/refresh')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Request password reset
   */
  async requestPasswordReset(username) {
    try {
      const response = await api.post('/auth/password-reset', {
        username,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Validate password reset token
   */
  async validatePasswordResetToken(token) {
    try {
      const response = await api.get(`/auth/password-reset/confirm/${token}`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Confirm password reset
   */
  async confirmPasswordReset(token, newPassword) {
    try {
      const response = await api.post(
        `/auth/password-reset/confirm/${token}`,
        {
          new_password: newPassword,
          new_password_confirm: newPassword,
        }
      )
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Validate OTP reset token
   */
  async validateOtpResetToken(token) {
    try {
      const response = await api.get(`/auth/otp-reset/confirm/${token}`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Confirm OTP reset
   */
  async confirmOtpResetToken(token, otpCode) {
    try {
      const response = await api.post(`/auth/otp-reset/confirm/${token}`, {
        otp_code: otpCode,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },
}

export default authService
