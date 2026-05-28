import {
  init as initSDK,
  isTMA,
  miniApp,
  setDebug,
  themeParams,
  viewport,
} from '@telegram-apps/sdk-react';

import { config } from '@/config/env';

/**
 * Initialise the Telegram Mini Apps SDK and mount the components the app shell
 * relies on (mini app chrome, theme params, viewport).
 *
 * Safe to call outside Telegram: when the runtime is missing we skip mounting
 * so the app can still boot in a plain browser for local development.
 *
 * @returns `true` when running inside the Telegram runtime, `false` otherwise.
 */
export function initTelegram(): boolean {
  setDebug(config.telegramDebug);

  // `isTMA` is cheap and never throws; bail out early outside Telegram.
  if (!isTMA()) {
    return false;
  }

  try {
    initSDK();

    if (miniApp.mountSync.isAvailable()) {
      miniApp.mountSync();
      miniApp.bindCssVars();
    }

    if (themeParams.mountSync.isAvailable()) {
      themeParams.mountSync();
      themeParams.bindCssVars();
    }

    if (viewport.mount.isAvailable()) {
      void viewport.mount().then(() => {
        viewport.bindCssVars();
        if (viewport.expand.isAvailable()) {
          viewport.expand();
        }
      });
    }

    return true;
  } catch (error) {
    // Never let SDK setup crash the whole app; degrade gracefully.
    if (config.telegramDebug) {
      console.error('[telegram] SDK initialisation failed', error);
    }
    return false;
  }
}
