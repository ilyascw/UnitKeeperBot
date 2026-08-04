import type { ReactNode } from 'react';
import { CircleAlert, Info, TriangleAlert } from 'lucide-react';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';

const toneStyles = {
  info: 'border-border bg-card text-card-foreground',
  warn: 'border-[color-mix(in_srgb,var(--uk-warn)_45%,transparent)] bg-[color-mix(in_srgb,var(--uk-warn)_12%,transparent)] text-foreground',
  error: 'border-destructive/40 bg-destructive/10 text-destructive',
} as const;

function Note({
  tone = 'info',
  children,
  className,
}: {
  tone?: keyof typeof toneStyles;
  children: ReactNode;
  className?: string;
}) {
  const Icon = tone === 'warn' ? TriangleAlert : tone === 'error' ? CircleAlert : Info;

  return (
    <Alert role="status" className={cn(toneStyles[tone], className)}>
      <Icon aria-hidden="true" />
      <AlertDescription className="text-current">{children}</AlertDescription>
    </Alert>
  );
}

export { Note };
