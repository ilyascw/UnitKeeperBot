import { Spinner, Text } from '@telegram-apps/telegram-ui';

/** Centred full-height loading indicator for screen-level async states. */
export function Loader({ label = 'Loading…' }: { label?: string }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 16,
        minHeight: '60vh',
        padding: 24,
      }}
    >
      <Spinner size="l" />
      <Text style={{ color: 'var(--tg-theme-hint-color)' }}>{label}</Text>
    </div>
  );
}
