import { Route, Routes } from 'react-router-dom';

import { AppLayout } from '@/components/AppLayout';
import { HomeScreen } from '@/screens/HomeScreen';
import { NotFoundScreen } from '@/screens/NotFoundScreen';
import { OnboardingScreen } from '@/screens/OnboardingScreen';

import { routes } from './paths';

/**
 * Application route table. Every screen renders inside the shared `AppLayout`
 * shell. New screens from later issues are added here.
 */
export function AppRoutes() {
  return (
    <AppLayout>
      <Routes>
        <Route path={routes.home} element={<HomeScreen />} />
        <Route path={routes.onboarding} element={<OnboardingScreen />} />
        <Route path="*" element={<NotFoundScreen />} />
      </Routes>
    </AppLayout>
  );
}
