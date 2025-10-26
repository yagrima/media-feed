/**
 * Dashboard API endpoints
 */

import apiClient from './client'

export interface MediaTypeStats {
  unique_count: number
  total_count: number
}

export interface RecentActivity {
  id: string
  media_id: string
  title: string
  type: string
  platform: string | null
  consumed_at: string | null
  season_number: number | null
  episode_title: string | null
}

export interface DashboardStatistics {
  statistics: {
    movie: MediaTypeStats
    tv_series: MediaTypeStats
    book: MediaTypeStats
    audiobook: MediaTypeStats
  }
  recent_activity: RecentActivity[]
  this_week_count: number
  total_items: number
}

export const dashboardApi = {
  /**
   * Get dashboard statistics
   */
  async getStatistics(): Promise<DashboardStatistics> {
    const response = await apiClient.get('/api/dashboard/statistics')
    return response.data
  },
}
