import { useQuery, type UseQueryResult } from '@tanstack/react-query';

import { useAuthToken } from '@/auth/useAuth';

import { ApiError } from './client';
import { getCurrentGroup, getSprintResults, listTasks } from './endpoints';
import type { GroupCardResponse, SprintResultsResponse, TaskResponse } from './types';

export const queryKeys = {
  currentGroup: ['groups', 'current'] as const,
  tasks: ['tasks'] as const,
  sprintResults: ['sprints', 'current', 'results'] as const,
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

/** The current group's active tasks with per-sprint completion counts. */
export function useTasks(): UseQueryResult<TaskResponse[], Error> {
  const token = useAuthToken();
  return useQuery({
    queryKey: queryKeys.tasks,
    queryFn: () => listTasks(token),
  });
}

/** Provisional results for the running sprint. */
export function useSprintResults(): UseQueryResult<SprintResultsResponse, Error> {
  const token = useAuthToken();
  return useQuery({
    queryKey: queryKeys.sprintResults,
    queryFn: () => getSprintResults(token),
  });
}
