import { describe, it, expect, vi } from 'vitest'
import recordService from '@/services/record'

// Mock API
vi.mock('@/services/record', () => ({
  default: {
    resolvePublicRecordPdfLink: vi.fn(async (encodedId) => {
      if (encodedId === 'validid') {
        return {
          record_id: '123',
          encoded_record_id: 'validid',
          target_api_url: '/api/v1/records/123/pages-gallery',
          frontend_record_path: '/records/123/pages-gallery',
        }
      } else {
        const error = new Error('Invalid encoded id')
        error.response = { data: { detail: 'Invalid encoded id' } }
        throw error
      }
    })
  }
}))

describe('recordService.resolvePublicRecordPdfLink', () => {
  it('returns record info for valid id', async () => {
    const result = await recordService.resolvePublicRecordPdfLink('validid')
    expect(result.record_id).toBe('123')
    expect(result.encoded_record_id).toBe('validid')
    expect(result.target_api_url).toContain('/pages-gallery')
    expect(result.frontend_record_path).toContain('/pages-gallery')
  })

  it('throws for invalid id', async () => {
    await expect(recordService.resolvePublicRecordPdfLink('invalidid')).rejects.toMatchObject({
      response: { data: { detail: 'Invalid encoded id' } }
    })
  })
})
