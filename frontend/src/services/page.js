import api from './api.js'

export const pageService = {
  /**
   * Start OCR job for a page
   */
  async startOcr(pageId) {
    try {
      const response = await api.post(`/pages/${pageId}/start-ocr`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },
  /**
   * Get all pages (optionally filtered by record_id)
   */
  async listPages(params = {}) {
    try {
      const response = await api.get('/pages', { params })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get a specific page by ID
   */
  async getPage(pageId) {
    try {
      const response = await api.get(`/pages/${pageId}`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Create a new page with optional file upload
   */
  async createPage(data) {
    try {
      const formData = new FormData()
      
      // Add text fields
      formData.append('name', data.name)
      formData.append('record_id', data.record_id)
      formData.append('restriction_id', data.restriction_id)
      
      if (data.description) formData.append('description', data.description)
      if (data.page) formData.append('page', data.page)
      if (data.comment) formData.append('comment', data.comment)
      if (data.workstatus_id) formData.append('workstatus_id', data.workstatus_id)
      if (data.order_by !== undefined && data.order_by !== null) formData.append('order_by', data.order_by)
      if (data.rotation !== undefined) formData.append('rotation', data.rotation)
      if (data.rotation_restriction !== undefined) formData.append('rotation_restriction', data.rotation_restriction)

      // Add file if provided
      if (data.file) {
        formData.append('file', data.file)
      }

      const response = await api.post('/pages', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Update an existing page with optional file upload
   */
  async updatePage(pageId, data) {
    try {
      const formData = new FormData()
      
      // Add text fields
      formData.append('name', data.name)
      formData.append('restriction_id', data.restriction_id)
      
      if (data.description) formData.append('description', data.description)
      if (data.page) formData.append('page', data.page)
      if (data.comment) formData.append('comment', data.comment)
      if (data.workstatus_id) formData.append('workstatus_id', data.workstatus_id)
      if (data.order_by !== undefined && data.order_by !== null) formData.append('order_by', data.order_by)
      if (data.rotation !== undefined) formData.append('rotation', data.rotation)
      if (data.rotation_restriction !== undefined) formData.append('rotation_restriction', data.rotation_restriction)
      if (data.delete_file !== undefined) formData.append('delete_file', data.delete_file)
      if (data.delete_restriction_file !== undefined) formData.append('delete_restriction_file', data.delete_restriction_file)

      // Add file if provided
      if (data.file) {
        formData.append('file', data.file)
      }
      if (data.restriction_file) {
        formData.append('restriction_file', data.restriction_file)
      }

      const response = await api.put(`/pages/${pageId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Delete a page (soft delete)
   */
  async deletePage(pageId) {
    try {
      const response = await api.delete(`/pages/${pageId}`)
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Download a user-specific watermarked PDF for a page.
   */
  async downloadWatermarkedPdf(pageId) {
    try {
      const response = await api.get(`/pages/${pageId}/download-watermarked`, {
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
   * Get watermarked PDF for viewing (returns blob)
   */
  async getViewPdf(pageId) {
    try {
      const response = await api.get(`/pages/${pageId}/view-pdf`, {
        responseType: 'blob',
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Get thumbnail with watermark (returns blob)
   */
  async getThumbnail(pageId, width = 200, preferRestriction = false) {
    try {
      const response = await api.get(`/pages/${pageId}/thumbnail`, {
        params: { width, prefer_restriction: preferRestriction },
        responseType: 'blob',
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },

  /**
   * Download a watermarked restriction PDF for a page.
   */
  async downloadRestrictionPdf(pageId) {
    try {
      const response = await api.get(`/pages/${pageId}/download-restriction-pdf`, {
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
   * Get watermarked restriction PDF for viewing (returns blob)
   */
  async getRestrictionViewPdf(pageId) {
    try {
      const response = await api.get(`/pages/${pageId}/view-restriction-pdf`, {
        responseType: 'blob',
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error
    }
  },
}

export default pageService
