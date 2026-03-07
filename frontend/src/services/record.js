/**
 * Service for Records API calls
 */

import api from './api'

export const recordService = {
  /**
   * Get all records with optional filters
   */
  async listRecords(params = {}) {
    try {
      const response = await api.get('/records', { params })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get reduced records list (id, name, signature), sorted by signature
   */
  async listReducedRecords(signature = null) {
    try {
      const params = {}
      if (signature) {
        params.signature = signature
      }
      const response = await api.get('/records/reduced', { params })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get a specific record by ID
   */
  async getRecord(recordId) {
    try {
      const response = await api.get(`/records/${recordId}`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Create a new record
   */
  async createRecord(data) {
    try {
      const response = await api.post('/records', data)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Update a record
   */
  async updateRecord(recordId, data) {
    try {
      const response = await api.put(`/records/${recordId}`, data)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Delete a record
   */
  async deleteRecord(recordId) {
    try {
      const response = await api.delete(`/records/${recordId}`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get all restrictions
   */
  async getRestrictions() {
    try {
      const response = await api.get('/records/metadata/restrictions')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get all workstatus
   */
  async getWorkStatus() {
    try {
      const response = await api.get('/records/metadata/workstatus')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },
}
