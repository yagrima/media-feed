/**
 * Axios client with automatic authentication and token refresh
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { tokenManager } from '@/lib/auth/token-manager'
import toast from 'react-hot-toast'

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

    // Show toast notifications for errors (with long duration for debugging)
    if (error.response && error.response.status !== 401) {
      const errorMessage = error.response.data?.detail || error.response.data?.message || 'An error occurred'

      // Special handling for auth errors - always show login/register errors
      const authErrors = ['/api/auth/login', '/api/auth/register']
      const isAuthError = originalRequest.url && authErrors.some(path => originalRequest.url?.includes(path))

      // Always show errors for debugging with extended duration
      console.log('🔍 Toast Debug - Error:', error.response?.status, errorMessage)
      
      // React Hot Toast implementation - clean and stable
      const message = isAuthError 
        ? error.response.status === 404 && errorMessage.includes('No account found')
          ? `Account Not Found: No account exists with this email address. Please register for a new account.`
          : error.response.status === 401 
          ? `Incorrect Password: The password you entered is incorrect. Please try again.`
          : `Login Failed: ${errorMessage}`
        : `Error (${error.response.status}): ${errorMessage}`
      
      console.log('🔥 React Hot Toast - Error:', error.response?.status, message)
      toast.error(message, {
        duration: 30000, // 30 seconds - plenty of time to read
        position: 'top-center',
        style: {
          background: '#ff6b6b',
          color: '#fff',
          fontSize: '16px',
          border: '2px solid #ff3333',
          borderRadius: '8px',
          boxShadow: '0 4px 20px rgba(255, 107, 107, 0.5)',
        }
      })
      
    } else if (error.request) {
      // Network error with React Hot Toast
      const message = 'Network Error: Unable to reach the server. Please check your connection.'
      console.log('🔥 React Hot Toast - Network Error:', message)
      toast.error(message, {
        duration: 30000,
        position: 'top-center',
        style: {
          background: '#ff9500',
          color: '#fff',
          border: '2px solid #ff7700',
        }
      })
    }

    return Promise.reject(error)
  }
)

export default apiClient
