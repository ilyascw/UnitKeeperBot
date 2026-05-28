import { AppRoot } from '@telegram-apps/telegram-ui';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useMemo } from 'react';
import { HashRouter } from 'react-router-dom';

import { ApiError } from '@/api/client';
import { AuthGate } from '@/auth/AuthGate';
import { AuthProvider } from '@/auth/AuthProvider';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { useAppearance } from '@/telegram/useAppearance';

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
  const appearance = useAppearance();
  const queryClient = useMemo(createQueryClient, []);

  return (
    <AppRoot appearance={appearance}>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <AuthGate>
              <HashRouter>
                <AppRoutes />
              </HashRouter>
            </AuthGate>
          </AuthProvider>
        </QueryClientProvider>
      </ErrorBoundary>
    </AppRoot>
  );
}
