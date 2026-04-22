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
   * Get QR code details for a record.
   */
  async getRecordQrCode(recordId) {
    try {
      const response = await api.get(`/public-links/records/${recordId}/qr-code`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Resolve frontend public link token (/lit/:encodedId) to a record id.
   */
  async resolvePublicRecordLink(encodedId) {
    try {
      const response = await api.get(`/public-links/lit/${encodedId}`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Resolve frontend public link token (/pdf/:encodedId) to a record id.
   */
  async resolvePublicRecordPdfLink(encodedId) {
    try {
      const response = await api.get(`/public-links/pdf/${encodedId}`)
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

  /**
   * Get loan types for record metadata selection
   */
  async listLoanTypes() {
    try {
      const response = await api.get('/library-metadata/loantypes')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get publication types for record metadata selection
   */
  async listPublicationTypes() {
    try {
      const response = await api.get('/library-metadata/publicationtypes')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get record conditions for record metadata selection
   */
  async listRecordConditions() {
    try {
      const response = await api.get('/library-metadata/record-conditions')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get lettering options for record metadata selection
   */
  async listLetterings() {
    try {
      const response = await api.get('/library-metadata/letterings')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get publishers for record metadata selection
   */
  async listPublishers(params = {}) {
    try {
      const response = await api.get('/library-metadata/publishers', { params })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Create a new publisher
   */
  async createPublisher(data) {
    try {
      const response = await api.post('/library-metadata/publishers', data)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get author types for record author assignments
   */
  async listAuthorTypes() {
    try {
      const response = await api.get('/library-metadata/authortypes')
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get authors for record author assignments
   */
  async listAuthors(params = {}) {
    try {
      const response = await api.get('/library-metadata/authors', { params })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Create a new author
   */
  async createAuthor(data) {
    try {
      const response = await api.post('/library-metadata/authors', data)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Download combined PDF with all pages of a record
   */
  async downloadCombinedPdf(recordId) {
    try {
      const response = await api.get(`/records/${recordId}/download-combined-pdf`, {
        responseType: 'blob',
      })
      return {
        blob: response.data,
        contentDisposition: response.headers['content-disposition'] || '',
      }
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Import records from an XLSX file (admin only)
   */
  async importRecordsXlsx(file) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await api.post('/admin/records-import/xlsx', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },
}
