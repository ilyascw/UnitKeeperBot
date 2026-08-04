import type { ComponentProps } from 'react';
import { ArrowLeft } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

function Screen({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      data-slot="screen"
      className={cn(
        'mx-auto flex min-h-[calc(100dvh-var(--uk-safe-top))] w-full max-w-[30rem] flex-col gap-4 px-4 pt-3 pb-[calc(2rem+var(--uk-safe-bottom))]',
        className,
      )}
      {...props}
    />
  );
}

function ScreenHeader({
  title,
  description,
  onBack,
  actions,
  className,
}: {
  title: string;
  description?: string;
  onBack?: () => void;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <header className={cn('flex min-h-11 items-center gap-2', className)}>
      {onBack ? (
        <Button type="button" variant="ghost" size="icon" aria-label="Назад" onClick={onBack}>
          <ArrowLeft />
        </Button>
      ) : null}
      <div className="min-w-0 flex-1">
        <h1 className="truncate text-lg font-semibold">{title}</h1>
        {description ? (
          <p className="truncate text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </header>
  );
}

export { Screen, ScreenHeader };
