/**
 * Media API endpoints
 */

import apiClient from './client'

export interface UserMedia {
  id: string
  user_id: string
  media_id: string
  consumed_at: string
  created_at: string
  media: Media
}

export interface Media {
  id: string
  title: string
  type: 'movie' | 'tv_series'
  platform: string
  base_title?: string
  season_number?: number
  watched_episodes_count?: number
  created_at: string
}

export interface UserMediaResponse {
  items: UserMedia[]
  total: number
  page: number
  limit: number
}

export interface MediaFilters {
  type?: 'movie' | 'tv_series' | 'all'
  page?: number
  limit?: number
}

export const mediaApi = {
  /**
   * Get user's media library
   */
  async getUserMedia(filters?: MediaFilters): Promise<UserMediaResponse> {
    const params: any = {
      page: filters?.page || 1,
      limit: filters?.limit || 20,
    }

    if (filters?.type && filters.type !== 'all') {
      params.type = filters.type
    }

    const response = await apiClient.get('/api/media', { params })
    return response.data
  },

  /**
   * Add media manually (placeholder for future implementation)
   */
  async addMedia(data: any): Promise<UserMedia> {
    const response = await apiClient.post('/api/media', data)
    return response.data
  },

  /**
   * Delete user media
   */
  async deleteMedia(id: string): Promise<void> {
    await apiClient.delete(`/api/media/${id}`)
  },
}
