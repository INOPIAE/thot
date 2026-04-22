import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

/**
 * Fetch records from backend
 * @param {Object} params - Query params or { endpoint }
 * @returns {Promise<Object>} Records response
 */
export async function fetchRecords(params = {}) {
  let endpoint = '/api/v1/records'
  let query = {}
  if (params.endpoint) {
    endpoint = params.endpoint
    // Remove endpoint from params
    params = { ...params }
    delete params.endpoint
  }
  query = params
  const url = new URL(endpoint, API_BASE_URL)
  Object.entries(query).forEach(([key, value]) => {
    if (value) url.searchParams.append(key, value)
  })
  const response = await axios.get(url.toString())
  return response.data
}
