import { useContext } from 'react';

import { AuthContext, type AuthState } from './context';

/** Access the current auth state. Must be used within an `AuthProvider`. */
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}

/**
 * Returns the Bearer token, asserting the session is authenticated. Use inside
 * screens rendered behind the auth gate where a token is guaranteed.
 */
export function useAuthToken(): string {
  const { token } = useAuth();
  if (!token) {
    throw new Error('useAuthToken called without an authenticated session');
  }
  return token;
}
