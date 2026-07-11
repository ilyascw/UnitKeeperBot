import type { ReactNode } from 'react';

/**
 * Root shell for every screen. Owns the dark liquid-glass backdrop and a
 * constrained mobile-first column. Individual screens render their own
 * `Screen` container from the UI kit.
 */
export function AppLayout({ children }: { children: ReactNode }) {
  return <div className="uk-app">{children}</div>;
}
