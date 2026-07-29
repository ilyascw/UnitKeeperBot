import { retrieveRawInitData } from '@tma.js/sdk-react';

import { config } from '@/config/env';

/**
 * Returns the raw Telegram init data string used to authenticate against the
 * backend, or `null` when it cannot be resolved.
 *
 * Resolution order:
 *  1. The Telegram SDK (`retrieveRawInitData`) — the canonical source inside
 *     the Telegram in-app browser.
 *  2. `window.Telegram.WebApp.initData` — a defensive fallback in case the SDK
 *     could not be initialised but the legacy runtime is present.
 *  3. `VITE_DEV_INIT_DATA` — a development-only escape hatch so the app can be
 *     run and debugged in a regular browser tab (never set in production).
 */
export function resolveRawInitData(): string | null {
  try {
    const raw = retrieveRawInitData();
    if (raw) return raw;
  } catch {
    // SDK not initialised or running outside Telegram — fall through.
  }

  const legacyRaw = window.Telegram?.WebApp?.initData;
  if (legacyRaw) return legacyRaw;

  if (config.devInitData) return config.devInitData;

  return null;
}

/** Whether the app is currently running inside the Telegram runtime. */
export function isTelegramEnvironment(): boolean {
  return Boolean(window.Telegram?.WebApp?.initData);
}
