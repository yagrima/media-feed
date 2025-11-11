/**
 * Audible API Client
 * 
 * Client functions for Audible integration endpoints
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

async function getAuthToken(): Promise<string> {
  if (typeof window === 'undefined') {
    throw new Error('Cannot access localStorage on server side');
  }
  
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('Not authenticated. Please log in first.');
  }
  
  return token;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData: AudibleErrorResponse = await response.json().catch(() => ({
      error: 'Unknown error occurred',
      detail: response.statusText
    }));
    
    throw new AudibleApiError(
      errorData.error || 'Request failed',
      response.status,
      errorData.error_type,
      errorData.detail
    );
  }
  
  return response.json();
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
    const token = await getAuthToken();
    
    const response = await fetch(`${API_URL}/api/audible/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });
    
    return handleResponse<AudibleConnectResponse>(response);
  },
  
  /**
   * Sync Audible library (fetch updates)
   * 
   * @returns Sync statistics
   * @throws AudibleApiError if sync fails
   */
  async sync(): Promise<AudibleSyncResponse> {
    const token = await getAuthToken();
    
    const response = await fetch(`${API_URL}/api/audible/sync`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return handleResponse<AudibleSyncResponse>(response);
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
    const token = await getAuthToken();
    
    const response = await fetch(`${API_URL}/api/audible/disconnect`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return handleResponse<AudibleDisconnectResponse>(response);
  },
  
  /**
   * Get Audible connection status
   * 
   * @returns Current connection status and metadata
   * @throws AudibleApiError if request fails
   */
  async getStatus(): Promise<AudibleStatusResponse> {
    const token = await getAuthToken();
    
    const response = await fetch(`${API_URL}/api/audible/status`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return handleResponse<AudibleStatusResponse>(response);
  }
};

export { AudibleApiError };
