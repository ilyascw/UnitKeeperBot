import { request } from './client';
import type {
  CreateGroupRequest,
  CreateTaskRequest,
  BulkImportTaskItem,
  CurrentContextResponse,
  GroupCardResponse,
  GroupMembersResponse,
  GroupResponse,
  JoinGroupRequest,
  SessionResponse,
  SprintResultsResponse,
  TaskLogResponse,
  TaskLogPageResponse,
  TaskResponse,
  UpdateTaskRequest,
  UpdateGroupSettingsRequest,
  UpdateWeightsRequest,
} from './types';

/**
 * Exchange Telegram init data for a backend session. The server validates the
 * init data signature, so no user id is ever passed from the client.
 */
export function authenticateTelegram(initData: string): Promise<SessionResponse> {
  return request<SessionResponse>('/auth/telegram', {
    method: 'POST',
    body: { init_data: initData },
  });
}

/** Resolve the current context (user + membership + group) for a saved token. */
export function getCurrentContext(token: string): Promise<CurrentContextResponse> {
  return request<CurrentContextResponse>('/auth/me', { token });
}

/** Fetch the rich card for the user's current group. 404 when not in a group. */
export function getCurrentGroup(token: string): Promise<GroupCardResponse> {
  return request<GroupCardResponse>('/groups/current', { token });
}

export function listCurrentGroupMembers(token: string): Promise<GroupMembersResponse> {
  return request<GroupMembersResponse>('/groups/current/members', { token });
}

export function createGroup(
  token: string,
  body: CreateGroupRequest,
): Promise<CurrentContextResponse> {
  return request<CurrentContextResponse>('/groups', { method: 'POST', body, token });
}

export function joinGroup(
  token: string,
  body: JoinGroupRequest,
): Promise<CurrentContextResponse> {
  return request<CurrentContextResponse>('/groups/join', { method: 'POST', body, token });
}

export function leaveGroup(token: string): Promise<void> {
  return request<void>('/groups/leave', { method: 'POST', token });
}

export function updateCurrentGroupSettings(
  token: string,
  body: UpdateGroupSettingsRequest,
): Promise<GroupResponse> {
  return request<GroupResponse>('/groups/current/settings', {
    method: 'PATCH',
    body,
    token,
  });
}

export function updateCurrentGroupWeights(
  token: string,
  body: UpdateWeightsRequest,
): Promise<GroupMembersResponse> {
  return request<GroupMembersResponse>('/groups/current/weights', {
    method: 'PUT',
    body,
    token,
  });
}

/** List the current group's active tasks with per-sprint completion counts. */
export function listTasks(token: string): Promise<TaskResponse[]> {
  return request<TaskResponse[]>('/tasks', { token });
}

export function createTask(token: string, body: CreateTaskRequest): Promise<TaskResponse> {
  return request<TaskResponse>('/tasks', { method: 'POST', body, token });
}

export function importTasks(token: string, items: BulkImportTaskItem[]): Promise<TaskResponse[]> {
  return request<TaskResponse[]>('/tasks/import', { method: 'POST', body: { items }, token });
}

export function updateTask(
  token: string,
  taskId: number,
  body: UpdateTaskRequest,
): Promise<TaskResponse> {
  return request<TaskResponse>(`/tasks/${taskId}`, { method: 'PATCH', body, token });
}

export function deleteTask(token: string, taskId: number): Promise<void> {
  return request<void>(`/tasks/${taskId}`, { method: 'DELETE', token });
}

export function increaseTaskFrequency(token: string, taskId: number): Promise<TaskResponse> {
  return request<TaskResponse>(`/tasks/${taskId}/increase-frequency`, { method: 'POST', token });
}

export function decreaseTaskFrequency(token: string, taskId: number): Promise<TaskResponse> {
  return request<TaskResponse>(`/tasks/${taskId}/decrease-frequency`, { method: 'POST', token });
}

/** Log a completion for a task; the entry awaits owner approval. */
export function markTaskDone(token: string, taskId: number): Promise<TaskLogResponse> {
  return request<TaskLogResponse>(`/tasks/${taskId}/done`, { method: 'POST', token });
}

export function listPendingApprovals(token: string): Promise<TaskLogPageResponse> {
  return request<TaskLogPageResponse>('/task-logs/pending-approval', { token });
}

export function listMyTaskLogs(token: string): Promise<TaskLogPageResponse> {
  return request<TaskLogPageResponse>('/task-logs/mine', { token });
}

export function listGroupTaskLogs(token: string): Promise<TaskLogPageResponse> {
  return request<TaskLogPageResponse>('/groups/current/task-logs', { token });
}

export function approveTaskLog(token: string, logId: number): Promise<TaskLogResponse> {
  return request<TaskLogResponse>(`/task-logs/${logId}/approve`, { method: 'POST', token });
}

export function rejectTaskLog(token: string, logId: number, reason: string): Promise<TaskLogResponse> {
  return request<TaskLogResponse>(`/task-logs/${logId}/reject`, {
    method: 'POST',
    body: { reason },
    token,
  });
}

/** Provisional results for the running sprint. */
export function getSprintResults(token: string): Promise<SprintResultsResponse> {
  return request<SprintResultsResponse>('/sprints/current/results', { token });
}
