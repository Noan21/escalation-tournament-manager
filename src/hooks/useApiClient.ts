'use client';

import { useCallback } from 'react';

import { apiFetch, type ApiFetchOptions } from '@/lib/api-client';
import { useAuthContext } from '@/context/auth-context';

type ClientRequestOptions = ApiFetchOptions & {
  requireAuth?: boolean;
};

export const useApiClient = () => {
  const { ensureValidToken } = useAuthContext();

  const request = useCallback(
    async <T>(path: string, options: ClientRequestOptions = {}) => {
      const { requireAuth = false, authToken, ...rest } = options;

      let tokenToUse = authToken ?? null;
      if (requireAuth) {
        tokenToUse = await ensureValidToken();
        if (!tokenToUse) {
          throw new Error('Authentication required');
        }
      }

      return apiFetch<T>(path, {
        authToken: tokenToUse,
        ...rest,
      });
    },
    [ensureValidToken]
  );

  return { request };
};
