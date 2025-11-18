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
  type: 'movie' | 'tv_series' | 'audiobook'
  platform: string
  base_title?: string
  season_number?: number
  watched_episodes_count?: number
  total_episodes?: number  // From TMDB
  total_seasons?: number   // From TMDB
  created_at: string
  media_metadata?: {
    series?: {
      title: string
      sequence?: string
    }
    authors?: string[]
    narrators?: string[]
    duration_minutes?: number
    cover_url?: string
    cover_images?: any
    rating?: number
    publisher?: string
  }
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

export interface Episode {
  id: string
  season_number: number | null
  episode_number: number | null
  episode_title: string | null
  consumed_at: string | null
  platform: string | null
}

export interface MediaDetailsResponse {
  media: {
    id: string
    title: string
    type: string
  }
  episodes: Episode[]
  total_episodes: number
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
   * Get detailed episode information for a media item
   */
  async getMediaEpisodes(mediaId: string): Promise<MediaDetailsResponse> {
    const response = await apiClient.get(`/api/media/${mediaId}/episodes`)
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
