import {
  init as initSDK,
  isTMA,
  miniApp,
  setDebug,
  themeParams,
  viewport,
} from '@tma.js/sdk-react';

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

    if (miniApp.mount.isAvailable()) {
      miniApp.mount();
      miniApp.bindCssVars();
    }

    if (themeParams.mount.isAvailable()) {
      themeParams.mount();
      themeParams.bindCssVars();
    }

    if (viewport.mount.isAvailable()) {
      void viewport.mount().then(() => {
        viewport.bindCssVars();
        // Expand to the full available height first (always supported), then
        // request true fullscreen on clients that support Bot API 8.0. The
        // safe-area CSS vars bound above keep our chrome clear of Telegram's
        // overlay controls when fullscreen is granted.
        if (viewport.expand.isAvailable()) {
          viewport.expand();
        }
        if (viewport.requestFullscreen.isAvailable()) {
          viewport.requestFullscreen().catch(() => {
            // Fullscreen can be refused (unsupported client, user setting);
            // the expanded viewport above is a fine fallback.
          });
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
