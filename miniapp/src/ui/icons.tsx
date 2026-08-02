import type { SVGProps } from 'react';

/**
 * Line-icon set used across the liquid-glass UI. Icons inherit `currentColor`
 * for the stroke and default to a 24px box; pass `width`/`height`/`style` to
 * resize or recolour at the call site.
 */
type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function base({ size = 24, ...props }: IconProps) {
  return {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 2,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    ...props,
  };
}

export const LogoIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 3l7 3v5c0 5-3 8.5-7 10-4-1.5-7-5-7-10V6l7-3z" />
    <path d="M9 12l2 2 4-4" />
  </svg>
);

export const BackIcon = (p: IconProps) => (
  <svg {...base(p)} strokeWidth={2.2}>
    <path d="M20 12H4" />
    <path d="M10 6l-6 6 6 6" />
  </svg>
);

export const ChevronIcon = (p: IconProps) => (
  <svg {...base(p)} strokeWidth={2.4}>
    <path d="M9 5l6 7-6 7" />
  </svg>
);

export const PlusIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <rect x="4" y="4" width="16" height="16" rx="5" />
    <path d="M12 8v8M8 12h8" />
  </svg>
);

export const PencilIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M4 20l1-4L16 5l3 3L8 19l-4 1z" />
    <path d="M14 7l3 3" />
  </svg>
);

export const TrashIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M5 7h14" />
    <path d="M9 7V5a2 2 0 012-2h2a2 2 0 012 2v2" />
    <rect x="6" y="7" width="12" height="13" rx="2" />
    <path d="M10 11v6M14 11v6" />
  </svg>
);

export const EnterIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M14 4h4a2 2 0 012 2v12a2 2 0 01-2 2h-4" />
    <path d="M3 12h13" />
    <path d="M12 8l4 4-4 4" />
  </svg>
);

export const InfoIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <circle cx="12" cy="8" r="1" fill="currentColor" stroke="none" />
    <path d="M10 11h2v6M10 17h4" />
  </svg>
);

export const AlertIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 3l9 9-9 9-9-9 9-9z" />
    <path d="M12 8v5M12 16h.01" />
  </svg>
);

export const ErrorIcon = (p: IconProps) => (
  <svg {...base(p)} strokeWidth={2.2}>
    <circle cx="12" cy="12" r="9" />
    <path d="M9 9l6 6M15 9l-6 6" />
  </svg>
);

export const CheckIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M8 12.5l2.5 2.5L16 9" />
  </svg>
);

export const CopyIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <rect x="3" y="3" width="12" height="12" rx="2" />
    <path d="M19 9v10a2 2 0 01-2 2H9" />
  </svg>
);

export const RefreshIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M4 12a8 8 0 0113.66-5.66L20 8" />
    <path d="M20 4v4h-4" />
    <path d="M20 12a8 8 0 01-13.66 5.66L4 16" />
    <path d="M4 20v-4h4" />
  </svg>
);

export const SettingsIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 3l7 4v10l-7 4-7-4V7l7-4z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

export const SlidersIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M6 21V10M6 6V3M12 21v-4M12 13V3M18 21v-8M18 9V3" />
    <circle cx="6" cy="12" r="2" />
    <circle cx="12" cy="15" r="2" />
    <circle cx="18" cy="11" r="2" />
  </svg>
);

export const CalendarIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <rect x="3" y="5" width="18" height="16" rx="2" />
    <path d="M3 10h18M8 3v4M16 3v4" />
    <path d="M9 15l2 2 4-4" />
  </svg>
);

export const SendIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M21 3L3 10l7 3 3 7 8-17z" />
    <path d="M10 13l4-4" />
  </svg>
);

export const LeaveIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M10 4H6a2 2 0 00-2 2v12a2 2 0 002 2h4" />
    <path d="M21 12H8" />
    <path d="M12 8l-4 4 4 4" />
  </svg>
);

export const PlaneIcon = (p: IconProps) => (
  <svg {...base(p)} strokeWidth={1.7}>
    <path d="M3 20L21 12L3 4l4 8-4 8z" />
    <path d="M7 12h9" />
  </svg>
);

export const HomeIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M4 11l8-7 8 7" />
    <path d="M6 10v10h12V10" />
    <path d="M10 20v-6h4v6" />
  </svg>
);

export const TasksIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M9 6h11M9 12h11M9 18h11" />
    <path d="M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2" />
  </svg>
);

export const ChartIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M4 20V4" />
    <path d="M4 20h16" />
    <rect x="7" y="13" width="3" height="7" rx="1" />
    <rect x="12" y="9" width="3" height="11" rx="1" />
    <rect x="17" y="5" width="3" height="15" rx="1" />
  </svg>
);

export const CoinIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v10" />
    <path d="M15 9.5c0-1.4-1.3-2-3-2s-3 .8-3 2 1.3 1.5 3 2 3 .8 3 2-1.3 2-3 2-3-.6-3-2" />
  </svg>
);

export const ClockIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 6v6l4 3" />
  </svg>
);

export const GroupIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="8" cy="8" r="3" />
    <circle cx="17" cy="8" r="3" />
    <path d="M2 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
    <path d="M14 14.5c2.8.3 5 2.7 5 5.5" />
  </svg>
);
