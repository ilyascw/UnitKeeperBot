import { Button, Placeholder } from '@telegram-apps/telegram-ui';

interface ErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
  retryLabel?: string;
}

/** Screen-level error placeholder with an optional retry action. */
export function ErrorState({
  title = 'Something went wrong',
  description,
  onRetry,
  retryLabel = 'Try again',
}: ErrorStateProps) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
      }}
    >
      <Placeholder header={title} description={description}>
        {onRetry ? (
          <Button size="m" onClick={onRetry}>
            {retryLabel}
          </Button>
        ) : null}
      </Placeholder>
    </div>
  );
}
