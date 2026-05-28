/**
 * Minimal typings for the legacy `window.Telegram.WebApp` object injected by
 * `telegram-web-app.js`. We only declare the few fields we read directly; the
 * `@telegram-apps/sdk-react` package is the primary, fully-typed integration.
 */
interface TelegramWebApp {
  initData: string;
  colorScheme?: 'light' | 'dark';
  ready?: () => void;
  expand?: () => void;
}

interface TelegramRuntime {
  WebApp?: TelegramWebApp;
}

interface Window {
  Telegram?: TelegramRuntime;
}
