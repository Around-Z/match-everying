'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiGet, apiPost, apiPut } from '@/lib/api';

interface User {
  id: string;
  email: string;
  username: string;
  role: string;
  contact_info: string;
  tags: string[];
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string, contactInfo: string, role?: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
  refreshUser: () => Promise<void>;
  updateProfile: (data: { username?: string; contact_info?: string; tags?: string[] }) => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  isAuthenticated: false,
  isAdmin: false,
  refreshUser: async () => {},
  updateProfile: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Initialize: load token from localStorage and validate
  useEffect(() => {
    const stored = localStorage.getItem('auth_token');
    if (stored) {
      setToken(stored);
      fetchUser(stored);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async (_authToken?: string) => {
    try {
      const data = await apiGet('/auth/me');
      setUser(data);
    } catch {
      // Token invalid or network error
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
    }
    setLoading(false);
  };

  const refreshUser = useCallback(async () => {
    if (token) {
      await fetchUser(token);
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    const data = await apiPost('/auth/login', { email, password });
    localStorage.setItem('auth_token', data.access_token);
    setToken(data.access_token);
    setUser(data.user);
  };

  const register = async (
    email: string,
    username: string,
    password: string,
    contactInfo: string,
    role: string = 'participant'
  ) => {
    const data = await apiPost('/auth/register', { email, username, password, contact_info: contactInfo, role });
    localStorage.setItem('auth_token', data.access_token);
    setToken(data.access_token);
    setUser(data.user);
  };

  const updateProfile = async (profileData: { username?: string; contact_info?: string; tags?: string[] }) => {
    const data = await apiPut('/auth/me', profileData);
    setUser(data);
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin',
        refreshUser,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}