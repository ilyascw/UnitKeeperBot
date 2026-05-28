import { useQuery, type UseQueryResult } from '@tanstack/react-query';

import { useAuthToken } from '@/auth/useAuth';

import { ApiError } from './client';
import { getCurrentGroup } from './endpoints';
import type { GroupCardResponse } from './types';

export const queryKeys = {
  currentGroup: ['groups', 'current'] as const,
};

/**
 * Loads the current group card. Returns `null` (not an error) when the user is
 * not in a group, so screens can branch into the onboarding flow.
 */
export function useCurrentGroup(): UseQueryResult<GroupCardResponse | null, Error> {
  const token = useAuthToken();
  return useQuery({
    queryKey: queryKeys.currentGroup,
    queryFn: async () => {
      try {
        return await getCurrentGroup(token);
      } catch (error) {
        if (error instanceof ApiError && error.isNotFound) {
          return null;
        }
        throw error;
      }
    },
  });
}
