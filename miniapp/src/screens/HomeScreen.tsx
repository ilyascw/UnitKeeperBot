import { Cell, List, Section } from '@telegram-apps/telegram-ui';
import { Navigate } from 'react-router-dom';

import { useCurrentGroup } from '@/api/queries';
import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';
import { Loader } from '@/components/Loader';
import { routes } from '@/routes/paths';

/**
 * Foundation dashboard. For Issue 01 this only proves the auth + group-read
 * wiring end to end: it greets the signed-in user and renders the current
 * group, or redirects to onboarding when there is no group yet. Real dashboard
 * widgets (sprint summary, balance, approvals) arrive in later issues.
 */
export function HomeScreen() {
  const { context } = useAuth();
  const { data: group, isPending, isError, error, refetch } = useCurrentGroup();

  if (isPending) {
    return <Loader label="Loading your group…" />;
  }

  if (isError) {
    return (
      <ErrorState description={error.message} onRetry={() => void refetch()} />
    );
  }

  if (group === null) {
    return <Navigate to={routes.onboarding} replace />;
  }

  const user = context?.user;
  const displayName = user?.first_name ?? user?.username ?? 'there';

  return (
    <List>
      <Section header={`Hi, ${displayName}`}>
        <Cell subtitle="Current group">{group.name}</Cell>
      </Section>
      <Section header="Sprint">
        <Cell subtitle="Starts on">{group.sprint_start_weekday}</Cell>
        <Cell subtitle="Duration">{group.sprint_duration_days} days</Cell>
        <Cell subtitle="Ends at">
          {new Date(group.sprint_ends_at).toLocaleString()}
        </Cell>
      </Section>
      <Section header="Members" footer="More screens land in upcoming issues.">
        {group.members.map((member) => (
          <Cell
            key={member.user_id}
            subtitle={member.is_owner ? 'Owner' : `Weight ${member.weight_percent}%`}
          >
            {member.first_name ?? member.username ?? `User ${member.user_id}`}
          </Cell>
        ))}
      </Section>
    </List>
  );
}
