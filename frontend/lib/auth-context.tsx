'use client';

import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { api, clearSession, getStoredUser, getToken, setSession } from './api';
import type { User } from './types';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (identifier: string, password: string) => Promise<User>;
  register: (payload: Record<string, unknown>) => Promise<User>;
  completeRegistration: (token: string, user: User) => void;
  logout: () => void;
  refresh: () => Promise<void>;
  setUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = getStoredUser();
    if (stored) setUserState(stored);
    if (getToken()) {
      api
        .me()
        .then((u) => setUserState(u))
        .catch(() => clearSession())
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (identifier: string, password: string) => {
    const res = await api.login(identifier, password);
    setSession(res.access_token, res.user);
    setUserState(res.user);
    return res.user;
  }, []);

  const register = useCallback(async (payload: Record<string, unknown>) => {
    const res = await api.register(payload);
    setSession(res.access_token, res.user);
    setUserState(res.user);
    return res.user;
  }, []);

  const completeRegistration = useCallback((token: string, u: User) => {
    setSession(token, u);
    setUserState(u);
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setUserState(null);
  }, []);

  const refresh = useCallback(async () => {
    const u = await api.me();
    setUserState(u);
  }, []);

  const setUser = useCallback((u: User) => {
    setSession(getToken() || '', u);
    setUserState(u);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, completeRegistration, logout, refresh, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
