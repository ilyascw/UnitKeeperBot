import { Loader2Icon } from 'lucide-react';

import { cn } from '@/lib/utils';

function Spinner({ className, ...props }: React.ComponentProps<'svg'>) {
  const hidden = props['aria-hidden'] === true || props['aria-hidden'] === 'true';

  return (
    <Loader2Icon
      data-slot="spinner"
      role={hidden ? undefined : 'status'}
      aria-label={hidden ? undefined : 'Загрузка'}
      className={cn('size-4 animate-spin', className)}
      {...props}
    />
  );
}

export { Spinner };
