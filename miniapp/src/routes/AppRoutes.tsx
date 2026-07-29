import type { ReactNode } from 'react';
import { Route, Switch } from 'wouter';

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

function TabbedLayout({ children }: { children: ReactNode }) {
  return (
    <div className="uk-tab-scope">
      {children}
      <TabBar />
    </div>
  );
}

export function AppRoutes() {
  return (
    <AppLayout>
      <Switch>
        <Route path={routes.home} component={HomeScreen} />
        <Route path={routes.onboarding} component={OnboardingScreen} />
        <Route path={routes.onboardingCreate} component={CreateGroupScreen} />
        <Route path={routes.onboardingJoin} component={JoinGroupScreen} />

        <Route path={routes.dashboard}>
          <TabbedLayout>
            <DashboardScreen />
          </TabbedLayout>
        </Route>
        <Route path={routes.tasks}>
          <TabbedLayout>
            <TasksScreen />
          </TabbedLayout>
        </Route>
        <Route path={routes.progress}>
          <TabbedLayout>
            <ProgressScreen />
          </TabbedLayout>
        </Route>
        <Route path={routes.balance}>
          <TabbedLayout>
            <BalanceScreen />
          </TabbedLayout>
        </Route>
        <Route path={routes.group}>
          <TabbedLayout>
            <GroupScreen />
          </TabbedLayout>
        </Route>

        <Route path={routes.groupSettings} component={GroupSettingsScreen} />
        <Route path={routes.groupWeights} component={GroupWeightsScreen} />
        <Route path={routes.balanceTransfer} component={TransferScreen} />
        <Route path={routes.taskLogs} component={TaskLogsScreen} />
        <Route component={NotFoundScreen} />
      </Switch>
    </AppLayout>
  );
}
