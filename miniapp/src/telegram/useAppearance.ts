import { miniApp, useSignal } from '@telegram-apps/sdk-react';
import { useEffect, useState } from 'react';

export type Appearance = 'light' | 'dark';

/**
 * Resolves the current Telegram colour scheme so the UI Kit `AppRoot` can match
 * the surrounding Telegram theme. Falls back to the legacy `colorScheme` field
 * and finally to `light` when nothing is available.
 */
export function useAppearance(): Appearance {
  // `miniApp.isDark` is a reactive signal; `useSignal` re-renders on change.
  // Guard the read so it works even when the mini app component is unmounted
  // (e.g. running outside Telegram during development).
  const isDark = useSignal(miniApp.isDark);

  const [legacyScheme, setLegacyScheme] = useState<Appearance | null>(
    () => window.Telegram?.WebApp?.colorScheme ?? null,
  );

  useEffect(() => {
    setLegacyScheme(window.Telegram?.WebApp?.colorScheme ?? null);
  }, []);

  if (typeof isDark === 'boolean') {
    return isDark ? 'dark' : 'light';
  }

  return legacyScheme ?? 'light';
}
