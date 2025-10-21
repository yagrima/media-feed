/**
 * Notifications API endpoints
 */

import apiClient from './client'

export interface Notification {
  id: string
  user_id: string
  type: 'sequel_detected' | 'import_complete' | 'import_failed' | 'system'
  title: string
  message: string
  data: Record<string, any>
  read: boolean
  created_at: string
  read_at: string | null
}

export interface NotificationResponse {
  items: Notification[]
  total: number
  unread_count: number
  page: number
  limit: number
}

export interface NotificationPreferences {
  email_enabled: boolean
  sequel_notifications: boolean
  import_notifications: boolean
  system_notifications: boolean
}

export const notificationsApi = {
  /**
   * Get user notifications
   */
  async getNotifications(page: number = 1, limit: number = 20): Promise<NotificationResponse> {
    const response = await apiClient.get('/api/notifications', {
      params: { page, limit },
    })
    return response.data
  },

  /**
   * Get unread notifications
   */
  async getUnread(): Promise<Notification[]> {
    const response = await apiClient.get('/api/notifications/unread')
    return response.data
  },

  /**
   * Mark notification as read
   */
  async markAsRead(id: string): Promise<void> {
    await apiClient.put(`/api/notifications/${id}/read`)
  },

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<void> {
    await apiClient.put('/api/notifications/mark-all-read')
  },

  /**
   * Delete notification
   */
  async deleteNotification(id: string): Promise<void> {
    await apiClient.delete(`/api/notifications/${id}`)
  },

  /**
   * Get notification preferences
   */
  async getPreferences(): Promise<NotificationPreferences> {
    const response = await apiClient.get('/api/notifications/preferences')
    return response.data
  },

  /**
   * Update notification preferences
   */
  async updatePreferences(preferences: Partial<NotificationPreferences>): Promise<NotificationPreferences> {
    const response = await apiClient.put('/api/notifications/preferences', preferences)
    return response.data
  },
}
