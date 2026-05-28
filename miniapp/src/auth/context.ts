import { createContext } from 'react';

import type { CurrentContextResponse } from '@/api/types';

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated' | 'error';

export interface AuthState {
  status: AuthStatus;
  /** Bearer token for API calls; present only when authenticated. */
  token: string | null;
  /** Current user / membership / group snapshot from the last auth call. */
  context: CurrentContextResponse | null;
  /** Populated when `status === 'error'`. */
  error: Error | null;
  /** Re-run the auth bootstrap (e.g. after a failure or expiry). */
  reauthenticate: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);
