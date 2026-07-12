import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
} from 'react';

import { avatarGradient } from './avatar';
import { BackIcon, InfoIcon, AlertIcon, ErrorIcon, LogoIcon } from './icons';

/* ---------------- Screen shell ---------------- */

export function Screen({
  children,
  centered = false,
}: {
  children: ReactNode;
  centered?: boolean;
}) {
  return <div className={`uk-screen${centered ? ' uk-screen--centered' : ''}`}>{children}</div>;
}

export function ScreenHeader({
  title,
  onBack,
}: {
  title: string;
  onBack?: () => void;
}) {
  return (
    <div className="uk-header">
      {onBack ? (
        <button type="button" className="uk-back" aria-label="Назад" onClick={onBack}>
          <BackIcon size={24} />
        </button>
      ) : null}
      <div className="uk-header__title">{title}</div>
    </div>
  );
}

/* ---------------- Card ---------------- */

export function Card({
  children,
  flush = false,
  style,
}: {
  children: ReactNode;
  flush?: boolean;
  style?: React.CSSProperties;
}) {
  return (
    <div className={`uk-card${flush ? ' uk-card--flush' : ''}`} style={style}>
      {children}
    </div>
  );
}

/* ---------------- Button ---------------- */

type Variant = 'primary' | 'ghost' | 'danger' | 'soft';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

export function Button({
  variant = 'primary',
  loading = false,
  disabled,
  children,
  className,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`uk-btn uk-btn--${variant}${className ? ` ${className}` : ''}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? <span className="uk-btn-spinner" aria-hidden /> : null}
      {children}
    </button>
  );
}

/* ---------------- Field ---------------- */

interface FieldProps {
  label?: string;
  hint?: ReactNode;
  error?: ReactNode;
  children?: ReactNode;
}

export function Field({ label, hint, error, children }: FieldProps) {
  return (
    <label className="uk-field">
      {label ? <span className="uk-field__label">{label}</span> : null}
      {children}
      {hint ? <span className="uk-field__hint">{hint}</span> : null}
      {error ? (
        <span className="uk-field__error">
          <ErrorIcon size={15} strokeWidth={2.2} />
          {error}
        </span>
      ) : null}
    </label>
  );
}

interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

export function TextInput({ invalid = false, className, ...rest }: TextInputProps) {
  return (
    <input
      className={`uk-input${invalid ? ' uk-input--invalid' : ''}${className ? ` ${className}` : ''}`}
      {...rest}
    />
  );
}

/* ---------------- Note ---------------- */

export function Note({
  tone = 'info',
  children,
}: {
  tone?: 'info' | 'warn' | 'error';
  children: ReactNode;
}) {
  const Icon = tone === 'warn' ? AlertIcon : tone === 'error' ? ErrorIcon : InfoIcon;
  return (
    <div className={`uk-note uk-note--${tone}`}>
      <Icon size={17} />
      <div>{children}</div>
    </div>
  );
}

/* ---------------- Segmented (weekday picker) ---------------- */

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  disabled = false,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
  disabled?: boolean;
}) {
  return (
    <div className="uk-segmented">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          disabled={disabled}
          onClick={() => onChange(opt.value)}
          className={`uk-segmented__item${
            opt.value === value ? ' uk-segmented__item--active' : ''
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

/* ---------------- Stepper ---------------- */

export function Stepper({
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
    <div className="uk-stepper">
      <div>
        <div style={{ font: "600 15px 'Manrope'" }}>{label}</div>
        {sublabel ? (
          <div style={{ font: "400 12px 'Manrope'", color: 'var(--uk-ink-55)' }}>{sublabel}</div>
        ) : null}
      </div>
      <div className="uk-stepper__controls">
        <button
          type="button"
          className="uk-stepper__btn uk-stepper__btn--dec"
          disabled={disabled || value <= min}
          onClick={() => onChange(Math.max(min, value - step))}
          aria-label="Меньше"
        >
          −
        </button>
        <span className="uk-stepper__value">
          {value} {suffix}
        </span>
        <button
          type="button"
          className="uk-stepper__btn uk-stepper__btn--inc"
          disabled={disabled || value >= max}
          onClick={() => onChange(Math.min(max, value + step))}
          aria-label="Больше"
        >
          +
        </button>
      </div>
    </div>
  );
}

/* ---------------- Spinner + Loader ---------------- */

export function BrandSpinner() {
  return (
    <div className="uk-spinner">
      <div className="uk-spinner__ring" />
      <div className="uk-logo" style={{ width: 64, height: 64 }}>
        <LogoIcon size={30} style={{ color: 'var(--uk-on-accent)' }} strokeWidth={2.2} />
      </div>
    </div>
  );
}

/* ---------------- Avatar ---------------- */

export function Avatar({ label, seed }: { label: string; seed: number }) {
  return (
    <div className="uk-avatar" style={{ background: avatarGradient(seed) }}>
      {label.slice(0, 1).toUpperCase()}
    </div>
  );
}

/* ---------------- Bottom sheet ---------------- */

export function Toast({
  message,
  tone = 'info',
}: {
  message: ReactNode;
  tone?: 'info' | 'success' | 'error';
}) {
  return (
    <div className={`uk-toast uk-toast--${tone}`} role="status" aria-live="polite">
      {message}
    </div>
  );
}

export function BottomSheet({
  onClose,
  children,
}: {
  onClose?: () => void;
  children: ReactNode;
}) {
  return (
    <div
      className="uk-scrim"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose?.();
      }}
    >
      <div className="uk-sheet" role="dialog" aria-modal="true">
        <div className="uk-sheet__grip" />
        {children}
      </div>
    </div>
  );
}
