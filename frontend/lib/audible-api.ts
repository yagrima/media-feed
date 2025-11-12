/**
 * Audible API Client
 * 
 * Client functions for Audible integration endpoints
 */

import apiClient from './api-client';

export interface AudibleConnectRequest {
  email: string;
  password: string;
  marketplace: string;
}

export interface AudibleConnectResponse {
  success: boolean;
  message: string;
  device_name: string | null;
  marketplace: string;
  books_imported: number | null;
}

export interface AudibleSyncResponse {
  success: boolean;
  message: string;
  imported: number;
  updated: number;
  skipped: number;
  errors: number;
  total: number;
}

export interface AudibleDisconnectResponse {
  success: boolean;
  message: string;
}

export interface AudibleStatusResponse {
  connected: boolean;
  marketplace: string | null;
  device_name: string | null;
  last_sync_at: string | null;
  books_count: number | null;
}

export interface AudibleErrorResponse {
  error: string;
  detail?: string;
  error_type?: string;
}

class AudibleApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public errorType?: string,
    public detail?: string
  ) {
    super(message);
    this.name = 'AudibleApiError';
  }
}

async function handleApiError(error: any): Promise<never> {
  if (error.response?.data) {
    const errorData = error.response.data as AudibleErrorResponse;
    throw new AudibleApiError(
      errorData.error || 'Request failed',
      error.response.status,
      errorData.error_type,
      errorData.detail
    );
  }
  
  throw new AudibleApiError(
    error.message || 'Network error occurred',
    error.response?.status || 500
  );
}

export const audibleApi = {
  /**
   * Connect Audible account and import library
   * 
   * @param data - Audible credentials and marketplace
   * @returns Connection result with imported books count
   * @throws AudibleApiError if connection fails
   */
  async connect(data: AudibleConnectRequest): Promise<AudibleConnectResponse> {
    try {
      const response = await apiClient.post('/api/audible/connect', data);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
  
  /**
   * Sync Audible library (fetch updates)
   * 
   * @returns Sync statistics
   * @throws AudibleApiError if sync fails
   */
  async sync(): Promise<AudibleSyncResponse> {
    try {
      const response = await apiClient.post('/api/audible/sync');
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
  
  /**
   * Disconnect Audible account
   * 
   * Removes stored credentials and deregisters device.
   * Audiobooks remain in library.
   * 
   * @returns Disconnection confirmation
   * @throws AudibleApiError if disconnect fails
   */
  async disconnect(): Promise<AudibleDisconnectResponse> {
    try {
      const response = await apiClient.delete('/api/audible/disconnect');
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
  
  /**
   * Get Audible connection status
   * 
   * @returns Current connection status and metadata
   * @throws AudibleApiError if request fails
   */
  async getStatus(): Promise<AudibleStatusResponse> {
    try {
      const response = await apiClient.get('/api/audible/status');
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  }
};

export { AudibleApiError };
