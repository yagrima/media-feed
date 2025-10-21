/**
 * Import API endpoints
 */

import apiClient from './client'

export interface ImportJob {
  id: string
  user_id: string
  source: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_rows: number
  processed_rows: number
  successful_rows: number
  failed_rows: number
  error_log: any[]
  filename: string
  file_size: number
  file_hash: string
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface ImportHistoryItem {
  job_id: string
  source: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_rows: number
  successful_rows: number
  failed_rows: number
  created_at: string
  completed_at: string | null
}

export interface ImportHistoryResponse {
  imports: ImportHistoryItem[]
  total: number
  page: number
  page_size: number
}

export const importApi = {
  /**
   * Upload CSV file
   */
  async uploadCSV(file: File): Promise<ImportJob> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post('/api/import/csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Get import job status
   */
  async getStatus(jobId: string): Promise<ImportJob> {
    const response = await apiClient.get(`/api/import/status/${jobId}`)
    return response.data
  },

  /**
   * Get import history
   */
  async getHistory(page: number = 1, limit: number = 20): Promise<ImportHistoryResponse> {
    const response = await apiClient.get('/api/import/history', {
      params: { page, page_size: limit },
    })
    return response.data
  },

  /**
   * Cancel import job
   */
  async cancelJob(jobId: string): Promise<void> {
    await apiClient.delete(`/api/import/job/${jobId}`)
  },
}
