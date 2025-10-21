/**
 * Token Manager
 * Handles JWT storage, retrieval, and automatic refresh
 */

interface TokenData {
  accessToken: string
  refreshToken: string
  expiresAt: number
}

const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const EXPIRES_AT_KEY = 'token_expires_at'

export const tokenManager = {
  /**
   * Store tokens in localStorage
   */
  setTokens(accessToken: string, refreshToken: string, expiresIn: number) {
    if (typeof window === 'undefined') return

    const expiresAt = Date.now() + expiresIn * 1000
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
    localStorage.setItem(EXPIRES_AT_KEY, expiresAt.toString())
  },

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  },

  /**
   * Get refresh token
   */
  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  },

  /**
   * Check if access token is expired
   */
  isTokenExpired(): boolean {
    if (typeof window === 'undefined') return true

    const expiresAt = localStorage.getItem(EXPIRES_AT_KEY)
    if (!expiresAt) return true

    // Consider token expired 30 seconds before actual expiry
    return Date.now() > parseInt(expiresAt) - 30000
  },

  /**
   * Clear all tokens (logout)
   */
  clearTokens() {
    if (typeof window === 'undefined') return

    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(EXPIRES_AT_KEY)
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getAccessToken() && !this.isTokenExpired()
  },
}
