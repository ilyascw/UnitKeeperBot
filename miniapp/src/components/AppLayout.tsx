import type { ReactNode } from 'react';

/**
 * Shared layout container for every screen. Provides a constrained,
 * mobile-first column that fills the Telegram viewport height and uses the
 * Telegram theme background. Screens render their own `List`/`Section` content.
 */
export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--tg-theme-secondary-bg-color, var(--tgui--secondary_bg_color))',
      }}
    >
      <main style={{ flex: 1, width: '100%', maxWidth: 640, marginInline: 'auto' }}>{children}</main>
    </div>
  );
}
