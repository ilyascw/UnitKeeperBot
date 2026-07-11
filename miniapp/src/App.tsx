import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useMemo } from 'react';
import { BrowserRouter } from 'react-router-dom';

import { ApiError } from '@/api/client';
import { AuthGate } from '@/auth/AuthGate';
import { AuthProvider } from '@/auth/AuthProvider';
import { ErrorBoundary } from '@/components/ErrorBoundary';

import { AppRoutes } from './routes/AppRoutes';

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: (failureCount, error) => {
          // Don't retry auth/not-found errors; they won't fix themselves.
          if (error instanceof ApiError && (error.isAuthError || error.isNotFound)) {
            return false;
          }
          return failureCount < 2;
        },
      },
    },
  });
}

export function App() {
  const queryClient = useMemo(createQueryClient, []);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <AuthGate>
            {/*
             * BrowserRouter (path-based), not HashRouter: Telegram appends its
             * launch params to the URL hash (`#tgWebAppData=...`). A hash router
             * would read that as a route and fall through to the 404 screen.
             * Path routing ignores the hash, leaving it for the Telegram SDK.
             */}
            <BrowserRouter>
              <AppRoutes />
            </BrowserRouter>
          </AuthGate>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
