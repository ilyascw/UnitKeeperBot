import { request } from './client';
import type { CurrentContextResponse, GroupCardResponse, SessionResponse } from './types';

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
