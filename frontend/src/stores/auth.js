/**
 * Pinia Store for Authentication
 */

import { defineStore } from 'pinia'
import api from '@/services/api'
import { useAppStore } from '@/stores/app'

const DEFAULT_SESSION_TIMEOUT_MINUTES = 60
const DEFAULT_TOKEN_REFRESH_INTERVAL_MINUTES = 55
const ACTIVITY_EVENTS = ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart']

function normalizeUserPayload(user) {
  if (!user || typeof user !== 'object') {
    return user
  }

  const roles = Array.isArray(user.roles)
    ? user.roles
      .map((role) => {
        if (typeof role === 'string') {
          return role
        }

        if (role && typeof role === 'object' && typeof role.name === 'string') {
          return role.name
        }

        return null
      })
      .filter(Boolean)
    : []

  const permissions = Array.isArray(user.permissions)
    ? user.permissions.filter((permission) => typeof permission === 'string')
    : []

  return {
    ...user,
    roles,
    permissions,
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('access_token') || null,
    isLoading: false,
    error: null,
    sessionTimeoutMinutes: DEFAULT_SESSION_TIMEOUT_MINUTES,
    tokenRefreshIntervalMinutes: DEFAULT_TOKEN_REFRESH_INTERVAL_MINUTES,
    lastActivityAt: Date.now(),
    inactivityTimerId: null,
    renewalTimerId: null,
    activityHandler: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user,
    hasRole: (state) => (role) => Array.isArray(state.user?.roles)
      ? state.user.roles.includes(role)
      : false,
    hasPermission: (state) => (permission) => Array.isArray(state.user?.permissions)
      ? state.user.permissions.includes(permission)
      : false,
  },

  actions: {
    async login(username, password, otpCode = null) {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.post('/auth/login', {
          username,
          password,
          otp_code: otpCode,
        })

        this.token = response.data.access_token
        this.user = normalizeUserPayload(response.data.user)
        localStorage.setItem('access_token', this.token)
        localStorage.setItem('last_activity_at', String(Date.now()))
        api.defaults.headers.common['Authorization'] = `Bearer ${this.token}`

        this.applySessionConfig()
        this.startSessionManagement()

        return true
      } catch (error) {
        this.error = error.response?.data?.detail || 'Login failed'
        return false
      } finally {
        this.isLoading = false
      }
    },

    async logout(options = {}) {
      const { auto = false } = options

      this.stopSessionManagement()
      this.token = null
      this.user = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('last_activity_at')
      delete api.defaults.headers.common['Authorization']

      if (auto && typeof window !== 'undefined' && window.location.pathname !== '/auth/login') {
        window.location.href = '/auth/login?reason=session-timeout'
      }
    },

    async register(username, email, tosAgreed, language = 'en') {
      this.isLoading = true
      this.error = null

      const normalizedUsername = typeof username === 'string' ? username.trim() : username
      const normalizedEmail = typeof email === 'string' ? email.trim() : email

      try {
        const response = await api.post('/auth/register', {
          username: normalizedUsername,
          email: normalizedEmail,
          tos_agreed: tosAgreed,
          language: language,
        })
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Registration failed'
        throw error.response?.data || error
      } finally {
        this.isLoading = false
      }
    },

    async resetPassword(username) {
      this.isLoading = true
      this.error = null

      try {
        await api.post('/auth/password-reset', { username })
        return true
      } catch (error) {
        this.error = error.response?.data?.detail || 'Password reset failed'
        return false
      } finally {
        this.isLoading = false
      }
    },

    async fetchUser() {
      if (!this.token) {
        return false
      }

      try {
        const response = await api.get('/users/profile')
        this.user = normalizeUserPayload(response.data)
        this.applySessionConfig()
        this.startSessionManagement()
        return true
      } catch (error) {
        // Token might be invalid, clear it
        this.logout()
        return false
      }
    },

    applySessionConfig() {
      const appStore = useAppStore()
      const configuredTimeout = Number(
        appStore.getConfig('sessionTimeoutMinutes', DEFAULT_SESSION_TIMEOUT_MINUTES)
      )
      const configuredRefresh = Number(
        appStore.getConfig('tokenRefreshIntervalMinutes', DEFAULT_TOKEN_REFRESH_INTERVAL_MINUTES)
      )

      this.sessionTimeoutMinutes = Number.isFinite(configuredTimeout) && configuredTimeout > 0
        ? configuredTimeout
        : DEFAULT_SESSION_TIMEOUT_MINUTES
      this.tokenRefreshIntervalMinutes = Number.isFinite(configuredRefresh) && configuredRefresh > 0
        ? configuredRefresh
        : Math.max(1, this.sessionTimeoutMinutes - 5)

      // Ensure refresh runs before inactivity timeout.
      if (this.tokenRefreshIntervalMinutes >= this.sessionTimeoutMinutes) {
        this.tokenRefreshIntervalMinutes = Math.max(1, this.sessionTimeoutMinutes - 1)
      }
    },

    markActivity() {
      const now = Date.now()
      this.lastActivityAt = now
      localStorage.setItem('last_activity_at', String(now))
    },

    isSessionInactive() {
      const timeoutMs = this.sessionTimeoutMinutes * 60 * 1000
      return Date.now() - this.lastActivityAt >= timeoutMs
    },

    startSessionManagement() {
      if (!this.token || typeof window === 'undefined') {
        return
      }

      this.stopSessionManagement()

      const persisted = Number(localStorage.getItem('last_activity_at') || 0)
      this.lastActivityAt = Number.isFinite(persisted) && persisted > 0 ? persisted : Date.now()

      let lastEventUpdate = 0
      this.activityHandler = () => {
        const now = Date.now()
        // Throttle noisy events.
        if (now - lastEventUpdate < 1000) {
          return
        }
        lastEventUpdate = now
        this.markActivity()
      }

      ACTIVITY_EVENTS.forEach((eventName) => {
        window.addEventListener(eventName, this.activityHandler, { passive: true })
      })

      this.inactivityTimerId = window.setInterval(() => {
        if (this.isSessionInactive()) {
          this.logout({ auto: true })
        }
      }, 30 * 1000)

      this.renewalTimerId = window.setInterval(async () => {
        if (!this.token) {
          return
        }

        if (this.isSessionInactive()) {
          await this.logout({ auto: true })
          return
        }

        try {
          const response = await api.post('/auth/refresh')
          const newToken = response?.data?.access_token
          if (!newToken) {
            throw new Error('Missing access token in refresh response')
          }

          this.token = newToken
          localStorage.setItem('access_token', newToken)
          api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
        } catch (error) {
          await this.logout({ auto: true })
        }
      }, this.tokenRefreshIntervalMinutes * 60 * 1000)
    },

    stopSessionManagement() {
      if (typeof window !== 'undefined' && this.activityHandler) {
        ACTIVITY_EVENTS.forEach((eventName) => {
          window.removeEventListener(eventName, this.activityHandler)
        })
      }

      if (this.inactivityTimerId) {
        clearInterval(this.inactivityTimerId)
        this.inactivityTimerId = null
      }

      if (this.renewalTimerId) {
        clearInterval(this.renewalTimerId)
        this.renewalTimerId = null
      }

      this.activityHandler = null
    },

    clearError() {
      this.error = null
    },
  },
})
