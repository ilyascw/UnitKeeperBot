import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';

import { ApiError } from '@/api/client';
import { authenticateTelegram, getCurrentContext } from '@/api/endpoints';
import type { CurrentContextResponse } from '@/api/types';
import { resolveRawInitData } from '@/telegram/launch';

import { AuthContext, type AuthState, type AuthStatus } from './context';
import { clearSession, loadSession, saveSession } from './session';

interface InternalState {
  status: AuthStatus;
  token: string | null;
  context: CurrentContextResponse | null;
  error: Error | null;
}

const INITIAL_STATE: InternalState = {
  status: 'loading',
  token: null,
  context: null,
  error: null,
};

/**
 * Bootstraps and owns the backend session.
 *
 * Flow on mount (and on `reauthenticate`):
 *  1. If a non-expired token is stored, validate it via `/auth/me` and reuse it.
 *  2. Otherwise exchange Telegram init data for a fresh session via
 *     `/auth/telegram`.
 *
 * The user id is never passed by the client — it is derived by the backend from
 * the signed init data, satisfying the "no manual user id" acceptance criterion.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<InternalState>(INITIAL_STATE);
  // Monotonic token to ignore results from superseded bootstrap runs.
  const runRef = useRef(0);

  const bootstrap = useCallback(async (): Promise<void> => {
    const runId = ++runRef.current;
    setState((prev) => ({ ...prev, status: 'loading', error: null }));

    const apply = (next: InternalState): void => {
      if (runRef.current === runId) setState(next);
    };

    // 1. Try to restore an existing session.
    const stored = loadSession();
    if (stored) {
      try {
        const context = await getCurrentContext(stored.accessToken);
        apply({ status: 'authenticated', token: stored.accessToken, context, error: null });
        return;
      } catch (error) {
        // An invalid/expired token: drop it and fall through to a fresh login.
        if (error instanceof ApiError && error.isAuthError) {
          clearSession();
        } else {
          apply({ status: 'error', token: null, context: null, error: error as Error });
          return;
        }
      }
    }

    // 2. Fresh authentication from Telegram init data.
    const initData = resolveRawInitData();
    if (!initData) {
      apply({
        status: 'unauthenticated',
        token: null,
        context: null,
        error: null,
      });
      return;
    }

    try {
      const session = await authenticateTelegram(initData);
      saveSession({ accessToken: session.access_token, expiresAt: session.expires_at });
      apply({
        status: 'authenticated',
        token: session.access_token,
        context: session.context,
        error: null,
      });
    } catch (error) {
      apply({ status: 'error', token: null, context: null, error: error as Error });
    }
  }, []);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  const reauthenticate = useCallback(() => {
    clearSession();
    void bootstrap();
  }, [bootstrap]);

  const value: AuthState = {
    status: state.status,
    token: state.token,
    context: state.context,
    error: state.error,
    reauthenticate,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
