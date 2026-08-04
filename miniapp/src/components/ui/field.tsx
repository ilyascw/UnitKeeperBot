import type { ComponentProps, ReactNode } from 'react';
import { CircleAlert } from 'lucide-react';

import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface FieldProps extends ComponentProps<'div'> {
  label?: ReactNode;
  htmlFor?: string;
  hint?: ReactNode;
  error?: ReactNode;
  messageId?: string;
}

function Field({
  className,
  label,
  htmlFor,
  hint,
  error,
  messageId,
  children,
  ...props
}: FieldProps) {
  return (
    <div data-slot="field" className={cn('grid gap-2', className)} {...props}>
      {label ? <Label htmlFor={htmlFor}>{label}</Label> : null}
      {children}
      {error ? (
        <div
          id={messageId}
          data-slot="field-error"
          className="flex items-start gap-1.5 text-sm text-destructive"
          role="alert"
        >
          <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      ) : hint ? (
        <div id={messageId} data-slot="field-description" className="text-sm text-muted-foreground">
          {hint}
        </div>
      ) : null}
    </div>
  );
}

export { Field };
