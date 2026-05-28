import type { ReactNode } from 'react';

import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';

import { useAuth } from './useAuth';

/**
 * Gates the authenticated app behind the session bootstrap. Renders children
 * only once a session exists; otherwise shows the appropriate loading / error /
 * "open from Telegram" state.
 */
export function AuthGate({ children }: { children: ReactNode }) {
  const { status, error, reauthenticate } = useAuth();

  if (status === 'loading') {
    return <Loader label="Signing you in…" />;
  }

  if (status === 'unauthenticated') {
    return (
      <ErrorState
        title="Open from Telegram"
        description="UnitKeeper runs as a Telegram Mini App. Please open it from the Telegram bot to continue."
        onRetry={reauthenticate}
        retryLabel="Retry"
      />
    );
  }

  if (status === 'error') {
    return (
      <ErrorState
        title="Couldn’t sign you in"
        description={error?.message ?? 'Please try again.'}
        onRetry={reauthenticate}
      />
    );
  }

  return <>{children}</>;
}
