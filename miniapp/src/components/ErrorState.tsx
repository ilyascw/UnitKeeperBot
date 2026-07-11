import type { ReactNode } from 'react';

import { Button, Screen } from '@/ui/kit';
import { AlertIcon } from '@/ui/icons';

interface ErrorStateProps {
  title?: string;
  description?: ReactNode;
  onRetry?: () => void;
  retryLabel?: string;
  icon?: ReactNode;
  accent?: string;
}

/** Screen-level error / empty placeholder with an optional retry action. */
export function ErrorState({
  title = 'Что-то пошло не так',
  description,
  onRetry,
  retryLabel = 'Повторить',
  icon,
  accent = 'rgba(94,199,255',
}: ErrorStateProps) {
  return (
    <Screen centered>
      <div
        style={{
          width: 110,
          height: 110,
          borderRadius: 34,
          display: 'grid',
          placeItems: 'center',
          background: `${accent},0.1)`,
          border: `1px solid ${accent},0.25)`,
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,.15)',
          marginBottom: 4,
        }}
      >
        {icon ?? <AlertIcon size={48} strokeWidth={1.7} style={{ color: 'var(--uk-blue)' }} />}
      </div>
      <div>
        <div style={{ font: "700 22px 'Manrope'", marginBottom: 10 }}>{title}</div>
        {description ? (
          <div
            style={{
              font: "400 15px/1.6 'Manrope'",
              color: 'var(--uk-ink-70)',
              maxWidth: 260,
              marginInline: 'auto',
            }}
          >
            {description}
          </div>
        ) : null}
      </div>
      {onRetry ? (
        <div style={{ width: '100%', maxWidth: 260, marginTop: 6 }}>
          <Button variant="primary" onClick={onRetry}>
            {retryLabel}
          </Button>
        </div>
      ) : null}
    </Screen>
  );
}
