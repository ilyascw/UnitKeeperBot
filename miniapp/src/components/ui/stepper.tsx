import { Minus, Plus } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface StepperProps {
  label: string;
  description?: string;
  value: number;
  suffix?: string;
  min?: number;
  max?: number;
  step?: number;
  onValueChange: (value: number) => void;
  disabled?: boolean;
  className?: string;
}

function Stepper({
  label,
  description,
  value,
  suffix = '',
  min = 1,
  max = 99,
  step = 1,
  onValueChange,
  disabled = false,
  className,
}: StepperProps) {
  return (
    <div
      data-slot="stepper"
      className={cn(
        'flex min-h-16 items-center justify-between gap-3 rounded-lg border border-input bg-background/40 px-3 py-2',
        className,
      )}
    >
      <div className="min-w-0">
        <div className="text-sm font-medium">{label}</div>
        {description ? (
          <div className="mt-0.5 text-xs text-muted-foreground">{description}</div>
        ) : null}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="icon"
          disabled={disabled || value <= min}
          aria-label={`Уменьшить: ${label}`}
          onClick={() => onValueChange(Math.max(min, value - step))}
        >
          <Minus />
        </Button>
        <output className="min-w-14 text-center text-base font-semibold" aria-live="polite">
          {value} {suffix}
        </output>
        <Button
          type="button"
          variant="secondary"
          size="icon"
          disabled={disabled || value >= max}
          aria-label={`Увеличить: ${label}`}
          onClick={() => onValueChange(Math.min(max, value + step))}
        >
          <Plus />
        </Button>
      </div>
    </div>
  );
}

export { Stepper };
