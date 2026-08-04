import type { QueryClient } from '@tanstack/react-query';

import { queryKeys } from './queries';

const TASK_DATA_QUERY_KEYS = [
  queryKeys.tasks,
  queryKeys.sprintResults,
  queryKeys.currentGroup,
  queryKeys.pendingApprovals,
  queryKeys.myTaskLogs,
  queryKeys.groupTaskLogs,
] as const;

interface RefreshTaskDataOptions {
  refetchType?: 'active' | 'all';
  throwOnError?: boolean;
}

export async function refreshTaskData(
  queryClient: QueryClient,
  { refetchType = 'active', throwOnError = false }: RefreshTaskDataOptions = {},
): Promise<void> {
  await Promise.all(
    TASK_DATA_QUERY_KEYS.map((queryKey) =>
      queryClient.invalidateQueries({ queryKey, refetchType }, { throwOnError }),
    ),
  );
}
