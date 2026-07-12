import { useQuery, type UseQueryResult } from '@tanstack/react-query';

import { useAuthToken } from '@/auth/useAuth';

import { ApiError } from './client';
import {
  getCurrentGroup,
  getSprintResults,
  listBalanceTransactions,
  listGroupTaskLogs,
  listMyTaskLogs,
  listPendingApprovals,
  listTasks,
  listTransferCandidates,
} from './endpoints';
import type {
  BalanceTransactionPageResponse,
  GroupCardResponse,
  SprintResultsResponse,
  TaskLogPageResponse,
  TaskResponse,
  TransferCandidatesResponse,
} from './types';

export const queryKeys = {
  currentGroup: ['groups', 'current'] as const,
  tasks: ['tasks'] as const,
  sprintResults: ['sprints', 'current', 'results'] as const,
  pendingApprovals: ['task-logs', 'pending-approval'] as const,
  myTaskLogs: ['task-logs', 'mine'] as const,
  groupTaskLogs: ['groups', 'current', 'task-logs'] as const,
  transferCandidates: ['balances', 'transfer-candidates'] as const,
  balanceTransactions: (limit: number, offset: number) =>
    ['balances', 'transactions', limit, offset] as const,
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

export function usePendingApprovals(enabled: boolean): UseQueryResult<TaskLogPageResponse, Error> {
  const token = useAuthToken();
  return useQuery({
    queryKey: queryKeys.pendingApprovals,
    queryFn: () => listPendingApprovals(token),
    enabled,
  });
}

export function useMyTaskLogs(): UseQueryResult<TaskLogPageResponse, Error> {
  const token = useAuthToken();
  return useQuery({ queryKey: queryKeys.myTaskLogs, queryFn: () => listMyTaskLogs(token) });
}

export function useGroupTaskLogs(enabled: boolean): UseQueryResult<TaskLogPageResponse, Error> {
  const token = useAuthToken();
  return useQuery({
    queryKey: queryKeys.groupTaskLogs,
    queryFn: () => listGroupTaskLogs(token),
    enabled,
  });
}

/** Active group members you can transfer units to, other than yourself. */
export function useTransferCandidates(): UseQueryResult<TransferCandidatesResponse, Error> {
  const token = useAuthToken();
  return useQuery({
    queryKey: queryKeys.transferCandidates,
    queryFn: () => listTransferCandidates(token),
  });
}

/** Paginated balance transaction history for the current user. */
export function useBalanceTransactions(
  { limit, offset }: { limit: number; offset: number },
  enabled = true,
): UseQueryResult<BalanceTransactionPageResponse, Error> {
  const token = useAuthToken();
  return useQuery({
    queryKey: queryKeys.balanceTransactions(limit, offset),
    queryFn: () => listBalanceTransactions(token, { limit, offset }),
    enabled,
  });
}
