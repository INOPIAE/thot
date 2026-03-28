/**
 * API Service
 */

import axios from 'axios'
import API_BASE_URL from '@/config/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    const requestUrl = error.config?.url || ''
    const isAuthRequest = requestUrl.startsWith('/auth/login')
      || requestUrl.startsWith('/auth/register')
      || requestUrl.startsWith('/auth/password-reset')
    const hasToken = Boolean(localStorage.getItem('access_token'))
    const isUnauthenticated = status === 401 || (status === 403 && detail === 'Not authenticated')

    // Only force logout for authenticated API calls, not during login/register flows.
    if (isUnauthenticated && hasToken && !isAuthRequest) {
      localStorage.removeItem('access_token')
      if (window.location.pathname !== '/auth/login') {
        const redirectTarget = `${window.location.pathname}${window.location.search}${window.location.hash}`
        window.location.href = `/auth/login?redirect=${encodeURIComponent(redirectTarget)}`
      }
    }

    return Promise.reject(error)
  }
)

export default api
