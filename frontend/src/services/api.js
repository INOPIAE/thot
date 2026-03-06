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
    const requestUrl = error.config?.url || ''
    const isAuthRequest = requestUrl.startsWith('/auth/login')
      || requestUrl.startsWith('/auth/register')
      || requestUrl.startsWith('/auth/password-reset')
    const hasToken = Boolean(localStorage.getItem('access_token'))

    // Only force logout for authenticated API calls, not during login/register flows.
    if (status === 401 && hasToken && !isAuthRequest) {
      localStorage.removeItem('access_token')
      if (window.location.pathname !== '/auth/login') {
        window.location.href = '/auth/login'
      }
    }

    return Promise.reject(error)
  }
)

export default api
