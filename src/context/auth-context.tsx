'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

import { ApiError } from '@/lib/api-client';
import { fetchProfile, refresh as refreshTokens } from '@/lib/auth-client';
import type { AuthTokens, UserProfile } from '@/types/auth';

interface AuthState {
  user: UserProfile | null;
  accessToken: string | null;
  refreshToken: string | null;
  expiresAt: number | null;
}

const STORAGE_KEY = 'angrom.auth.session';

const initialState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  expiresAt: null,
};

interface AuthContextValue extends AuthState {
  isInitializing: boolean;
  isAuthenticated: boolean;
  setSession: (tokens: AuthTokens, profile?: UserProfile | null) => Promise<UserProfile | null>;
  updateUser: (profile: UserProfile | null) => void;
  clearSession: () => void;
  ensureValidToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const readStoredState = (): AuthState => {
  if (typeof window === 'undefined') {
    return initialState;
  }

  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return initialState;
  }

  try {
    const parsed = JSON.parse(raw) as AuthState;
    return {
      user: parsed.user ?? null,
      accessToken: parsed.accessToken ?? null,
      refreshToken: parsed.refreshToken ?? null,
      expiresAt: parsed.expiresAt ?? null,
    };
  } catch (error) {
    console.warn('Failed to parse stored auth state', error);
    return initialState;
  }
};

const persistState = (state: AuthState): void => {
  if (typeof window === 'undefined') {
    return;
  }

  if (!state.accessToken || !state.refreshToken) {
    window.localStorage.removeItem(STORAGE_KEY);
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
};

export const AuthProvider = ({ children }: { children: React.ReactNode }): JSX.Element => {
  const [state, setState] = useState<AuthState>(initialState);
  const [isInitializing, setInitializing] = useState(true);
  const refreshingRef = useRef(false);

  useEffect(() => {
    const stored = readStoredState();
    setState(stored);
    setInitializing(false);
  }, []);

  useEffect(() => {
    persistState(state);
  }, [state]);

  const setSession = useCallback(
    async (tokens: AuthTokens, profile?: UserProfile | null): Promise<UserProfile | null> => {
      const expiresAt = Date.now() + tokens.expires_in * 1000;
      let nextProfile = profile ?? null;

      if (!nextProfile && tokens.access_token) {
        try {
          nextProfile = await fetchProfile(tokens.access_token);
        } catch (error) {
          console.error('Failed to fetch user profile after login', error);
        }
      }

      const nextState: AuthState = {
        user: nextProfile,
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        expiresAt,
      };

      setState(nextState);
      return nextProfile;
    },
    []
  );

  const updateUser = useCallback((profile: UserProfile | null) => {
    setState((current) => ({
      ...current,
      user: profile,
    }));
  }, []);

  const clearSession = useCallback(() => {
    setState(initialState);
  }, []);

  const ensureValidToken = useCallback(async (): Promise<string | null> => {
    if (!state.accessToken || !state.refreshToken || !state.expiresAt) {
      return null;
    }

    const now = Date.now();
    const bufferMs = 30_000; // refresh 30s before expiry
    if (state.expiresAt - bufferMs > now) {
      return state.accessToken;
    }

    if (refreshingRef.current) {
      // Another refresh is in-flight; wait briefly then return latest token
      await new Promise((resolve) => setTimeout(resolve, 150));
      return state.accessToken;
    }

    refreshingRef.current = true;
    try {
      const tokens = await refreshTokens({ refresh_token: state.refreshToken }, state.accessToken);
      await setSession(tokens, state.user);
      return tokens.access_token;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        clearSession();
      }
      console.error('Token refresh failed', error);
      return null;
    } finally {
      refreshingRef.current = false;
    }
  }, [clearSession, setSession, state.accessToken, state.expiresAt, state.refreshToken, state.user]);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      isInitializing,
      isAuthenticated: Boolean(state.accessToken && state.refreshToken),
      setSession,
      updateUser,
      clearSession,
      ensureValidToken,
    }),
    [clearSession, ensureValidToken, isInitializing, setSession, state, updateUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuthContext = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuthContext must be used within AuthProvider');
  }
  return ctx;
};
