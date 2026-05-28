import { request } from './client';
import type {
  CreateGroupRequest,
  CurrentContextResponse,
  GroupCardResponse,
  GroupMembersResponse,
  GroupResponse,
  JoinGroupRequest,
  SessionResponse,
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
