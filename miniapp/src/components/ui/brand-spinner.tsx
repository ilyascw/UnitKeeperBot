import { Spinner } from '@/components/ui/spinner';
import { cn } from '@/lib/utils';

function BrandSpinner({ className }: { className?: string }) {
  return <Spinner data-slot="brand-spinner" className={cn('size-16 text-primary', className)} />;
}

export { BrandSpinner };
