import { Route, Routes } from 'react-router-dom';

import { AppLayout } from '@/components/AppLayout';
import { CreateGroupScreen } from '@/screens/CreateGroupScreen';
import { GroupScreen } from '@/screens/GroupScreen';
import { GroupSettingsScreen } from '@/screens/GroupSettingsScreen';
import { GroupWeightsScreen } from '@/screens/GroupWeightsScreen';
import { HomeScreen } from '@/screens/HomeScreen';
import { JoinGroupScreen } from '@/screens/JoinGroupScreen';
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
        <Route path={routes.onboardingCreate} element={<CreateGroupScreen />} />
        <Route path={routes.onboardingJoin} element={<JoinGroupScreen />} />
        <Route path={routes.group} element={<GroupScreen />} />
        <Route path={routes.groupSettings} element={<GroupSettingsScreen />} />
        <Route path={routes.groupWeights} element={<GroupWeightsScreen />} />
        <Route path="*" element={<NotFoundScreen />} />
      </Routes>
    </AppLayout>
  );
}
