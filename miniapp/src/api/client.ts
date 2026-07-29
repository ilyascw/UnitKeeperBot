import { config } from '@/config/env';

import type { ErrorResponse } from './types';

/**
 * Error thrown for any non-2xx API response. Carries the backend's structured
 * `code`/`message` when present so the UI can branch on specific conditions
 * (e.g. a missing group or an expired session).
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly details: unknown;

  constructor(status: number, message: string, code: string | null, details: unknown = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }

  /** The session token is missing, invalid, or expired. */
  get isAuthError(): boolean {
    return this.status === 401;
  }

  /** The requested resource does not exist for the current user. */
  get isNotFound(): boolean {
    return this.status === 404;
  }
}

/** Network failure: the request never reached the backend. */
export class NetworkError extends Error {
  constructor(cause: unknown) {
    super('Network request failed');
    this.name = 'NetworkError';
    this.cause = cause;
  }
}

export interface RequestOptions {
  method?: string;
  body?: unknown;
  /** Bearer token attached as `Authorization` when provided. */
  token?: string | null;
  signal?: AbortSignal;
}

async function parseError(response: Response): Promise<ApiError> {
  let message = response.statusText || 'Request failed';
  let code: string | null = null;
  try {
    const payload = (await response.json()) as Partial<ErrorResponse>;
    if (payload && typeof payload.message === 'string') {
      message = payload.message;
    }
    if (payload && typeof payload.code === 'string') {
      code = payload.code;
    }
    return new ApiError(response.status, message, code, payload?.details);
  } catch {
    // Non-JSON error body; keep the status-derived message.
  }
  return new ApiError(response.status, message, code);
}

/**
 * Low-level typed fetch wrapper. Resolves the JSON body for 2xx responses,
 * `undefined` for 204, and throws `ApiError` / `NetworkError` otherwise.
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, token, signal } = options;

  const headers: Record<string, string> = { Accept: 'application/json' };
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${config.apiBaseUrl}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error;
    }
    throw new NetworkError(error);
  }

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
