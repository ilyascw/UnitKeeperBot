import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import '@telegram-apps/telegram-ui/dist/styles.css';
import './index.css';

import { App } from './App';
import { initTelegram } from './telegram/init';

// Initialise the Telegram SDK before the first render so theme params and
// launch data are available synchronously to the component tree.
initTelegram();

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element #root not found');
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
