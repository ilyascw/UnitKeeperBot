import type { ReactNode } from 'react';
import { CheckCircle2, CircleAlert, Info } from 'lucide-react';

import { cn } from '@/lib/utils';

const toneStyles = {
  info: 'text-foreground',
  success: 'text-[var(--uk-positive)]',
  error: 'text-destructive',
} as const;

function Toast({
  children,
  tone = 'info',
  className,
}: {
  children: ReactNode;
  tone?: keyof typeof toneStyles;
  className?: string;
}) {
  const Icon = tone === 'success' ? CheckCircle2 : tone === 'error' ? CircleAlert : Info;

  return (
    <div
      data-slot="toast"
      className={cn(
        'fixed right-4 bottom-[calc(1rem+var(--uk-safe-bottom))] left-4 z-[70] mx-auto flex min-h-12 max-w-[28rem] items-center gap-2 rounded-lg border border-border bg-popover/95 px-4 py-3 text-sm font-medium shadow-lg backdrop-blur-xl',
        toneStyles[tone],
        className,
      )}
      role="status"
      aria-live="polite"
    >
      <Icon className="size-4 shrink-0" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}

export { Toast };
