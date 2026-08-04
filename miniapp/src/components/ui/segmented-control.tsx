import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { cn } from '@/lib/utils';

interface SegmentedControlProps<Value extends string> {
  options: ReadonlyArray<{ value: Value; label: string }>;
  value: Value;
  onValueChange: (value: Value) => void;
  disabled?: boolean;
  className?: string;
  label: string;
}

function SegmentedControl<Value extends string>({
  options,
  value,
  onValueChange,
  disabled = false,
  className,
  label,
}: SegmentedControlProps<Value>) {
  return (
    <ToggleGroup
      value={[value]}
      onValueChange={(nextValue) => {
        const selected = nextValue.at(-1);
        if (selected) onValueChange(selected as Value);
      }}
      disabled={disabled}
      multiple={false}
      spacing={1}
      aria-label={label}
      className={cn('grid w-full auto-cols-fr grid-flow-col rounded-lg bg-muted/60 p-1', className)}
    >
      {options.map((option) => (
        <ToggleGroupItem
          key={option.value}
          value={option.value}
          className="h-10 w-full min-w-0 px-2 aria-pressed:bg-primary aria-pressed:text-primary-foreground"
        >
          <span className="truncate">{option.label}</span>
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  );
}

export { SegmentedControl };
