/**
 * Authentication context for managing user state
 */
'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiClient, { setTokens, clearTokens, isAuthenticated as checkAuth } from './api-client';

interface User {
  id: string;
  email: string;
  email_verified: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch current user on mount
  useEffect(() => {
    const fetchUser = async () => {
      if (checkAuth()) {
        try {
          const response = await apiClient.get('/api/auth/me');
          setUser(response.data);
        } catch (error) {
          console.error('Failed to fetch user:', error);
          clearTokens();
          setUser(null);
        }
      }
      setLoading(false);
    };

    fetchUser();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await apiClient.post('/api/auth/login', {
      email,
      password,
    });

    const { access_token, refresh_token } = response.data;
    setTokens(access_token, refresh_token);

    // Fetch user data
    const userResponse = await apiClient.get('/api/auth/me');
    setUser(userResponse.data);
  };

  const register = async (email: string, password: string) => {
    await apiClient.post('/api/auth/register', {
      email,
      password,
    });

    // Auto-login after registration
    await login(email, password);
  };

  const logout = async () => {
    try {
      await apiClient.post('/api/auth/logout');
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      clearTokens();
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
