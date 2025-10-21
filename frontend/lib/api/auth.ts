/**
 * Authentication API endpoints
 */

import apiClient from './client'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface User {
  id: string
  email: string
  created_at: string
}

export const authApi = {
  /**
   * Login user
   */
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post('/api/auth/login', data)
    return response.data
  },

  /**
   * Register new user
   */
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post('/api/auth/register', data)
    return response.data
  },

  /**
   * Refresh access token
   */
  async refresh(refreshToken: string): Promise<AuthResponse> {
    const response = await apiClient.post('/api/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    await apiClient.post('/api/auth/logout')
  },

  /**
   * Get current user info
   */
  async me(): Promise<User> {
    const response = await apiClient.get('/api/auth/me')
    return response.data
  },
}
