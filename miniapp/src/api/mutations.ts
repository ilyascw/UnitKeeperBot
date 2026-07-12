import { useMutation, useQueryClient, type UseMutationResult } from '@tanstack/react-query';

import { useAuthToken } from '@/auth/useAuth';

import {
  createGroup,
  createTask,
  importTasks,
  decreaseTaskFrequency,
  deleteTask,
  increaseTaskFrequency,
  joinGroup,
  leaveGroup,
  markTaskDone,
  approveTaskLog,
  rejectTaskLog,
  updateTask,
  updateCurrentGroupSettings,
  updateCurrentGroupWeights,
} from './endpoints';
import { queryKeys } from './queries';
import type {
  CreateGroupRequest,
  CreateTaskRequest,
  BulkImportTaskItem,
  CurrentContextResponse,
  GroupMembersResponse,
  GroupResponse,
  JoinGroupRequest,
  TaskLogResponse,
  TaskResponse,
  UpdateTaskRequest,
  UpdateGroupSettingsRequest,
  UpdateWeightsRequest,
} from './types';

/**
 * Invalidate every query whose data could be affected by group membership or
 * settings changes. Centralised here so each mutation stays a one-liner.
 */
function useInvalidateGroup(): () => Promise<void> {
  const qc = useQueryClient();
  return async () => {
    await qc.invalidateQueries({ queryKey: queryKeys.currentGroup });
  };
}

/**
 * Invalidate everything a task completion or a new task can shift: the task
 * list, the sprint results, and the balances shown on the group card.
 */
function useInvalidateTasks(): () => Promise<void> {
  const qc = useQueryClient();
  return async () => {
    await Promise.all([
      qc.invalidateQueries({ queryKey: queryKeys.tasks }),
      qc.invalidateQueries({ queryKey: queryKeys.sprintResults }),
      qc.invalidateQueries({ queryKey: queryKeys.currentGroup }),
      qc.invalidateQueries({ queryKey: queryKeys.pendingApprovals }),
      qc.invalidateQueries({ queryKey: queryKeys.myTaskLogs }),
      qc.invalidateQueries({ queryKey: queryKeys.groupTaskLogs }),
    ]);
  };
}

export function useImportTasks(): UseMutationResult<TaskResponse[], Error, BulkImportTaskItem[]> {
  const token = useAuthToken();
  const invalidate = useInvalidateTasks();
  return useMutation({ mutationFn: (items) => importTasks(token, items), onSuccess: () => invalidate() });
}

export function useCreateGroup(): UseMutationResult<
  CurrentContextResponse,
  Error,
  CreateGroupRequest
> {
  const token = useAuthToken();
  const invalidate = useInvalidateGroup();
  return useMutation({
    mutationFn: (body: CreateGroupRequest) => createGroup(token, body),
    onSuccess: () => invalidate(),
  });
}

export function useJoinGroup(): UseMutationResult<
  CurrentContextResponse,
  Error,
  JoinGroupRequest
> {
  const token = useAuthToken();
  const invalidate = useInvalidateGroup();
  return useMutation({
    mutationFn: (body: JoinGroupRequest) => joinGroup(token, body),
    onSuccess: () => invalidate(),
  });
}

export function useLeaveGroup(): UseMutationResult<void, Error, void> {
  const token = useAuthToken();
  const invalidate = useInvalidateGroup();
  return useMutation({
    mutationFn: () => leaveGroup(token),
    onSuccess: () => invalidate(),
  });
}

export function useUpdateGroupSettings(): UseMutationResult<
  GroupResponse,
  Error,
  UpdateGroupSettingsRequest
> {
  const token = useAuthToken();
  const invalidate = useInvalidateGroup();
  return useMutation({
    mutationFn: (body: UpdateGroupSettingsRequest) => updateCurrentGroupSettings(token, body),
    onSuccess: () => invalidate(),
  });
}

export function useUpdateGroupWeights(): UseMutationResult<
  GroupMembersResponse,
  Error,
  UpdateWeightsRequest
> {
  const token = useAuthToken();
  const invalidate = useInvalidateGroup();
  return useMutation({
    mutationFn: (body: UpdateWeightsRequest) => updateCurrentGroupWeights(token, body),
    onSuccess: () => invalidate(),
  });
}

export function useCreateTask(): UseMutationResult<TaskResponse, Error, CreateTaskRequest> {
  const token = useAuthToken();
  const invalidate = useInvalidateTasks();
  return useMutation({
    mutationFn: (body: CreateTaskRequest) => createTask(token, body),
    onSuccess: () => invalidate(),
  });
}

export function useUpdateTask(): UseMutationResult<
  TaskResponse,
  Error,
  { taskId: number; body: UpdateTaskRequest }
> {
  const token = useAuthToken();
  const invalidate = useInvalidateTasks();
  return useMutation({
    mutationFn: ({ taskId, body }) => updateTask(token, taskId, body),
    onSuccess: () => invalidate(),
  });
}

export function useDeleteTask(): UseMutationResult<void, Error, number> {
  const token = useAuthToken();
  const invalidate = useInvalidateTasks();
  return useMutation({
    mutationFn: (taskId: number) => deleteTask(token, taskId),
    onSuccess: () => invalidate(),
  });
}

export function useIncreaseTaskFrequency(): UseMutationResult<TaskResponse, Error, number> {
  const token = useAuthToken();
  const invalidate = useInvalidateTasks();
  return useMutation({
    mutationFn: (taskId: number) => increaseTaskFrequency(token, taskId),
    onSuccess: () => invalidate(),
  });
}

export function useDecreaseTaskFrequency(): UseMutationResult<TaskResponse, Error, number> {
  const token = useAuthToken();
  const invalidate = useInvalidateTasks();
  return useMutation({
    mutationFn: (taskId: number) => decreaseTaskFrequency(token, taskId),
    onSuccess: () => invalidate(),
  });
}

export function useMarkTaskDone(): UseMutationResult<TaskLogResponse, Error, number> {
  const token = useAuthToken();
  const invalidate = useInvalidateTasks();
  return useMutation({
    mutationFn: (taskId: number) => markTaskDone(token, taskId),
    onSuccess: () => invalidate(),
  });
}

export function useApproveTaskLog(): UseMutationResult<TaskLogResponse, Error, number> {
  const token = useAuthToken();
  const invalidate = useInvalidateTasks();
  return useMutation({ mutationFn: (logId) => approveTaskLog(token, logId), onSuccess: () => invalidate() });
}

export function useRejectTaskLog(): UseMutationResult<
  TaskLogResponse,
  Error,
  { logId: number; reason: string }
> {
  const token = useAuthToken();
  const invalidate = useInvalidateTasks();
  return useMutation({
    mutationFn: ({ logId, reason }) => rejectTaskLog(token, logId, reason),
    onSuccess: () => invalidate(),
  });
}
