/**
 * Configuration Service - Loads app config from backend
 */

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

function normalizeLogoUrl(logoUrl) {
  if (!logoUrl || typeof logoUrl !== 'string') {
    return logoUrl
  }

  const value = logoUrl.trim()
  if (!value) {
    return value
  }

  // Keep absolute URLs unchanged.
  if (/^https?:\/\//i.test(value)) {
    return value
  }

  // Resolve relative paths against backend host so assets are loaded from API server.
  return new URL(value, API_BASE_URL).toString()
}

/**
 * Fetch application configuration from backend
 * @returns {Promise<Object>} Application configuration
 */
export async function fetchAppConfig() {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/v1/config`)
    const config = response.data || getDefaultConfig()
    return {
      ...config,
      logoUrl: normalizeLogoUrl(config.logoUrl),
    }
  } catch (error) {
    console.warn('Failed to fetch config from backend, using defaults:', error.message)
    return getDefaultConfig()
  }
}

/**
 * Default fallback configuration
 * Used when backend is unavailable
 */
function getDefaultConfig() {
  return {
    appName: 'NLF Database',
    appVersion: '1.0.0',
    companyName: 'Your Company',
    logoUrl: '/logo.png',
    copyrightYear: new Date().getFullYear(),
    itemsPerPageDefault: 10,
    itemsPerPageOptions: [10, 20, 50],
    tokenRefreshIntervalMinutes: 55,
    sessionTimeoutMinutes: 60,
    features: {
      otp: true,
      emailVerification: true,
      corporateApprovals: true,
    },
    languages: {
      en: 'English',
      de: 'Deutsch',
    },
    defaultLanguage: 'en',
  }
}

export default {
  fetchAppConfig,
}
