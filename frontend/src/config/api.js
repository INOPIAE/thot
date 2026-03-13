/**
 * Frontend API Configuration
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const API_ENDPOINTS = {
  // Auth
  AUTH_REGISTER: '/auth/register',
  AUTH_REGISTER_CONFIRM: '/auth/register/confirm/:token',
  AUTH_LOGIN: '/auth/login',
  AUTH_LOGOUT: '/auth/logout',
  AUTH_REFRESH: '/auth/refresh',

  // Password Management
  PASSWORD_RESET_REQUEST: '/auth/password-reset',
  PASSWORD_RESET_CONFIRM: '/auth/password-reset/confirm/:token',

  // User Profile
  USER_PROFILE: '/users/profile',
  USER_UPDATE: '/users/profile',
  USER_CHANGE_PASSWORD: '/users/password-change',
  USER_EMAIL_CHANGE: '/users/email-change',
  USER_EMAIL_CHANGE_CONFIRM: '/users/email-change/confirm/:token',
  USER_OTP_ENABLE: '/users/otp/enable',
  USER_OTP_DISABLE: '/users/otp/disable',
  USER_OTP_RESET: '/users/otp/reset',
  USER_OTP_RESET_CONFIRM: '/users/otp/reset/confirm',

  // User Management (Support)
  USERS_LIST: '/users',
  USERS_DETAIL: '/users/:id',
  USERS_UPDATE: '/users/:id',

  // Documentation
  API_DOCS: '/docs',
  API_REDOC: '/redoc',
}

export default API_BASE_URL
