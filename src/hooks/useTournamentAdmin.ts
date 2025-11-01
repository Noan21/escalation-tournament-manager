'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useApiClient } from '@/hooks/useApiClient';
import type {
  EventProfile,
  EventRegistration,
  MatchResultPayload,
  RoundProfile,
  SeasonLeaderboard,
  StandingsPayload,
} from '@/types/tournament';

export const useRegistrationsQuery = (eventId: string | null) => {
  const { request } = useApiClient();
  return useQuery<EventRegistration[]>({
    queryKey: ['registrations', eventId],
    queryFn: async () => request<EventRegistration[]>(`/api/registrations/events/${eventId}`, { requireAuth: true }),
    enabled: Boolean(eventId),
    staleTime: 15_000,
  });
};

export const useConfirmRegistration = (eventId: string | null, registrationId: string | null) => {
  const { request } = useApiClient();
  const queryClient = useQueryClient();
  return useMutation<EventRegistration, Error, { status: string }>({
    mutationFn: async (payload) => {
      if (!registrationId) {
        throw new Error('Missing registration id');
      }
      return request<EventRegistration>(`/api/registrations/${registrationId}/status`, {
        method: 'PATCH',
        requireAuth: true,
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['registrations', eventId] });
    },
  });
};

export const useGenerateRound = (stageId: string | null) => {
  const { request } = useApiClient();
  return useMutation<RoundProfile, Error, { pairing_seed?: string | null; round_number?: number }>({
    mutationFn: async (payload) => {
      if (!stageId) {
        throw new Error('Missing stage id');
      }
      return request<RoundProfile>(`/api/stages/${stageId}/pairings/rounds`, {
        method: 'POST',
        requireAuth: true,
        body: JSON.stringify(payload ?? {}),
      });
    },
  });
};

export const useLockRound = (roundId: string | null) => {
  const { request } = useApiClient();
  return useMutation<RoundProfile, Error>({
    mutationFn: async () => {
      if (!roundId) {
        throw new Error('Missing round id');
      }
      return request<RoundProfile>(`/api/rounds/${roundId}/lock`, {
        method: 'POST',
        requireAuth: true,
      });
    },
  });
};

export const useStandingsQuery = (stageId: string | null) => {
  const { request } = useApiClient();
  return useQuery<StandingsPayload>({
    queryKey: ['standings', stageId],
    queryFn: async () => request<StandingsPayload>(`/api/stages/${stageId}/standings`, { requireAuth: true }),
    enabled: Boolean(stageId),
    staleTime: 10_000,
  });
};

export const useRecomputeSeason = (seasonId: string | null) => {
  const { request } = useApiClient();
  return useMutation<SeasonLeaderboard, Error>({
    mutationFn: async () => {
      if (!seasonId) {
        throw new Error('Missing season id');
      }
      return request<SeasonLeaderboard>(`/api/seasons/${seasonId}/recompute`, {
        method: 'POST',
        requireAuth: true,
      });
    },
  });
};

export const useSeasonEvents = (seasonId: string | null) => {
  const { request } = useApiClient();
  return useQuery<EventProfile[]>({
    queryKey: ['season-events', seasonId],
    queryFn: async () => request<EventProfile[]>(`/api/seasons/${seasonId}/events`, { requireAuth: true }),
    enabled: Boolean(seasonId),
    staleTime: 30_000,
  });
};

export const useSubmitMatchResult = () => {
  const { request } = useApiClient();
  return useMutation<void, Error, MatchResultPayload>({
    mutationFn: async (payload) => {
      await request(`/api/matches/${payload.match_id}/result`, {
        method: 'POST',
        requireAuth: true,
        body: JSON.stringify(payload),
      });
    },
  });
};
