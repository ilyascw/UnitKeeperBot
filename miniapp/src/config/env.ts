/**
 * Centralised, validated access to build-time configuration.
 *
 * Everything that reads `import.meta.env` should go through here so the rest of
 * the app depends on a typed, normalised config object instead of raw strings.
 */

function readBoolean(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined) return fallback;
  return value === 'true' || value === '1';
}

function readString(value: string | undefined, fallback: string): string {
  const trimmed = value?.trim();
  return trimmed ? trimmed : fallback;
}

export interface AppConfig {
  /** Backend API base URL, already including the `/api/v1` prefix. */
  apiBaseUrl: string;
  /** Verbose Telegram SDK logging. */
  telegramDebug: boolean;
  /** Whether we are running a production build. */
  isProduction: boolean;
  /**
   * Development-only raw init data used when the app runs outside Telegram.
   * Always empty in production builds.
   */
  devInitData: string;
}

export const config: AppConfig = {
  apiBaseUrl: readString(import.meta.env.VITE_API_BASE_URL, '/api/v1').replace(/\/+$/, ''),
  telegramDebug: readBoolean(import.meta.env.VITE_TELEGRAM_DEBUG, false),
  isProduction: import.meta.env.PROD,
  devInitData: import.meta.env.PROD ? '' : readString(import.meta.env.VITE_DEV_INIT_DATA, ''),
};
