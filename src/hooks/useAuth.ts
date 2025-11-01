'use client';

import { useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';

import { ApiError } from '@/lib/api-client';
import {
  changePassword as changePasswordRequest,
  consumeMagicLink as consumeMagicLinkRequest,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
  requestMagicLink as requestMagicLinkRequest,
} from '@/lib/auth-client';
import { useAuthContext } from '@/context/auth-context';
import type {
  AuthTokens,
  ChangePasswordRequest,
  LoginRequest,
  MagicLinkConsumeRequest,
  MagicLinkRequest,
  RegisterRequest,
  UserProfile,
} from '@/types/auth';

export const useSession = () => {
  const { user, accessToken, refreshToken, isAuthenticated, isInitializing } = useAuthContext();
  return { user, accessToken, refreshToken, isAuthenticated, isInitializing };
};

export const useRegister = () => {
  return useMutation<UserProfile, ApiError, RegisterRequest>({
    mutationFn: (payload) => registerRequest(payload),
  });
};

export const useLogin = () => {
  const { setSession } = useAuthContext();

  return useMutation<AuthTokens, ApiError, LoginRequest>({
    mutationFn: (payload) => loginRequest(payload),
    onSuccess: async (tokens) => {
      await setSession(tokens);
    },
  });
};

export const useLogout = () => {
  const { ensureValidToken, refreshToken, clearSession } = useAuthContext();

  return useMutation<void, ApiError, void>({
    mutationFn: async () => {
      const authToken = await ensureValidToken();
      if (!authToken || !refreshToken) {
        clearSession();
        return;
      }
      await logoutRequest(authToken, { refresh_token: refreshToken });
    },
    onSettled: () => {
      clearSession();
    },
  });
};

export const useRequestMagicLink = () =>
  useMutation<void, ApiError, MagicLinkRequest>({
    mutationFn: (payload) => requestMagicLinkRequest(payload),
  });

export const useConsumeMagicLink = () => {
  const { setSession } = useAuthContext();

  return useMutation<AuthTokens, ApiError, MagicLinkConsumeRequest>({
    mutationFn: (payload) => consumeMagicLinkRequest(payload),
    onSuccess: async (tokens) => {
      await setSession(tokens);
    },
  });
};

export const useChangePassword = () => {
  const { ensureValidToken } = useAuthContext();

  return useMutation<void, ApiError, ChangePasswordRequest>({
    mutationFn: async (payload) => {
      const token = await ensureValidToken();
      if (!token) {
        throw new ApiError(401, 'Not authenticated');
      }
      await changePasswordRequest(token, payload);
    },
  });
};

export const useAuthHelpers = () => {
  const { ensureValidToken, updateUser } = useAuthContext();

  const getValidToken = useCallback(() => ensureValidToken(), [ensureValidToken]);
  return { ensureValidToken: getValidToken, updateUser };
};
