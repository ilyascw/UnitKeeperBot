import type { ReactNode } from 'react';

import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { PlaneIcon } from '@/ui/icons';

import { useAuth } from './useAuth';

/**
 * Gates the authenticated app behind the session bootstrap. Renders children
 * only once a session exists; otherwise shows the appropriate loading / error /
 * "open from Telegram" state.
 */
export function AuthGate({ children }: { children: ReactNode }) {
  const { status, error, reauthenticate } = useAuth();

  if (status === 'loading') {
    return <Loader title="Входим…" label="Проверяем ваш профиль Telegram. Это займёт секунду." />;
  }

  if (status === 'unauthenticated') {
    return (
      <ErrorState
        title="Откройте из Telegram"
        description="UnitKeeper работает внутри Telegram. Найдите бота в чате и нажмите «Открыть»."
        icon={<PlaneIcon size={52} style={{ color: 'var(--uk-blue)' }} />}
        onRetry={reauthenticate}
        retryLabel="Повторить"
      />
    );
  }

  if (status === 'error') {
    return (
      <ErrorState
        title="Не удалось войти"
        description={error?.message ?? 'Попробуйте ещё раз.'}
        accent="rgba(217,118,124"
        onRetry={reauthenticate}
      />
    );
  }

  return <>{children}</>;
}
