import { Navigate } from 'react-router-dom';

import { useCurrentGroup } from '@/api/queries';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';

/**
 * Root entry point. Routes the signed-in user to onboarding when they have no
 * group, otherwise to the group surface. Screen content lives in dedicated
 * routes so deep links and back/forward navigation work cleanly.
 */
export function HomeScreen() {
  const { data: group, isPending, isError, error, refetch } = useCurrentGroup();

  if (isPending) {
    return <Loader label="Loading your group…" />;
  }

  if (isError) {
    return <ErrorState description={error.message} onRetry={() => void refetch()} />;
  }

  return <Navigate to={group === null ? routes.onboarding : routes.group} replace />;
}
