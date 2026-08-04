import type { ButtonHTMLAttributes, CSSProperties, InputHTMLAttributes, ReactNode } from 'react';
import { CircleAlert } from 'lucide-react';

import { BrandSpinner as UiBrandSpinner } from '@/components/ui/brand-spinner';
import { Button as UiButton } from '@/components/ui/button';
import { Card as UiCard } from '@/components/ui/card';
import { Drawer, DrawerContent, DrawerDescription, DrawerTitle } from '@/components/ui/drawer';
import { Input } from '@/components/ui/input';
import { MemberAvatar } from '@/components/ui/member-avatar';
import { Note as UiNote } from '@/components/ui/note';
import { Screen as UiScreen, ScreenHeader as UiScreenHeader } from '@/components/ui/screen';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { Stepper as UiStepper } from '@/components/ui/stepper';
import { Toast as UiToast } from '@/components/ui/toast';
import { cn } from '@/lib/utils';

function Screen({ children, centered = false }: { children: ReactNode; centered?: boolean }) {
  return (
    <UiScreen
      className={centered ? 'min-h-[78dvh] items-center justify-center text-center' : undefined}
    >
      {children}
    </UiScreen>
  );
}

function ScreenHeader({ title, onBack }: { title: string; onBack?: () => void }) {
  return <UiScreenHeader title={title} onBack={onBack} />;
}

function Card({
  children,
  flush = false,
  style,
  className,
}: {
  children: ReactNode;
  flush?: boolean;
  style?: CSSProperties;
  className?: string;
}) {
  return (
    <UiCard className={cn('gap-0', flush ? 'py-0' : 'p-4', className)} style={style}>
      {children}
    </UiCard>
  );
}

type LegacyButtonVariant = 'primary' | 'ghost' | 'danger' | 'soft';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: LegacyButtonVariant;
  loading?: boolean;
}

const buttonVariants = {
  primary: 'default',
  ghost: 'outline',
  danger: 'destructive',
  soft: 'secondary',
} as const;

function Button({
  variant = 'primary',
  loading = false,
  children,
  className,
  ...props
}: ButtonProps) {
  return (
    <UiButton
      variant={buttonVariants[variant]}
      loading={loading}
      className={cn('w-full', className)}
      {...props}
    >
      {children}
    </UiButton>
  );
}

function Field({
  label,
  hint,
  error,
  children,
}: {
  label?: string;
  hint?: ReactNode;
  error?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <label className="grid gap-2 text-left">
      {label ? <span className="text-sm font-medium">{label}</span> : null}
      {children}
      {error ? (
        <span className="flex items-start gap-1.5 text-sm text-destructive" role="alert">
          <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </span>
      ) : hint ? (
        <span className="text-sm text-muted-foreground">{hint}</span>
      ) : null}
    </label>
  );
}

interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

function TextInput({ invalid = false, ...props }: TextInputProps) {
  return <Input aria-invalid={invalid || undefined} {...props} />;
}

function Note({
  tone = 'info',
  children,
}: {
  tone?: 'info' | 'warn' | 'error';
  children: ReactNode;
}) {
  return <UiNote tone={tone}>{children}</UiNote>;
}

function Segmented<Value extends string>({
  options,
  value,
  onChange,
  disabled = false,
}: {
  options: Array<{ value: Value; label: string }>;
  value: Value;
  onChange: (value: Value) => void;
  disabled?: boolean;
}) {
  return (
    <SegmentedControl
      options={options}
      value={value}
      onValueChange={onChange}
      disabled={disabled}
      label="Выбор значения"
    />
  );
}

function Stepper({
  label,
  sublabel,
  value,
  suffix = '',
  min = 1,
  max = 99,
  step = 1,
  onChange,
  disabled = false,
}: {
  label: string;
  sublabel?: string;
  value: number;
  suffix?: string;
  min?: number;
  max?: number;
  step?: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}) {
  return (
    <UiStepper
      label={label}
      description={sublabel}
      value={value}
      suffix={suffix}
      min={min}
      max={max}
      step={step}
      onValueChange={onChange}
      disabled={disabled}
    />
  );
}

function BrandSpinner() {
  return <UiBrandSpinner />;
}

function Avatar({ label, seed }: { label: string; seed: number }) {
  return <MemberAvatar label={label} seed={seed} />;
}

function Toast({
  message,
  tone = 'info',
}: {
  message: ReactNode;
  tone?: 'info' | 'success' | 'error';
}) {
  return (
    <UiToast tone={tone} className="bottom-[calc(6.5rem+var(--uk-safe-bottom))]">
      {message}
    </UiToast>
  );
}

function BottomSheet({ onClose, children }: { onClose?: () => void; children: ReactNode }) {
  return (
    <Drawer
      open
      onOpenChange={(open) => {
        if (!open) onClose?.();
      }}
      showSwipeHandle
    >
      <DrawerContent className="mx-auto max-w-[30rem] border-border bg-popover/95 backdrop-blur-2xl">
        <DrawerTitle className="sr-only">Дополнительные действия</DrawerTitle>
        <DrawerDescription className="sr-only">
          Проверьте данные и выполните нужное действие.
        </DrawerDescription>
        <div className="min-h-0 overflow-y-auto p-4 pb-[calc(1rem+var(--uk-safe-bottom))]">
          {children}
        </div>
      </DrawerContent>
    </Drawer>
  );
}

export {
  Avatar,
  BottomSheet,
  BrandSpinner,
  Button,
  Card,
  Field,
  Note,
  Screen,
  ScreenHeader,
  Segmented,
  Stepper,
  TextInput,
  Toast,
};
