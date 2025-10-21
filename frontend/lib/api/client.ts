/**
 * Axios client with automatic authentication and token refresh
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { tokenManager } from '@/lib/auth/token-manager'
import { toast } from 'sonner'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
})

// Request interceptor: Add auth token to requests
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenManager.getAccessToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: Handle 401 errors, refresh token, and show error toasts
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ detail?: string; message?: string }>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // If 401 and not already retried, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = tokenManager.getRefreshToken()
        if (!refreshToken) {
          throw new Error('No refresh token available')
        }

        // Attempt to refresh the access token
        const response = await axios.post(`${API_URL}/api/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const { access_token, refresh_token: newRefreshToken, expires_in } = response.data

        // Store new tokens
        tokenManager.setTokens(access_token, newRefreshToken, expires_in)

        // Retry original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`
        }
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        tokenManager.clearTokens()
        toast.error('Session expired. Please login again.')
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      }
    }

    // Show toast notifications for errors (except 401 which is handled above)
    if (error.response && error.response.status !== 401) {
      const errorMessage = error.response.data?.detail || error.response.data?.message || 'An error occurred'

      // Don't show toast for expected validation errors (let components handle them)
      const silentErrors = ['/api/auth/login', '/api/auth/register']
      const isSilent = originalRequest.url && silentErrors.some(path => originalRequest.url?.includes(path))

      if (!isSilent) {
        if (error.response.status === 403) {
          toast.error('Access denied', { description: errorMessage })
        } else if (error.response.status === 404) {
          toast.error('Not found', { description: errorMessage })
        } else if (error.response.status === 429) {
          toast.error('Too many requests', { description: 'Please slow down and try again later' })
        } else if (error.response.status >= 500) {
          toast.error('Server error', { description: 'Something went wrong. Please try again later.' })
        } else if (error.response.status >= 400) {
          toast.error('Request failed', { description: errorMessage })
        }
      }
    } else if (error.request) {
      // Network error
      toast.error('Network error', { description: 'Unable to reach the server. Please check your connection.' })
    }

    return Promise.reject(error)
  }
)

export default apiClient
