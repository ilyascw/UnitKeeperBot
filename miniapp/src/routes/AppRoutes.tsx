import { Outlet, Route, Routes } from 'react-router-dom';

import { AppLayout } from '@/components/AppLayout';
import { TabBar } from '@/components/TabBar';
import { BalanceScreen } from '@/screens/BalanceScreen';
import { CreateGroupScreen } from '@/screens/CreateGroupScreen';
import { DashboardScreen } from '@/screens/DashboardScreen';
import { GroupScreen } from '@/screens/GroupScreen';
import { GroupSettingsScreen } from '@/screens/GroupSettingsScreen';
import { GroupWeightsScreen } from '@/screens/GroupWeightsScreen';
import { HomeScreen } from '@/screens/HomeScreen';
import { JoinGroupScreen } from '@/screens/JoinGroupScreen';
import { NotFoundScreen } from '@/screens/NotFoundScreen';
import { OnboardingScreen } from '@/screens/OnboardingScreen';
import { ProgressScreen } from '@/screens/ProgressScreen';
import { TasksScreen } from '@/screens/TasksScreen';
import { TaskLogsScreen } from '@/screens/TaskLogsScreen';
import { TransferScreen } from '@/screens/TransferScreen';

import { routes } from './paths';

/**
 * Layout for the five in-group sections: the active section renders in the
 * outlet with the shared bottom tab bar fixed beneath it.
 */
function TabbedLayout() {
  return (
    <div className="uk-tab-scope">
      <Outlet />
      <TabBar />
    </div>
  );
}

/**
 * Application route table. Every screen renders inside the shared `AppLayout`
 * shell. The daily-work sections sit under `TabbedLayout` so they share the
 * bottom navigation; onboarding and group sub-screens stand alone.
 */
export function AppRoutes() {
  return (
    <AppLayout>
      <Routes>
        <Route path={routes.home} element={<HomeScreen />} />
        <Route path={routes.onboarding} element={<OnboardingScreen />} />
        <Route path={routes.onboardingCreate} element={<CreateGroupScreen />} />
        <Route path={routes.onboardingJoin} element={<JoinGroupScreen />} />

        <Route element={<TabbedLayout />}>
          <Route path={routes.dashboard} element={<DashboardScreen />} />
          <Route path={routes.tasks} element={<TasksScreen />} />
          <Route path={routes.progress} element={<ProgressScreen />} />
          <Route path={routes.balance} element={<BalanceScreen />} />
          <Route path={routes.group} element={<GroupScreen />} />
        </Route>

        <Route path={routes.groupSettings} element={<GroupSettingsScreen />} />
        <Route path={routes.groupWeights} element={<GroupWeightsScreen />} />
        <Route path={routes.balanceTransfer} element={<TransferScreen />} />
        <Route path={routes.taskLogs} element={<TaskLogsScreen />} />
        <Route path="*" element={<NotFoundScreen />} />
      </Routes>
    </AppLayout>
  );
}
